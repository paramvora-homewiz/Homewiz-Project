from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class DocumentBase(BaseModel):
    title: str
    document_type: str
    content: Optional[str] = None
    tenant_id: Optional[str] = None
    lead_id: Optional[str] = None
    room_id: Optional[str] = None
    building_id: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class Document(DocumentBase):
    document_id: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DocumentGenerationRequest(BaseModel):
    document_type: str
    tenant_id: Optional[str] = None
    lead_id: Optional[str] = None
    room_id: Optional[str] = None
    building_id: Optional[str] = None
    parameters: Optional[dict] = None