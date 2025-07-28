# tests/test_sql_executor.py

from app.ai_services.sql_executor import (
    SQLExecutor, 
    get_room_availability_status, 
    get_building_occupancy_rates
)


def test_sql_executor():
    """Test the SQL executor with various queries."""
    
    executor = SQLExecutor()
    
    print("🧪 Testing SQL Executor")
    print("=" * 60)
    
    # Test 1: Connection test
    print("\n1️⃣ Testing connection...")
    if executor.test_connection():
        print("✅ Connection successful!")
    else:
        print("❌ Connection failed!")
        return
    
    # Test 2: Simple select
    print("\n2️⃣ Testing simple SELECT...")
    result = executor.execute_query("SELECT COUNT(*) as total_rooms FROM rooms")
    if result['success']:
        print(f"✅ Total rooms: {result['data'][0]['total_rooms']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 3: Complex query
    print("\n3️⃣ Testing complex query with JOIN...")
    sql = """
        SELECT 
            r.room_id,
            r.room_number,
            r.private_room_rent,
            r.status,
            b.building_name,
            b.area
        FROM rooms r
        JOIN buildings b ON r.building_id = b.building_id
        WHERE r.status = 'Available'
        AND r.private_room_rent <= 2000
        ORDER BY r.private_room_rent
        LIMIT 5
    """
    result = executor.execute_query(sql)
    if result['success']:
        print(f"✅ Found {result['row_count']} available rooms under $2000")
        for room in result['data']:
            print(f"   Room {room['room_number']} in {room['building_name']}: ${room['private_room_rent']}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 4: Aggregate query
    print("\n4️⃣ Testing aggregate query...")
    sql = """
        SELECT 
            MIN(private_room_rent) as min_rent,
            MAX(private_room_rent) as max_rent,
            ROUND(AVG(private_room_rent), 2) as avg_rent
        FROM rooms
        WHERE status = 'Available'
    """
    result = executor.execute_aggregate(sql)
    if result:
        print(f"✅ Rent statistics:")
        print(f"   Min: ${result.get('min_rent', 0)}")
        print(f"   Max: ${result.get('max_rent', 0)}")
        print(f"   Avg: ${result.get('avg_rent', 0)}")
    
    # Test 5: Utility functions
    print("\n5️⃣ Testing utility functions...")
    
    print("\nRoom availability:")
    availability = get_room_availability_status()
    for status, count in availability.items():
        print(f"   {status}: {count} rooms")
    
    print("\nBuilding occupancy rates:")
    occupancy = get_building_occupancy_rates()
    for building in occupancy[:3]:  # Show top 3
        print(f"   {building['building_name']}: {building['occupancy_rate']}% ({building['occupied_rooms']}/{building['total_rooms']})")
    
    # Close connection
    executor.close()
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_sql_executor()