# app/ai_dispatcher.py
from typing import Dict, Any

from app.ai_functions import admin_data_query_function, create_communication_function, filter_rooms_function, find_buildings_rooms_function, generate_document_function, generate_insights_function, manage_checklist_function, process_maintenance_request_function, schedule_event_function, schedule_showing_function
from app.db.connection import get_db  # Import get_db
from fastapi import Depends  # Import Depends
from sqlalchemy.orm import Session  # Import Session

# Define AI_FUNCTIONS_REGISTRY here, in app/ai_dispatcher.py
AI_FUNCTIONS_REGISTRY = {
    "find_buildings_rooms_function": find_buildings_rooms_function,  # Use function_name as key
    "admin_data_query_function": admin_data_query_function,
    "schedule_showing_function": schedule_showing_function,
    "filter_rooms_function": filter_rooms_function,
    "schedule_event_function": schedule_event_function,
    "process_maintenance_request_function": process_maintenance_request_function,
    "generate_insights_function": generate_insights_function,
    "create_communication_function": create_communication_function,
    "generate_document_function": generate_document_function,
    "manage_checklist_function": manage_checklist_function,
}


def function_dispatcher(
    function_name: str, parameters: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, Any]:  # Add db Dependency to Dispatcher
    """Dispatches function calls based on function name and parameters, resolving db dependency."""
    function = AI_FUNCTIONS_REGISTRY.get(function_name)
    if function:
        try:
            print(
                f"Dispatching function: {function_name} with params: {parameters}"
            )  # Logging dispatch
            result = function(db=db, **parameters)  # Call the function with db and other parameters
            return result
        except Exception as e:
            error_message = f"Error executing function {function_name}: {e}"
            print(error_message)
            return {
                "error": f"Function execution failed: {function_name} - {e}"
            }  # Basic error response
    else:
        error_message = f"Function '{function_name}' not found in registry."
        print(error_message)  # Log function not found error
        return {
            "error": error_message
        }  # Function not found error response