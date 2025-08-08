# app/ai_services/gemini_sql_generator.py

import json
import re
from typing import Dict, Any, Optional, List
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.db.database_schema import get_schema_for_sql_generation, DATABASE_SCHEMA
from app.db.database_constants import format_values_for_prompt, get_column_type, get_valid_values, validate_value

class GeminiSQLGenerator:
    """
    Universal SQL generation service using Google Gemini.
    Converts filters, requirements, and query specifications into SQL.
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
    def generate_sql(
        self,
        filters: Dict[str, Any],
        query_type: str = "search",
        tables: List[str] = None,
        joins: Optional[List[Dict[str, str]]] = None,
        aggregations: Optional[List[Dict[str, str]]] = None,
        group_by: Optional[List[str]] = None,
        order_by: Optional[List[Dict[str, str]]] = None,
        limit: Optional[int] = 15
    ) -> Dict[str, Any]:
        """
        Generate SQL query based on provided specifications.
        
        Args:
            filters: Dictionary of filter conditions
            query_type: Type of query ("search", "analytics", "aggregation")
            tables: List of tables to query
            joins: List of join specifications [{"from": "table1", "to": "table2", "on": "column", "type": "INNER"}]
            aggregations: List of aggregations [{"function": "COUNT", "column": "*", "alias": "total_count"}]
            group_by: List of columns to group by
            order_by: List of order specifications [{"column": "name", "direction": "ASC"}]
            limit: Result limit
            
        Returns:
            Dictionary containing SQL query and metadata
        """
        
        # Validate filters before generating SQL
        validated_filters = self._validate_filters(filters, tables or [])
        
        # Get schema
        schema_text = get_schema_for_sql_generation()
        
        # Build prompt with validated filters
        prompt = self._build_prompt(
            validated_filters, query_type, tables, joins, 
            aggregations, group_by, order_by, limit, schema_text
        )
        
        try:
            # Generate SQL using Gemini
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=500
                )
            )
            
            # Parse response
            result = self._parse_response(response.text)
            result['original_filters'] = filters
            result['validated_filters'] = validated_filters
            result['query_specifications'] = {
                'query_type': query_type,
                'tables': tables,
                'joins': joins,
                'aggregations': aggregations,
                'group_by': group_by,
                'order_by': order_by,
                'limit': limit
            }
            
            return result
            
        except Exception as e:
            return {
                "sql": None,
                "success": False,
                "error": str(e),
                "explanation": f"Failed to generate SQL: {str(e)}"
            }
    
    def _build_prompt(
        self, filters, query_type, tables, joins, 
        aggregations, group_by, order_by, limit, schema_text
    ) -> str:
        """Build comprehensive prompt for SQL generation with valid database values."""
        
        # Get formatted valid values
        valid_values = format_values_for_prompt()
        
        prompt = f"""
You are an expert PostgreSQL SQL generator for a property management system.

## Database Schema
{schema_text}

{valid_values}

## Query Requirements

### Query Type: {query_type}

### Tables to Use:
{json.dumps(tables, indent=2) if tables else "Determine based on filters"}

### Filters to Apply:
{json.dumps(filters, indent=2)}

### Join Requirements:
{json.dumps(joins, indent=2) if joins else "Determine necessary joins based on filters and tables"}

### Aggregations:
{json.dumps(aggregations, indent=2) if aggregations else "None"}

### Group By:
{json.dumps(group_by, indent=2) if group_by else "None"}

### Order By:
{json.dumps(order_by, indent=2) if order_by else "Determine appropriate ordering"}

### Limit: {limit}

## CRITICAL SQL Generation Rules:
**COLUMN SELECTION FOR ROOM QUERIES**:
   - When joining rooms and buildings tables,
   - ONLY IF building columns are not already selected in query THEN:
        - ALWAYS select these exact columns and also other building columns that are relevant:
        - SELECT r.*, b.building_name, b.area, b.full_address, b.wifi_included, 
                b.laundry_onsite, b.fitness_area, b.pet_friendly, b.nearby_conveniences_walk, b.public_transit_info
        - This is MANDATORY for any query involving rooms table with buildings join
**COLUMN SELECTION FOR BUILDING QUERIES**:
   - SELECT b.*, 
   - When joining rooms and buildings tables, select all room columns in those buildings for users   

1. **VALUE MATCHING RULES**:
   - **Text columns with specific values**: Use EXACT values from "Valid Database Values" section
     - Example: status = 'Available' (NOT 'available' or 'AVAILABLE')
     - Example: bathroom_type = 'Private' (NOT 'private')
   - **Boolean columns**: Always use 'true' or 'false' (stored as strings in database)
     - Example: wifi_included = 'true' (NOT TRUE or true without quotes)
   - **Numeric columns**: Use numeric comparisons with ranges provided
     - Example: private_room_rent BETWEEN 1000 AND 2000
   - **Text columns without listed values**: Use ILIKE for partial matching
     - Example: building_name ILIKE '%sunset%'

2. **Filter Mapping Rules**:
   - price_min/price_max → private_room_rent (numeric comparison)
   - room_type: "private" → maximum_people_in_room = 1
   - room_type: "shared" → maximum_people_in_room > 1
   - status → MUST use exact values: 'Available', 'Occupied', 'Maintenance', 'Reserved'
   - bathroom_type → MUST use exact values: 'Private', 'Shared', 'En-Suite'
   - bed_size → MUST use exact values: 'Twin', 'Full', 'Queen', 'King', 'Bunk'
   - area → MUST use exact values from list (e.g., 'SOMA', 'North Beach')
   - Boolean filters → map to 'true'/'false' strings (e.g., building_wifi_included → wifi_included = 'true')

3. **Table Aliases** (ALWAYS USE):
   - rooms → r
   - buildings → b
   - tenants → t
   - leads → l
   - operators → o

4. **Join Rules**:
   - rooms ↔ buildings: r.building_id = b.building_id
   - tenants ↔ rooms: t.room_id = r.room_id
   - leads ↔ rooms: l.selected_room_id = r.room_id

5. **Date Handling**:
   - Date columns are stored as TEXT
   - Use ::date casting for date comparisons
   - Example: lease_start_date::date >= '2024-01-01'

6. **AVOID These Common Errors**:
   - ❌ Don't use lowercase for status/enum values
   - ❌ Don't use LIKE for columns with specific valid values
   - ❌ Don't use string 'true'/'false' for boolean columns
   - ❌ Don't forget table aliases
   - ❌ Don't use json operators on TEXT columns (parking_info is TEXT, not JSON)

7. **Query Examples**:
   - Correct: WHERE r.status = 'Available' AND b.wifi_included = 'true'
   - Wrong: WHERE r.status = 'available' AND b.wifi_included = TRUE

## Response Format:
Return ONLY a valid JSON object:
{{
    "sql": "Complete SQL query here",
    "explanation": "Brief explanation of what the query does",
    "tables_used": ["table1", "table2"],
    "joins_applied": ["description of joins"],
    "filters_applied": ["description of filters with exact values used"],
    "success": true
}}

Generate the SQL query now:
"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response to extract SQL and metadata."""
        
        try:
            # Clean response
            response_text = response_text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Ensure required fields
                result.setdefault('success', True)
                result.setdefault('error', None)
                
                # Clean SQL
                if result.get('sql'):
                    sql = result['sql'].strip()
                    sql = sql.replace('\\n', ' ')  # Remove escaped newlines
                    sql = ' '.join(sql.split())
                    if not sql.endswith(';'):
                        sql += ';'
                    result['sql'] = sql
                
                return result
            else:
                # Try to extract SQL directly
                sql_match = re.search(r'SELECT.*?(?:;|$)', response_text, re.IGNORECASE | re.DOTALL)
                if sql_match:
                    sql = sql_match.group(0).strip()
                    if not sql.endswith(';'):
                        sql += ';'
                    
                    return {
                        "sql": sql,
                        "explanation": "SQL extracted from response",
                        "tables_used": self._extract_tables(sql),
                        "success": True,
                        "error": None
                    }
                else:
                    return {
                        "sql": None,
                        "success": False,
                        "error": "No SQL found in response",
                        "explanation": "Failed to extract SQL from response"
                    }
                    
        except Exception as e:
            return {
                "sql": None,
                "success": False,
                "error": str(e),
                "explanation": f"Error parsing response: {str(e)}"
            }
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL."""
        tables = []
        
        # FROM clause
        from_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if from_match:
            tables.append(from_match.group(1))
        
        # JOIN clauses
        join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.extend(join_matches)
        
        return list(set(tables))
    
    def _validate_filters(self, filters: Dict[str, Any], tables: List[str]) -> Dict[str, Any]:
        """Validate and correct filter values before SQL generation."""
        
        validated_filters = {}
        
        for key, value in filters.items():
            # Determine table from filter key
            table = None
            column = key
            
            # Handle prefixed filters (e.g., "room_mini_fridge" -> table="rooms", column="mini_fridge")
            if key.startswith("room_"):
                table = "rooms"
                column = key[5:]  # Remove "room_" prefix
            elif key.startswith("building_"):
                table = "buildings"
                column = key[9:]  # Remove "building_" prefix
            elif key.startswith("tenant_"):
                table = "tenants"
                column = key[7:]  # Remove "tenant_" prefix
            elif key.startswith("lead_"):
                table = "leads"
                column = key[5:]  # Remove "lead_" prefix
            else:
                # Try to infer table from provided tables list
                if tables and len(tables) == 1:
                    table = tables[0]
            
            if table:
                is_valid, corrected_value = validate_value(table, column, value)
                if not is_valid and corrected_value is not None:
                    print(f"⚠️ Corrected {table}.{column}: '{value}' -> '{corrected_value}'")
                    validated_filters[key] = corrected_value
                else:
                    validated_filters[key] = value
            else:
                # Can't validate without knowing the table
                validated_filters[key] = value
        
        return validated_filters