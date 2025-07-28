# tests/test_unified_room_finder.py

import json
from app.ai_services.unified_room_finder import unified_room_search_function


def test_unified_search():
    """Test the unified room search with various queries."""
    
    test_queries = [
        "Show me available rooms under $2000 with private bathroom",
        "Find rooms in SOMA with wifi and laundry in the building",
        "I need a room with city view, gym in building, and parking",
        "Rooms under $1800 with mini fridge and work desk"
    ]
    
    print("🧪 Testing Unified Room Search")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📍 Query: {query}")
        result = unified_room_search_function(query)
        
        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        if result.get('search_criteria'):
            print(f"Criteria: {json.dumps(result['search_criteria'], indent=2)}")
        print("-" * 50)


if __name__ == "__main__":
    test_unified_search()