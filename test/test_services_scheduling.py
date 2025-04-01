import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, timedelta

from app.db.connection import Base
from app.services import scheduling_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for scheduling."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create a test building, room, operator, lead, and tenant
        building = models.Building(
            building_id="TEST_BUILDING_1",
            building_name="Test Building"
        )
        room = models.Room(
            room_id="TEST_ROOM_1",
            room_number="101",
            building_id="TEST_BUILDING_1",
            private_room_rent=1500.00
        )
        operator = models.Operator(
            name="Test Operator",
            email="test_operator@example.com"
        )
        lead = models.Lead(
            lead_id="TEST_LEAD_1",
            email="test_lead@example.com",
            status="EXPLORING"
        )
        tenant = models.Tenant(
            tenant_id="TEST_TENANT_1",
            tenant_name="Test Tenant",
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            tenant_email="test_tenant@example.com"
        )
        
        db_session.add(building)
        db_session.add(room)
        db_session.add(operator)
        db_session.add(lead)
        db_session.add(tenant)
        db_session.commit()
        
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_event(db):
    """Tests creating a new scheduled event."""
    event_type = "SHOWING"
    title = "Test Showing Event"
    description = "This is a test showing event"
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    event = scheduling_service.create_event(
        db=db,
        event_type=event_type,
        title=title,
        description=description,
        start_time=start_time,
        end_time=end_time,
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        operator_id=1,
        lead_id="TEST_LEAD_1"
    )
    
    assert event.event_id is not None
    assert event.event_id.startswith("EVENT_")
    assert event.event_type == event_type
    assert event.title == title
    assert event.description == description
    assert event.start_time == start_time
    assert event.end_time == end_time
    assert event.status == "SCHEDULED"
    assert event.room_id == "TEST_ROOM_1"
    assert event.building_id == "TEST_BUILDING_1"
    assert event.operator_id == 1
    assert event.lead_id == "TEST_LEAD_1"
    assert event.tenant_id is None
    assert event.created_at is not None

def test_get_event_by_id(db):
    """Tests retrieving an event by ID."""
    # Create an event
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    event = scheduling_service.create_event(
        db=db,
        event_type="MAINTENANCE",
        title="Test Get Event",
        description="This is a retrievable event",
        start_time=start_time,
        end_time=end_time,
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        operator_id=1,
        tenant_id="TEST_TENANT_1"
    )
    
    # Retrieve the event
    retrieved_event = scheduling_service.get_event_by_id(db, event_id=event.event_id)
    
    assert retrieved_event is not None
    assert retrieved_event.event_id == event.event_id
    assert retrieved_event.title == "Test Get Event"
    assert retrieved_event.event_type == "MAINTENANCE"

def test_get_event_by_id_not_found(db):
    """Tests retrieving a non-existent event."""
    non_existent_id = f"EVENT_{uuid.uuid4()}"
    event = scheduling_service.get_event_by_id(db, event_id=non_existent_id)
    assert event is None

def test_update_event_status(db):
    """Tests updating an event's status."""
    # Create an event
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    event = scheduling_service.create_event(
        db=db,
        event_type="SHOWING",
        title="Event to Update Status",
        description="This event's status will be updated",
        start_time=start_time,
        end_time=end_time,
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        lead_id="TEST_LEAD_1"
    )
    
    assert event.status == "SCHEDULED"
    
    # Update the status
    updated_event = scheduling_service.update_event_status(db, event_id=event.event_id, status="CONFIRMED")
    
    assert updated_event.status == "CONFIRMED"
    
    # Verify changes were persisted
    retrieved_event = scheduling_service.get_event_by_id(db, event_id=event.event_id)
    assert retrieved_event.status == "CONFIRMED"

def test_update_event_status_not_found(db):
    """Tests updating status of a non-existent event."""
    non_existent_id = f"EVENT_{uuid.uuid4()}"
    result = scheduling_service.update_event_status(db, event_id=non_existent_id, status="CONFIRMED")
    assert result is None

def test_update_event(db):
    """Tests updating event details."""
    # Create an event
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    event = scheduling_service.create_event(
        db=db,
        event_type="MOVE_IN",
        title="Event to Update",
        description="This event will be updated",
        start_time=start_time,
        end_time=end_time,
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1"
    )
    
    # Prepare update data
    new_title = "Updated Event Title"
    new_description = "Updated event description"
    new_start_time = start_time + timedelta(hours=2)
    new_end_time = end_time + timedelta(hours=2)
    
    update_data = {
        "title": new_title,
        "description": new_description,
        "start_time": new_start_time,
        "end_time": new_end_time
    }
    
    # Update the event
    updated_event = scheduling_service.update_event(db, event_id=event.event_id, event_update=update_data)
    
    assert updated_event.title == new_title
    assert updated_event.description == new_description
    assert updated_event.start_time == new_start_time
    assert updated_event.end_time == new_end_time
    
    # Verify changes were persisted
    retrieved_event = scheduling_service.get_event_by_id(db, event_id=event.event_id)
    assert retrieved_event.title == new_title
    assert retrieved_event.description == new_description

def test_delete_event(db):
    """Tests deleting an event."""
    # Create an event
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    event = scheduling_service.create_event(
        db=db,
        event_type="SHOWING",
        title="Event to Delete",
        description="This event will be deleted",
        start_time=start_time,
        end_time=end_time,
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        lead_id="TEST_LEAD_1"
    )
    
    # Delete the event
    success = scheduling_service.delete_event(db, event_id=event.event_id)
    
    assert success is True
    
    # Verify the event was deleted
    retrieved_event = scheduling_service.get_event_by_id(db, event_id=event.event_id)
    assert retrieved_event is None

def test_get_operator_events(db):
    """Tests retrieving events for a specific operator."""
    operator_id = 1
    start_time = datetime.now() + timedelta(days=1)
    
    # Create several events for the operator
    for i in range(3):
        scheduling_service.create_event(
            db=db,
            event_type="SHOWING",
            title=f"Operator Event {i+1}",
            description=f"This is operator event {i+1}",
            start_time=start_time + timedelta(hours=i),
            end_time=start_time + timedelta(hours=i+1),
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            operator_id=operator_id,
            lead_id="TEST_LEAD_1"
        )
    
    # Create an event for another operator
    scheduling_service.create_event(
        db=db,
        event_type="SHOWING",
        title="Other Operator Event",
        description="This is for another operator",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        operator_id=2,
        lead_id="TEST_LEAD_1"
    )
    
    # Retrieve events for our test operator
    events = scheduling_service.get_operator_events(db, operator_id=operator_id)
    
    assert len(events) == 3
    for event in events:
        assert event.operator_id == operator_id

def test_get_building_events(db):
    """Tests retrieving events for a specific building."""
    building_id = "TEST_BUILDING_1"
    start_time = datetime.now() + timedelta(days=1)
    
    # Create several events for the building
    for i in range(3):
        scheduling_service.create_event(
            db=db,
            event_type="MAINTENANCE",
            title=f"Building Event {i+1}",
            description=f"This is building event {i+1}",
            start_time=start_time + timedelta(hours=i),
            end_time=start_time + timedelta(hours=i+1),
            building_id=building_id,
            tenant_id="TEST_TENANT_1"
        )
    
    # Create an event for another building
    scheduling_service.create_event(
        db=db,
        event_type="MAINTENANCE",
        title="Other Building Event",
        description="This is for another building",
        start_time=start_time,
        end_time=start_time + timedelta(hours=1),
        building_id="OTHER_BUILDING",
        tenant_id="TEST_TENANT_1"
    )
    
    # Retrieve events for our test building
    events = scheduling_service.get_building_events(db, building_id=building_id)
    
    assert len(events) == 3
    for event in events:
        assert event.building_id == building_id

def test_find_available_slots(db):
    """Tests finding available time slots."""
    building_id = "TEST_BUILDING_1"
    room_id = "TEST_ROOM_1"
    operator_id = 1
    
    # Current time rounded to the nearest hour
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    tomorrow = now + timedelta(days=1)
    
    # Create a busy slot
    busy_start = tomorrow.replace(hour=10)
    busy_end = tomorrow.replace(hour=11)
    
    scheduling_service.create_event(
        db=db,
        event_type="SHOWING",
        title="Busy Slot",
        description="This slot is busy",
        start_time=busy_start,
        end_time=busy_end,
        room_id=room_id,
        building_id=building_id,
        operator_id=operator_id,
        lead_id="TEST_LEAD_1"
    )
    
    # Find available slots
    date_from = tomorrow.replace(hour=9)
    date_to = tomorrow.replace(hour=17)
    duration_minutes = 60
    
    slots = scheduling_service.find_available_slots(
        db=db,
        event_type="SHOWING",
        duration_minutes=duration_minutes,
        date_from=date_from,
        date_to=date_to,
        operator_id=operator_id,
        building_id=building_id,
        room_id=room_id
    )
    
    # Verify busy slot is excluded
    for slot_start, slot_end in slots:
        assert not (slot_end > busy_start and slot_start < busy_end)
    
    # There should be multiple available slots
    assert len(slots) > 0