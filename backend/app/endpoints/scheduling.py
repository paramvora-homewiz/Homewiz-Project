from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import scheduling_service
from ..db.connection import get_db
from ..models import scheduled_event as event_models

router = APIRouter()

@router.post("/events/", response_model=event_models.ScheduledEvent, status_code=201)
def create_event(event: event_models.ScheduledEventCreate, db: Session = Depends(get_db)):
    """
    Create a new scheduled event.
    """
    db_event = scheduling_service.create_event(
        db=db,
        event_type=event.event_type,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        room_id=event.room_id,
        building_id=event.building_id,
        operator_id=event.operator_id,
        lead_id=event.lead_id,
        tenant_id=event.tenant_id
    )
    return db_event

@router.get("/events/{event_id}", response_model=event_models.ScheduledEvent)
def read_event(event_id: str, db: Session = Depends(get_db)):
    """
    Get event by ID.
    """
    db_event = scheduling_service.get_event_by_id(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@router.put("/events/{event_id}/status", response_model=event_models.ScheduledEvent)
def update_event_status(event_id: str, status: str, db: Session = Depends(get_db)):
    """
    Update event status.
    """
    db_event = scheduling_service.update_event_status(db, event_id=event_id, status=status)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@router.put("/events/{event_id}", response_model=event_models.ScheduledEvent)
def update_event(event_id: str, event_update: event_models.ScheduledEventUpdate, db: Session = Depends(get_db)):
    """
    Update event details.
    """
    db_event = scheduling_service.update_event(db, event_id=event_id, event_update=event_update.dict(exclude_unset=True))
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: str, db: Session = Depends(get_db)):
    """
    Delete event by ID.
    """
    success = scheduling_service.delete_event(db, event_id=event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"ok": True}

@router.get("/operators/{operator_id}/events/", response_model=List[event_models.ScheduledEvent])
def read_operator_events(
    operator_id: int,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get events for a specific operator.
    """
    events = scheduling_service.get_operator_events(
        db=db,
        operator_id=operator_id,
        from_date=from_date,
        to_date=to_date,
        event_type=event_type,
        status=status
    )
    return events

@router.get("/buildings/{building_id}/events/", response_model=List[event_models.ScheduledEvent])
def read_building_events(
    building_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get events for a specific building.
    """
    events = scheduling_service.get_building_events(
        db=db,
        building_id=building_id,
        from_date=from_date,
        to_date=to_date,
        event_type=event_type,
        status=status
    )
    return events

@router.get("/rooms/{room_id}/events/", response_model=List[event_models.ScheduledEvent])
def read_room_events(
    room_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get events for a specific room.
    """
    events = scheduling_service.get_room_events(
        db=db,
        room_id=room_id,
        from_date=from_date,
        to_date=to_date,
        event_type=event_type,
        status=status
    )
    return events

@router.get("/leads/{lead_id}/events/", response_model=List[event_models.ScheduledEvent])
def read_lead_events(
    lead_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get events for a specific lead.
    """
    events = scheduling_service.get_lead_events(
        db=db,
        lead_id=lead_id,
        from_date=from_date,
        to_date=to_date,
        event_type=event_type,
        status=status
    )
    return events

@router.get("/tenants/{tenant_id}/events/", response_model=List[event_models.ScheduledEvent])
def read_tenant_events(
    tenant_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get events for a specific tenant.
    """
    events = scheduling_service.get_tenant_events(
        db=db,
        tenant_id=tenant_id,
        from_date=from_date,
        to_date=to_date,
        event_type=event_type,
        status=status
    )
    return events

@router.post("/availability/", response_model=List[event_models.AvailabilitySlot])
def find_available_slots(availability_request: event_models.AvailabilityRequest, db: Session = Depends(get_db)):
    """
    Find available time slots for scheduling events.
    """
    slots = scheduling_service.find_available_slots(
        db=db,
        event_type=availability_request.event_type,
        duration_minutes=availability_request.duration_minutes,
        date_from=availability_request.date_from,
        date_to=availability_request.date_to,
        operator_id=availability_request.operator_id,
        building_id=availability_request.building_id,
        room_id=availability_request.room_id
    )
    
    # Convert tuple results to AvailabilitySlot objects
    availability_slots = [
        event_models.AvailabilitySlot(start_time=start, end_time=end)
        for start, end in slots
    ]
    
    return availability_slots