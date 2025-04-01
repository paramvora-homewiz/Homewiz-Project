from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class MaintenanceRequestBase(BaseModel):
    title: str
    description: str
    priority: Optional[str] = "MEDIUM"
    room_id: str
    building_id: str
    tenant_id: str
    assigned_to: Optional[int] = None

class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass

class MaintenanceRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None

class MaintenanceRequest(MaintenanceRequestBase):
    request_id: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        orm_mode = True