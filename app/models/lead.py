from typing import List, Optional
from datetime import datetime  # Import datetime from datetime module

from pydantic import BaseModel


# Pydantic models for request and response validation

class LeadBase(BaseModel):
    email: str
    status: Optional[str] = "EXPLORING"  # Default status


class LeadCreate(LeadBase):
    pass  # Inherits fields from LeadBase


class LeadUpdateStatus(BaseModel):
    status: str


class LeadUpdateWishlist(BaseModel):
    wishlist: List[str] # List of room_ids


class Lead(LeadBase):
    lead_id: str
    interaction_count: int
    rooms_interested: Optional[str] = None
    selected_room_id: Optional[str] = None
    showing_dates: Optional[List[str]] = None
    planned_move_in: Optional[str] = None # Date as string (or use pydantic.datetime)
    planned_move_out: Optional[str] = None # Date as string
    visa_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None # Datetime as string - Let's keep it as Optional[str] for now for API input/output, but handle serialization
    last_modified: Optional[str] = None # Datetime as string - Let's keep it as Optional[str] for now for API input/output, but handle serialization

    class Config:
        orm_mode = True

        @staticmethod
        def schema_extra(schema): # Custom schema_extra to handle datetime serialization for OpenAPI/Swagger UI
            for prop in schema.get("properties", {}).values():
                if "format" in prop and prop["format"] == "date-time":
                    prop["type"] = "string"
                    prop["format"] = "date-time" # Keep format for documentation, but type is string for serialization