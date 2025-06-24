from google.genai.types import FunctionDeclaration
from typing import Dict, Any, List

def create_function_selection_tools() -> List[FunctionDeclaration]:
    """Create function declarations for all available functions"""
    
    # Define all your functions for the LLM to choose from
    function_declarations = [
        FunctionDeclaration(
            name="find_buildings_rooms_function",
            description="Basic room search for available rooms based on simple preferences like price, view, bathroom type, bed size, basic amenities",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {"type": "STRING", "description": "User's room search query"}
                },
                "required": ["query"]
            }
        ),
        FunctionDeclaration(
            name="filter_rooms_function", 
            description="Advanced room and building filtering with complex criteria like building features (gym, laundry, WiFi, utilities, pet-friendly), location preferences, floor requirements, size needs, availability dates, and special requirements",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {"type": "STRING", "description": "User's filtering requirements including building features"},
                    "min_price": {"type": "NUMBER", "description": "Minimum price filter"},
                    "max_price": {"type": "NUMBER", "description": "Maximum price filter"},
                    "room_type": {"type": "STRING", "description": "PRIVATE or SHARED"},
                    "amenities": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Desired room amenities"},
                    "move_in_date": {"type": "STRING", "description": "Desired move-in date YYYY-MM-DD"},
                    "building_features": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Building features like 'gym', 'laundry', 'wifi', 'pet-friendly'"},
                    "location": {"type": "STRING", "description": "Location preferences like 'downtown', 'near transit'"},
                    "floor_preferences": {"type": "STRING", "description": "Floor requirements like 'high floors', 'upper floors'"},
                    "special_requirements": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Special needs like 'quiet', 'furnished', 'spacious'"}
                },
                "required": ["query"]
            }
        ),
        FunctionDeclaration(
            name="schedule_showing_function",
            description="Schedule property showings, tours, or viewings for prospective tenants",
            parameters={
                "type": "OBJECT", 
                "properties": {
                    "lead_id": {"type": "STRING", "description": "ID of the prospect"},
                    "room_id": {"type": "STRING", "description": "Room to show"},
                    "date": {"type": "STRING", "description": "Preferred date"},
                    "time": {"type": "STRING", "description": "Preferred time"}
                },
                "required": ["lead_id", "room_id", "date", "time"]
            }
        ),
        FunctionDeclaration(
            name="generate_insights_function",
            description="Generate analytics, reports, and business insights about occupancy, financials, leads, maintenance, etc.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "insight_type": {
                        "type": "STRING", 
                        "description": "Type of insight: OCCUPANCY, FINANCIAL, LEAD_CONVERSION, MAINTENANCE, ROOM_PERFORMANCE, TENANT, DASHBOARD"
                    },
                    "building_id": {"type": "STRING", "description": "Optional building to analyze"},
                    "start_date": {"type": "STRING", "description": "Analysis start date YYYY-MM-DD"},
                    "end_date": {"type": "STRING", "description": "Analysis end date YYYY-MM-DD"}
                },
                "required": ["insight_type"]
            }
        ),
        FunctionDeclaration(
            name="process_maintenance_request_function",
            description="Create, update, or assign maintenance requests and work orders",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "action": {"type": "STRING", "description": "CREATE, UPDATE, or ASSIGN"},
                    "title": {"type": "STRING", "description": "Issue title"},
                    "description": {"type": "STRING", "description": "Issue description"},
                    "room_id": {"type": "STRING", "description": "Affected room"},
                    "priority": {"type": "STRING", "description": "LOW, MEDIUM, HIGH, EMERGENCY"}
                },
                "required": ["action"]
            }
        ),
        FunctionDeclaration(
            name="create_communication_function",
            description="Send messages, notifications, or announcements to tenants, leads, or staff",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "communication_type": {"type": "STRING", "description": "MESSAGE, NOTIFICATION, ANNOUNCEMENT"},
                    "content": {"type": "STRING", "description": "Message content"},
                    "recipient_type": {"type": "STRING", "description": "TENANT, LEAD, OPERATOR"},
                    "recipient_id": {"type": "STRING", "description": "Recipient ID"}
                },
                "required": ["communication_type", "content"]
            }
        )
        # Add more function declarations as needed...
    ]
    
    return function_declarations