# app/models/operator.py
from typing import List, Optional
from datetime import date

from pydantic import BaseModel

class OperatorBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = True
    date_joined: Optional[date] = None
    last_active: Optional[date] = None

class OperatorCreate(OperatorBase):
    pass # No extra fields for creation

class OperatorUpdate(OperatorBase):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[Optional[str]] = None
    role: Optional[Optional[str]] = None
    active: Optional[Optional[bool]] = None
    date_joined: Optional[Optional[date]] = None
    last_active: Optional[Optional[date]] = None

class Operator(OperatorBase):
    operator_id: int

    class Config:
        orm_mode = True