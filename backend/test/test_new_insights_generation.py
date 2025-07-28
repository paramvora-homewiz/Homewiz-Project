# tests/test_insights_generation.py

from app.ai_services.v3_intelligent_insights_sql import generate_insights_function


def test_insights_generation():
    """Test insight generation with SQL."""
    
    print("🧪 Testing SQL-based Insights Generation")
    print("=" * 60)
    
    test_cases = [
        ("OCCUPANCY", {}),
        ("FINANCIAL", {"building_id": "BLDG001"}),
        ("LEAD_CONVERSION", {"start_date": "2024-01-01", "end_date": "2024-12-31"}),
        ("TENANT", {}),
        ("MAINTENANCE", {}),
        ("ROOM_PERFORMANCE", {}),
        ("DASHBOARD", {}),
        # Test with natural language dates
        ("LEAD_CONVERSION", {"query": "How many leads converted last quarter?"}),
        ("FINANCIAL", {"query": "Show revenue for last month"})
    ]
    
    for test_case in test_cases:
        if isinstance(test_case[1], dict):
            insight_type = test_case[0]
            context = test_case[1]
        else:
            insight_type = test_case[0]
            context = test_case[1]
            
        print(f"\n📊 Testing {insight_type} insights")
        print(f"Context: {context}")
        
        result = generate_insights_function(insight_type=insight_type, **context)
        
        if result['success']:
            print(f"✅ Success!")
            print(f"Summary: {result.get('summary', 'N/A')}")
            print(f"Analysis: {result.get('analysis', 'N/A')[:200]}...")
            if 'metadata' in result and 'date_range' in result['metadata']:
                print(f"Date Range: {result['metadata']['date_range']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        print("-" * 50)


if __name__ == "__main__":
    test_insights_generation()