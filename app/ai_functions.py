# app/ai_functions.py
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

# New function declarations for Gemini
filter_rooms_function_declaration = {
    "name": "filter_rooms_function",
    "description": "Filter rooms based on detailed user preferences and criteria.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Natural language query describing room preferences.",
            },
            "min_price": {
                "type": "NUMBER",
                "description": "Minimum price for filtering rooms.",
            },
            "max_price": {
                "type": "NUMBER",
                "description": "Maximum price for filtering rooms.",
            },
            "room_type": {
                "type": "STRING",
                "description": "Type of room (PRIVATE, SHARED).",
            },
            "bathroom_type": {
                "type": "STRING",
                "description": "Type of bathroom (PRIVATE, SHARED, EN_SUITE).",
            },
            "amenities": {
                "type": "ARRAY",
                "items": {
                    "type": "STRING"
                },
                "description": "List of desired amenities.",
            },
            "move_in_date": {
                "type": "STRING",
                "description": "Desired move-in date (YYYY-MM-DD format).",
            }
        },
        "required": ["query"],
    },
}

schedule_event_function_declaration = {
    "name": "schedule_event_function",
    "description": "Schedule an event such as a showing, maintenance visit, or move-in/out.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "event_type": {
                "type": "STRING",
                "description": "Type of event (SHOWING, MAINTENANCE, MOVE_IN, MOVE_OUT).",
            },
            "title": {
                "type": "STRING",
                "description": "Title of the event.",
            },
            "description": {
                "type": "STRING",
                "description": "Description of the event.",
            },
            "start_time": {
                "type": "STRING",
                "description": "Start time of the event (ISO format).",
            },
            "end_time": {
                "type": "STRING",
                "description": "End time of the event (ISO format).",
            },
            "room_id": {
                "type": "STRING",
                "description": "ID of the room for the event.",
            },
            "building_id": {
                "type": "STRING",
                "description": "ID of the building for the event.",
            },
            "operator_id": {
                "type": "STRING",
                "description": "ID of the operator for the event.",
            },
            "lead_id": {
                "type": "STRING",
                "description": "ID of the lead for the event.",
            },
            "tenant_id": {
                "type": "STRING",
                "description": "ID of the tenant for the event.",
            }
        },
        "required": ["event_type", "title", "start_time", "end_time"],
    },
}

process_maintenance_request_function_declaration = {
    "name": "process_maintenance_request_function",
    "description": "Create or update a maintenance request.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Action to perform (CREATE, UPDATE, ASSIGN).",
            },
            "request_id": {
                "type": "STRING",
                "description": "ID of the maintenance request to update.",
            },
            "title": {
                "type": "STRING",
                "description": "Title of the maintenance request.",
            },
            "description": {
                "type": "STRING",
                "description": "Description of the maintenance issue.",
            },
            "room_id": {
                "type": "STRING",
                "description": "ID of the room with the issue.",
            },
            "building_id": {
                "type": "STRING",
                "description": "ID of the building with the issue.",
            },
            "tenant_id": {
                "type": "STRING",
                "description": "ID of the tenant reporting the issue.",
            },
            "priority": {
                "type": "STRING",
                "description": "Priority of the issue (LOW, MEDIUM, HIGH, EMERGENCY).",
            },
            "assigned_to": {
                "type": "STRING",
                "description": "ID of the operator to assign the request to.",
            },
            "status": {
                "type": "STRING",
                "description": "New status for the request.",
            }
        },
        "required": ["action"],
    },
}

generate_insights_function_declaration = {
    "name": "generate_insights_function",
    "description": "Generate insights and analytics for properties and operations.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "insight_type": {
                "type": "STRING",
                "description": "Type of insight to generate (OCCUPANCY, FINANCIAL, LEAD_CONVERSION, MAINTENANCE, ROOM_PERFORMANCE, TENANT, DASHBOARD).",
            },
            "building_id": {
                "type": "STRING",
                "description": "Optional ID of the building to analyze.",
            },
            "start_date": {
                "type": "STRING",
                "description": "Start date for the analysis period (YYYY-MM-DD format).",
            },
            "end_date": {
                "type": "STRING",
                "description": "End date for the analysis period (YYYY-MM-DD format).",
            },
        },
        "required": ["insight_type"],
    },
}

create_communication_function_declaration = {
    "name": "create_communication_function",
    "description": "Send communications to leads, tenants, or operators.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "communication_type": {
                "type": "STRING",
                "description": "Type of communication (MESSAGE, NOTIFICATION, ANNOUNCEMENT).",
            },
            "content": {
                "type": "STRING",
                "description": "Content of the communication.",
            },
            "sender_type": {
                "type": "STRING",
                "description": "Type of sender (SYSTEM, OPERATOR, TENANT, LEAD).",
            },
            "sender_id": {
                "type": "STRING",
                "description": "ID of the sender.",
            },
            "recipient_type": {
                "type": "STRING",
                "description": "Type of recipient (OPERATOR, TENANT, LEAD, ALL).",
            },
            "recipient_id": {
                "type": "STRING",
                "description": "ID of the recipient.",
            },
            "recipient_ids": {
                "type": "ARRAY",
                "items": {
                    "type": "STRING"
                },
                "description": "List of recipient IDs for bulk communication.",
            },
            "title": {
                "type": "STRING",
                "description": "Title or subject of the communication.",
            },
            "building_id": {
                "type": "STRING",
                "description": "ID of the building for announcements.",
            }
        },
        "required": ["communication_type", "content"],
    },
}

generate_document_function_declaration = {
    "name": "generate_document_function",
    "description": "Generate documents like leases or applications.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "document_type": {
                "type": "STRING",
                "description": "Type of document to generate (LEASE, APPLICATION).",
            },
            "tenant_id": {
                "type": "STRING",
                "description": "ID of the tenant for the document.",
            },
            "lead_id": {
                "type": "STRING",
                "description": "ID of the lead for the document.",
            },
            "room_id": {
                "type": "STRING",
                "description": "ID of the room for the document.",
            },
            "building_id": {
                "type": "STRING",
                "description": "ID of the building for the document.",
            },
            "lease_start_date": {
                "type": "STRING",
                "description": "Start date for lease document.",
            },
            "lease_end_date": {
                "type": "STRING",
                "description": "End date for lease document.",
            },
            "monthly_rent": {
                "type": "NUMBER",
                "description": "Monthly rent amount for lease document.",
            },
            "deposit_amount": {
                "type": "NUMBER",
                "description": "Security deposit amount for lease document.",
            }
        },
        "required": ["document_type"],
    },
}

manage_checklist_function_declaration = {
    "name": "manage_checklist_function",
    "description": "Create or manage move-in/out checklists.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Action to perform (CREATE, UPDATE_STATUS, UPDATE_ITEM).",
            },
            "checklist_type": {
                "type": "STRING",
                "description": "Type of checklist (MOVE_IN, MOVE_OUT, INSPECTION).",
            },
            "checklist_id": {
                "type": "STRING",
                "description": "ID of the checklist to update.",
            },
            "item_id": {
                "type": "STRING",
                "description": "ID of the checklist item to update.",
            },
            "room_id": {
                "type": "STRING",
                "description": "ID of the room for the checklist.",
            },
            "building_id": {
                "type": "STRING",
                "description": "ID of the building for the checklist.",
            },
            "tenant_id": {
                "type": "STRING",
                "description": "ID of the tenant for the checklist.",
            },
            "operator_id": {
                "type": "STRING",
                "description": "ID of the operator for the checklist.",
            },
            "status": {
                "type": "STRING",
                "description": "New status for the checklist or item.",
            },
            "notes": {
                "type": "STRING",
                "description": "Notes for the checklist item.",
            }
        },
        "required": ["action"],
    },
}

# Implementation of the new AI functions
def filter_rooms_function(query: str, db: Session = Depends(get_db), **kwargs) -> Dict[str, Any]:
    """
    Advanced room filtering based on detailed user preferences.
    """
    print(f"AI Function Called: filter_rooms_function with query: '{query}' and params: {kwargs}")
    
    # Initialize filters
    filters = []
    
    # Basic filters from the query (reusing logic from find_buildings_rooms_function)
    keywords = query.lower().split()
    
    # Additional parameter-based filters
    if "min_price" in kwargs and kwargs["min_price"] is not None:
        filters.append(models.Room.private_room_rent >= kwargs["min_price"])
    
    if "max_price" in kwargs and kwargs["max_price"] is not None:
        filters.append(models.Room.private_room_rent <= kwargs["max_price"])
    
    if "room_type" in kwargs and kwargs["room_type"] is not None:
        if kwargs["room_type"].upper() == "PRIVATE":
            filters.append(models.Room.maximum_people_in_room == 1)
        elif kwargs["room_type"].upper() == "SHARED":
            filters.append(models.Room.maximum_people_in_room > 1)
    
    if "bathroom_type" in kwargs and kwargs["bathroom_type"] is not None:
        filters.append(models.Room.bathroom_type == kwargs["bathroom_type"])
    
    # Handle amenities
    if "amenities" in kwargs and kwargs["amenities"] is not None:
        for amenity in kwargs["amenities"]:
            amenity_lower = amenity.lower()
            if "fridge" in amenity_lower or "refrigerator" in amenity_lower:
                filters.append(models.Room.mini_fridge == True)
            if "sink" in amenity_lower:
                filters.append(models.Room.sink == True)
            if "bed" in amenity_lower and "bedding" in amenity_lower:
                filters.append(models.Room.bedding_provided == True)
            if "desk" in amenity_lower or "workspace" in amenity_lower:
                filters.append(models.Room.work_desk == True)
            if "chair" in amenity_lower:
                filters.append(models.Room.work_chair == True)
            if "heat" in amenity_lower or "heating" in amenity_lower:
                filters.append(models.Room.heating == True)
            if "air" in amenity_lower or "a/c" in amenity_lower or "ac" in amenity_lower:
                filters.append(models.Room.air_conditioning == True)
            if "tv" in amenity_lower or "television" in amenity_lower:
                filters.append(models.Room.cable_tv == True)
    
    # Handle move-in date
    if "move_in_date" in kwargs and kwargs["move_in_date"] is not None:
        try:
            move_in_date = datetime.strptime(kwargs["move_in_date"], "%Y-%m-%d").date()
            filters.append(ord(
                models.Room.booked_till < move_in_date,
                models.Room.booked_till == None
            ))
            filters.append(models.Room.ready_to_rent == True)
        except ValueError:
            print(f"Invalid move_in_date format: {kwargs['move_in_date']}")
    
    # Apply filters
    rooms_query = db.query(models.Room)
    if filters:
        rooms_query = rooms_query.filter(*filters)
    
    # Limit results and convert to list of dictionaries
    rooms = rooms_query.limit(20).all()
    
    room_data_list = []
    for room in rooms:
        # Get building info
        building = room.building
        
        room_data = {
            "room_id": room.room_id,
            "room_number": room.room_number,
            "building_id": room.building_id,
            "building_name": building.building_name if building else "Unknown",
            "full_address": building.full_address if building else "Unknown",
            "view": room.view,
            "private_room_rent": room.private_room_rent,
            "shared_room_rent_2": room.shared_room_rent_2,
            "status": room.status,
            "bathroom_type": room.bathroom_type,
            "bed_size": room.bed_size,
            "bed_type": room.bed_type,
            "sq_footage": room.sq_footage,
            "floor_number": room.floor_number,
            "maximum_people_in_room": room.maximum_people_in_room,
            "features": {
                "mini_fridge": room.mini_fridge,
                "sink": room.sink,
                "bedding_provided": room.bedding_provided,
                "work_desk": room.work_desk,
                "work_chair": room.work_chair,
                "heating": room.heating,
                "air_conditioning": room.air_conditioning,
                "cable_tv": room.cable_tv,
                "room_storage": room.room_storage,
            }
        }
        
        room_data_list.append(room_data)
    
    # Generate a helpful response analyzing the results
    gemini_response_text = ""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""Analyze these search results for a room search query: "{query}". 
            Total results found: {len(room_data_list)}. 
            Give a helpful summary of the types of rooms found, price ranges, and notable features. 
            Keep it under 3 paragraphs."""
        )
        gemini_response_text = response.text
    except Exception as e:
        gemini_response_text = f"Found {len(room_data_list)} rooms matching your criteria."
    
    return {
        "response": gemini_response_text,
        "data": room_data_list,
        "total_results": len(room_data_list),
        "query": query,
        "applied_filters": str(filters)
    }

def schedule_event_function(
    event_type: str,
    title: str,
    start_time: str,
    end_time: str,
    db: Session = Depends(get_db),
    **kwargs
) -> Dict[str, Any]:
    """
    Schedules an event such as a showing, maintenance visit, or move-in/out.
    """
    print(f"AI Function Called: schedule_event_function with event_type: '{event_type}' and title: '{title}'")
    
    # Import scheduling service
    from services import scheduling_service
    
    try:
        # Parse start and end times
        start_datetime = datetime.fromisoformat(start_time)
        end_datetime = datetime.fromisoformat(end_time)
        
        # Extract optional parameters
        description = kwargs.get("description")
        room_id = kwargs.get("room_id")
        building_id = kwargs.get("building_id")
        operator_id = int(kwargs["operator_id"]) if "operator_id" in kwargs and kwargs["operator_id"] else None
        lead_id = kwargs.get("lead_id")
        tenant_id = kwargs.get("tenant_id")
        
        # Create the event
        event = scheduling_service.create_event(
            db=db,
            event_type=event_type,
            title=title,
            description=description,
            start_time=start_datetime,
            end_time=end_datetime,
            room_id=room_id,
            building_id=building_id,
            operator_id=operator_id,
            lead_id=lead_id,
            tenant_id=tenant_id
        )
        
        # Get a friendly confirmation message from Gemini
        confirmation_message = ""
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""Create a friendly confirmation message for a {event_type.lower()} that was just scheduled:
                - Title: {title}
                - Date: {start_datetime.strftime('%A, %B %d, %Y')}
                - Time: {start_datetime.strftime('%I:%M %p')} to {end_datetime.strftime('%I:%M %p')}
                - {'Room: ' + room_id if room_id else ''}
                - {'Building: ' + building_id if building_id else ''}
                
                Keep it brief and conversational."""
            )
            confirmation_message = response.text
        except Exception as e:
            confirmation_message = f"Your {event_type.lower()} has been scheduled for {start_datetime.strftime('%A, %B %d at %I:%M %p')}."
        
        return {
            "success": True,
            "event_id": event.event_id,
            "event_type": event.event_type,
            "title": event.title,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "status": event.status,
            "response": confirmation_message
        }
    
    except Exception as e:
        error_message = f"Error scheduling event: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem scheduling the {event_type.lower()}. Please try again."
        }

def process_maintenance_request_function(
    action: str,
    db: Session = Depends(get_db),
    **kwargs
) -> Dict[str, Any]:
    """
    Creates, updates, or assigns a maintenance request.
    """
    print(f"AI Function Called: process_maintenance_request_function with action: '{action}'")
    
    # Import maintenance service
    from services import maintenance_service
    
    try:
        if action.upper() == "CREATE":
            # Validate required parameters
            required_params = ["title", "description", "room_id", "building_id", "tenant_id"]
            for param in required_params:
                if param not in kwargs or not kwargs[param]:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to create a maintenance request."
                    }
            
            # Create the request
            priority = kwargs.get("priority", "MEDIUM")
            assigned_to = int(kwargs["assigned_to"]) if "assigned_to" in kwargs and kwargs["assigned_to"] else None
            
            request = maintenance_service.create_maintenance_request(
                db=db,
                title=kwargs["title"],
                description=kwargs["description"],
                room_id=kwargs["room_id"],
                building_id=kwargs["building_id"],
                tenant_id=kwargs["tenant_id"],
                priority=priority,
                assigned_to=assigned_to
            )
            
            # Generate confirmation message
            confirmation_message = f"Maintenance request '{request.title}' has been created with {priority.lower()} priority and is currently {request.status.lower()}."
            
            return {
                "success": True,
                "request_id": request.request_id,
                "status": request.status,
                "priority": request.priority,
                "response": confirmation_message
            }
        
        elif action.upper() == "UPDATE":
            # Validate required parameters
            if "request_id" not in kwargs or not kwargs["request_id"]:
                return {
                    "success": False,
                    "error": "Missing required parameter: request_id",
                    "response": "Please provide the request ID to update a maintenance request."
                }
            
            if "status" not in kwargs or not kwargs["status"]:
                return {
                    "success": False,
                    "error": "Missing required parameter: status",
                    "response": "Please provide the new status to update a maintenance request."
                }
            
            # Update the request status
            request = maintenance_service.update_maintenance_request_status(
                db=db,
                request_id=kwargs["request_id"],
                status=kwargs["status"],
                notes=kwargs.get("notes")
            )
            
            if not request:
                return {
                    "success": False,
                    "error": f"Request not found with ID: {kwargs['request_id']}",
                    "response": "The maintenance request could not be found. Please check the request ID."
                }
            
            # Generate confirmation message
            confirmation_message = f"Maintenance request '{request.title}' has been updated to status: {request.status}."
            
            return {
                "success": True,
                "request_id": request.request_id,
                "status": request.status,
                "response": confirmation_message
            }
        
        elif action.upper() == "ASSIGN":
            # Validate required parameters
            if "request_id" not in kwargs or not kwargs["request_id"]:
                return {
                    "success": False,
                    "error": "Missing required parameter: request_id",
                    "response": "Please provide the request ID to assign a maintenance request."
                }
            
            if "assigned_to" not in kwargs or not kwargs["assigned_to"]:
                return {
                    "success": False,
                    "error": "Missing required parameter: assigned_to",
                    "response": "Please provide the operator ID to assign a maintenance request."
                }
            
            # Assign the request
            request = maintenance_service.assign_maintenance_request(
                db=db,
                request_id=kwargs["request_id"],
                operator_id=int(kwargs["assigned_to"])
            )
            
            if not request:
                return {
                    "success": False,
                    "error": f"Request not found with ID: {kwargs['request_id']}",
                    "response": "The maintenance request could not be found. Please check the request ID."
                }
            
            # Generate confirmation message
            confirmation_message = f"Maintenance request '{request.title}' has been assigned to operator ID: {request.assigned_to}."
            
            return {
                "success": True,
                "request_id": request.request_id,
                "assigned_to": request.assigned_to,
                "status": request.status,
                "response": confirmation_message
            }
        
        else:
            return {
                "success": False,
                "error": f"Invalid action: {action}",
                "response": f"'{action}' is not a valid action for maintenance requests. Please use CREATE, UPDATE, or ASSIGN."
            }
    
    except Exception as e:
        error_message = f"Error processing maintenance request: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": "There was a problem processing the maintenance request. Please try again."
        }

def generate_insights_function(
    insight_type: str,
    db: Session = Depends(get_db),
    **kwargs
) -> Dict[str, Any]:
    """
    Generates analytics and insights for property management.
    """
    print(f"AI Function Called: generate_insights_function with insight_type: '{insight_type}'")
    
    # Import analytics service
    from services import analytics_service
    
    try:
        # Parse optional parameters
        building_id = kwargs.get("building_id")
        
        # Parse dates if provided
        start_date = None
        end_date = None
        
        if "start_date" in kwargs and kwargs["start_date"]:
            try:
                start_date = datetime.strptime(kwargs["start_date"], "%Y-%m-%d")
            except ValueError:
                print(f"Invalid start_date format: {kwargs['start_date']}")
        
        if "end_date" in kwargs and kwargs["end_date"]:
            try:
                end_date = datetime.strptime(kwargs["end_date"], "%Y-%m-%d")
            except ValueError:
                print(f"Invalid end_date format: {kwargs['end_date']}")
        
        # Generate the insights based on type
        insight_data = {}
        insight_summary = ""
        
        if insight_type.upper() == "OCCUPANCY":
            insight_data = analytics_service.get_occupancy_rate(db, building_id)
            insight_summary = f"Current occupancy rate is {insight_data['occupancy_rate']}% with {insight_data['occupied_rooms']} out of {insight_data['total_rooms']} rooms occupied."
        
        elif insight_type.upper() == "FINANCIAL":
            insight_data = analytics_service.get_financial_metrics(db, building_id, start_date, end_date)
            insight_summary = f"Estimated monthly revenue is ${insight_data['estimated_monthly_revenue']} with average private room rent at ${insight_data['avg_private_rent']}."
        
        elif insight_type.upper() == "LEAD_CONVERSION":
            insight_data = analytics_service.get_lead_conversion_metrics(db, start_date, end_date)
            insight_summary = f"Overall lead conversion rate is {insight_data['overall_conversion_rate']}% with {insight_data['total_leads']} total leads in the period."
        
        elif insight_type.upper() == "MAINTENANCE":
            insight_data = analytics_service.get_maintenance_metrics(db, building_id, start_date, end_date)
            avg_resolution = insight_data.get('avg_resolution_time_hours')
            avg_resolution_text = f"Average resolution time is {avg_resolution} hours." if avg_resolution else "Average resolution time not available."
            insight_summary = f"There were {insight_data['total_requests']} maintenance requests in the period. {avg_resolution_text}"
        
        elif insight_type.upper() == "ROOM_PERFORMANCE":
            insight_data = analytics_service.get_room_performance_metrics(db, building_id)
            insight_summary = f"Analysis of {insight_data['total_rooms']} rooms showing top and bottom performers based on revenue generation."
        
        elif insight_type.upper() == "TENANT":
            insight_data = analytics_service.get_tenant_metrics(db, building_id)
            insight_summary = f"There are {insight_data['total_active_tenants']} active tenants with average lease duration of {insight_data['avg_lease_duration_days']} days."
        
        elif insight_type.upper() == "DASHBOARD":
            insight_data = analytics_service.get_dashboard_metrics(db, building_id)
            insight_summary = "Comprehensive dashboard with occupancy, financial, lead, maintenance, room, and tenant metrics."
        
        else:
            return {
                "success": False,
                "error": f"Invalid insight type: {insight_type}",
                "response": f"'{insight_type}' is not a valid insight type. Please choose from OCCUPANCY, FINANCIAL, LEAD_CONVERSION, MAINTENANCE, ROOM_PERFORMANCE, TENANT, or DASHBOARD."
            }
        
        # Get a detailed analysis from Gemini
        detailed_analysis = ""
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""Analyze these {insight_type.lower()} metrics and provide business insights:
                {json.dumps(insight_data, indent=2)}
                
                Focus on key trends, notable metrics, and actionable recommendations.
                Format the analysis in a business-friendly way with clear sections."""
            )
            detailed_analysis = response.text
        except Exception as e:
            detailed_analysis = f"Analysis of {insight_type.lower()} metrics shows {insight_summary}"
        
        return {
            "success": True,
            "insight_type": insight_type,
            "data": insight_data,
            "summary": insight_summary,
            "analysis": detailed_analysis,
            "response": detailed_analysis
        }
    
    except Exception as e:
        error_message = f"Error generating insights: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem generating {insight_type.lower()} insights. Please try again."
        }

def create_communication_function(
    communication_type: str,
    content: str,
    db: Session = Depends(get_db),
    **kwargs
) -> Dict[str, Any]:
    """
    Sends communications to leads, tenants, or operators.
    """
    print(f"AI Function Called: create_communication_function with type: '{communication_type}'")
    
    try:
        # Import services
        from services import message_service, notification_service, announcement_service
        
        if communication_type.upper() == "MESSAGE":
            # Validate required parameters
            required_params = ["sender_type", "recipient_type"]
            for param in required_params:
                if param not in kwargs or not kwargs[param]:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to send a message."
                    }
            
            # Check if this is a bulk message
            if "recipient_ids" in kwargs and kwargs["recipient_ids"]:
                # Send bulk message
                messages = message_service.send_bulk_message(
                    db=db,
                    content=content,
                    sender_type=kwargs["sender_type"],
                    recipient_type=kwargs["recipient_type"],
                    recipient_ids=kwargs["recipient_ids"],
                    message_type=kwargs.get("message_type", "TEXT"),
                    sender_id=kwargs.get("sender_id")
                )
                
                return {
                    "success": True,
                    "message_count": len(messages),
                    "recipient_count": len(kwargs["recipient_ids"]),
                    "response": f"Message sent to {len(messages)} recipients."
                }
            else:
                # Validate recipient_id
                if "recipient_id" not in kwargs or not kwargs["recipient_id"]:
                    return {
                        "success": False,
                        "error": "Missing required parameter: recipient_id",
                        "response": "Please provide the recipient ID to send a message."
                    }
                
                # Send individual message
                message = message_service.create_message(
                    db=db,
                    content=content,
                    sender_type=kwargs["sender_type"],
                    recipient_type=kwargs["recipient_type"],
                    message_type=kwargs.get("message_type", "TEXT"),
                    sender_id=kwargs.get("sender_id"),
                    recipient_id=kwargs["recipient_id"]
                )
                
                return {
                    "success": True,
                    "message_id": message.message_id,
                    "status": message.status,
                    "response": f"Message sent to {kwargs['recipient_type'].lower()} {kwargs['recipient_id']}."
                }
        
        elif communication_type.upper() == "NOTIFICATION":
            # Validate required parameters
            required_params = ["user_type", "user_id", "title"]
            for param in required_params:
                if param not in kwargs or not kwargs[param]:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to send a notification."
                    }
            
            # Create notification
            notification = notification_service.create_notification(
                db=db,
                user_type=kwargs["user_type"],
                user_id=kwargs["user_id"],
                title=kwargs["title"],
                content=content,
                notification_type=kwargs.get("notification_type", "GENERAL"),
                priority=kwargs.get("priority", "NORMAL")
            )
            
            return {
                "success": True,
                "notification_id": notification.notification_id,
                "status": notification.status,
                "response": f"Notification sent to {kwargs['user_type'].lower()} {kwargs['user_id']}."
            }
        
        elif communication_type.upper() == "ANNOUNCEMENT":
            # Validate required parameters
            required_params = ["building_id", "title"]
            for param in required_params:
                if param not in kwargs or not kwargs[param]:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to create an announcement."
                    }
            
            # Create announcement
            announcement = announcement_service.create_announcement(
                db=db,
                building_id=kwargs["building_id"],
                title=kwargs["title"],
                content=content,
                priority=kwargs.get("priority", "NORMAL"),
                expires_at=datetime.fromisoformat(kwargs["expires_at"]) if "expires_at" in kwargs and kwargs["expires_at"] else None,
                send_notifications=kwargs.get("send_notifications", True)
            )
            
            return {
                "success": True,
                "announcement_id": announcement.announcement_id,
                "building_id": announcement.building_id,
                "response": f"Announcement '{kwargs['title']}' created for building {kwargs['building_id']}."
            }
        
        else:
            return {
                "success": False,
                "error": f"Invalid communication type: {communication_type}",
                "response": f"'{communication_type}' is not a valid communication type. Please use MESSAGE, NOTIFICATION, or ANNOUNCEMENT."
            }
    
    except Exception as e:
        error_message = f"Error creating communication: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem sending the {communication_type.lower()}. Please try again."
        }

def generate_document_function(
    document_type: str,
    db: Session = Depends(get_db),
    **kwargs
) -> Dict[str, Any]:
    """
    Generates documents like leases or applications.
    """
    print(f"AI Function Called: generate_document_function with type: '{document_type}'")
    
    # Import document service
    from services import document_service
    
    try:
        if document_type.upper() == "LEASE":
            # Validate required parameters for lease document
            required_params = ["tenant_id", "room_id", "building_id", "lease_start_date", "lease_end_date", "monthly_rent", "deposit_amount"]
            for param in required_params:
                if param not in kwargs or kwargs[param] is None:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to generate a lease document."
                    }
            
            # Parse dates
            try:
                lease_start = datetime.strptime(kwargs["lease_start_date"], "%Y-%m-%d")
                lease_end = datetime.strptime(kwargs["lease_end_date"], "%Y-%m-%d")
            except ValueError as e:
                return {
                    "success": False,
                    "error": f"Invalid date format: {str(e)}",
                    "response": "Please provide dates in YYYY-MM-DD format."
                }
            
            # Generate lease document
            document = document_service.generate_lease_document(
                db=db,
                tenant_id=kwargs["tenant_id"],
                room_id=kwargs["room_id"],
                building_id=kwargs["building_id"],
                lease_start_date=lease_start,
                lease_end_date=lease_end,
                monthly_rent=float(kwargs["monthly_rent"]),
                deposit_amount=float(kwargs["deposit_amount"])
            )
            
            return {
                "success": True,
                "document_id": document.document_id,
                "document_type": document.document_type,
                "title": document.title,
                "status": document.status,
                "response": f"Lease document '{document.title}' has been generated and is ready for review."
            }
        
        elif document_type.upper() == "APPLICATION":
            # Validate required parameters for application
            if "lead_id" not in kwargs or not kwargs["lead_id"]:
                return {
                    "success": False,
                    "error": "Missing required parameter: lead_id",
                    "response": "Please provide a lead ID to generate an application document."
                }
            
            # Generate application document
            document = document_service.generate_application_document(
                db=db,
                lead_id=kwargs["lead_id"],
                room_id=kwargs.get("room_id"),
                building_id=kwargs.get("building_id")
            )
            
            return {
                "success": True,
                "document_id": document.document_id,
                "document_type": document.document_type,
                "title": document.title,
                "status": document.status,
                "response": f"Application document '{document.title}' has been generated as a draft."
            }
        
        else:
            return {
                "success": False,
                "error": f"Invalid document type: {document_type}",
                "response": f"'{document_type}' is not a valid document type. Please use LEASE or APPLICATION."
            }
    
    except Exception as e:
        error_message = f"Error generating document: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem generating the {document_type.lower()} document. Please try again."
        }

def manage_checklist_function(
    action: str,
    db: Session = Depends(get_db),
    **kwargs
) -> Dict[str, Any]:
    """
    Creates or manages move-in/out checklists.
    """
    print(f"AI Function Called: manage_checklist_function with action: '{action}'")
    
    # Import checklist service
    from services import checklist_service
    
    try:
        if action.upper() == "CREATE":
            # Validate required parameters
            required_params = ["checklist_type", "room_id", "building_id"]
            for param in required_params:
                if param not in kwargs or not kwargs[param]:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to create a checklist."
                    }
            
            # Create a checklist based on type
            checklist_type = kwargs["checklist_type"].upper()
            
            if checklist_type == "MOVE_IN":
                # For move-in checklist, tenant_id is required
                if "tenant_id" not in kwargs or not kwargs["tenant_id"]:
                    return {
                        "success": False,
                        "error": "Missing required parameter: tenant_id",
                        "response": "Please provide a tenant ID to create a move-in checklist."
                    }
                
                checklist = checklist_service.create_move_in_checklist(
                    db=db,
                    room_id=kwargs["room_id"],
                    building_id=kwargs["building_id"],
                    tenant_id=kwargs["tenant_id"],
                    operator_id=int(kwargs["operator_id"]) if "operator_id" in kwargs and kwargs["operator_id"] else None
                )
            
            elif checklist_type == "MOVE_OUT":
                # For move-out checklist, tenant_id is required
                if "tenant_id" not in kwargs or not kwargs["tenant_id"]:
                    return {
                        "success": False,
                        "error": "Missing required parameter: tenant_id",
                        "response": "Please provide a tenant ID to create a move-out checklist."
                    }
                
                checklist = checklist_service.create_move_out_checklist(
                    db=db,
                    room_id=kwargs["room_id"],
                    building_id=kwargs["building_id"],
                    tenant_id=kwargs["tenant_id"],
                    operator_id=int(kwargs["operator_id"]) if "operator_id" in kwargs and kwargs["operator_id"] else None
                )
            
            elif checklist_type == "INSPECTION":
                # Create a custom inspection checklist
                checklist = checklist_service.create_checklist(
                    db=db,
                    checklist_type="INSPECTION",
                    room_id=kwargs["room_id"],
                    building_id=kwargs["building_id"],
                    tenant_id=kwargs.get("tenant_id"),
                    operator_id=int(kwargs["operator_id"]) if "operator_id" in kwargs and kwargs["operator_id"] else None,
                    items=[{"description": "General room condition inspection"}]  # Default item
                )
            
            else:
                return {
                    "success": False,
                    "error": f"Invalid checklist type: {checklist_type}",
                    "response": f"'{checklist_type}' is not a valid checklist type. Please use MOVE_IN, MOVE_OUT, or INSPECTION."
                }
            
            return {
                "success": True,
                "checklist_id": checklist.checklist_id,
                "checklist_type": checklist.checklist_type,
                "status": checklist.status,
                "response": f"A {checklist_type.lower()} checklist has been created for room {kwargs['room_id']}."
            }
        
        elif action.upper() == "UPDATE_STATUS":
            # Validate required parameters
            required_params = ["checklist_id", "status"]
            for param in required_params:
                if param not in kwargs or not kwargs[param]:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to update a checklist status."
                    }
            
            # Update the checklist status
            checklist = checklist_service.update_checklist_status(
                db=db,
                checklist_id=kwargs["checklist_id"],
                status=kwargs["status"]
            )
            
            if not checklist:
                return {
                    "success": False,
                    "error": f"Checklist not found with ID: {kwargs['checklist_id']}",
                    "response": "The checklist could not be found. Please check the checklist ID."
                }
            
            return {
                "success": True,
                "checklist_id": checklist.checklist_id,
                "status": checklist.status,
                "response": f"Checklist status has been updated to {kwargs['status'].lower()}."
            }
        
        elif action.upper() == "UPDATE_ITEM":
            # Validate required parameters
            required_params = ["item_id", "status"]
            for param in required_params:
                if param not in kwargs or not kwargs[param]:
                    return {
                        "success": False,
                        "error": f"Missing required parameter: {param}",
                        "response": f"Please provide the {param.replace('_', ' ')} to update a checklist item."
                    }
            
            # Update the checklist item
            item = checklist_service.update_checklist_item_status(
                db=db,
                item_id=kwargs["item_id"],
                status=kwargs["status"],
                notes=kwargs.get("notes")
            )
            
            if not item:
                return {
                    "success": False,
                    "error": f"Checklist item not found with ID: {kwargs['item_id']}",
                    "response": "The checklist item could not be found. Please check the item ID."
                }
            
            return {
                "success": True,
                "item_id": item.item_id,
                "status": item.status,
                "response": f"Checklist item has been updated to {kwargs['status'].lower()}."
            }
        
        else:
            return {
                "success": False,
                "error": f"Invalid action: {action}",
                "response": f"'{action}' is not a valid action for checklists. Please use CREATE, UPDATE_STATUS, or UPDATE_ITEM."
            }
    
    except Exception as e:
        error_message = f"Error managing checklist: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem managing the checklist. Please try again."
        }