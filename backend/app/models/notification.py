from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class NotificationBase(BaseModel):
    user_type: str
    user_id: str
    title: str
    content: str
    type: str
    priority: Optional[str] = "NORMAL"

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class NotificationRead(BaseModel):
    pass

class Notification(NotificationBase):
    notification_id: str
    status: str
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    class Config:
        orm_mode = True