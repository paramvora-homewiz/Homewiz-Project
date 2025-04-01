from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class MessageBase(BaseModel):
    content: str
    message_type: Optional[str] = "TEXT"
    sender_type: str
    sender_id: Optional[str] = None
    recipient_type: str
    recipient_id: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    status: Optional[str] = None

class Message(MessageBase):
    message_id: str
    status: str
    created_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class BulkMessageRequest(BaseModel):
    content: str
    message_type: str
    sender_type: str
    sender_id: Optional[str] = None
    recipient_ids: List[str]
    recipient_type: str