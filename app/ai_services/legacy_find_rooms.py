from datetime import datetime
import json
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
from google.genai import types

# Define the function declaration for finding buildings and rooms
find_buildings_rooms_function_declaration = {
    "name": "find_buildings_rooms_function",
    "description": "Find buildings and rooms based on user query and filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language query from the user describing their room preferences (e.g., location, view, price range).",
            },
        },
        "required": ["query"],
    },
}

# Configure the client and tools
client = genai.Client(api_key=GEMINI_API_KEY)
tools = types.Tool(function_declarations=[find_buildings_rooms_function_declaration])
config = types.GenerateContentConfig(
    tools=[tools],              # Pass the tool
    temperature=0
)


def apply_room_filters(query: str, db: Session) -> list:
    """
    Apply keyword-based filters for room search based on user query.
    """
    filters = []  # List to accumulate filters
    keywords = query.lower().split()  # Split query into keywords
    room_data_list = []  # List to store room data

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
    if "ensuite bathroom" in query.lower() or "en-suite bathroom" in query.lower():
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

    # --- Price Range Filter ---
    price_keywords = ["cheap", "affordable", "budget", "inexpensive", "low rent", "under"]
    if any(keyword in query.lower() for keyword in price_keywords):
        filters.append(models.Room.private_room_rent <= 2000)  # Example: cheap rooms under $2000

    
    # New Filters for Room Status


      # --- Maximum People in Room Filter ---
    if "maximum people" in query.lower() or "max people" in query.lower():
        for keyword in keywords:
            if keyword.isdigit():  # Check if the keyword is a number
                filters.append(models.Room.maximum_people_in_room <= int(keyword))

    # --- Floor Number Filter ---
    if "floor" in query.lower():
        for keyword in keywords:
            if keyword.isdigit():  # Check if the keyword is a number
                filters.append(models.Room.floor_number == int(keyword))

    # --- Total Rooms in House Filter ---
    if "total rooms" in query.lower():
        for keyword in keywords:
            if keyword.isdigit():  # Check if the keyword is a number
                filters.append(models.Room.total_rooms == int(keyword))

    # --- Room Size (Sq. Footage) Filter ---
    if "sq footage" in query.lower() or "square footage" in query.lower():
        for keyword in keywords:
            if keyword.isdigit():  # Check if the keyword is a number
                filters.append(models.Room.sq_footage >= int(keyword))  # Minimum room size filter    

    # Apply filters to query
    rooms_query = db.query(models.Room)  # Start with base query
    if filters:
        rooms_query = rooms_query.filter(*filters)  # Apply combined filters using *filters

    # Fetch rooms and structure the data
    rooms = rooms_query.limit(10).all()  # Limit results to 10 for example

    for room in rooms:
        room_data_list.append(
            {
                "room_id": room.room_id,
                "room_number": room.room_number,
                "building_id": room.building_id,
                "building_name": room.building.building_name,
                "full_address": room.building.full_address,
                "view": room.view,
                "private_room_rent": room.private_room_rent,
                "status": room.status,
                "bathroom_type": room.bathroom_type,
                "bed_size": room.bed_size,
                "bed_type": room.bed_type,
                "sq_footage": room.sq_footage,
            }
        )

    return room_data_list


def find_buildings_rooms_function(query: str, db: Session) -> dict:
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",                      #"gemini-2.0-flash",  
            contents=f"""
            You are an EXTREMELY helpful AI assistant for function calling.
            User Query: '{query}'
            Your ABSOLUTE PRIMARY TASK is to use the 'find_buildings_rooms_function' to respond.
            Respond ONLY with the function call, NO TEXT.
            """,  
            config=config,  # Pass config with tools
        )


        gemini_response_text = response.text  # Extract text response from Gemini API
        # Check for a function call in the response (Kept this part as is, per your request)
        if response.function_calls:  # Check for function_calls (same structure as original)
            function_call = response.function_calls[0]  # Access function_calls list
            function_name = function_call.name
            arguments = function_call.args  # Access args directly - args is already a dict-like object

            print(f"Function to call: {function_name}")
            print(f"Arguments: {arguments}")

            # Check if the function name is 'find_buildings_rooms_function' before processing
            if function_name == "find_buildings_rooms_function":
                # Call the filtering function with the user query
                room_data_list = apply_room_filters(query, db)  # Apply filters based on the user query
                # Log and return results
                function_result_success = {"response": gemini_response_text, "data": room_data_list, "parameters": arguments}
                print(f"AI Functions - find_buildings_rooms_function - Success Return Value: {function_result_success}")
                return function_result_success  # Return Gemini response and room data
            else:
                # Handle unexpected function name (security or logic)
                function_result_error = {
                    "error": f"Unexpected function name: {function_name}",
                    "response": "Function call error - Name mismatch",
                }
                print(f"AI Functions - find_buildings_rooms_function - Error Return Value: {function_result_error}")
                return function_result_error  # Handle unexpected function name

        else:
            # No function calls found in the response
            function_result_fallback = {
                "response": gemini_response_text,
                "data": [],
                "warning": "No function call detected in Gemini response - Fallback text response.",
            }
            print(f"AI Functions - find_buildings_rooms_function - Fallback Return Value: {function_result_fallback}")
            gemini_response_text = response.text  # Fallback to text response if no function call (though prompt is designed for function call)
            return function_result_fallback  # Indicate fallback response

    except Exception as e:
        error_message = f"Error during Gemini API call (V3 - No Dispatch Call in AI Functions): {e}"
        print(f"AI Functions - find_buildings_rooms_function - Error: {error_message}")
        function_result_error = {
            "error": error_message,
            "function_name": "find_buildings_rooms_function",
            # "parameters": parameters,
            "response": "Error in room search - Function Calling V3 - No Dispatch Call in AI Functions",
            # "data": parameters,  # Include parameters in error response
        }
        return function_result_error  # Return error with details