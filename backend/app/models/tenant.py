# app/models/tenant.py
from typing import List, Optional
from datetime import date

from pydantic import BaseModel

class TenantBase(BaseModel):
    tenant_name: str
    room_id: str
    room_number: Optional[str] = None
    lease_start_date: Optional[date] = None
    lease_end_date: Optional[date] = None
    operator_id: Optional[int] = None
    booking_type: Optional[str] = "LEASE"
    tenant_nationality: Optional[str] = None
    tenant_email: str
    phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    building_id: str
    status: Optional[str] = "ACTIVE"
    deposit_amount: Optional[float] = 0.0
    payment_status: Optional[str] = "PENDING"
    special_requests: Optional[str] = None

class TenantCreate(TenantBase):
    tenant_id: str # Client needs to provide tenant_id

class TenantUpdate(TenantBase):
    tenant_name: Optional[str] = None
    room_id: Optional[str] = None
    room_number: Optional[Optional[str]] = None
    lease_start_date: Optional[Optional[date]] = None
    lease_end_date: Optional[Optional[date]] = None
    operator_id: Optional[Optional[int]] = None
    booking_type: Optional[Optional[str]] = None
    tenant_nationality: Optional[Optional[str]] = None
    tenant_email: Optional[str] = None
    phone: Optional[Optional[str]] = None
    emergency_contact_name: Optional[Optional[str]] = None
    emergency_contact_phone: Optional[Optional[str]] = None
    emergency_contact_relation: Optional[Optional[str]] = None
    building_id: Optional[Optional[str]] = None
    status: Optional[Optional[str]] = None
    deposit_amount: Optional[Optional[float]] = None
    payment_status: Optional[Optional[str]] = None
    special_requests: Optional[Optional[str]] = None

class Tenant(TenantBase):
    tenant_id: str

    class Config:
        orm_mode = True