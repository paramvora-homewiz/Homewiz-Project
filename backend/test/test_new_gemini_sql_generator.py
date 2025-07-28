# tests/test_gemini_sql_generator.py

from app.ai_services.gemini_sql_generator import GeminiSQLGenerator


def test_sql_generator():
    """Test SQL generation with various scenarios."""
    
    generator = GeminiSQLGenerator()
    
    # Test 1: Simple room search with correct status
    print("🧪 Test 1: Simple Room Search (Corrected)")
    result = generator.generate_sql(
        filters={
            "price_max": 2000,
            "bathroom_type": "Private",
            "status": "Available"  # Correct case
        },
        query_type="search",
        tables=["rooms"],
        limit=20
    )
    print(f"SQL: {result.get('sql')}")
    print(f"Success: {result.get('success')}")
    print("-" * 50)
    
    # Test 2: Complex search with joins
    print("\n🧪 Test 2: Complex Search with Building Features")
    result = generator.generate_sql(
        filters={
            "price_max": 2500,
            "view_types": ["Street View", "Courtyard"],  # Correct values
            "building_features": {
                "wifi_included": True,
                "laundry_onsite": True,
                "fitness_area": True
            },
            "area": "SOMA"  # Correct value
        },
        query_type="search",
        tables=["rooms", "buildings"],
        joins=[{
            "from": "rooms",
            "to": "buildings",
            "on": "building_id",
            "type": "INNER"
        }],
        limit=30
    )
    print(f"SQL: {result.get('sql')}")
    print(f"Explanation: {result.get('explanation')}")
    print("-" * 50)
    
    # Test 3: Parking search (corrected)
    print("\n🧪 Test 3: Search with Parking (TEXT column)")
    result = generator.generate_sql(
        filters={
            "view_types": ["Street View"],
            "building_features": {
                "fitness_area": True,
                "parking_available": True  # Simplified filter
            }
        },
        query_type="search",
        tables=["rooms", "buildings"],
        joins=[{
            "from": "rooms",
            "to": "buildings",
            "on": "building_id",
            "type": "INNER"
        }],
        limit=20
    )
    print(f"SQL: {result.get('sql')}")
    print("-" * 50)
    
    # Test 4: Analytics query
    print("\n🧪 Test 4: Analytics Query")
    result = generator.generate_sql(
        filters={},
        query_type="analytics",
        tables=["rooms", "buildings"],
        joins=[{
            "from": "rooms",
            "to": "buildings", 
            "on": "building_id",
            "type": "INNER"
        }],
        aggregations=[
            {"function": "COUNT", "column": "r.room_id", "alias": "total_rooms"},
            {"function": "COUNT", "column": "CASE WHEN r.status = 'Occupied' THEN 1 END", "alias": "occupied_rooms"},
            {"function": "AVG", "column": "r.private_room_rent", "alias": "avg_rent"}
        ],
        group_by=["b.building_name", "b.building_id"],
        order_by=[{"column": "occupied_rooms", "direction": "DESC"}]
    )
    print(f"SQL: {result.get('sql')}")
    print(f"Tables Used: {result.get('tables_used')}")
    print("-" * 50)


if __name__ == "__main__":
    test_sql_generator()