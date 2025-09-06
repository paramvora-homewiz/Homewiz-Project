# app/ai_services/supabase_update_executor.py

import logging
from typing import Dict, Any, List
from app.db.supabase_connection import get_supabase
from app.db.database_schema import get_table_columns

class SupabaseUpdateExecutor:
    """
    Executes Supabase updates with multi-layer verification.
    """
    
    def __init__(self):
        self.supabase = get_supabase()
        logging.info("SupabaseUpdateExecutor initialized")
    
    def execute_update(self, update_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute update with verification layers.
        
        Args:
            update_spec: Dictionary with table, update_data, where_conditions
            
        Returns:
            Dictionary with success status and results
        """
        
        try:
            # Layer 1: Preview what will be affected
            preview_result = self._preview_update(update_spec)
            
            if not preview_result["success"]:
                return preview_result
            
            affected_count = preview_result["count"]
            affected_data = preview_result["data"]
            
            # Layer 2: Safety checks
            if affected_count == 0:
                return {
                    "success": False,
                    "error": "No rows match the WHERE conditions",
                    "data": [],
                    "row_count": 0
                }
            
            if affected_count > 100:
                return {
                    "success": False,
                    "error": f"Safety limit: Update would affect {affected_count} rows (max 100)",
                    "data": affected_data[:10],  # Show first 10 as preview
                    "row_count": 0,
                    "preview_count": affected_count
                }
            
            # Layer 3: Build and execute the update query
            table = update_spec["table"]
            update_data = update_spec["update_data"]
            where_conditions = update_spec["where_conditions"]
            
            # Start building query
            query = self.supabase.table(table)
            
            # Apply update data
            query = query.update(update_data)
            
            # Apply WHERE conditions
            for column, operator, value in where_conditions:
                query = self._apply_where_condition(query, column, operator, value)
            
            # Execute update
            logging.info(f"Executing update on {table}: {update_data} WHERE {where_conditions}")
            response = query.execute()
            
            # Return success response
            return {
                "success": True,
                "data": response.data if response.data else affected_data,
                "row_count": len(response.data) if response.data else affected_count,
                "error": None,
                "preview_data": affected_data
            }
            
        except Exception as e:
            logging.error(f"Update execution error: {str(e)}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "data": [],
                "row_count": 0
            }
    
    def _preview_update(self, update_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview what rows will be affected by the update.
        
        Returns:
            Dictionary with success, count, and preview data
        """
        try:
            table = update_spec["table"]
            where_conditions = update_spec["where_conditions"]
            
            # Build SELECT query with same WHERE conditions
            query = self.supabase.table(table).select("*")
            
            # Apply WHERE conditions
            for column, operator, value in where_conditions:
                query = self._apply_where_condition(query, column, operator, value)
            
            # Execute preview query
            response = query.execute()
            
            return {
                "success": True,
                "count": len(response.data) if response.data else 0,
                "data": response.data if response.data else []
            }
            
        except Exception as e:
            logging.error(f"Preview error: {str(e)}")
            return {
                "success": False,
                "error": f"Preview failed: {str(e)}",
                "count": 0,
                "data": []
            }
    
    def _apply_where_condition(self, query, column: str, operator: str, value: Any):
        """
        Apply a WHERE condition to the query using the appropriate Supabase method.
        
        Args:
            query: Supabase query builder
            column: Column name
            operator: Operator (eq, neq, gt, etc.)
            value: Value to compare
            
        Returns:
            Modified query
        """
        operator_mapping = {
            "eq": lambda q, c, v: q.eq(c, v),
            "neq": lambda q, c, v: q.neq(c, v),
            "gt": lambda q, c, v: q.gt(c, v),
            "gte": lambda q, c, v: q.gte(c, v),
            "lt": lambda q, c, v: q.lt(c, v),
            "lte": lambda q, c, v: q.lte(c, v),
            "like": lambda q, c, v: q.like(c, v),
            "ilike": lambda q, c, v: q.ilike(c, v),
            "in": lambda q, c, v: q.in_(c, v),
            "is": lambda q, c, v: q.is_(c, v)
        }
        
        if operator in operator_mapping:
            return operator_mapping[operator](query, column, value)
        else:
            # Default to eq if operator not recognized
            logging.warning(f"Unknown operator '{operator}', defaulting to 'eq'")
            return query.eq(column, value)
    
    def validate_value_types(self, table: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and convert value types before update.
        
        Returns:
            Dictionary with converted values
        """
        from app.db.database_constants import validate_value
        
        converted_data = {}
        
        for column, value in update_data.items():
            is_valid, corrected_value = validate_value(table, column, value)
            
            if not is_valid:
                logging.warning(f"Value correction for {column}: {value} -> {corrected_value}")
            
            converted_data[column] = corrected_value
        
        return converted_data