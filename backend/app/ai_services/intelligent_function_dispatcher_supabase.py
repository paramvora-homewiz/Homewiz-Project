# app/ai_services/intelligent_function_dispatcher_supabase.py

import json
from typing import Dict, Any
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig

# Import Supabase versions of functions
from app.ai_services.v1_intelligent_room_finder_supabase import find_buildings_rooms_function
from app.ai_services.v2_intelligent_room_finder_supabase import filter_rooms_function
from app.ai_services.v3_intelligent_insights_supabase import generate_insights_function

# Import other functions (these need to be updated to Supabase too)
# Comment out for now until they're converted
# from app.ai_functions import (
#     admin_data_query_function, 
#     schedule_showing_function,
#     schedule_event_function,
#     process_maintenance_request_function,
#     create_communication_function,
#     generate_document_function,
#     manage_checklist_function
# )

# Create function registry - now includes insights function
AI_FUNCTIONS_REGISTRY = {
    "find_buildings_rooms_function": find_buildings_rooms_function,
    "filter_rooms_function": filter_rooms_function,
    "generate_insights_function": generate_insights_function,  # Added insights function
    # Add other functions as they get converted
}

client = genai.Client(api_key=GEMINI_API_KEY)

def intelligent_function_selection(query: str) -> Dict[str, Any]:
    """
    Use LLM to determine which function to call and execute it directly
    Note: Removed db parameter as Supabase functions don't need it
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
    Use find_buildings_rooms_function for:
    - Basic room searches: price, view, bathroom, bed size, room amenities
    - Simple queries about rooms without building features

    Use filter_rooms_function for:
    - Building features: gym, laundry, wifi, utilities, pet-friendly, security
    - Location queries: downtown, area, neighborhood, transportation
    - Advanced room criteria combined with building features
    - Complex queries mentioning both room and building requirements

    Use generate_insights_function for:
    - Analytics requests: occupancy rates, financial metrics, revenue analysis
    - Reports: dashboard, performance metrics, tenant statistics
    - Business insights: lead conversion, maintenance analytics
    - Any query asking for statistics, metrics, analysis, or insights
    - Keywords: analytics, insights, report, metrics, statistics, occupancy, revenue, performance

    Respond ONLY with the function call, NO TEXT
    Return JSON with:
    {{
        "function_name": "<exact_function_name_from_registry>",
        "parameters": {{"query": "{query}", "insight_type": "<type>"}},
        "confidence": <0.0-1.0>
    }}
    
    For generate_insights_function, extract the insight_type from keywords:
    - occupancy, availability → "OCCUPANCY"
    - revenue, financial, money → "FINANCIAL"
    - leads, conversion, sales → "LEAD_CONVERSION"
    - maintenance, repairs → "MAINTENANCE"
    - room performance → "ROOM_PERFORMANCE"
    - tenant, resident → "TENANT"
    - dashboard, overview, all → "DASHBOARD"
    
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
            
            # Get the function from registry
            function_to_call = AI_FUNCTIONS_REGISTRY[function_name]
            
            # Execute function with parameters (no db needed for Supabase)
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
        # Fallback to default room search
        try:
            result = AI_FUNCTIONS_REGISTRY["find_buildings_rooms_function"](query=query)
            return {
                "success": True,
                "function_called": "find_buildings_rooms_function",
                "result": result,
                "confidence": 0.5,
                "note": "Fallback function used due to LLM error"
            }
        except Exception as fallback_error:
            return {
                "success": False,
                "error": f"Both LLM and fallback failed: {e}, {fallback_error}"
            }