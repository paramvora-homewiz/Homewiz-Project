# app/tests/test_insights_function.py
# Test file for the generate_insights_function

import json
from datetime import datetime
from app.ai_services.intelligent_function_dispatcher_supabase import intelligent_function_selection
from app.ai_services.v3_intelligent_insights_supabase import generate_insights_function

def test_direct_function_calls():
    """Test calling the insights function directly with different parameters"""
    print("=" * 80)
    print("TESTING DIRECT FUNCTION CALLS")
    print("=" * 80)
    
    # Test 1: Occupancy insights
    print("\n1. Testing OCCUPANCY insights:")
    result = generate_insights_function(
        insight_type="OCCUPANCY",
        building_id="building_001"
    )
    print(f"Success: {result.get('success')}")
    print(f"Summary: {result.get('summary')}")
    print(f"Data keys: {list(result.get('data', {}).keys())}")
    
    # Test 2: Financial insights with date range
    print("\n2. Testing FINANCIAL insights with date range:")
    result = generate_insights_function(
        insight_type="FINANCIAL",
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    print(f"Success: {result.get('success')}")
    print(f"Summary: {result.get('summary')}")
    
    # Test 3: Dashboard insights
    print("\n3. Testing DASHBOARD insights:")
    result = generate_insights_function(insight_type="DASHBOARD")
    print(f"Success: {result.get('success')}")
    print(f"Response length: {len(result.get('response', ''))}")
    
    # Test 4: Invalid insight type
    print("\n4. Testing invalid insight type:")
    result = generate_insights_function(insight_type="INVALID_TYPE")
    print(f"Success: {result.get('success')}")
    print(f"Error: {result.get('error')}")

def test_dispatcher_integration():
    """Test calling insights through the intelligent dispatcher"""
    print("\n" + "=" * 80)
    print("TESTING DISPATCHER INTEGRATION")
    print("=" * 80)
    
    test_queries = [
        "show me current occupancy rate",
        "what's our monthly revenue?",
        "generate financial analytics for last quarter",
        "how many maintenance requests this month?",
        "show tenant statistics",
        "give me a full dashboard report",
        "analyze room performance metrics",
        "what's the lead conversion rate?",
        "occupancy insights for building_001"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = intelligent_function_selection(query)
        
        if result.get('success'):
            print(f"✅ Function called: {result.get('function_called')}")
            print(f"   Confidence: {result.get('confidence')}")
            
            # Check if insights function was called
            if result.get('function_called') == 'generate_insights_function':
                insights_result = result.get('result', {})
                print(f"   Insight type: {insights_result.get('insight_type')}")
                print(f"   Data available: {insights_result.get('data') is not None}")
                print(f"   Summary: {insights_result.get('summary', '')[:100]}...")
        else:
            print(f"❌ Error: {result.get('error')}")

def test_parameter_extraction():
    """Test how well the dispatcher extracts parameters from natural language"""
    print("\n" + "=" * 80)
    print("TESTING PARAMETER EXTRACTION")
    print("=" * 80)
    
    complex_queries = [
        {
            "query": "show me occupancy analytics for building_123 from January to March 2024",
            "expected_params": ["building_id", "start_date", "end_date"]
        },
        {
            "query": "financial report for last month",
            "expected_params": ["start_date", "end_date"]
        },
        {
            "query": "tenant metrics for all buildings",
            "expected_params": []
        }
    ]
    
    for test in complex_queries:
        print(f"\n📝 Query: '{test['query']}'")
        result = intelligent_function_selection(test['query'])
        
        if result.get('success') and result.get('function_called') == 'generate_insights_function':
            insights_result = result.get('result', {})
            print(f"✅ Successfully called insights function")
            print(f"   Parameters detected: {test['expected_params']}")
            print(f"   Insight type: {insights_result.get('insight_type')}")

def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "=" * 80)
    print("TESTING ERROR HANDLING")
    print("=" * 80)
    
    # Test with invalid date format
    print("\n1. Testing invalid date format:")
    result = generate_insights_function(
        insight_type="FINANCIAL",
        start_date="invalid-date-format"
    )
    print(f"Success: {result.get('success')}")
    print(f"Handled gracefully: {'error' not in result}")
    
    # Test with None parameters
    print("\n2. Testing with None parameters:")
    result = generate_insights_function(
        insight_type="OCCUPANCY",
        building_id=None,
        start_date=None,
        end_date=None
    )
    print(f"Success: {result.get('success')}")
    print(f"Handled gracefully: {result.get('success', False)}")

def run_all_tests():
    """Run all test suites"""
    print("\n🚀 STARTING INSIGHTS FUNCTION TESTS")
    print("=" * 80)
    
    try:
        # test_direct_function_calls()
        # test_dispatcher_integration()
        test_parameter_extraction()
        # test_error_handling()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()