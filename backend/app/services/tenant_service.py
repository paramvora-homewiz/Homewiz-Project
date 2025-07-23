# app/services/tenant_service.py
from typing import List, Optional

from sqlalchemy.orm import Session

from ..db import models
from ..models import tenant as tenant_models

def create_tenant(db: Session, tenant: tenant_models.TenantCreate) -> models.Tenant:
    """
    Creates a new tenant in the database.
    """
    db_tenant = models.Tenant(**tenant.dict())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

def get_tenant_by_id(db: Session, tenant_id: str) -> Optional[models.Tenant]:
    """
    Retrieves a tenant from the database by their tenant_id.
    """
    return db.query(models.Tenant).filter(models.Tenant.tenant_id == tenant_id).first()

def update_tenant(db: Session, tenant_id: str, tenant_update: tenant_models.TenantUpdate) -> Optional[models.Tenant]:
    """
    Updates the details of a tenant in the database.
    """
    db_tenant = get_tenant_by_id(db, tenant_id)
    if db_tenant:
        for key, value in tenant_update.dict(exclude_unset=True).items():
            setattr(db_tenant, key, value)
        db.commit()
        db.refresh(db_tenant)
        return db_tenant
    return None

def delete_tenant(db: Session, tenant_id: str) -> bool:
    """
    Deletes a tenant from the database by their tenant_id.
    """
    db_tenant = get_tenant_by_id(db, tenant_id)
    if db_tenant:
        db.delete(db_tenant)
        db.commit()
        return True
    return False

def get_all_tenants(db: Session) -> List[models.Tenant]:
    """
    Retrieves all tenants from the database.
    """
    return db.query(models.Tenant).all()