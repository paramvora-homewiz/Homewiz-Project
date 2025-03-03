# app/models/room.py
from typing import List, Optional
from datetime import date

from pydantic import BaseModel

class RoomBase(BaseModel):
    room_number: str
    building_id: str
    ready_to_rent: Optional[bool] = True
    status: Optional[str] = "AVAILABLE"
    booked_from: Optional[date] = None
    booked_till: Optional[date] = None
    active_tenants: Optional[int] = 0
    maximum_people_in_room: Optional[int] = 1
    private_room_rent: float
    shared_room_rent_2: Optional[float] = None
    last_check: Optional[date] = None
    last_check_by: Optional[int] = None
    current_booking_types: Optional[str] = None
    floor_number: Optional[int] = 1
    bed_count: Optional[int] = 1
    bathroom_type: Optional[str] = "Shared"
    bed_size: Optional[str] = "Twin"
    bed_type: Optional[str] = "Single"
    view: Optional[str] = "Street"
    sq_footage: Optional[int] = 200
    mini_fridge: Optional[bool] = False
    sink: Optional[bool] = False
    bedding_provided: Optional[bool] = False
    work_desk: Optional[bool] = False
    work_chair: Optional[bool] = False
    heating: Optional[bool] = False
    air_conditioning: Optional[bool] = False
    cable_tv: Optional[bool] = False
    room_storage: Optional[str] = "Built-in Closet"

class RoomCreate(RoomBase):
    room_id: str # Client needs to provide room_id

class RoomUpdate(RoomBase):
    room_number: Optional[str] = None
    building_id: Optional[str] = None
    ready_to_rent: Optional[Optional[bool]] = None
    status: Optional[Optional[str]] = None
    booked_from: Optional[Optional[date]] = None
    booked_till: Optional[Optional[date]] = None
    active_tenants: Optional[Optional[int]] = None
    maximum_people_in_room: Optional[Optional[int]] = None
    private_room_rent: Optional[float] = None
    shared_room_rent_2: Optional[Optional[float]] = None
    last_check: Optional[Optional[date]] = None
    last_check_by: Optional[Optional[int]] = None
    current_booking_types: Optional[Optional[str]] = None
    floor_number: Optional[Optional[int]] = None
    bed_count: Optional[Optional[int]] = None
    bathroom_type: Optional[Optional[str]] = None
    bed_size: Optional[Optional[str]] = None
    bed_type: Optional[Optional[str]] = None
    view: Optional[Optional[str]] = None
    sq_footage: Optional[Optional[int]] = None
    mini_fridge: Optional[Optional[bool]] = None
    sink: Optional[Optional[bool]] = None
    bedding_provided: Optional[Optional[bool]] = None
    work_desk: Optional[Optional[bool]] = None
    work_chair: Optional[Optional[bool]] = None
    heating: Optional[Optional[bool]] = None
    air_conditioning: Optional[Optional[bool]] = None
    cable_tv: Optional[Optional[bool]] = None
    room_storage: Optional[Optional[str]] = None

class Room(RoomBase):
    room_id: str

    class Config:
        orm_mode = True