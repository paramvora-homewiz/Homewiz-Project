import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import date

from app.db.connection import Base
from app.services import lead_service
from app.db import models
from app.models import lead as lead_models  # Pydantic models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for leads."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_lead(db):
    """Tests creating a new lead."""
    email = f"test_lead_{uuid.uuid4()}@example.com"
    created_lead = lead_service.create_lead(db, email=email)
    assert created_lead.lead_id is not None
    assert created_lead.email == email
    assert created_lead.status == "EXPLORING" # Default status

def test_get_lead_by_id(db):
    """Tests retrieving a lead by ID."""
    email = f"get_lead_id_{uuid.uuid4()}@example.com"
    created_lead = lead_service.create_lead(db, email=email)
    retrieved_lead = lead_service.get_lead_by_id(db, lead_id=created_lead.lead_id)
    assert retrieved_lead.lead_id == created_lead.lead_id
    assert retrieved_lead.email == email

def test_get_lead_by_id_not_found(db):
    """Tests retrieving a non-existent lead by ID."""
    non_existent_lead_id = "NON_EXISTENT_LEAD_ID"
    retrieved_lead = lead_service.get_lead_by_id(db, lead_id=non_existent_lead_id)
    assert retrieved_lead is None

def test_get_lead_by_email(db):
    """Tests retrieving a lead by email."""
    email = f"get_lead_email_{uuid.uuid4()}@example.com"
    created_lead = lead_service.create_lead(db, email=email)
    retrieved_lead = lead_service.get_lead_by_email(db, email=email)
    assert retrieved_lead.lead_id == created_lead.lead_id
    assert retrieved_lead.email == email

def test_get_lead_by_email_not_found(db):
    """Tests retrieving a non-existent lead by email."""
    non_existent_email = f"non_existent_{uuid.uuid4()}@example.com"
    retrieved_lead = lead_service.get_lead_by_email(db, email=non_existent_email)
    assert retrieved_lead is None

def test_update_lead_status(db):
    """Tests updating a lead's status."""
    email = f"update_status_lead_{uuid.uuid4()}@example.com"
    created_lead = lead_service.create_lead(db, email=email)
    updated_status = "SHOWING_SCHEDULED"
    updated_lead = lead_service.update_lead_status(db, lead_id=created_lead.lead_id, status=updated_status)
    assert updated_lead.lead_id == created_lead.lead_id
    assert updated_lead.status == updated_status

def test_update_lead_status_not_found(db):
    """Tests updating status of a non-existent lead."""
    non_existent_lead_id = "NON_EXISTENT_LEAD_ID"
    updated_status = "LEASE_REQUESTED"
    updated_lead = lead_service.update_lead_status(db, lead_id=non_existent_lead_id, status=updated_status)
    assert updated_lead is None

def test_update_lead_wishlist(db):
    """Tests updating a lead's wishlist."""
    email = f"update_wishlist_lead_{uuid.uuid4()}@example.com"
    created_lead = lead_service.create_lead(db, email=email)
    wishlist = ["ROOM123", "ROOM456"]
    updated_lead = lead_service.update_lead_wishlist(db, lead_id=created_lead.lead_id, wishlist=wishlist)
    assert updated_lead.lead_id == created_lead.lead_id
    assert updated_lead.rooms_interested == str(wishlist) # Wishlist is stored as string

def test_update_lead_wishlist_not_found(db):
    """Tests updating wishlist of a non-existent lead."""
    non_existent_lead_id = "NON_EXISTENT_LEAD_ID"
    wishlist = ["ROOM789"]
    updated_lead = lead_service.update_lead_wishlist(db, lead_id=non_existent_lead_id, wishlist=wishlist)
    assert updated_lead is None

def test_get_all_leads(db):
    """Tests retrieving all leads."""
    # Create a few leads
    lead_service.create_lead(db, email=f"all_leads_test1_{uuid.uuid4()}@example.com")
    lead_service.create_lead(db, email=f"all_leads_test2_{uuid.uuid4()}@example.com")

    leads_list = lead_service.get_all_leads(db)
    assert isinstance(leads_list, list)
    assert len(leads_list) >= 2