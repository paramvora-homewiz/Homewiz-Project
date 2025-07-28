# tests/test_function_dispatcher.py

from app.ai_services.intelligent_function_dispatcher_supabase import intelligent_function_selection


def test_function_dispatcher():
    """Test the function dispatcher with various queries."""
    
    test_queries = [
        # Room search queries
        "Show me available rooms under $2000",
        "Find apartments in downtown with wifi and gym",
        "I need a room with private bathroom",
        
        # Analytics queries
        "What's the current occupancy rate?",
        "Show me revenue metrics for this month",
        "How many leads converted last quarter?",
        "Generate a dashboard report",
        
        # Edge cases
        "Hello",
        "What's the weather?"
    ]
    
    print("🧪 Testing Function Dispatcher")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = intelligent_function_selection(query)
        
        if result['success']:
            print(f"✅ Function: {result['function_called']}")
            print(f"🎯 Confidence: {result.get('confidence', 'N/A')}")
            if 'result' in result and isinstance(result['result'], dict):
                print(f"📊 Response: {result['result'].get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Error: {result['error']}")
        
        print("-" * 40)


if __name__ == "__main__":
    test_function_dispatcher()