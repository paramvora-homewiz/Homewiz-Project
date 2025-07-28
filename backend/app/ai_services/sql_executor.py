# app/ai_services/sql_executor.py

import json
from typing import Dict, Any, List, Optional
from app.db.supabase_connection import get_supabase
import logging
import pandas as pd

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
            
            # Execute via RPC
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


# Test function
def test_sql_executor():
    """Test the SQL executor with Supabase client."""
    
    executor = SQLExecutor()
    
    print("🧪 Testing SQL Executor with Supabase Client")
    print("=" * 60)
    
    # Test 1: Connection test
    print("\n1️⃣ Testing connection...")
    if executor.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return
    
    # Test 2: Alternative - using query builder
    print("\n2️⃣ Testing Supabase query builder...")
    query_builder = SupabaseQueryBuilder()
    results = query_builder.search_rooms_with_buildings({
        'status': 'Available',
        'price_max': 2000,
        'building_area': 'SOMA'
    })
    print(f"✅ Found {len(results)} rooms")
    for room in results[:3]:
        building = room.get('buildings', {})
        print(f"   Room {room['room_number']} in {building.get('building_name', 'Unknown')}: ${room['private_room_rent']}")
    
    # Test 3: If RPC function is created, test it
    print("\n3️⃣ Testing RPC execution (if function exists)...")
    try:
        sql = "SELECT COUNT(*) as total FROM rooms WHERE status = 'Available'"
        result = executor.execute_query(sql)
        if result['success']:
            print(f"✅ RPC query successful: {result['data']}")
        else:
            print(f"⚠️  RPC not available: {result['error']}")
            print("   Using query builder approach instead")
    except Exception as e:
        print(f"⚠️  RPC function not set up: {e}")
        print("   Continue with query builder approach")
    
    print("\n✅ Tests completed!")


if __name__ == "__main__":
    test_sql_executor()