import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
import uuid

from app.db.connection import Base
from app.services import tenant_service
from app.db import models
from app.models import tenant as tenant_models # Pydantic models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """
    Function-scoped test database fixture for tenants.
    """
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_tenant(db):
    """Tests creating a new tenant."""
    tenant_id = f"TNT_TEST_{uuid.uuid4()}"
    tenant_data = {
        "tenant_id": tenant_id,
        "tenant_name": "Test Tenant",
        "room_id": "ROOM123",
        "building_id": "BLD_TEST",
        "tenant_email": f"test_tenant_{uuid.uuid4()}@example.com",
        "deposit_amount": 1500.00
    }
    tenant_create = tenant_models.TenantCreate(**tenant_data)
    created_tenant = tenant_service.create_tenant(db, tenant_create)
    assert created_tenant.tenant_id == tenant_id
    assert created_tenant.tenant_name == tenant_data["tenant_name"]
    assert created_tenant.tenant_email == tenant_data["tenant_email"]
    assert created_tenant.deposit_amount == tenant_data["deposit_amount"]

def test_get_tenant_by_id(db):
    """Tests retrieving a tenant by ID."""
    tenant_id = f"TNT_TEST_{uuid.uuid4()}"
    tenant_data = {
        "tenant_id": tenant_id,
        "tenant_name": "Tenant to Get",
        "room_id": "ROOM456",
        "building_id": "BLD_TEST",
        "tenant_email": f"get_tenant_{uuid.uuid4()}@example.com",
        "deposit_amount": 2000.00
    }
    tenant_create = tenant_models.TenantCreate(**tenant_data)
    created_tenant = tenant_service.create_tenant(db, tenant_create)
    retrieved_tenant = tenant_service.get_tenant_by_id(db, tenant_id=tenant_id)
    assert retrieved_tenant.tenant_id == tenant_id
    assert retrieved_tenant.tenant_name == tenant_data["tenant_name"]

def test_get_tenant_by_id_not_found(db):
    """Tests retrieving a non-existent tenant."""
    non_existent_tenant_id = "NON_EXISTENT_TENANT_ID"
    retrieved_tenant = tenant_service.get_tenant_by_id(db, tenant_id=non_existent_tenant_id)
    assert retrieved_tenant is None

def test_update_tenant(db):
    """Tests updating tenant details."""
    tenant_id = f"TNT_TEST_{uuid.uuid4()}"
    tenant_data = {
        "tenant_id": tenant_id,
        "tenant_name": "Tenant to Update",
        "room_id": "ROOM789",
        "building_id": "BLD_TEST",
        "tenant_email": f"update_tenant_{uuid.uuid4()}@example.com",
        "deposit_amount": 2500.00
    }
    tenant_create = tenant_models.TenantCreate(**tenant_data)
    created_tenant = tenant_service.create_tenant(db, tenant_create)

    tenant_update_data = {
        "tenant_name": "Updated Tenant Name",
        "payment_status": "CURRENT"
    }
    tenant_update_model = tenant_models.TenantUpdate(**tenant_update_data)
    updated_tenant = tenant_service.update_tenant(db, tenant_id=tenant_id, tenant_update=tenant_update_model)
    assert updated_tenant.tenant_id == tenant_id
    assert updated_tenant.tenant_name == tenant_update_data["tenant_name"]
    assert updated_tenant.payment_status == tenant_update_data["payment_status"]

def test_delete_tenant(db):
    """Tests deleting a tenant."""
    tenant_id = f"TNT_TEST_{uuid.uuid4()}"
    tenant_data = {
        "tenant_id": tenant_id,
        "tenant_name": "Tenant to Delete",
        "room_id": "ROOM101112",
        "building_id": "BLD_TEST",
        "tenant_email": f"delete_tenant_{uuid.uuid4()}@example.com",
        "deposit_amount": 3000.00
    }
    tenant_create = tenant_models.TenantCreate(**tenant_data)
    created_tenant = tenant_service.create_tenant(db, tenant_create)
    deletion_successful = tenant_service.delete_tenant(db, tenant_id=tenant_id)
    assert deletion_successful
    retrieved_tenant = tenant_service.get_tenant_by_id(db, tenant_id=tenant_id)
    assert retrieved_tenant is None

def test_get_all_tenants(db):
    """Tests retrieving all tenants."""
    # Create a few tenants
    tenant_data1 = {
        "tenant_id": f"TNT_TEST_{uuid.uuid4()}",
        "tenant_name": "Tenant One",
        "room_id": "ROOM_A",
        "building_id": "BLD_TEST",
        "tenant_email": f"tenant1_{uuid.uuid4()}@example.com",
        "deposit_amount": 1000.00
    }
    tenant_create1 = tenant_models.TenantCreate(**tenant_data1)
    tenant_service.create_tenant(db, tenant_create1)

    tenant_data2 = {
        "tenant_id": f"TNT_TEST_{uuid.uuid4()}",
        "tenant_name": "Tenant Two",
        "room_id": "ROOM_B",
        "building_id": "BLD_TEST",
        "tenant_email": f"tenant2_{uuid.uuid4()}@example.com",
        "deposit_amount": 1200.00
    }
    tenant_create2 = tenant_models.TenantCreate(**tenant_data2)
    tenant_service.create_tenant(db, tenant_create2)

    tenants_list = tenant_service.get_all_tenants(db)
    assert isinstance(tenants_list, list)
    assert len(tenants_list) >= 2
    tenant_ids_in_response = {tenant.tenant_id for tenant in tenants_list}
    assert tenant_data1["tenant_id"] in tenant_ids_in_response
    assert tenant_data2["tenant_id"] in tenant_ids_in_response