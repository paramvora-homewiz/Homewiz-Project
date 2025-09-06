# Test script to debug UPDATE queries
from app.ai_services.sql_executor import SQLExecutor

def test_update_queries():
    executor = SQLExecutor()
    
    # Test queries from simplest to more complex
    test_queries = [
        # 1. Super simple UPDATE
        "UPDATE rooms SET status = 'Available'",
        
        # 2. UPDATE with numeric WHERE
        "UPDATE rooms SET status = 'Available' WHERE room_number = 101",
        
        # 3. UPDATE with simple text WHERE
        "UPDATE rooms SET status = 'Available' WHERE room_id = 'test'",
        
        # 4. UPDATE with the actual room_id (shorter)
        "UPDATE rooms SET status = 'Available' WHERE room_id = 'BLDG_1080_FOLSOM'",
        
        # 5. UPDATE with full room_id
        "UPDATE rooms SET status = 'Occupied' WHERE room_id = 'BLDG_1080_FOLSOM_R011'",
        
        # 6. Try with lowercase
        "update rooms set status = 'Occupied' where room_id = 'BLDG_1080_FOLSOM_R011'",
        
        # 7. Try with double quotes on identifier
        'UPDATE "rooms" SET "status" = \'Occupied\' WHERE "room_id" = \'BLDG_1080_FOLSOM_R011\'',
        
        # 8. Try simpler table
        "UPDATE operators SET active = true WHERE operator_id = 1",
        
        # 9. Try with explicit schema (if needed)
        "UPDATE public.rooms SET status = 'Occupied' WHERE room_id = 'BLDG_1080_FOLSOM_R011'",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print(f"{'='*60}")
        
        result = executor.execute_query(query)
        
        if result['success']:
            print(f"✅ SUCCESS! Rows affected: {result.get('row_count', 0)}")
        else:
            print(f"❌ FAILED! Error: {result.get('error', 'Unknown error')}")
        
        print(f"Full result: {result}")

# Also test if SELECT works with RPC
def test_select_queries():
    executor = SQLExecutor()
    
    test_selects = [
        "SELECT room_id, status FROM rooms LIMIT 5",
        "SELECT room_id, status FROM rooms WHERE room_id = 'BLDG_1080_FOLSOM_R011'",
        "SELECT COUNT(*) as count FROM rooms",
    ]
    
    print("\n\nTesting SELECT queries to ensure RPC works:")
    for query in test_selects:
        print(f"\n{query}")
        result = executor.execute_query(query)
        print(f"Result: {result}")

if __name__ == "__main__":
    test_update_queries()
    test_select_queries()