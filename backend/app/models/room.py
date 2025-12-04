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

    # NEW: Room image fields
    room_images: Optional[List[str]] = []  # List of room image URLs
    virtual_tour_url: Optional[str] = None

    # NEW: Room type and pricing for shared rooms (frontend enhancement)
    room_type: Optional[str] = "Standard"  # Standard, Shared, Suite, Studio, etc.
    shared_room_rent_3: Optional[float] = None  # 3-person occupancy pricing
    shared_room_rent_4: Optional[float] = None  # 4+ person occupancy pricing

    # NEW: Per-bed configuration (frontend enhancement)
    bed_configurations: Optional[str] = None  # JSON array of bed configs
    beds_configuration: Optional[str] = None  # JSON array - alternative name for frontend compatibility

    # NEW: AI-optimized bed query fields (for "find a bed under $800" queries)
    min_bed_rent: Optional[float] = None  # Minimum rent across all beds in room
    max_bed_rent: Optional[float] = None  # Maximum rent across all beds in room
    available_beds_count: Optional[int] = 0  # Count of beds with status 'Available'
    has_available_beds: Optional[bool] = True  # Quick filter for any available bed

    # NEW: Maintenance tracking (frontend enhancement)
    room_condition_score: Optional[int] = None  # 1-10 rating
    cleaning_frequency: Optional[str] = None  # DAILY, WEEKLY, BIWEEKLY, MONTHLY, AS_NEEDED
    utilities_meter_id: Optional[str] = None
    last_cleaning_date: Optional[date] = None
    last_maintenance_staff_id: Optional[int] = None
    description: Optional[str] = None  # Room description

    # NEW: Utilities included as structured data (frontend enhancement)
    utilities_included_details: Optional[str] = None  # JSON object of which utilities are included

class RoomCreate(RoomBase):
    room_id: str # Client needs to provide room_id
    room_images: Optional[List[str]] = []

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
    # NEW: Image fields in update model
    room_images: Optional[List[str]] = None
    virtual_tour_url: Optional[str] = None

    # NEW: Room type and pricing for shared rooms
    room_type: Optional[str] = None
    shared_room_rent_3: Optional[float] = None
    shared_room_rent_4: Optional[float] = None

    # NEW: Per-bed configuration
    bed_configurations: Optional[str] = None
    beds_configuration: Optional[str] = None  # Alternative name for frontend compatibility

    # NEW: AI-optimized bed query fields
    min_bed_rent: Optional[float] = None
    max_bed_rent: Optional[float] = None
    available_beds_count: Optional[int] = None
    has_available_beds: Optional[bool] = None

    # NEW: Maintenance tracking
    room_condition_score: Optional[int] = None
    cleaning_frequency: Optional[str] = None
    utilities_meter_id: Optional[str] = None
    last_cleaning_date: Optional[date] = None
    last_maintenance_staff_id: Optional[int] = None
    description: Optional[str] = None

    # NEW: Utilities included as structured data
    utilities_included_details: Optional[str] = None

class Room(RoomBase):
    room_id: str

    class Config:
        from_attributes = True

# Additional models for room image operations
class RoomImageUploadResponse(BaseModel):
    """Response model for room image upload"""
    image_url: str
    image_path: str
    file_name: str
    original_name: str
    room_id: str
    building_id: str

class RoomImageUpdate(BaseModel):
    """Model for updating room images"""
    room_id: str
    building_id: str
    image_urls: List[str]

class RoomWithImageCount(Room):
    """Room model with additional image count info"""
    image_count: Optional[int] = 0
    storage_image_count: Optional[int] = 0


# NEW: Bed-level search models for AI queries like "find a bed under $800"
class BedInfo(BaseModel):
    """Individual bed information extracted from beds_configuration JSON"""
    bed_id: str
    bedName: str
    bedType: Optional[str] = None
    rent: Optional[float] = None
    status: str = "Available"
    availableFrom: Optional[str] = None
    availableUntil: Optional[str] = None
    view: Optional[str] = None
    maxOccupancy: int = 1


class BedSearchResult(BaseModel):
    """Result model for bed-level searches (AI chatbot queries)"""
    # Bed details
    bed_id: str
    bedName: str
    bedType: Optional[str] = None
    rent: Optional[float] = None
    status: str = "Available"
    availableFrom: Optional[str] = None
    availableUntil: Optional[str] = None
    view: Optional[str] = None
    maxOccupancy: int = 1

    # Room context
    room_id: str
    room_number: str
    room_type: Optional[str] = None
    floor_number: Optional[int] = None
    bathroom_type: Optional[str] = None

    # Building context
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    building_city: Optional[str] = None
    building_address: Optional[str] = None
    building_state: Optional[str] = None


class BedSearchParams(BaseModel):
    """Parameters for bed-level search queries"""
    max_rent: Optional[float] = None
    min_rent: Optional[float] = None
    status: Optional[str] = "Available"  # Available, Reserved, Occupied
    available_from: Optional[str] = None
    bed_type: Optional[str] = None
    city: Optional[str] = None
    building_id: Optional[str] = None