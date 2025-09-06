# app/ai_services/supabase_update_generator.py

import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.db.database_schema import DATABASE_SCHEMA

class SupabaseUpdateGenerator:
    """
    Generates Supabase native update calls with zero hallucination capability.
    Uses strict schema constraints and validation.
    """
    
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.schema = DATABASE_SCHEMA
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Rate limiting
    
    async def generate_update_code(
        self, 
        natural_query: str, 
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate Supabase update specification with strict hallucination prevention."""
        
        if user_context is None:
            user_context = {"permissions": ["basic"], "role": "user"}

        natural_query = self._preprocess_query(natural_query)
        
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        
        # Get exact schema and allowed tables
        exact_schema = self._format_exact_schema()
        allowed_tables = self._get_allowed_tables_for_update(user_context.get("permissions", []))
        
        # Build prompt for Supabase native calls
        generation_prompt = self._build_supabase_update_prompt(
            natural_query, exact_schema, allowed_tables, user_context
        )
        
        try:
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
            update_spec = self._parse_response(response.text)
            
            # Validate the specification
            validation_result = self._validate_update_spec(update_spec, allowed_tables)
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "update_spec": None
                }
            
            update_spec["success"] = True
            update_spec["generation_time"] = time.time() - current_time
            return update_spec
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "update_spec": None
            }
    
    def _format_exact_schema(self) -> str:
        """Format schema with EXACT names and types for Supabase."""
        formatted_tables = []
        
        for table_name, table_info in self.schema["tables"].items():
            formatted_tables.append(f"\nTABLE: {table_name}")
            formatted_tables.append(f"  Description: {table_info.get('description', 'No description')}")
            
            # Show updateable columns only
            updateable_columns = []
            for col_name, col_info in table_info["columns"].items():
                # Skip primary keys and auto-generated fields
                if col_info.get("primary_key") or col_info.get("auto_increment"):
                    continue
                
                col_type = col_info["type"]
                type_hint = self._get_type_hint(col_type)
                updateable_columns.append(f"  {col_name}: {col_type} ({type_hint})")
            
            formatted_tables.append("  UPDATEABLE COLUMNS:")
            formatted_tables.extend(updateable_columns)
        
        return "\n".join(formatted_tables)
    
    def _get_type_hint(self, col_type: str) -> str:
        """Get Python type hint for column type."""
        type_mapping = {
            "TEXT": "string",
            "BIGINT": "integer",
            "INTEGER": "integer", 
            "BOOLEAN": "boolean (True/False)",
            "DOUBLE PRECISION": "float",
            "NUMERIC": "float",
            "TIMESTAMP": "string (ISO format)",
            "JSONB": "dict/object"
        }
        
        for sql_type, python_type in type_mapping.items():
            if sql_type in col_type.upper():
                return python_type
        return "string"
    
    def _build_supabase_update_prompt(
        self,
        query: str,
        schema: str,
        allowed_tables: List[str],
        context: Dict
    ) -> str:
        """Build prompt for Supabase native update generation."""
        
        # Get valid values from database constants
        from app.db.database_constants import format_values_for_prompt
        valid_values = format_values_for_prompt()
        
        return f"""
You are a Supabase update code generator. Generate ONLY the update specification JSON.

NATURAL LANGUAGE UPDATE REQUEST: "{query}"

USER PERMISSIONS: Can update tables: {allowed_tables}
USER ROLE: {context.get('role', 'user')}

EXACT DATABASE SCHEMA (USE ONLY THESE):
{schema}

VALID COLUMN VALUES:
{valid_values}

STRICT RULES:
1. Return ONLY a JSON object with this exact structure
2. Use ONLY table names from: {allowed_tables}
3. Use ONLY column names shown in the schema
4. For enum columns: Use EXACT values from "VALID COLUMN VALUES" (case-sensitive)
5. For boolean columns: Use True or False (Python booleans, not strings)
6. ALWAYS include where_conditions to prevent mass updates
7. Match based on unique identifiers when possible (room_id, tenant_id, etc.)
8. If matching by room_number, tenant_name, etc., use exact match

REQUIRED JSON FORMAT:
{{
    "table": "table_name",
    "update_data": {{
        "column_name": value
    }},
    "where_conditions": [
        ["column_name", "operator", value]
    ],
    "explanation": "Clear explanation of what will be updated",
    "estimated_rows": 1
}}

CRITICAL RULES FOR BUILDING IDENTIFICATION:
- If the value looks like "BLDG_XXX" pattern, it's a building_id, use: ["building_id", "eq", "BLDG_XXX"]
- If the value is a readable name like "1080 Folsom Residences", it's a building_name, use: ["building_name", "eq", "name"]
- NEVER use building_name for BLDG_ prefixed values!

OPERATORS AVAILABLE:
- "eq": equals (most common)
- "neq": not equals
- "gt": greater than
- "gte": greater than or equal
- "lt": less than
- "lte": less than or equal
- "like": pattern match
- "ilike": case-insensitive pattern match

EXAMPLES:

Request: "change room 101 status to occupied"
{{
    "table": "rooms",
    "update_data": {{
        "status": "Occupied"
    }},
    "where_conditions": [
        ["room_number", "eq", 101]
    ],
    "explanation": "Updates room 101 status to Occupied",
    "estimated_rows": 1
}}

Request: "update John Smith's payment status to late"
{{
    "table": "tenants", 
    "update_data": {{
        "payment_status": "Late"
    }},
    "where_conditions": [
        ["tenant_name", "eq", "John Smith"]
    ],
    "explanation": "Updates John Smith's payment status to Late",
    "estimated_rows": 1
}}

Request: "mark all rooms in building BLDG_1080_FOLSOM as available"
{{
    "table": "rooms",
    "update_data": {{
        "status": "Available"
    }},
    "where_conditions": [
        ["building_id", "eq", "BLDG_1080_FOLSOM"]
    ],
    "explanation": "Updates all rooms in building BLDG_1080_FOLSOM to Available status",
    "estimated_rows": 15
}}

Request: "update building BLDG_524_COLUMBUS fitness_area to true"
{{
    "table": "buildings",
    "update_data": {{
        "fitness_area": true
    }},
    "where_conditions": [
        ["building_id", "eq", "BLDG_524_COLUMBUS"]  // Note: building_id, not building_name!
    ],
    "explanation": "Updates building BLDG_524_COLUMBUS to have fitness area",
    "estimated_rows": 1
}}

Request: "update building 524 Columbus Residences fitness_area to true"
{{
    "table": "buildings",
    "update_data": {{
        "fitness_area": true
    }},
    "where_conditions": [
        ["building_name", "eq", "524 Columbus Residences"]  // Note: building_name for readable names
    ],
    "explanation": "Updates 524 Columbus Residences to have fitness area",
    "estimated_rows": 1
}}

Request: "set 1080 Folsom Residences wifi to true"
{{
    "table": "buildings",
    "update_data": {{
        "wifi_included": true
    }},
    "where_conditions": [
        ["building_name", "eq", "1080 Folsom Residences"]
    ],
    "explanation": "Updates 1080 Folsom Residences to include wifi",
    "estimated_rows": 1
}}

Generate the update specification for the user's request.
"""
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query to make it more LLM-friendly."""
        
        # Common replacements for clearer intent
        replacements = {
            "has fitness center set": "fitness_area to",
            "wifi included": "wifi_included", 
            "fitness center": "fitness_area",
            "Modify": "Update",
            "set True": "to true",
            "set False": "to false"
        }
        
        processed = query
        for old, new in replacements.items():
            processed = processed.replace(old, new)
        
        return processed
    
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
            required_fields = ["table", "update_data", "where_conditions", "explanation"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "raw_response": response_text
            }
    
    def _validate_update_spec(self, spec: Dict[str, Any], allowed_tables: List[str]) -> Dict[str, Any]:
        """Validate the update specification against schema."""
        
        # Check for parsing errors
        if spec.get("error"):
            return {"valid": False, "error": spec["error"]}
        
        # Validate table
        table = spec.get("table")
        if not table:
            return {"valid": False, "error": "No table specified"}
        
        if table not in allowed_tables:
            return {"valid": False, "error": f"Table '{table}' not allowed for updates"}
        
        if table not in self.schema["tables"]:
            return {"valid": False, "error": f"Table '{table}' does not exist"}
        
        # Validate update columns
        update_data = spec.get("update_data", {})
        if not update_data:
            return {"valid": False, "error": "No update data specified"}
        
        table_columns = self.schema["tables"][table]["columns"]
        for column in update_data.keys():
            if column not in table_columns:
                return {"valid": False, "error": f"Column '{column}' does not exist in table '{table}'"}
            
            # Don't allow updating primary keys
            if table_columns[column].get("primary_key"):
                return {"valid": False, "error": f"Cannot update primary key column '{column}'"}
        
        # Validate where conditions
        where_conditions = spec.get("where_conditions", [])
        if not where_conditions:
            return {"valid": False, "error": "No WHERE conditions - would update all rows!"}
        
        for condition in where_conditions:
            if len(condition) != 3:
                return {"valid": False, "error": f"Invalid where condition format: {condition}"}
            
            col, op, val = condition
            if col not in table_columns:
                return {"valid": False, "error": f"WHERE column '{col}' does not exist"}
            
            valid_ops = ["eq", "neq", "gt", "gte", "lt", "lte", "like", "ilike", "in", "is"]
            if op not in valid_ops:
                return {"valid": False, "error": f"Invalid operator '{op}'"}
        
        return {"valid": True}
    
    def _get_allowed_tables_for_update(self, permissions: List[str]) -> List[str]:
        """Get allowed tables for UPDATE operations based on user permissions."""
        if "admin" in permissions:
            return ["rooms", "buildings", "tenants", "leads", "operators", "maintenance_requests"]
        elif "manager" in permissions:
            return ["rooms", "tenants", "maintenance_requests"]
        elif "agent" in permissions:
            return ["leads"]
        else:
            return []  # Basic users can't update anything