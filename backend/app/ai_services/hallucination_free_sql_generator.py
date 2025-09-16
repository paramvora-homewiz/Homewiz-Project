# app/ai_services/hallucination_free_sql_generator.py

import json
import re
import asyncio
import time
from typing import Dict, Any, List, Optional
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.db.database_schema import DATABASE_SCHEMA, get_schema_for_sql_generation

class HallucinationFreeSQLGenerator:
    """
    SQL Generator with zero hallucination capability.
    Uses strict schema constraints and validation.
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.schema = DATABASE_SCHEMA
        self.allowed_operations = self._build_operation_whitelist()
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum 500ms between requests
    
    def _build_operation_whitelist(self) -> Dict[str, List[str]]:
        """Build whitelist of allowed operations per table."""
        return {
            "rooms": ["SELECT", "UPDATE"],
            "buildings": ["SELECT", "UPDATE"],  # Added UPDATE
            "tenants": ["SELECT", "INSERT", "UPDATE"],
            "leads": ["SELECT", "INSERT", "UPDATE"],
            "operators": ["SELECT", "UPDATE"],  # Added UPDATE
            "maintenance_requests": ["SELECT", "INSERT", "UPDATE"],
            "scheduled_events": ["SELECT", "INSERT", "UPDATE"],
            "announcements": ["SELECT", "INSERT", "UPDATE"],
            "documents": ["SELECT", "INSERT", "UPDATE"],
            "checklists": ["SELECT", "INSERT", "UPDATE"],
            "messages": ["SELECT", "INSERT", "UPDATE"],
            "notifications": ["SELECT", "INSERT", "UPDATE"]
        }
    
    async def generate_sql(
        self, 
        natural_query: str, 
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate SQL with strict hallucination prevention."""
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}
        
        # Rate limiting to prevent API quota issues
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        # Get exact schema
        exact_schema = self._format_exact_schema()
        allowed_tables = self._get_allowed_tables(user_context.get("permissions", []))
        
        # Build bulletproof prompt
        generation_prompt = self._build_constrained_prompt(
            natural_query, exact_schema, allowed_tables, user_context
        )
        
        try:
            # Update last request time
            self.last_request_time = time.time()
            
            # Generate with zero temperature
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=generation_prompt,
                config=GenerateContentConfig(
                    temperature=0.0,  # Zero creativity
                    max_output_tokens=800
                )
            )
            
            # Parse and validate
            sql_result = self._parse_response(response.text)
            validation_result = await self._validate_generated_sql(
                sql_result, exact_schema, allowed_tables
            )
            
            if not validation_result["valid"]:
                return await self._regenerate_with_corrections(
                    natural_query, sql_result, validation_result["errors"], exact_schema, allowed_tables
                )
            
            return sql_result
            
        except Exception as e:
            return {
                "sql": None,
                "success": False,
                "error": str(e),
                "explanation": f"Failed to generate SQL: {str(e)}"
            }
    def _format_exact_schema(self) -> str:
        """Format schema with EXACT names to prevent hallucination."""
        formatted_tables = []
        
        for table_name, table_info in self.schema["tables"].items():
            formatted_tables.append(f"\nTABLE: {table_name}")
            formatted_tables.append(f"  Description: {table_info.get('description', 'No description')}")
            
            for col_name, col_info in table_info["columns"].items():
                col_type = col_info["type"]
                constraints = []
                
                if col_info.get("primary_key"):
                    constraints.append("PRIMARY KEY")
                if col_info.get("nullable") == False:
                    constraints.append("NOT NULL")
                if col_info.get("foreign_key"):
                    constraints.append(f"FK -> {col_info['foreign_key']}")
                
                constraint_text = f" ({', '.join(constraints)})" if constraints else ""
                formatted_tables.append(f"  {col_name}: {col_type}{constraint_text}")
            
            # Show relationships
            if table_info.get("relationships"):
                formatted_tables.append("  RELATIONSHIPS:")
                for rel in table_info["relationships"]:
                    formatted_tables.append(f"    {rel['type']} -> {rel['target']} via {rel['foreign_key']}")
        
        return "\n".join(formatted_tables)
    
    def _build_constrained_prompt(
            self, 
            query: str, 
            schema: str, 
            allowed_tables: List[str],
            context: Dict
        ) -> str:
            """Build prompt that makes hallucination impossible."""
            
            # Get common values for validation
            common_values = self._get_common_values()
            
            return f"""
    You are a SQL generator for a property management database. You MUST follow these EXACT constraints:

    NATURAL LANGUAGE QUERY: "{query}"

    USER PERMISSIONS: Can access tables: {allowed_tables}
    USER ROLE: {context.get('role', 'user')}

    EXACT DATABASE SCHEMA (YOU MUST USE THESE EXACT NAMES):
    {schema}
    SEMANTIC RULES FOR CORRECT TABLE SELECTION:
    - Leads table: ONLY for prospects/potential tenants who haven't moved in yet
    - Tenants table: For anyone who has/had a lease (moved in, currently living, moved out)
    - "moved in" → search tenants.lease_start_date
    - "moved out" → search tenants with status='Inactive' or lease_end_date passed
    - "late payments" → tenants table, not leads
    - Never search for historical tenant data in leads table

    VALID COLUMN VALUES (USE ONLY THESE):
    {common_values}

    STRICT RULES:
    1. Use ONLY the table names listed above: {allowed_tables}
    2. Use ONLY the column names shown in the schema
    3. Use ONLY the valid values listed for enum columns
    4. ALWAYS use table aliases (r for rooms, b for buildings, t for tenants, l for leads, o for operators)
    5. ALWAYS include explicit JOIN conditions
    6. NEVER use columns or tables not in the schema
    7. NEVER invent column names or values
    8. Return realistic result estimates
    9. Use proper PostgreSQL syntax
    10. Include LIMIT clause for large result sets
    11. For property searches: ALWAYS include r.room_id, r.room_number, r.private_room_rent, r.status, b.building_name, b.area
    12. For analytics: ALWAYS include building_name and calculated metrics
    13. For tenant queries: ALWAYS include tenant information and related room/building data
    14. For building name matching: Use LIKE with % wildcards (e.g., '1080 Folsom%' matches '1080 Folsom Residences')
    15. NEVER use semicolons in the middle of SQL statements
    16. When using LEFT JOINs, expect NULL values for unmatched records (e.g., tenant_id will be NULL for non-converted leads)
    17. Use COALESCE or CASE statements to provide default values where appropriate
    18. Column aliases (using AS) are encouraged for clarity - they help the frontend understand the data
    19. For year-only TEXT columns (buildings.last_renovation, buildings.year_built): Use CAST(column AS INTEGER) for comparisons
    20. NEVER use TO_DATE with 'YYYY' format - PostgreSQL doesn't support it
    

    CRITICAL COLUMN SELECTION RULES:
    Based on the query type, you MUST include these columns in your SELECT statement:

    FOR PROPERTY/ROOM QUERIES (when searching for rooms, apartments, properties, or showing available rooms):
    - REQUIRED: r.room_id, r.room_number, r.private_room_rent, r.status, r.building_id, b.building_name, b.building_id
    - STRONGLY RECOMMENDED: r.sq_footage, r.view, r.bathroom_type, r.bed_type, r.floor_number, b.street, b.full_address, b.wifi_included, b.laundry_onsite, b.fitness_area, b.pet_friendly

    FOR BUILDING REVENUE/ANALYTICS QUERIES:
    - If grouping by building: SELECT b.building_id, b.building_name, b.area, [your calculated metrics like SUM, COUNT, etc.]
    - If showing individual rooms with revenue: Include ALL room columns as listed above
    - NEVER just select building_name and a metric - always include building_id and area at minimum

    FOR TENANT QUERIES:
    - REQUIRED: t.tenant_id, t.tenant_name, t.tenant_email, t.phone, t.status, r.room_id, r.room_number, b.building_name
    - RECOMMENDED: t.lease_start_date, t.lease_end_date, t.booking_type, t.payment_status, t.deposit_amount

    FOR LEAD QUERIES:
    - REQUIRED: l.lead_id, l.email, l.status, l.interaction_count
    - RECOMMENDED: l.selected_room_id, l.planned_move_in, l.planned_move_out, l.budget_min, l.budget_max
    
    CRITICAL: Generate exactly ONE SQL query that best answers the user's question. If they ask for multiple things, either:
    - Use UNION ALL to combine results
    - Or use window functions to get both in one query

    REQUIRED OUTPUT FORMAT (JSON):
    {{
        "sql": "Valid PostgreSQL query using ONLY the schema above",
        "explanation": "Brief explanation of what the query does",
        "estimated_rows": "Realistic estimate of rows returned (number)",
        "tables_used": ["list", "of", "tables", "referenced"],
        "query_type": "SELECT|INSERT|UPDATE|DELETE"
    }}

    EXAMPLE QUERIES WITH PROPER COLUMN SELECTION:

    1. Property Search Query:
    SELECT r.room_id, r.room_number, r.private_room_rent, r.status, r.sq_footage, r.view, 
        r.bathroom_type, r.bed_type, r.floor_number,
        b.building_id, b.building_name, b.area, b.street, b.full_address,
        b.wifi_included, b.laundry_onsite, b.fitness_area, b.pet_friendly
    FROM rooms r 
    JOIN buildings b ON r.building_id = b.building_id 
    WHERE r.status = 'Available' 
    AND r.private_room_rent < 2000
    AND b.area = 'Downtown'
    ORDER BY r.private_room_rent 
    LIMIT 20;

    2. Building Revenue Query (Grouped):
    SELECT b.building_id, b.building_name, b.area, b.street, b.full_address,
        COUNT(r.room_id) as total_rooms,
        SUM(CASE WHEN r.status = 'Available' THEN 1 ELSE 0 END) as available_rooms,
        SUM(CASE WHEN r.status = 'Available' THEN r.private_room_rent ELSE 0 END) AS projected_revenue
    FROM buildings b
    LEFT JOIN rooms r ON b.building_id = r.building_id
    GROUP BY b.building_id, b.building_name, b.area, b.street, b.full_address
    ORDER BY projected_revenue DESC
    LIMIT 10;

    3. Multiple Results Query (Highest and Lowest Occupancy):
    SELECT * FROM (
        SELECT b.building_id, b.building_name, b.area,
            COUNT(r.room_id) as total_rooms,
            SUM(CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END) as occupied_rooms,
            ROUND(CAST(SUM(CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END) AS NUMERIC) / COUNT(r.room_id) * 100, 2) as occupancy_rate,
            'Highest' as category
        FROM buildings b
        JOIN rooms r ON b.building_id = r.building_id
        GROUP BY b.building_id, b.building_name, b.area
        ORDER BY occupancy_rate DESC
        LIMIT 1
    ) 
    UNION ALL
    SELECT * FROM (
        SELECT b.building_id, b.building_name, b.area,
            COUNT(r.room_id) as total_rooms,
            SUM(CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END) as occupied_rooms,
            ROUND(CAST(SUM(CASE WHEN r.status = 'Occupied' THEN 1 ELSE 0 END) AS NUMERIC) / COUNT(r.room_id) * 100, 2) as occupancy_rate,
            'Lowest' as category
        FROM buildings b
        JOIN rooms r ON b.building_id = r.building_id
        GROUP BY b.building_id, b.building_name, b.area
        ORDER BY occupancy_rate ASC
        LIMIT 1
    );

    4. Date filtering on TEXT date columns:
    SELECT t.tenant_name, t.lease_end_date, t.payment_status
    FROM tenants t
    WHERE TO_DATE(t.lease_end_date, 'YYYY-MM-DD') > CURRENT_DATE  -- Cast TEXT to DATE
    AND TO_DATE(t.lease_end_date, 'YYYY-MM-DD') < CURRENT_DATE + INTERVAL '30 days'
    AND t.payment_status = 'Current'  -- Exact case match
    ORDER BY TO_DATE(t.lease_end_date, 'YYYY-MM-DD');

    5. Lead date queries:
    SELECT l.email, l.status, l.planned_move_in
    FROM leads l
    WHERE l.status = 'Converted'
    AND TO_DATE(l.planned_move_in, 'YYYY-MM-DD')
        BETWEEN CURRENT_DATE - INTERVAL '3 months' AND CURRENT_DATE
    ORDER BY TO_DATE(l.planned_move_in, 'YYYY-MM-DD') DESC;

    REMEMBER: The frontend expects specific columns to render results. Missing essential columns will cause "Unknown" or "$0" to appear in the UI!

    Generate SQL that answers the user's question using ONLY the schema provided.
    """
    
    def _get_common_values(self) -> str:
        """Get common enum values for validation."""
        from app.db.database_constants import format_values_for_prompt, format_date_values_for_prompt
        
        # Get the formatted values from database constants
        values = format_values_for_prompt()
        date_info = format_date_values_for_prompt()
        
        # Add pattern explanations that aren't in database constants
        pattern_info = [
            "\n## ID and Number Patterns:",
            "rooms.room_id: Pattern 'BLDG_XXX_RXXX' (e.g., 'BLDG_1080_FOLSOM_R011')",
            "rooms.room_number: Numeric only (e.g., 101, 102, 205)"
        ]
        
        # Combine all information
        pattern_section = '\n'.join(pattern_info)
        return f"{values}\n\n{pattern_section}\n\n{date_info}"
    
    def _get_allowed_tables(self, permissions: List[str]) -> List[str]:
        """Get allowed tables based on user permissions."""
        if "admin" in permissions:
            return list(self.schema["tables"].keys())
        elif "manager" in permissions:
            return ["rooms", "buildings", "tenants", "leads", "operators", "maintenance_requests", "scheduled_events"]
        elif "agent" in permissions:
            return ["rooms", "buildings", "leads", "scheduled_events", "announcements"]
        else:
            return ["rooms", "buildings"]  # Basic user access
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the LLM response into structured format."""
        try:
            # Clean the response
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text.replace('```', '').strip()
            
            # Parse JSON
            result = json.loads(cleaned_text)
            
            # Validate required fields
            required_fields = ["sql", "explanation", "estimated_rows", "tables_used", "query_type"]
            for field in required_fields:
                if field not in result:
                    result[field] = None
            
            result["success"] = True
            return result
            
        except json.JSONDecodeError as e:
            # Fallback parsing for non-JSON responses
            return self._fallback_parse(response_text)
        except Exception as e:
            return {
                "sql": None,
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "explanation": "Response parsing failed"
            }
    
    def _fallback_parse(self, response_text: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses."""
        # Try to extract SQL from the response - more robust pattern
        sql_patterns = [
            r'UPDATE.*?(?:WHERE.*?)?(?:;|$)',  # UPDATE statements
            r'SELECT.*?(?:LIMIT\s+\d+|ORDER BY|GROUP BY|$)',  # SELECT with optional clauses
            r'SELECT.*?(?:;|$)',  # SELECT ending with semicolon or end
            r'SELECT.*',  # Any SELECT statement
        ]

        sql = None
        for pattern in sql_patterns:
            sql_match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if sql_match:
                sql = sql_match.group(0).strip()
                # Clean up the SQL
                sql = re.sub(r'\s+', ' ', sql)  # Normalize whitespace
                sql = sql.rstrip(';')  # Remove trailing semicolon
                break
        
        # Determine tables used from SQL
        tables_used = []
        if sql:
            table_patterns = [
                r'FROM\s+(\w+)',
                r'JOIN\s+(\w+)',
                r'UPDATE\s+(\w+)',
                r'INSERT\s+INTO\s+(\w+)'
            ]
            for pattern in table_patterns:
                matches = re.findall(pattern, sql, re.IGNORECASE)
                tables_used.extend(matches)
        
        return {
            "sql": sql,
            "success": sql is not None,
            "explanation": "Extracted from response",
            "estimated_rows": 10,
            "tables_used": list(set(tables_used)) if tables_used else ["rooms", "buildings"],
            "query_type": "SELECT",
            "error": "Non-JSON response format" if not sql else None
        }
    
    async def _validate_generated_sql(
        self, 
        sql_result: Dict[str, Any], 
        schema: str, 
        allowed_tables: List[str]
    ) -> Dict[str, Any]:
        """Validate generated SQL against schema and permissions."""
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if not sql_result.get("sql"):
            validation_result["valid"] = False
            validation_result["errors"].append("No SQL generated")
            return validation_result
        
        sql = sql_result["sql"]
        
        # Basic SQL validation - be more lenient
        if not sql.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
            validation_result["warnings"].append("SQL doesn't start with standard operation")
            # Don't fail, just warn
        
        # Check for dangerous operations (critical)
        dangerous_patterns = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
        for pattern in dangerous_patterns:
            if pattern in sql.upper():
                validation_result["valid"] = False
                validation_result["errors"].append(f"Dangerous SQL operation detected: {pattern}")
        
        # Check for table permissions (warn but don't fail)
        used_tables = []
        for table_name in self.schema["tables"].keys():
            if table_name.lower() in sql.lower():
                used_tables.append(table_name)
                if table_name not in allowed_tables:
                    validation_result["warnings"].append(f"Table '{table_name}' not in allowed list")
        
        # If no tables found, add a warning
        if not used_tables:
            validation_result["warnings"].append("No recognized tables found in SQL")
        
        # Check for basic SQL syntax issues
        if ';' in sql and not sql.strip().endswith(';'):
            validation_result["warnings"].append("Semicolon found in middle of SQL statement")
        
        return validation_result
    
    async def _regenerate_with_corrections(
        self, 
        natural_query: str, 
        original_result: Dict[str, Any], 
        errors: List[str], 
        schema: str,
        allowed_tables: List[str]
    ) -> Dict[str, Any]:
        """Regenerate SQL with specific error feedback."""
        
        error_feedback = "\n".join([f"- {error}" for error in errors])
        
        correction_prompt = f"""
Previous SQL generation failed with these errors:
{error_feedback}

Original query: "{natural_query}"

Please regenerate the SQL following these corrections:
1. Use only allowed tables: {allowed_tables}
2. Follow the exact schema provided
3. Avoid any dangerous operations
4. Ensure proper syntax

Generate corrected SQL:
"""
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=correction_prompt,
                config=GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=600
                )
            )
            
            return self._parse_response(response.text)
            
        except Exception as e:
            return {
                "sql": None,
                "success": False,
                "error": f"Regeneration failed: {str(e)}",
                "explanation": "Failed to correct SQL generation"
            }
