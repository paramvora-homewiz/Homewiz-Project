# app/ai_services/gemini_sql_generator.py

import json
import re
from typing import Dict, Any, Optional, List
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.db.database_schema import get_schema_for_sql_generation, DATABASE_SCHEMA

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
        
        # Get schema
        schema_text = get_schema_for_sql_generation()
        
        # Build prompt
        prompt = self._build_prompt(
            filters, query_type, tables, joins, 
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
        """Build comprehensive prompt for SQL generation."""
        
        prompt = f"""
You are an expert PostgreSQL SQL generator for a property management system.

## Database Schema
{schema_text}

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

## SQL Generation Rules:

1. **Filter Mapping**:
   - price_min/max → private_room_rent
   - view_types → view column (use ILIKE with OR for multiple) ("Limited View", "Street View", "Courtyard")
   - bathroom_type → exact match
   - bed_size → exact match
   - room_type: "private" → maximum_people_in_room = 1, "shared" → maximum_people_in_room > 1
   - amenities → map to boolean columns (mini_fridge, sink, work_desk, etc.)
   - building features → wifi_included, laundry_onsite, fitness_area, etc.
   - location/area → area column (use ILIKE) ("SOMA", "North Beach")
   - status filters → exact match in Title Case ("Available", "Occupied", "Maintenance")

2. **Join Rules**:
   - Always use table aliases (r for rooms, b for buildings, t for tenants, l for leads, o for operators)
   - rooms ↔ buildings: via building_id
   - tenants ↔ rooms: via room_id
   - leads ↔ rooms: via selected_room_id
   
3. **Query Type Specific**:
   - "search": Return detailed records with all relevant columns
   - "analytics": Focus on aggregated metrics
   - "aggregation": Must include GROUP BY if aggregations present

4. **Important Data Type Considerations**:
   - parking_info is TEXT column, NOT JSON - use ILIKE for text search
   - rooms_interested in leads table is JSONB
   - Most date fields are stored as TEXT
   - Status values are Title Case, not uppercase
   - Boolean columns use TRUE/FALSE (PostgreSQL style)

5. **Avoid These Common Errors**:
   - Don't use json functions on TEXT columns
   - Don't assume uppercase for status values
   - Don't use = for text searches on descriptive fields, use ILIKE

## Response Format:
Return ONLY a valid JSON object:
{{
    "sql": "Complete SQL query here",
    "explanation": "Brief explanation of what the query does",
    "tables_used": ["table1", "table2"],
    "joins_applied": ["description of joins"],
    "filters_applied": ["description of filters"],
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


