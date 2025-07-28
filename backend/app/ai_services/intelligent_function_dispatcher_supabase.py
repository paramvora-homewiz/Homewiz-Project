# app/ai_services/intelligent_function_dispatcher_supabase.py

import json
from typing import Dict, Any
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig


from app.ai_services.intelligent_building_room_finder import unified_room_search_function
from app.ai_services.v3_intelligent_insights_supabase import generate_insights_function

# Import other functions (if they exist and are converted to Supabase)
# from app.ai_services.schedule_showing_function import schedule_showing_function
# from app.ai_services.other_functions import other_function

# Create function registry with updated functions
AI_FUNCTIONS_REGISTRY = {
    "unified_room_search_function": unified_room_search_function,  
    "generate_insights_function": generate_insights_function,       
    # Add other functions
}

client = genai.Client(api_key=GEMINI_API_KEY)

def intelligent_function_selection(query: str) -> Dict[str, Any]:
    """
    Use LLM to determine which function to call and execute it directly
    """
    print(f"🤖 Analyzing query: '{query}'")
    
    # Get available function names for the prompt
    available_functions = list(AI_FUNCTIONS_REGISTRY.keys())
    functions_list = ", ".join(available_functions)
    
    system_prompt = f"""
    You are an intelligent property management assistant. Analyze the user query and determine the most appropriate function to call.
    
    User Query: "{query}"
    
    Available functions: {functions_list}
    
    Guidelines:
    
    Use unified_room_search_function for:
    - ANY room or property search queries
    - Queries about available rooms, apartments, or properties
    - Searches with criteria like price, location, amenities, features
    - Questions about room details, building features, or availability
    - Keywords: room, apartment, property, available, find, search, show, looking for, need
    - This handles BOTH room-specific AND building-specific features
    
    Use generate_insights_function for:
    - Analytics requests: occupancy rates, financial metrics, revenue analysis
    - Reports: dashboard, performance metrics, tenant statistics
    - Business insights: lead conversion, maintenance analytics
    - Any query asking for statistics, metrics, analysis, or insights
    - Keywords: analytics, insights, report, metrics, statistics, occupancy, revenue, performance, how many, conversion rate, dashboard
    
    Respond ONLY with the function call, NO TEXT
    Return JSON with:
    {{
        "function_name": "<exact_function_name_from_registry>",
        "parameters": {{"query": "{query}"}},
        "confidence": <0.0-1.0>
    }}
    
    For generate_insights_function, also extract the insight_type from keywords:
    - occupancy, availability, occupied → "OCCUPANCY"
    - revenue, financial, money, income → "FINANCIAL"
    - leads, conversion, sales funnel → "LEAD_CONVERSION"
    - maintenance, repairs, issues → "MAINTENANCE"
    - room performance, best/worst rooms → "ROOM_PERFORMANCE"
    - tenant, resident, lease → "TENANT"
    - dashboard, overview, summary, all metrics → "DASHBOARD"
    
    Examples:
    - "show me available rooms under 2000" → unified_room_search_function
    - "find rooms in downtown with gym" → unified_room_search_function
    - "what's the occupancy rate?" → generate_insights_function with insight_type: "OCCUPANCY"
    - "revenue report for last month" → generate_insights_function with insight_type: "FINANCIAL"
    
    Choose the most appropriate function and extract relevant parameters from the query.
    Return ONLY JSON.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=system_prompt,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=150
            )
        )
        
        # Parse JSON response
        result_text = response.text.strip()
        if result_text.startswith('```json'):
            result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(result_text)
        function_name = result.get("function_name")
        parameters = result.get("parameters", {"query": query})
        
        # Validate and execute function
        if function_name in AI_FUNCTIONS_REGISTRY:
            print(f"✅ Executing: {function_name}")
            print(f"📋 Parameters: {parameters}")
            
            # Get the function from registry
            function_to_call = AI_FUNCTIONS_REGISTRY[function_name]
            
            # Execute function with parameters
            try:
                function_result = function_to_call(**parameters)
                
                return {
                    "success": True,
                    "function_called": function_name,
                    "result": function_result,
                    "confidence": result.get("confidence", 0.8)                 
                }
                
            except Exception as func_error:
                print(f"❌ Function execution error: {func_error}")
                import traceback
                traceback.print_exc()
                return {
                    "success": False,
                    "error": f"Function execution failed: {func_error}",
                    "function_called": function_name
                }
        
        else:
            print(f"❌ Invalid function: {function_name}")
            return {
                "success": False,
                "error": f"Function '{function_name}' not found in registry",
                "available_functions": available_functions
            }
    
    except Exception as e:
        print(f"❌ LLM analysis failed: {e}")
        # Fallback to room search for property queries
        if any(word in query.lower() for word in ['room', 'apartment', 'property', 'available', 'find']):
            try:
                result = AI_FUNCTIONS_REGISTRY["unified_room_search_function"](query=query)
                return {
                    "success": True,
                    "function_called": "unified_room_search_function",
                    "result": result,
                    "confidence": 0.5,
                    "note": "Fallback function used due to LLM error"
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "error": f"Both LLM and fallback failed: {e}, {fallback_error}"
                }
        else:
            return {
                "success": False,
                "error": f"LLM analysis failed: {e}"
            }


# Test the dispatcher
def test_function_dispatcher():
    """Test the function dispatcher with various queries."""
    
    test_queries = [
        # Room search queries
        # "Show me available rooms under $2000",
        "Find apartments in north beach with wifi and gym having rooms rent under $2000",
        # "I need a room with private bathroom",
        
        # Analytics queries
        # "What's the current occupancy rate?",
        # "Show me revenue metrics for this month",
        # "How many leads converted last quarter?",
        # "Generate a dashboard report",
        
        # Edge cases
        # "Hello",
        # "What's the weather?"
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