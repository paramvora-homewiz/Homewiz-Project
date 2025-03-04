# app/ai_functions.py
from typing import Dict, Any, List
from google import genai
from app.config import GEMINI_API_KEY  # Import API Key from config
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.connection import get_db
from app.db import models
from google.genai.types import (  # Double check these imports are exactly as shown
            FunctionDeclaration,
            GenerateContentConfig,
            Tool,
        )

# Initialize Gemini Client - using genai.Client as per docs
client = genai.Client(api_key=GEMINI_API_KEY)

# Define function declaration for Gemini Function Calling
find_buildings_rooms_function_declaration = {
    "name": "find_buildings_rooms_function",  # MUST match function name in AI_FUNCTIONS_REGISTRY
    "description": "Find buildings and rooms based on user query and filters.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query from the user describing their room preferences (e.g., location, view, price range).",
            }
        },
        "required": ["query"],
    },
}


def find_buildings_rooms_function(query: str, db: Session = Depends(get_db)) -> Dict[str, Any]:  # function_dispatcher import REMOVED - no longer needed
    """Finds buildings and rooms based on user query using Gemini Function Calling and database."""
    print(f"AI Function Called: find_buildings_rooms_function with query: '{query}'")

    parameters = {}  # Initialize parameters HERE, BEFORE the try block
    room_data_list = [] # Initialize room_data_list here for database results
    gemini_response_text = "" # Initialize gemini_response_text

    # --- Gemini API Call with Function Calling ---
    try:
        # --- Function Declaration (Simplified for Troubleshooting) ---
        find_buildings_rooms_declaration_local = FunctionDeclaration(  # Using FunctionDeclaration class - LOCAL VARIABLE
            name="find_buildings_rooms_function",  # MUST match registry key
            description="Find buildings and rooms based on user query and filters.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",  # Using STRING type as in example - was "string" before
                        "description": "Natural language query from the user",
                    }
                },
                "required": ["query"],
            },
        )

        sales_tool = Tool(  # Create Tool object
            function_declarations=[find_buildings_rooms_declaration_local],  # Pass list of FunctionDeclarations - LOCAL VARIABLE
        )

        generate_content_config = GenerateContentConfig(  # Create GenerateContentConfig
            tools=[sales_tool],  # Pass the Tool
            temperature=0,  # Set temperature
        )

        response = client.models.generate_content(  # client.models.generate_content - CORRECT client call
            model="gemini-2.0-flash",  
            contents=f"""
    You are an EXTREMELY helpful AI assistant for function calling.
    User Query: '{query}'
    Your ABSOLUTE PRIMARY TASK is to use the 'find_buildings_rooms_function' to respond.
    Respond ONLY with the function call, NO TEXT.
    """,  # Simplified, direct prompt - focus on function call
            config=generate_content_config,  # Pass config with tools
        )

        if response.function_calls:  # Check for function_calls (different attribute name in response object)
            function_call = response.function_calls[0]  # Access function_calls list
            function_name = function_call.name
            arguments = function_call.args  # Access args directly - args is already a dict-like object

            print(
                f"Gemini Function Call Detected (Actual - V3 - No Dispatch Call in AI Functions): Function Name: {function_name}, Arguments: {arguments}"  # V3 log - no dispatch call
            )

            if function_name == "find_buildings_rooms_function":  # Verify function name matches (important for security and control)

                # --- Database Query (Improved Keyword-Based Filtering - V2 - Added bathroom, bed size, price) ---
                filters = []  # List to accumulate filters
                keywords = query.lower().split()  # Split query into keywords

                # --- View Filters ---
                if "city view" in query.lower():
                    filters.append(models.Room.view.ilike(f"%city%"))
                if "bay view" in query.lower():
                    filters.append(models.Room.view.ilike(f"%bay%"))
                if "garden view" in query.lower():
                    filters.append(models.Room.view.ilike(f"%garden%"))
                if "street view" in query.lower():
                    filters.append(models.Room.view.ilike(f"%street%"))

                # --- Bathroom Type Filters ---
                if "private bathroom" in query.lower():
                    filters.append(models.Room.bathroom_type == "Private")
                if "ensuite bathroom" in query.lower() or "en-suite bathroom" in query.lower():  # Handle variations
                    filters.append(models.Room.bathroom_type == "En-Suite")
                if "shared bathroom" in query.lower():
                    filters.append(models.Room.bathroom_type == "Shared")

                # --- Bed Size Filters ---
                if "king bed" in query.lower():
                    filters.append(models.Room.bed_size == "King")
                if "queen bed" in query.lower():
                    filters.append(models.Room.bed_size == "Queen")
                if "full bed" in query.lower():
                    filters.append(models.Room.bed_size == "Full")
                if "twin bed" in query.lower():
                    filters.append(models.Room.bed_size == "Twin")

                # --- Basic Price Range Filter (Example - needs more robust parsing for real app) ---
                price_keywords = ["cheap", "affordable", "budget", "inexpensive", "low rent", "under"]  # Simple price keywords
                if any(keyword in query.lower() for keyword in price_keywords):  # Check if any price keyword is present
                    filters.append(
                        models.Room.private_room_rent <= 2000
                    )  # Example: cheap rooms under $2000 - HARDCODED for now

                rooms_query = db.query(models.Room)  # Start with base query
                if filters:  # Apply filters only if there are any
                    rooms_query = rooms_query.filter(*filters)  # Apply combined filters using *filters (splat operator)

                rooms = rooms_query.limit(10).all()  # Limit results

                for room in rooms:
                    room_data_list.append(
                        {  # Structure room data as dictionaries
                            "room_id": room.room_id,
                            "room_number": room.room_number,
                            "building_id": room.building_id,
                            "building_name": room.building.building_name,  # Include building name for clarity in data
                            "full_address": room.building.full_address,  # Include full address
                            "view": room.view,
                            "private_room_rent": room.private_room_rent,
                            "status": room.status,
                            "bathroom_type": room.bathroom_type,
                            "bed_size": room.bed_size,
                            "bed_type": room.bed_type,
                            "sq_footage": room.sq_footage,
                            # Add other relevant room attributes to include in the response
                        }
                    )
                function_result_success = {"response": gemini_response_text, "data": room_data_list}  # Capture success response in variable
                print(
                    f"AI Functions - find_buildings_rooms_function - Success Return Value: {function_result_success}"
                )  # ADD THIS LOG - Log success return value
                return function_result_success  # Return Gemini response and room data
            else:
                return {
                    "error": f"Unexpected function name from Gemini: {function_name}",
                    "response": "Function call error - Name mismatch",
                }  # Handle unexpected function name

        else:  # No function call in Gemini response (unlikely in this setup, but good to handle)
            function_result_fallback = {"response": gemini_response_text, "data": [], "warning": "No function call detected in Gemini response - Fallback text response."}  # Capture fallback response in variable
            print(f"AI Functions - find_buildings_rooms_function - Fallback Return Value: {function_result_fallback}")  # ADD THIS LOG - Log fallback return value
            gemini_response_text = response.text  # Fallback to text response if no function call (though prompt is designed for function call)
            return function_result_fallback  # Indicate fallback

    except Exception as e:
        error_message = f"Error during Gemini API call (V3 - No Dispatch Call in AI Functions): {e}"  # V3 log - no dispatch call
        print(error_message)
        return {
            "error": error_message,
            "function_name": "find_buildings_rooms_function",  # Added function_name for clarity in error case
            "parameters": parameters,  # Include parameters in error response - parameters will now always be defined (even if empty)
            "response": "Error in room search - Function Calling V3 - No Dispatch Call in AI Functions",  # V3 error message
            "data": parameters,  # Include parameters in error response
        }


def admin_data_query_function(query: str) -> Dict[str, Any]:
    """Handles admin data queries using Gemini."""
    print(f"AI Function Called: admin_data_query_function with query: '{query}'")

    # --- Gemini API Call for Admin Data Query ---
    try:
        response = client.models.generate_content(  # Use client.models.generate_content
            model="gemini-2.0-flash",  # Specify model here - using "gemini-2.0-flash"
            contents=f"Answer this admin data query: {query}. Provide a structured JSON response with 'response' (text summary) and 'data' (list of key-value pairs or table data if applicable).",
        )
        gemini_response_text = response.text
        # **Important**: In a real app, you would parse Gemini's response to extract structured data
        # For now, returning raw text and sample data structure
        sample_admin_data = [
            {"metric": "Simulated Occupancy Rate", "value": "92%"},
            {"metric": "Simulated Average Rent", "value": "$2500"},
        ]  # Still using sample data for now, Gemini will provide text response
        return {
            "response": gemini_response_text,
            "data": sample_admin_data,
        }  # Modify to parse structured data from Gemini later

    except Exception as e:
        error_message = f"Error during Gemini API call for admin query: {e}"
        print(error_message)
        return {
            "error": error_message,
            "response": "Error processing admin query.",
        }  # Basic error response


def schedule_showing_function(lead_id: str, room_id: str, operator_id: str, date: str, time: str) -> Dict[str, str]:
    """Schedules a showing (simulated backend logic for now)."""
    print(
        f"AI Function Called: schedule_showing_function for lead_id: {lead_id}, room_id: {room_id}, operator: {operator_id}, date: {date}, time: {time}"
    )

    # --- Gemini API Call for Showing Confirmation (Optional - for richer response) ---
    try:
        response = client.models.generate_content(  # Use client.models.generate_content
            model="gemini-2.0-flash",  # Specify model here - using "gemini-2.0-flash"
            contents=f"Confirm showing scheduled for lead ID {lead_id}, room ID {room_id}, operator ID {operator_id}, date {date}, time {time}. Provide a confirmation message.",
        )
        confirmation_message = response.text  # Use Gemini's confirmation message
    except Exception as e:
        confirmation_message = (
            f"Showing scheduled (Gemini confirmation failed - {e})"
        )  # Fallback message

    # --- Simulated Backend Logic (No actual scheduling system yet) ---
    # In a real implementation, you would:
    # 1. Update database to record showing details
    # 2. Interact with a calendar/scheduling system
    # 3. Potentially notify operator and lead

    return {
        "response": confirmation_message,
        "status": "scheduled",
    }  # Return Gemini's confirmation or fallback