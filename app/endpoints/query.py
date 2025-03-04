# app/endpoints/query.py
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# from ..services import query_service
from app.ai_dispatcher import function_dispatcher
from app.ai_functions import find_buildings_rooms_function
from app.db.connection import get_db

router = APIRouter()


@router.post("/query/", response_model=Dict[str, Any])
def process_query(query_request: Dict[str, str], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Process a natural language query using the AI function dispatcher (simulated AI agent).
    """
    query = query_request.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Query text is required in the request body.")

    print(f"Received User Query: {query}")  # Log user query

    # --- SIMULATE Gemini Structured Function Call Output ---
    # Simulating a more realistic Gemini function call response format
    if "find room" in query.lower() or "building" in query.lower() or "room" in query.lower() or "building" in query.lower():
        gemini_structured_output = {
            "action_type": "function_call",
            "function_call_details": {
                "name": "find_buildings_rooms_function",
                "parameters": {"query": query},
            },
        }
    elif "admin report" in query.lower() or "metrics" in query.lower() or "admin data" in query.lower():
        gemini_structured_output = {
            "action_type": "function_call",
            "function_call_details": {
                "name": "admin_data_query_function",
                "parameters": {"query": query},
            },
        }
    elif "schedule showing" in query.lower() or "viewing" in query.lower():
        gemini_structured_output = {
            "action_type": "function_call",
            "function_call_details": {
                "name": "schedule_showing_function",
                "parameters": {
                    "lead_id": "LEAD_TEST_123",  # Hardcoded for simulation
                    "room_id": "ROOM_TEST_456",  # Hardcoded
                    "operator_id": "1",  # Hardcoded
                    "date": "2024-07-28",  # Hardcoded
                    "time": "10:00 AM",  # Hardcoded
                },
            },
        }
    else:
        gemini_structured_output = {
            "response": "Sorry, I didn't understand that request. (No function call simulated for this query.)"
        }  # Default text response

    if "function_call_details" in gemini_structured_output:  # Check for function call
        function_call_details = gemini_structured_output["function_call_details"]
        function_name = function_call_details["name"]
        parameters = function_call_details.get("parameters", {})
        print(
            f"Parameters being passed to function_dispatcher: {parameters}"
        )  # ADDED LOG LINE - Verify parameters content
        function_result = function_dispatcher(
            function_name, parameters, db=db
        )
        return function_result # CORRECTED - Return function_result in IF branch
    else:
        return gemini_structured_output  # Return default text response in ELSE branch # CORRECTED - Return gemini_structured_output in ELSE branch TOO