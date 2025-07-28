# app/ai_services/v4_intelligent_scheduling_supabase.py
# Scheduling Functions - Supabase Version

import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.db.supabase_connection import get_supabase
import uuid

client = genai.Client(api_key=GEMINI_API_KEY)

def schedule_showing_function(
    lead_id: str,
    room_id: str,
    date: str,
    time: str,
    operator_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Schedules a property showing for a lead.
    Creates an entry in scheduled_events table.
    """
    print(f"AI Function Called: schedule_showing_function for lead {lead_id}, room {room_id}")
    
    try:
        supabase = get_supabase()
        
        # Step 1: Validate inputs exist
        # Check if lead exists
        lead_response = supabase.table('leads').select('lead_id, email').eq('lead_id', lead_id).single().execute()
        if not lead_response.data:
            return {
                "success": False,
                "error": f"Lead ID {lead_id} not found",
                "response": "Could not find the specified lead. Please check the lead ID."
            }
        lead_email = lead_response.data.get('email', 'Guest')
        
        # Check if room exists and get building info
        room_response = supabase.table('rooms').select('room_id, room_number, building_id').eq('room_id', room_id).single().execute()
        if not room_response.data:
            return {
                "success": False,
                "error": f"Room ID {room_id} not found",
                "response": "Could not find the specified room. Please check the room ID."
            }
        room_data = room_response.data
        room_number = room_data.get('room_number', 'Unknown')
        building_id = room_data.get('building_id')
        
        # Step 2: Parse and combine date/time
        try:
            # Parse date and time
            showing_date = datetime.strptime(date, "%Y-%m-%d")
            time_parts = time.split(":")
            showing_datetime = showing_date.replace(
                hour=int(time_parts[0]),
                minute=int(time_parts[1]) if len(time_parts) > 1 else 0
            )
            
            # End time is 30 minutes after start
            end_datetime = showing_datetime + timedelta(minutes=30)
            
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid date/time format: {e}",
                "response": "Please provide date as YYYY-MM-DD and time as HH:MM"
            }
        
        # Step 3: Check for conflicts (optional - can be enhanced)
        # Check if room is already booked at that time
        conflict_check = supabase.table('scheduled_events').select('event_id, title')\
            .eq('room_id', room_id)\
            .eq('event_type', 'showing')\
            .gte('start_time', showing_datetime.isoformat())\
            .lt('start_time', end_datetime.isoformat())\
            .execute()
        
        if conflict_check.data:
            return {
                "success": False,
                "error": "Time slot conflict",
                "response": f"Room {room_number} already has a showing scheduled at that time. Please choose a different time."
            }
        
        # Step 4: Create the showing event
        event_data = {
            "event_id": str(uuid.uuid4()),
            "event_type": "showing",
            "title": f"Property Showing - Room {room_number}",
            "description": f"Showing for {lead_email} at Room {room_number}",
            "start_time": showing_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "status": "SCHEDULED",
            "room_id": room_id,
            "building_id": building_id,
            "lead_id": lead_id,
            "operator_id": operator_id if operator_id else None
        }
        
        # Insert into database
        insert_response = supabase.table('scheduled_events').insert(event_data).execute()
        
        if not insert_response.data:
            return {
                "success": False,
                "error": "Failed to create showing",
                "response": "Could not schedule the showing. Please try again."
            }
        
        # Step 5: Generate friendly confirmation using Gemini
        confirmation_message = ""
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""Create a friendly confirmation message for a property showing:
                - Room: {room_number}
                - Date: {showing_datetime.strftime('%A, %B %d, %Y')}
                - Time: {showing_datetime.strftime('%I:%M %p')}
                - Duration: 30 minutes
                - Lead: {lead_email}
                
                Keep it brief, professional, and include all details.""",
                config=GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=150
                )
            )
            confirmation_message = response.text
        except Exception as e:
            # Fallback message if Gemini fails
            confirmation_message = f"Showing confirmed for Room {room_number} on {showing_datetime.strftime('%B %d at %I:%M %p')}."
        
        return {
            "success": True,
            "event_id": event_data["event_id"],
            "response": confirmation_message,
            "status": "scheduled",
            "details": {
                "room_number": room_number,
                "date": showing_datetime.strftime('%Y-%m-%d'),
                "time": showing_datetime.strftime('%H:%M'),
                "duration": "30 minutes",
                "lead_email": lead_email
            }
        }
        
    except Exception as e:
        print(f"Error in schedule_showing_function: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "Failed to schedule the showing. Please try again."
        }


def schedule_event_function(
    event_type: str,
    title: str,
    start_time: str,
    end_time: str,
    room_id: Optional[str] = None,
    building_id: Optional[str] = None,
    operator_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Schedules a general event (maintenance, move-in/out, inspection, etc.)
    More flexible than schedule_showing_function.
    """
    print(f"AI Function Called: schedule_event_function with type '{event_type}' and title '{title}'")
    
    try:
        supabase = get_supabase()
        
        # Step 1: Validate event type
        valid_event_types = ['showing', 'maintenance', 'move-in', 'move-out', 'inspection', 'meeting', 'other']
        if event_type.lower() not in valid_event_types:
            return {
                "success": False,
                "error": f"Invalid event type: {event_type}",
                "response": f"Event type must be one of: {', '.join(valid_event_types)}"
            }
        
        # Step 2: Parse datetime strings
        try:
            start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Validate end time is after start time
            if end_datetime <= start_datetime:
                return {
                    "success": False,
                    "error": "Invalid time range",
                    "response": "End time must be after start time."
                }
                
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid datetime format: {e}",
                "response": "Please provide datetime in ISO format (YYYY-MM-DDTHH:MM:SS)"
            }
        
        # Step 3: Validate related entities if provided
        validation_errors = []
        
        if room_id:
            room_check = supabase.table('rooms').select('room_id').eq('room_id', room_id).single().execute()
            if not room_check.data:
                validation_errors.append(f"Room ID {room_id} not found")
        
        if building_id:
            building_check = supabase.table('buildings').select('building_id').eq('building_id', building_id).single().execute()
            if not building_check.data:
                validation_errors.append(f"Building ID {building_id} not found")
        
        if lead_id:
            lead_check = supabase.table('leads').select('lead_id').eq('lead_id', lead_id).single().execute()
            if not lead_check.data:
                validation_errors.append(f"Lead ID {lead_id} not found")
        
        if tenant_id:
            tenant_check = supabase.table('tenants').select('tenant_id').eq('tenant_id', tenant_id).single().execute()
            if not tenant_check.data:
                validation_errors.append(f"Tenant ID {tenant_id} not found")
        
        if validation_errors:
            return {
                "success": False,
                "error": "Validation failed",
                "response": f"Validation errors: {'; '.join(validation_errors)}"
            }
        
        # Step 4: Check for conflicts if room is specified
        if room_id:
            conflict_check = supabase.table('scheduled_events').select('event_id, title')\
                .eq('room_id', room_id)\
                .neq('status', 'CANCELLED')\
                .or_(f"start_time.gte.{start_datetime.isoformat()},start_time.lt.{end_datetime.isoformat()}")\
                .or_(f"end_time.gt.{start_datetime.isoformat()},end_time.lte.{end_datetime.isoformat()}")\
                .execute()
            
            if conflict_check.data:
                conflicting_event = conflict_check.data[0]
                return {
                    "success": False,
                    "error": "Schedule conflict",
                    "response": f"Time conflict with existing event: {conflicting_event.get('title')}. Please choose a different time."
                }
        
        # Step 5: Create the event
        event_data = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type.lower(),
            "title": title,
            "description": description or f"{event_type} event",
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "status": "SCHEDULED",
            "room_id": room_id,
            "building_id": building_id,
            "operator_id": operator_id,
            "lead_id": lead_id,
            "tenant_id": tenant_id
        }
        
        # Insert into database
        insert_response = supabase.table('scheduled_events').insert(event_data).execute()
        
        if not insert_response.data:
            return {
                "success": False,
                "error": "Failed to create event",
                "response": "Could not schedule the event. Please try again."
            }
        
        # Step 6: Generate confirmation message
        confirmation_message = ""
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"""Create a confirmation message for a scheduled event:
                - Type: {event_type}
                - Title: {title}
                - Date: {start_datetime.strftime('%A, %B %d, %Y')}
                - Time: {start_datetime.strftime('%I:%M %p')} to {end_datetime.strftime('%I:%M %p')}
                - {'Room: ' + room_id if room_id else ''}
                - {'Building: ' + building_id if building_id else ''}
                
                Keep it brief and professional.""",
                config=GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=150
                )
            )
            confirmation_message = response.text
        except Exception as e:
            # Fallback message
            confirmation_message = f"{title} scheduled for {start_datetime.strftime('%B %d at %I:%M %p')}."
        
        return {
            "success": True,
            "event_id": event_data["event_id"],
            "event_type": event_type,
            "title": title,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "status": "SCHEDULED",
            "response": confirmation_message
        }
        
    except Exception as e:
        error_message = f"Error scheduling event: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "response": f"There was a problem scheduling the {event_type}. Please try again."
        }