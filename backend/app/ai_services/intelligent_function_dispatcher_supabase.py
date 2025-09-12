# Fixed version for intelligent_function_dispatcher_supabase.py

import json
from typing import Dict, Any
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig

from app.ai_services.update_handler import update_function_sync
from app.ai_services.intelligent_building_room_finder import unified_room_search_function
from app.ai_services.v3_intelligent_insights_supabase import generate_insights_function
from app.ai_services.hallucination_free_query_processor import HallucinationFreeQueryProcessor

# Initialize the universal query processor
universal_processor = HallucinationFreeQueryProcessor()

def universal_query_function(query: str, **kwargs) -> Dict[str, Any]:
    """
    Universal query function using hallucination-free processor.
    Handles any natural language query with guaranteed accuracy.
    Modified to work without nest_asyncio.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    # Default user context
    user_context = {
        "user_id": kwargs.get("user_id", "anonymous"),
        "permissions": kwargs.get("permissions", ["basic"]),
        "role": kwargs.get("role", "user")
    }
    
    # Process query using the universal processor
    try:
        # Run async function in a thread pool to avoid event loop conflicts
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(universal_processor.process_query(query, user_context))
            finally:
                loop.close()
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            result = future.result()
        
        return {
            "success": result.success,
            "response": result.message,
            "data": result.data,
            "metadata": result.metadata,
            "errors": result.errors,
            "warnings": result.warnings
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Universal query processing failed: {str(e)}",
            "response": "Failed to process your query. Please try again.",
            "data": []
        }

# Create function registry with updated functions
AI_FUNCTIONS_REGISTRY = {
    # "unified_room_search_function": unified_room_search_function,  
    # "generate_insights_function": generate_insights_function,
    "universal_query_function": universal_query_function,  # NEW: Universal query function
    "update_function": update_function_sync,
    # Add other functions
}

client = genai.Client(api_key=GEMINI_API_KEY)

def intelligent_function_selection(query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Use LLM to determine which function to call and execute it directly
    """
    print(f"🤖 Analyzing query: '{query}'")
    print(f"📋 User context received: {user_context}")  # Add debug
    
    # Default user context if not provided
    if user_context is None:
        user_context = {"role": "user", "permissions": ["basic"]}

    
    # Get available function names for the prompt
    available_functions = list(AI_FUNCTIONS_REGISTRY.keys())
    functions_list = ", ".join(available_functions)
    
    system_prompt = f"""
    You are an intelligent property management assistant. Analyze the user query and determine the most appropriate function to call.
    
    User Query: "{query}"
    
    Available functions: {functions_list}
    
    Guidelines:    

    Use universal_query_function for:
    - ANY query that reads, searches, or analyzes data
    - ANY query that doesn't fit the above categories
    - Keywords: find, show, list, search, display, what, how many, get, view, report, analyze
    - This handles ALL read operations including room searches and analytics
    - Complex queries requiring multiple tables
    - Custom queries not covered by specific functions
    - Queries about tenants, leads, maintenance, scheduling, etc.
    - When you're unsure which specific function to use
    - Keywords: tenant, lead, maintenance, schedule, event, document, message, notification, checklist
    - This is the most flexible and powerful option for any query
    
    Use update_function for:
    - ANY query that modifies, changes, or updates existing data
    - Room updates: status changes, price adjustments, amenity updates, maintenance flags
    - Tenant updates: payment status, lease dates, contact info, move-out dates
    - Lead updates: status progression, contact info, conversion tracking
    - Building updates: amenity changes, policy updates
    - Keywords: update, change, modify, set, mark, edit, fix, correct, adjust, make, convert, switch, turn, assign, revise
    - Examples: 
      * "change room 101 to occupied" 
      * "mark tenant John Doe's payment as late"
      * "update room 205 rent to $2500"
      * "set building A as pet-friendly"
      * "mark all rooms in building B for maintenance"
      * "convert lead Sarah to approved status"
      * "fix the wrong rent amount for room 303"
      * "assign room 102 to maintenance status"
      * "revise tenant lease end date to next month"
      * "make room 201 available"
      * "switch Sarah's lead status to viewing scheduled"
    - DO NOT use for: creating new records, deleting records, or reading/searching data
    - This handles ALL update/modification operations on existing records
    
    Respond ONLY with the function call, NO TEXT
    Return JSON with:
    {{
        "function_name": "<exact_function_name_from_registry>",
        "parameters": {{
            "query": "{query}",
            "user_context": {{
                "role": "user",
                "permissions": ["basic"]
            }}
        }},
        "confidence": <0.0-1.0>
    }}
    Examples:
    - "show all tenants with late payments" → universal_query_function
    - "find maintenance requests by priority" → universal_query_function
    - "list leads in showing scheduled status" → universal_query_function
    
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
        
        parameters["query"] = query
        parameters["user_context"] = user_context
        
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
        # Fallback to universal query for read operations
        try:
            # Simple keyword check for fallback
            update_keywords = ['update', 'change', 'modify', 'set', 'mark', 'edit', 'fix', 'correct']
            is_update = any(keyword in query.lower() for keyword in update_keywords)
            
            if is_update:
                function_name = "update_function"
            else:
                function_name = "universal_query_function"
            
            result = AI_FUNCTIONS_REGISTRY[function_name](
                query=query,
                user_context=user_context  
            )
            
            return {
                "success": True,
                "function_called": function_name,
                "result": result,
                "confidence": 0.5,
                "note": "Fallback function selection due to LLM error"
            }
        except Exception as fallback_error:
            return {
                "success": False,
                "error": f"Both LLM and fallback failed: {e}, {fallback_error}"
            }