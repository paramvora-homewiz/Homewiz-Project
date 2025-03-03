from typing import Dict, Any, List
import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient # Import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
import uuid # Import uuid
from app.db import models
from app.endpoints import leads
from app.db.connection import Base, get_db, SessionLocal # Import original get_db and SessionLocal
from app.main import app as fastapi_app  # Import your main FastAPI app


# TEST_DATABASE_URL = "sqlite:///:memory:" # No longer using in-memory DB - REMOVE this line
DATABASE_URL = os.getenv("SUPABASE_DB_URL")
@pytest.fixture(scope="session", autouse=True)
def test_db():
    """
    Session-wide test database fixture.
    Now just ensures tables exist once at session start (optional, assuming DB is already setup).
    """
    engine = create_engine(DATABASE_URL) # Use your actual DATABASE_URL
    # Base.metadata.create_all(engine) # No longer creating/dropping tables in tests - REMOVE this line

    yield # Run tests

    # Base.metadata.drop_all(engine) # No longer creating/dropping tables in tests - REMOVE this line


@pytest.fixture()
def client(test_db): # test_db fixture is automatically used because of parameter
    """
    Test client fixture using FastAPI's TestClient and your Supabase DB, with cleanup, logging, and rollback.
    """
    created_lead_ids = [] # List to track lead_ids created in this test function
    import logging # Import logging here, inside the fixture

    def override_get_db():
        db_session = SessionLocal() # Create a NEW session for each test
        try:
            yield db_session
        except Exception as e: # Catch any exceptions during test execution
            logging.error(f"Error in override_get_db setup: {e}") # Log error during setup
            db_session.rollback() # Rollback the session in case of error during setup
            raise e # Re-raise the exception to fail the test
        finally:
            logging.info(f"Cleanup started for test function. Created lead_ids: {created_lead_ids}") # Log cleanup start
            # Cleanup: Delete leads created in this test function
            for lead_id_to_delete in created_lead_ids:
                lead_to_delete = db_session.query(models.Lead).filter(models.Lead.lead_id == lead_id_to_delete).first()
                if lead_to_delete:
                    db_session.delete(lead_to_delete)
                    logging.info(f"Deleted lead with lead_id: {lead_id_to_delete}") # Log deletion
                else:
                    logging.warning(f"Lead with lead_id: {lead_id_to_delete} not found during cleanup.") # Log if not found
            db_session.commit()
            db_session.close() # Ensure session is closed in finally block
            logging.info(f"Cleanup finished for test function.") # Log cleanup finish

    fastapi_app.dependency_overrides[get_db] = override_get_db # Override DB dependency
    test_client = TestClient(fastapi_app)

    def test_client_with_cleanup(): # Wrapper to track created lead_ids
        test_client.created_lead_ids = created_lead_ids # Attach the list to the client
        return test_client

    yield test_client_with_cleanup() # Yield the wrapped client

    fastapi_app.dependency_overrides.clear() # Clear overrides after test


def test_create_lead(client: TestClient): # client is now the wrapped client
    """
    Tests creating a new lead.
    """
    unique_suffix = uuid.uuid4() # Generate a unique UUID suffix
    lead_data = {"email": f"test_unique_create_{unique_suffix}@example.com"} # Unique email
    response = client.post("/leads/", json=lead_data)
    assert response.status_code == 201
    created_lead = response.json()
    client.created_lead_ids.append(created_lead["lead_id"]) # Add lead_id to cleanup list
    assert created_lead["email"] == lead_data["email"]
    assert created_lead["status"] == "EXPLORING"
    assert "lead_id" in created_lead
    assert "created_at" in created_lead
    assert "last_modified" in created_lead


def test_read_lead(client: TestClient): # client is now the wrapped client
    """
    Tests reading a lead by ID.
    """
    # First, create a lead to read
    unique_suffix = uuid.uuid4() # Generate a unique UUID suffix
    lead_data = {"email": f"test_unique_read_{unique_suffix}@example.com"} # Unique email
    create_response = client.post("/leads/", json=lead_data)
    assert create_response.status_code == 201
    created_lead = create_response.json()
    client.created_lead_ids.append(created_lead["lead_id"]) # Add lead_id to cleanup list
    lead_id_to_read = created_lead["lead_id"]

    # Now, read the created lead
    read_response = client.get(f"/leads/{lead_id_to_read}")
    assert read_response.status_code == 200
    read_lead = read_response.json()
    assert read_lead["lead_id"] == lead_id_to_read
    assert read_lead["email"] == lead_data["email"]


def test_read_lead_not_found(client: TestClient): # client is now the wrapped client
    """
    Tests reading a lead with an ID that does not exist.
    """
    non_existent_lead_id = "NON_EXISTENT_LEAD_ID"
    response = client.get(f"/leads/{non_existent_lead_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Lead not found"}


def test_update_lead_status(client: TestClient): # client is now the wrapped client
    """
    Tests updating the status of a lead.
    """
    # First, create a lead
    unique_suffix = uuid.uuid4() # Generate a unique UUID suffix
    lead_data = {"email": f"test_unique_update_status_{unique_suffix}@example.com"} # Unique email
    create_response = client.post("/leads/", json=lead_data)
    assert create_response.status_code == 201
    created_lead = create_response.json()
    client.created_lead_ids.append(created_lead["lead_id"]) # Add lead_id to cleanup list
    lead_id_to_update = created_lead["lead_id"]

    # Now, update the status
    status_update_data = {"status": "SHOWING_SCHEDULED"}
    update_response = client.put(f"/leads/{lead_id_to_update}/status", json=status_update_data)
    assert update_response.status_code == 200
    updated_lead = update_response.json()
    assert updated_lead["lead_id"] == lead_id_to_update
    assert updated_lead["status"] == status_update_data["status"]


def test_update_lead_status_not_found(client: TestClient): # client is now the wrapped client
    """
    Tests updating the status of a lead that does not exist.
    """
    non_existent_lead_id = "NON_EXISTENT_LEAD_ID"
    status_update_data = {"status": "SHOWING_SCHEDULED"}
    response = client.put(f"/leads/{non_existent_lead_id}/status", json=status_update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Lead not found"}


def test_update_lead_wishlist(client: TestClient): # client is now the wrapped client
    """
    Tests updating the wishlist of a lead.
    """
    # First, create a lead
    unique_suffix = uuid.uuid4() # Generate a unique UUID suffix
    lead_data = {"email": f"test_unique_update_wishlist_{unique_suffix}@example.com"} # Unique email
    create_response = client.post("/leads/", json=lead_data)
    assert create_response.status_code == 201
    created_lead = create_response.json()
    client.created_lead_ids.append(created_lead["lead_id"]) # Add lead_id to cleanup list
    lead_id_to_update = created_lead["lead_id"]

    # Now, update the wishlist
    wishlist_update_data = {"wishlist": ["ROOM123", "ROOM456"]}
    update_response = client.put(f"/leads/{lead_id_to_update}/wishlist", json=wishlist_update_data)
    assert update_response.status_code == 200
    updated_lead = update_response.json()
    # Wishlist is stored as string in DB, so we expect string back, not list directly
    assert updated_lead["lead_id"] == lead_id_to_update
    assert updated_lead["rooms_interested"] == str(wishlist_update_data["wishlist"])


def test_update_lead_wishlist_not_found(client: TestClient): # client is now the wrapped client
    """
    Tests updating the wishlist of a lead that does not exist.
    """
    non_existent_lead_id = "NON_EXISTENT_LEAD_ID"
    wishlist_update_data = {"wishlist": ["ROOM123", "ROOM456"]}
    response = client.put(f"/leads/{non_existent_lead_id}/wishlist", json=wishlist_update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Lead not found"}


def test_read_leads(client: TestClient): # client is now the wrapped client
    """
    Tests reading all leads.
    """
    # Create a few leads first - using unique emails for Supabase test
    unique_suffix1 = uuid.uuid4() # Unique suffix for lead 1
    unique_suffix2 = uuid.uuid4() # Unique suffix for lead 2
    lead_data1 = {"email": f"test_unique_all_leads1_{unique_suffix1}@example.com"} # Unique email 1
    lead_data2 = {"email": f"test_unique_all_leads2_{unique_suffix2}@example.com"} # Unique email 2
    response1 = client.post("/leads/", json=lead_data1)
    assert response1.status_code == 201
    created_lead1 = response1.json()
    client.created_lead_ids.append(created_lead1["lead_id"])

    response2 = client.post("/leads/", json=lead_data2)
    assert response2.status_code == 201
    created_lead2 = response2.json()
    client.created_lead_ids.append(created_lead2["lead_id"])

    response = client.get("/leads/")
    assert response.status_code == 200
    leads_list = response.json()
    assert isinstance(leads_list, list)
    assert len(leads_list) >= 2 # At least 2 leads should be returned
    emails_in_response = {lead["email"] for lead in leads_list}
    assert lead_data1["email"] in emails_in_response
    assert lead_data2["email"] in emails_in_response


def test_create_lead_duplicate_email(client: TestClient): # client is now the wrapped client
    """
    Tests creating a lead with a duplicate email, which should fail.
    """
    unique_suffix = uuid.uuid4() # Generate a unique UUID suffix
    lead_data = {"email": f"test_unique_duplicate_{unique_suffix}@example.com"} # Unique email
    # Create the lead once successfully
    response1 = client.post("/leads/", json=lead_data)
    assert response1.status_code == 201
    created_lead = response1.json()
    client.created_lead_ids.append(created_lead["lead_id"]) # Add lead_id to cleanup list

    # Try to create again with the same email
    response2 = client.post("/leads/", json=lead_data)
    assert response2.status_code == 400
    assert response2.json() == {"detail": "Lead with this email already registered"}