from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class AnnouncementBase(BaseModel):
    building_id: str
    title: str
    content: str
    priority: Optional[str] = "NORMAL"
    expires_at: Optional[datetime] = None

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    expires_at: Optional[datetime] = None

class Announcement(AnnouncementBase):
    announcement_id: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True