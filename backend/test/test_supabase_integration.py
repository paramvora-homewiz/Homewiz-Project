# test_supabase_integration.py
"""
Test script to verify the Supabase integration is working correctly
"""

import asyncio
from app.ai_services.intelligent_function_dispatcher_supabase import intelligent_function_selection

def test_queries():
    """Test various query types"""
    
    test_cases = [
        # Basic room queries
        # "Find me all rooms",
        # "Show me rooms under $2000",
        # "Private rooms with city view",
        # "Queen bed rooms with private bathroom",
        
        # # Building feature queries
        # "Buildings with gym and laundry",
        # "Pet-friendly buildings with wifi",
        # "Rooms in buildings with rooftop access",
        
        # Combined queries
        "Spacious rooms under $2500 in buildings with gym",
        "Private bathroom rooms in pet-friendly buildings near transit",
        
        # # Complex queries
        # "Furnished queen bed rooms on high floors with city view in buildings with laundry and gym under $3000",
    ]
    
    print("=" * 80)
    print("TESTING SUPABASE INTEGRATION")
    print("=" * 80)
    
    for i, query in enumerate(test_cases, 1):
        print(f"\nTest {i}: {query}")
        print("-" * 40)
        
        try:
            result = intelligent_function_selection(query)
            
            if result.get("success"):
                function_called = result.get("function_called")
                data = result.get("result", {}).get("data", [])
                response = result.get("result", {}).get("response", "")
                
                print(f"✅ Success!")
                print(f"   Function: {function_called}")
                print(f"   Results: {len(data)} rooms found")
                print(f"   Response: {response}")
                
                # Show first result details
                if data:
                    first_room = data[0]
                    print(f"\n   First match:")
                    print(f"   - Room: {first_room.get('room_number')}")
                    print(f"   - Price: ${first_room.get('private_room_rent')}")
                    print(f"   - Score: {first_room.get('match_score')}")
                    print(f"   - Reasons: {', '.join(first_room.get('match_reasons', []))}")
            
            else:
                print(f"❌ Failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()

def test_specific_functions():
    """Test specific function calls directly"""
    
    print("\n" + "=" * 80)
    print("TESTING SPECIFIC FUNCTIONS")
    print("=" * 80)
    
    # # Test V1 function
    # print("\n1. Testing find_buildings_rooms_function directly:")
    # try:
    #     from app.ai_services.v1_intelligent_room_finder_supabase import find_buildings_rooms_function
    #     result = find_buildings_rooms_function("rooms under $2000 with private bathroom")
    #     print(f"✅ V1 function works! Found {result.get('total_results', 0)} rooms")
    # except Exception as e:
    #     print(f"❌ V1 function failed: {e}")
    
    # Test V2 function
    print("\n2. Testing filter_rooms_function directly:")
    try:
        from app.ai_services.v2_intelligent_room_finder_supabase import filter_rooms_function
        result = filter_rooms_function("rooms in buildings with gym and wifi")
        print(f"✅ V2 function works! Found {result.get('total_results', 0)} rooms")
    except Exception as e:
        print(f"❌ V2 function failed: {e}")

if __name__ == "__main__":
    # Test connection first
    print("Testing Supabase connection...")
    try:
        from app.db.supabase_connection import get_supabase
        supabase = get_supabase()
        response = supabase.table('rooms').select('count', count='exact').limit(1).execute()
        print(f"✅ Connected to Supabase! Total rooms in database: {response.count}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        exit(1)
    
    # # Run tests
    test_queries()
    # test_specific_functions()
    
    # print("\n" + "=" * 80)
    # print("TESTING COMPLETE")
    # print("=" * 80)