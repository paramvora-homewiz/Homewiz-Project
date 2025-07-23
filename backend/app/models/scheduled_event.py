from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ScheduledEventBase(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    
    # These can be null depending on event type
    room_id: Optional[str] = None
    building_id: Optional[str] = None
    operator_id: Optional[int] = None
    lead_id: Optional[str] = None
    tenant_id: Optional[str] = None

class ScheduledEventCreate(ScheduledEventBase):
    pass

class ScheduledEventUpdate(BaseModel):
    event_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    room_id: Optional[str] = None
    building_id: Optional[str] = None
    operator_id: Optional[int] = None
    lead_id: Optional[str] = None
    tenant_id: Optional[str] = None

class ScheduledEvent(ScheduledEventBase):
    event_id: str
    status: str
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None

    class Config:
        orm_mode = True

class AvailabilityRequest(BaseModel):
    event_type: str
    duration_minutes: int
    date_from: datetime
    date_to: datetime
    operator_id: Optional[int] = None
    building_id: Optional[str] = None
    room_id: Optional[str] = None

class AvailabilitySlot(BaseModel):
    start_time: datetime
    end_time: datetime