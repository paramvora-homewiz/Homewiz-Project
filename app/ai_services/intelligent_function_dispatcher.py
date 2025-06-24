# app/ai_services/intelligent_function_dispatcher.py

import json
from typing import Dict, Any
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from sqlalchemy.orm import Session

# Import all functions
from app.ai_services.v1_intelligent_room_finder import find_buildings_rooms_function
from app.ai_services.v2_intelligent_room_finder import filter_rooms_function
from app.ai_functions import (
    admin_data_query_function, 
    schedule_showing_function,
    filter_rooms_function,
    schedule_event_function,
    process_maintenance_request_function,
    generate_insights_function,
    create_communication_function,
    generate_document_function,
    manage_checklist_function
)

# Create function registry
AI_FUNCTIONS_REGISTRY = {
    "find_buildings_rooms_function": find_buildings_rooms_function,
    "filter_rooms_function": filter_rooms_function,
    "admin_data_query_function": admin_data_query_function,
    "schedule_showing_function": schedule_showing_function,
    "schedule_event_function": schedule_event_function,
    "process_maintenance_request_function": process_maintenance_request_function,
    "generate_insights_function": generate_insights_function,
    "create_communication_function": create_communication_function,
    "generate_document_function": generate_document_function,
    "manage_checklist_function": manage_checklist_function,
}

client = genai.Client(api_key=GEMINI_API_KEY)

def intelligent_function_selection(query: str, db: Session) -> Dict[str, Any]:
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
    Use find_buildings_rooms_function for:
    - Basic room searches: price, view, bathroom, bed size, room amenities

    Use filter_rooms_function for:
    - Building features: gym, laundry, wifi, utilities, pet-friendly, security
    - Location queries: downtown, area, neighborhood, transportation
    - Advanced room criteria: floor preferences, size requirements, availability dates

    Other functions:
    - For scheduling tours, showings, appointments → use schedule_showing_function
    - For reports, analytics, metrics, dashboard requests → use generate_insights_function
    - For maintenance issues, repairs, work orders → use process_maintenance_request_function
    - For sending messages, notifications, announcements → use create_communication_function
    - For admin data queries → use admin_data_query_function
    - For document generation → use generate_document_function
    - For checklist management → use manage_checklist_function
    - For event scheduling → use schedule_event_function

    Respond ONLY with the function call, NO TEXT
    Return JSON with:
    {{
        "function_name": "<exact_function_name_from_registry>",
        "parameters": {{"query": "{query}", "additional_param": "value"}},
        "confidence": <0.0-1.0>
    }}
    
    Choose the most appropriate function and extract relevant parameters from the query.
    Return ONLY JSON.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=system_prompt,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=100
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
            
            # Execute function with parameters
            try:
                # Pass db session and parameters to the function
                function_result = function_to_call(db=db, **parameters)
                
                return {
                    "success": True,
                    "function_called": function_name,
                    "result": function_result,
                    "confidence": result.get("confidence", 0.8)                 
                }
                
            except Exception as func_error:
                print(f"❌ Function execution error: {func_error}")
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
            result = AI_FUNCTIONS_REGISTRY["find_buildings_rooms_function"](db=db, query=query)
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