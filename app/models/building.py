# app/models/building.py
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel

class BuildingBase(BaseModel):
    building_id: str
    building_name: str
    full_address: Optional[str] = None
    operator_id: Optional[int] = None
    available: Optional[bool] = True
    street: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    floors: Optional[int] = 1
    total_rooms: Optional[int] = 0
    total_bathrooms: Optional[int] = 0
    bathrooms_on_each_floor: Optional[int] = 0
    common_kitchen: Optional[str] = "None"
    min_lease_term: Optional[int] = 1
    pref_min_lease_term: Optional[int] = 1
    wifi_included: Optional[bool] = False
    laundry_onsite: Optional[bool] = False
    common_area: Optional[str] = None
    secure_access: Optional[bool] = False
    bike_storage: Optional[bool] = False
    rooftop_access: Optional[bool] = False
    pet_friendly: Optional[str] = "No"
    cleaning_common_spaces: Optional[str] = None
    utilities_included: Optional[bool] = False
    fitness_area: Optional[bool] = False
    work_study_area: Optional[bool] = False
    social_events: Optional[bool] = False
    nearby_conveniences_walk: Optional[str] = None
    nearby_transportation: Optional[str] = None
    priority: Optional[int] = 0
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None

class BuildingCreate(BuildingBase):
    pass # No extra fields for creation

class BuildingUpdate(BuildingBase):
    building_name: Optional[str] = None
    full_address: Optional[Optional[str]] = None
    operator_id: Optional[Optional[int]] = None
    available: Optional[Optional[bool]] = None
    street: Optional[Optional[str]] = None
    area: Optional[Optional[str]] = None
    city: Optional[Optional[str]] = None
    state: Optional[Optional[str]] = None
    zip: Optional[Optional[str]] = None
    floors: Optional[Optional[int]] = None
    total_rooms: Optional[Optional[int]] = None
    total_bathrooms: Optional[Optional[int]] = None
    bathrooms_on_each_floor: Optional[Optional[int]] = None
    common_kitchen: Optional[Optional[str]] = None
    min_lease_term: Optional[Optional[int]] = None
    pref_min_lease_term: Optional[Optional[int]] = None
    wifi_included: Optional[Optional[bool]] = None
    laundry_onsite: Optional[Optional[bool]] = None
    common_area: Optional[Optional[str]] = None
    secure_access: Optional[Optional[bool]] = None
    bike_storage: Optional[Optional[bool]] = None
    rooftop_access: Optional[Optional[bool]] = None
    pet_friendly: Optional[Optional[str]] = None
    cleaning_common_spaces: Optional[Optional[str]] = None
    utilities_included: Optional[Optional[bool]] = None
    fitness_area: Optional[Optional[bool]] = None
    work_study_area: Optional[Optional[bool]] = None
    social_events: Optional[Optional[bool]] = None
    nearby_conveniences_walk: Optional[Optional[str]] = None
    nearby_transportation: Optional[Optional[str]] = None
    priority: Optional[Optional[int]] = None
    created_at: Optional[Optional[datetime]] = None
    last_modified: Optional[Optional[datetime]] = None


class Building(BuildingBase):
    # building_id: str # building_id is in BuildingBase

    class Config:
        orm_mode = True