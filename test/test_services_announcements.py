import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, timedelta

from app.db.connection import Base
from app.services import announcement_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for announcements."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create test buildings and tenants
        building1 = models.Building(
            building_id="TEST_BUILDING_1",
            building_name="Test Building 1"
        )
        building2 = models.Building(
            building_id="TEST_BUILDING_2",
            building_name="Test Building 2"
        )
        
        # Create tenants for building 1
        for i in range(3):
            tenant = models.Tenant(
                tenant_id=f"TEST_TENANT_{i+1}",
                tenant_name=f"Test Tenant {i+1}",
                room_id=f"TEST_ROOM_{i+1}",
                building_id="TEST_BUILDING_1",
                tenant_email=f"tenant{i+1}@example.com",
                status="ACTIVE"
            )
            db_session.add(tenant)
        
        # Create a tenant for building 2
        tenant = models.Tenant(
            tenant_id="TEST_TENANT_4",
            tenant_name="Test Tenant 4",
            room_id="TEST_ROOM_4",
            building_id="TEST_BUILDING_2",
            tenant_email="tenant4@example.com",
            status="ACTIVE"
        )
        
        db_session.add(building1)
        db_session.add(building2)
        db_session.add(tenant)
        db_session.commit()
        
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_announcement(db):
    """Tests creating a new building announcement."""
    building_id = "TEST_BUILDING_1"
    title = "Test Announcement"
    content = "This is a test announcement"
    priority = "NORMAL"
    
    announcement = announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title=title,
        content=content,
        priority=priority,
        send_notifications=False  # Don't send notifications in test
    )
    
    assert announcement.announcement_id is not None
    assert announcement.announcement_id.startswith("ANN_")
    assert announcement.building_id == building_id
    assert announcement.title == title
    assert announcement.content == content
    assert announcement.priority == priority
    assert announcement.created_at is not None
    assert announcement.expires_at is None

def test_create_announcement_with_expiry(db):
    """Tests creating an announcement with expiry date."""
    building_id = "TEST_BUILDING_1"
    title = "Expiring Announcement"
    content = "This announcement will expire"
    priority = "HIGH"
    expires_at = datetime.now() + timedelta(days=7)
    
    announcement = announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title=title,
        content=content,
        priority=priority,
        expires_at=expires_at,
        send_notifications=False
    )
    
    assert announcement.announcement_id is not None
    assert announcement.building_id == building_id
    assert announcement.title == title
    assert announcement.priority == priority
    assert announcement.expires_at == expires_at

def test_get_announcement_by_id(db):
    """Tests retrieving an announcement by ID."""
    # Create an announcement
    announcement = announcement_service.create_announcement(
        db=db,
        building_id="TEST_BUILDING_1",
        title="Announcement to Retrieve",
        content="This announcement will be retrieved",
        send_notifications=False
    )
    
    # Retrieve the announcement
    retrieved_announcement = announcement_service.get_announcement_by_id(db, announcement_id=announcement.announcement_id)
    
    assert retrieved_announcement is not None
    assert retrieved_announcement.announcement_id == announcement.announcement_id
    assert retrieved_announcement.title == "Announcement to Retrieve"

def test_get_announcement_by_id_not_found(db):
    """Tests retrieving a non-existent announcement."""
    non_existent_id = f"ANN_{uuid.uuid4()}"
    announcement = announcement_service.get_announcement_by_id(db, announcement_id=non_existent_id)
    assert announcement is None

def test_update_announcement(db):
    """Tests updating an announcement."""
    # Create an announcement
    announcement = announcement_service.create_announcement(
        db=db,
        building_id="TEST_BUILDING_1",
        title="Announcement to Update",
        content="This announcement will be updated",
        priority="NORMAL",
        send_notifications=False
    )
    
    # Update the announcement
    new_title = "Updated Announcement Title"
    new_content = "This is the updated announcement content"
    new_priority = "HIGH"
    new_expires_at = datetime.now() + timedelta(days=14)
    
    updated_announcement = announcement_service.update_announcement(
        db=db,
        announcement_id=announcement.announcement_id,
        title=new_title,
        content=new_content,
        priority=new_priority,
        expires_at=new_expires_at
    )
    
    assert updated_announcement.title == new_title
    assert updated_announcement.content == new_content
    assert updated_announcement.priority == new_priority
    assert updated_announcement.expires_at == new_expires_at
    
    # Verify changes were persisted
    retrieved_announcement = announcement_service.get_announcement_by_id(db, announcement_id=announcement.announcement_id)
    assert retrieved_announcement.title == new_title
    assert retrieved_announcement.content == new_content
    assert retrieved_announcement.priority == new_priority
    assert retrieved_announcement.expires_at == new_expires_at

def test_update_announcement_not_found(db):
    """Tests updating a non-existent announcement."""
    non_existent_id = f"ANN_{uuid.uuid4()}"
    result = announcement_service.update_announcement(
        db=db,
        announcement_id=non_existent_id,
        title="New Title",
        content="New Content"
    )
    assert result is None

def test_delete_announcement(db):
    """Tests deleting an announcement."""
    # Create an announcement
    announcement = announcement_service.create_announcement(
        db=db,
        building_id="TEST_BUILDING_1",
        title="Announcement to Delete",
        content="This announcement will be deleted",
        send_notifications=False
    )
    
    # Delete the announcement
    success = announcement_service.delete_announcement(db, announcement_id=announcement.announcement_id)
    
    assert success is True
    
    # Verify the announcement was deleted
    retrieved_announcement = announcement_service.get_announcement_by_id(db, announcement_id=announcement.announcement_id)
    assert retrieved_announcement is None

def test_get_building_announcements(db):
    """Tests retrieving announcements for a specific building."""
    building_id = "TEST_BUILDING_1"
    
    # Create several announcements for the building
    for i in range(3):
        announcement_service.create_announcement(
            db=db,
            building_id=building_id,
            title=f"Building Announcement {i+1}",
            content=f"This is building announcement {i+1}",
            send_notifications=False
        )
    
    # Create an announcement for another building
    announcement_service.create_announcement(
        db=db,
        building_id="TEST_BUILDING_2",
        title="Other Building Announcement",
        content="This is for another building",
        send_notifications=False
    )
    
    # Retrieve announcements for our test building
    announcements = announcement_service.get_building_announcements(
        db=db,
        building_id=building_id,
        include_expired=True
    )
    
    assert len(announcements) == 3
    for announcement in announcements:
        assert announcement.building_id == building_id

def test_get_building_announcements_exclude_expired(db):
    """Tests retrieving non-expired announcements for a building."""
    building_id = "TEST_BUILDING_1"
    
    # Create a non-expiring announcement
    announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title="Non-expiring Announcement",
        content="This announcement does not expire",
        send_notifications=False
    )
    
    # Create an active announcement with future expiry
    announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title="Future Expiry Announcement",
        content="This announcement expires in the future",
        expires_at=datetime.now() + timedelta(days=7),
        send_notifications=False
    )
    
    # Create an expired announcement
    announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title="Expired Announcement",
        content="This announcement has expired",
        expires_at=datetime.now() - timedelta(days=1),
        send_notifications=False
    )
    
    # Retrieve non-expired announcements
    announcements = announcement_service.get_building_announcements(
        db=db,
        building_id=building_id,
        include_expired=False
    )
    
    assert len(announcements) == 2
    announcement_titles = [a.title for a in announcements]
    assert "Non-expiring Announcement" in announcement_titles
    assert "Future Expiry Announcement" in announcement_titles
    assert "Expired Announcement" not in announcement_titles

def test_get_active_announcements_for_tenant(db):
    """Tests retrieving active announcements for a specific tenant."""
    tenant_id = "TEST_TENANT_1"
    building_id = "TEST_BUILDING_1"
    
    # Create active announcements for the tenant's building
    announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title="Active Announcement 1",
        content="This is an active announcement",
        send_notifications=False
    )
    
    announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title="Active Announcement 2",
        content="This is another active announcement",
        expires_at=datetime.now() + timedelta(days=7),
        send_notifications=False
    )
    
    # Create an expired announcement
    announcement_service.create_announcement(
        db=db,
        building_id=building_id,
        title="Expired Announcement",
        content="This announcement has expired",
        expires_at=datetime.now() - timedelta(days=1),
        send_notifications=False
    )
    
    # Create an announcement for another building
    announcement_service.create_announcement(
        db=db,
        building_id="TEST_BUILDING_2",
        title="Other Building Announcement",
        content="This is for another building",
        send_notifications=False
    )
    
    # Retrieve active announcements for the tenant
    announcements = announcement_service.get_active_announcements_for_tenant(
        db=db,
        tenant_id=tenant_id
    )
    
    assert len(announcements) == 2
    announcement_titles = [a.title for a in announcements]
    assert "Active Announcement 1" in announcement_titles
    assert "Active Announcement 2" in announcement_titles
    assert "Expired Announcement" not in announcement_titles
    assert "Other Building Announcement" not in announcement_titles