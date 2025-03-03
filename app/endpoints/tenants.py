# app/endpoints/tenants.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import tenant_service
from ..db.connection import get_db
from ..models import tenant as tenant_models  # Import Pydantic models

router = APIRouter()

@router.post("/tenants/", response_model=tenant_models.Tenant, status_code=201)
def create_tenant(tenant: tenant_models.TenantCreate, db: Session = Depends(get_db)):
    """
    Create a new tenant.
    """
    db_tenant = tenant_service.create_tenant(db=db, tenant=tenant)
    return db_tenant

@router.get("/tenants/{tenant_id}", response_model=tenant_models.Tenant)
def read_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """
    Get tenant by ID.
    """
    db_tenant = tenant_service.get_tenant_by_id(db, tenant_id=tenant_id)
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.put("/tenants/{tenant_id}", response_model=tenant_models.Tenant)
def update_tenant(tenant_id: str, tenant_update: tenant_models.TenantUpdate, db: Session = Depends(get_db)):
    """
    Update tenant by ID.
    """
    db_tenant = tenant_service.update_tenant(db, tenant_id=tenant_id, tenant_update=tenant_update)
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@router.delete("/tenants/{tenant_id}", status_code=204)
def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """
    Delete tenant by ID.
    """
    db_tenant = tenant_service.get_tenant_by_id(db, tenant_id=tenant_id)
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_service.delete_tenant(db, tenant_id=tenant_id)
    return {"ok": True}

@router.get("/tenants/", response_model=List[tenant_models.Tenant])
def read_tenants(db: Session = Depends(get_db)):
    """
    Get all tenants.
    """
    tenants_list = tenant_service.get_all_tenants(db)
    return tenants_list