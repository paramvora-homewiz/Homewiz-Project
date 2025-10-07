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
        
        # if user_context is None:
        #     user_context = {"permissions": ["basic"], "role": "user"}
        print(f"🔧 SQL Generator - Query: {natural_query}")
        print(f"🔧 SQL Generator - User context: {user_context}")
        print(f"🔧 SQL Generator - Permissions: {user_context.get('permissions') if user_context else 'None'}")
        # Rate limiting to prevent API quota issues
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        # Get exact schema
        exact_schema = self._format_exact_schema()
        allowed_tables = self._get_allowed_tables(user_context.get("permissions", []))
        print(f"🔧 SQL Generator - Allowed tables: {allowed_tables}")
        
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
                    # max_output_tokens=800
                )
            )
            
            # Parse and validate
            sql_result = self._parse_response(response.text)
            # if sql_result.get("sql"):
            #     categorical_validation = await self._validate_categorical_values(
            #         sql_result["sql"], sql_result
            #     )
            
            #     if not categorical_validation["valid"]:
            #         # Add validation errors to result
            #         sql_result["success"] = False
            #         sql_result["error"] = "Categorical value validation failed"
            #         sql_result["validation_errors"] = categorical_validation["errors"]
            #         sql_result["validation_score"] = categorical_validation["score"]
                    
            #         # Attempt regeneration with specific feedback
            #         return await self._regenerate_with_corrections(
            #             natural_query, 
            #             sql_result, 
            #             categorical_validation["errors"], 
            #             exact_schema, 
            #             allowed_tables
            #         )

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
        You are a SQL generator for a property management database. Generate PostgreSQL queries following these rules:

        NATURAL LANGUAGE QUERY: "{query}"
        USER PERMISSIONS: Can access tables: {allowed_tables}
        USER ROLE: {context.get('role', 'user')}

        EXACT DATABASE SCHEMA (USE THESE EXACT NAMES):
        {schema}

        VALID COLUMN VALUES (USE ONLY THESE):
        {common_values}

        CRITICAL RULES:

        1. TABLE SELECTION:
        - Tours scheduled/booked → tour_bookings (has lead_id, status='Scheduled')
            * "tours scheduled", "booked tours", "tour bookings" → tour_bookings table
            * "available tour slots", "tour availability", "open slots" → tour_availability_slots table
            * Key difference: tour_bookings has actual bookings with lead_id, tour_availability_slots has open slots
        - Available tour slots → tour_availability_slots (has is_available flag)
        - Current/past tenants → tenants table (anyone who has/had a lease)
        - Tenant Queries:
            * "current tenants", "residents", "people living" → tenants table
            * "moved in", "moved out", "lease dates" → tenants table (check lease_start_date/lease_end_date)
            * "late payments" → tenants table (check payment_status)
        - Prospects/leads → leads table (potential tenants)
            * "prospects", "interested people", "potential tenants" → leads table
            * "showings scheduled" → leads table (check status='Showing Scheduled')
        - Properties/rooms → rooms table joined with buildings
            * "available rooms", "properties", "units" → rooms table joined with buildings
            * Always join rooms with buildings for complete information

        2. COLUMN MATCHING:
        - Building names: Use ILIKE with fuzzy matching
            * Fuzzy Matching Example: WHERE building_name ILIKE '%' || REPLACE('folsom', ' ', '%') || '%'
            * Handle typos: WHERE building_name ILIKE '%folsom%' (catches 'follsom')
            * Partial match: WHERE building_name ILIKE '%1080%' (catches by number)
            * Example: User says "follsom residence" → WHERE building_name ILIKE '%folsom%' OR building_name ILIKE '%1080%'
        - Status/enum fields: Use exact match with correct case
            Example: WHERE status = 'Available' (not 'available' or 'AVAILABLE')
        - Dates stored as TEXT: Use TO_DATE() for comparisons
            Example: WHERE TO_DATE(slot_date, 'YYYY-MM-DD') >= CURRENT_DATE

        3. REQUIRED COLUMNS:
        - Property queries: Include room_id, room_number, private_room_rent, status, building_name, building_id, building_images_url
        - Analytics: Include building_id, building_name, building_images_url with aggregates
        - Always include enough columns for meaningful results

        4. JOIN PATTERNS:
        - rooms → buildings via building_id
        - tenants → rooms via room_id
        - tour_bookings → tour_availability_slots via slot_id
        - Use proper aliases: r=rooms, b=buildings, t=tenants, l=leads, tb=tour_bookings, tas=tour_availability_slots

        5. FORBIDDEN:
        - Never use columns/tables not in schema
        - Never use values not in VALID COLUMN VALUES
        - Never use DROP, TRUNCATE, ALTER, CREATE
        - Never access tables outside allowed list: {allowed_tables}
        - Never use exact match (=) for building names unless specifically requested
        - Never assume exact spelling for building names

        OUTPUT FORMAT (JSON):
        {{
            "sql": "Your PostgreSQL query here",
            "explanation": "Brief explanation",
            "estimated_rows": realistic_number,
            "tables_used": ["list", "of", "tables"],
            "query_type": "SELECT"
        }}

        EXAMPLE QUERIES WITH PROPER COLUMN SELECTION:

            1. Property Search Query:
            SELECT r.room_id, r.room_number, r.private_room_rent, r.status, r.sq_footage, r.view, 
                r.bathroom_type, r.bed_type, r.floor_number,
                b.building_id, b.building_name, b.area, b.street, b.full_address,
                b.wifi_included, b.laundry_onsite, b.fitness_area, b.pet_friendly, b.building_images_url
            FROM rooms r 
            JOIN buildings b ON r.building_id = b.building_id 
            WHERE r.status = 'Available' 
            AND r.private_room_rent < 2000
            AND b.area = 'Downtown'
            ORDER BY r.private_room_rent 
            LIMIT 20;

            2. Building Revenue Query (Grouped):
            SELECT b.building_id, b.building_name, b.area, b.street, b.full_address, b.building_images_url
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
                SELECT b.building_id, b.building_name, b.area, b.building_images_url
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
                SELECT b.building_id, b.building_name, b.area, b.building_images_url
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

        Generate exactly ONE SQL query that best answers the user's question.
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
        elif "lead" in permissions:
            return ["rooms", "buildings"]  # Lead access: can read these 3 tables
        else:
            return ["rooms", "buildings"]  # Basic user access
    # async def _validate_categorical_values(
    #     self, 
    #     sql: str, 
    #     sql_result: Dict[str, Any]
    # ) -> Dict[str, Any]:
    #     """
    #     Validate that all categorical values in WHERE/GROUP BY clauses exist in database constants.
    #     """
    #     from app.db.database_constants import DATABASE_DISTINCT_VALUES
        
    #     validation_result = {
    #         "valid": True,
    #         "errors": [],
    #         "score": 100
    #     }
        
    #     # Extract WHERE clause values using regex
    #     # Pattern to find column = 'value' or column IN ('value1', 'value2')
    #     where_pattern = r"(\w+)\.(\w+)\s*=\s*'([^']+)'|(\w+)\.(\w+)\s+IN\s*\(([^)]+)\)"
        
    #     for match in re.finditer(where_pattern, sql, re.IGNORECASE):
    #         if match.group(1):  # Single value comparison
    #             table = match.group(1)
    #             column = match.group(2)
    #             value = match.group(3).strip()
                
    #             # Check if this table/column combo has valid values
    #             if table in DATABASE_DISTINCT_VALUES:
    #                 text_columns = DATABASE_DISTINCT_VALUES[table].get("text_columns", {})
    #                 if column in text_columns and text_columns[column]:  # Has valid values list
    #                     valid_list = text_columns[column]
    #                     if value not in valid_list:
    #                         validation_result["valid"] = False
    #                         validation_result["score"] -= 100
    #                         validation_result["errors"].append(
    #                             f"Invalid value '{value}' for {table}.{column}. Allowed: {valid_list[:3]}..."
    #                         )
            
    #         elif match.group(4):  # IN clause
    #             table = match.group(4)
    #             column = match.group(5)
    #             values_str = match.group(6).strip()
    #             values = [v.strip().strip("'\"") for v in values_str.split(',')]
                
    #             if table in DATABASE_DISTINCT_VALUES:
    #                 text_columns = DATABASE_DISTINCT_VALUES[table].get("text_columns", {})
    #                 if column in text_columns and text_columns[column]:
    #                     valid_list = text_columns[column]
    #                     for value in values:
    #                         if value not in valid_list:
    #                             validation_result["valid"] = False
    #                             validation_result["score"] -= 100
    #                             validation_result["errors"].append(
    #                                 f"Invalid value '{value}' for {table}.{column}"
    #                             )
        
    #     # Also check LIKE patterns for categorical columns
    #     like_pattern = r"(\w+)\.(\w+)\s+(?:LIKE|ILIKE)\s+'%([^%]+)%'"
        
    #     for match in re.finditer(like_pattern, sql, re.IGNORECASE):
    #         table = match.group(1)
    #         column = match.group(2)
    #         search_term = match.group(3)
            
    #         if table in DATABASE_DISTINCT_VALUES:
    #             text_columns = DATABASE_DISTINCT_VALUES[table].get("text_columns", {})
    #             if column in text_columns and text_columns[column]:
    #                 # Check if search term appears in ANY valid value
    #                 valid_list = text_columns[column]
    #                 term_found = any(search_term in val for val in valid_list)
                    
    #                 if not term_found:
    #                     validation_result["valid"] = False
    #                     validation_result["score"] -= 100
    #                     validation_result["errors"].append(
    #                         f"Search term '{search_term}' not found in any valid value for {table}.{column}"
    #                     )
        
    #     return validation_result

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
            # Check if this is a permission-related response
        permission_keywords = [
            "permission", "not allowed", "can't access", "cannot access",
            "restricted", "unauthorized", "don't have access", "requires elevated"
        ]
        
        response_lower = response_text.lower()
        if any(keyword in response_lower for keyword in permission_keywords):
            return {
                "sql": None,
                "success": False,
                "error": "Permission Denied",
                "explanation": response_text.strip(),
                "is_permission_error": True,
                "query_type": "PERMISSION_DENIED"
            }
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
        
        # # Check for table permissions (warn but don't fail)
        # used_tables = []
        # for table_name in self.schema["tables"].keys():
        #     if table_name.lower() in sql.lower():
        #         used_tables.append(table_name)
        #         if table_name not in allowed_tables:
        #             validation_result["warnings"].append(f"Table '{table_name}' not in allowed list")
        
            # STRICT TABLE PERMISSION CHECK - FAIL IF UNAUTHORIZED TABLES ARE USED
        used_tables = []
        unauthorized_tables = []
    
        # Check all tables mentioned in the SQL
        for table_name in self.schema["tables"].keys():
            if re.search(rf'\b{table_name}\b', sql, re.IGNORECASE):
                used_tables.append(table_name)
                if table_name not in allowed_tables:
                    unauthorized_tables.append(table_name)
        
        # If unauthorized tables are found, fail the validation
        if unauthorized_tables:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Unauthorized table access: {', '.join(unauthorized_tables)}. "
                f"User with role '{self.schema.get('user_role', 'user')}' can only access: {', '.join(allowed_tables)}"
            )

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
1. You can ONLY access these tables: {allowed_tables}
    - Do NOT generate any SQL accessing forbidden tables
    - Explain that the user lacks permission to access that data
2. Follow the exact schema provided and use exact values from the VALID COLUMN VALUES section
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
