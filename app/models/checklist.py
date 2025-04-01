from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ChecklistItemBase(BaseModel):
    description: str
    status: Optional[str] = "PENDING"
    notes: Optional[str] = None

class ChecklistItemCreate(ChecklistItemBase):
    checklist_id: str

class ChecklistItemUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ChecklistItem(ChecklistItemBase):
    item_id: str
    checklist_id: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ChecklistBase(BaseModel):
    checklist_type: str
    room_id: str
    building_id: str
    tenant_id: Optional[str] = None
    operator_id: Optional[int] = None

class ChecklistCreate(ChecklistBase):
    items: Optional[List[ChecklistItemBase]] = None

class ChecklistUpdate(BaseModel):
    checklist_type: Optional[str] = None
    status: Optional[str] = None
    tenant_id: Optional[str] = None
    operator_id: Optional[int] = None

class Checklist(ChecklistBase):
    checklist_id: str
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items: Optional[List[ChecklistItem]] = None

    class Config:
        orm_mode = True