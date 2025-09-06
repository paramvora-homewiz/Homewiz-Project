# app/ai_services/sql_executor.py

import json
from typing import Dict, Any, List, Optional
from app.db.supabase_connection import get_supabase
import logging
import pandas as pd
import re

class SQLExecutor:
    """
    Handles SQL query execution using Supabase client with RPC.
    """
    
    def __init__(self):
        self.supabase = get_supabase()
        logging.info("SQLExecutor initialized with Supabase client")
    
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a SQL query using Supabase RPC.
        
        Args:
            sql: SQL query to execute
            params: Optional parameters (not supported in this implementation)
            
        Returns:
            Dictionary with success status, data, and error info
        """
        try:
            # Clean SQL
            sql = sql.strip()
            sql = sql.replace('\\n', ' ').replace('\n', ' ')
            if sql.endswith(';'):
                sql = sql[:-1]
            
            # Log query (be careful in production)
            logging.info(f"Executing SQL via Supabase RPC: {sql[:100]}...")
            # if sql.upper().startswith('UPDATE'):
            #     return self._execute_update_native(sql)  # Use native .update()
            # else:
            #     # return self._execute_rpc(sql)  # Use RPC for SELECT
            #     # Execute via RPC
            response = self.supabase.rpc('execute_sql', {'query_text': sql}).execute()
            
            # Parse response
            if response.data is not None:
                # Handle the response - it comes as JSON
                if isinstance(response.data, str):
                    data = json.loads(response.data)
                elif isinstance(response.data, list):
                    data = response.data
                else:
                    data = response.data if response.data else []
                
                # Extract columns from first row if data exists
                columns = list(data[0].keys()) if data and len(data) > 0 else []
                
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": columns,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "columns": [],
                    "error": "No data returned"
                }
                
        except Exception as e:
            logging.error(f"SQL execution error: {str(e)}")
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "columns": [],
                "error": f"Error: {str(e)}"
            }
        
    def _execute_update_native(self, sql: str) -> Dict[str, Any]:
        """
        Execute UPDATE query using native Supabase methods.
        """
        try:
            # Parse UPDATE statement
            # Pattern: UPDATE table_name SET column = value WHERE condition
            update_pattern = r"UPDATE\s+[\"']?(\w+)[\"']?\s+SET\s+(.+?)\s+WHERE\s+(.+?)$"
            match = re.match(update_pattern, sql, re.IGNORECASE | re.DOTALL)
            
            if not match:
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "error": "UPDATE without WHERE clause not allowed for safety"
                }
            
            table_name = match.group(1)
            set_clause = match.group(2)
            where_clause = match.group(3)
            
            # Parse SET clause
            updates = {}
            # Handle multiple assignments separated by commas
            set_parts = re.split(r',(?![^\']*\'(?:[^\']*\'[^\']*\')*[^\']*$)', set_clause)
            
            for part in set_parts:
                # Extract column = value
                set_match = re.match(r"\s*[\"']?(\w+)[\"']?\s*=\s*(.+)", part.strip())
                if set_match:
                    col = set_match.group(1)
                    val = set_match.group(2).strip()
                    
                    # Remove quotes if present
                    if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
                        val = val[1:-1]
                    
                    # Handle boolean values
                    if val.lower() in ['true', 'false']:
                        val = val.lower() == 'true'
                    # Handle null
                    elif val.upper() == 'NULL':
                        val = None
                    # Handle numeric values
                    elif val.replace('.', '').replace('-', '').isdigit():
                        if '.' in val:
                            val = float(val)
                        else:
                            val = int(val)
                    
                    updates[col] = val
            
            # Parse WHERE clause - handle simple equality for now
            where_match = re.match(r"\s*[\"']?(\w+)[\"']?\s*=\s*(.+)", where_clause.strip())
            if not where_match:
                return {
                    "success": False,
                    "data": [],
                    "row_count": 0,
                    "error": "Could not parse WHERE clause"
                }
            
            where_col = where_match.group(1)
            where_val = where_match.group(2).strip()
            
            # Remove quotes if present
            if (where_val.startswith("'") and where_val.endswith("'")) or (where_val.startswith('"') and where_val.endswith('"')):
                where_val = where_val[1:-1]
            
            # Handle numeric values in WHERE
            if where_val.replace('.', '').replace('-', '').isdigit():
                if '.' in where_val:
                    where_val = float(where_val)
                else:
                    where_val = int(where_val)
            
            # Log the update operation
            logging.info(f"Executing native update on {table_name}: {updates} WHERE {where_col} = {where_val}")
            
            # Execute update with correct Supabase syntax
            # IMPORTANT: Apply filter BEFORE calling update()
            response = self.supabase.table(table_name).eq(where_col, where_val).update(updates).execute()
            
            # Return result
            if hasattr(response, 'data') and response.data is not None:
                return {
                    "success": True,
                    "data": response.data if isinstance(response.data, list) else [response.data],
                    "row_count": len(response.data) if isinstance(response.data, list) else 1,
                    "columns": list(response.data[0].keys()) if response.data and isinstance(response.data, list) and len(response.data) > 0 else [],
                    "error": None
                }
            else:
                return {
                    "success": True,
                    "data": [],
                    "row_count": 0,
                    "columns": [],
                    "error": None
                }
                
        except Exception as e:
            logging.error(f"Native update error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "data": [],
                "row_count": 0,
                "error": f"Update failed: {str(e)}"
            }
    
    def execute_select(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return only the data.
        """
        result = self.execute_query(sql, params)
        return result['data'] if result['success'] else []
    
    def execute_aggregate(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an aggregate query and return the first row as a dict.
        """
        result = self.execute_query(sql, params)
        if result['success'] and result['data']:
            return result['data'][0]
        return {}
    
    def test_connection(self) -> bool:
        """Test if database connection is working."""
        try:
            # Use a simple Supabase query instead
            response = self.supabase.table('rooms').select('room_id').limit(1).execute()
            return bool(response.data is not None)
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
    
    def close(self):
        """No need to close Supabase client connection."""
        logging.info("SQLExecutor cleanup completed")


# Alternative: Direct Supabase query methods (without raw SQL)
class SupabaseQueryBuilder:
    """
    Alternative approach using Supabase's query builder instead of raw SQL.
    """
    
    def __init__(self):
        self.supabase = get_supabase()
    
    def search_rooms_with_buildings(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search rooms with building information using Supabase query builder.
        """
        # Start with rooms query and join buildings
        query = self.supabase.table('rooms').select(
            '*, buildings!inner(*)'
        )
        
        # Apply room filters
        if filters.get('status'):
            query = query.eq('status', filters['status'])
        
        if filters.get('price_max'):
            query = query.lte('private_room_rent', filters['price_max'])
        
        if filters.get('price_min'):
            query = query.gte('private_room_rent', filters['price_min'])
        
        if filters.get('bathroom_type'):
            query = query.eq('bathroom_type', filters['bathroom_type'])
        
        if filters.get('bed_size'):
            query = query.eq('bed_size', filters['bed_size'])
        
        # Apply building filters using the joined table
        if filters.get('building_wifi_included'):
            query = query.eq('buildings.wifi_included', True)
        
        if filters.get('building_laundry_onsite'):
            query = query.eq('buildings.laundry_onsite', True)
        
        if filters.get('building_fitness_area'):
            query = query.eq('buildings.fitness_area', True)
        
        if filters.get('building_area'):
            query = query.ilike('buildings.area', f"%{filters['building_area']}%")
        
        # Order and limit
        query = query.order('private_room_rent', desc=False).limit(50)
        
        # Execute
        response = query.execute()
        
        return response.data if response.data else []


