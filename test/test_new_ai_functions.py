import pytest
from unittest import mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

from app.db.connection import Base
from app.db import models
from app.ai_functions import (
    filter_rooms_function,
    schedule_event_function,
    process_maintenance_request_function,
    generate_insights_function,
    create_communication_function,
    generate_document_function,
    manage_checklist_function
)

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture with test data."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create test data
        building = models.Building(
            building_id="BLD_TEST_1",
            building_name="Test Building 1",
            full_address="123 Test St, Testville, CA 90210"
        )
        db_session.add(building)
        
        # Create rooms with various features
        rooms = [
            models.Room(
                room_id="ROOM_TEST_1",
                room_number="101",
                building_id="BLD_TEST_1",
                view="City",
                bathroom_type="Private",
                private_room_rent=2000.00,
                status="AVAILABLE",
                ready_to_rent=True,
                bed_size="Queen",
                maximum_people_in_room=1,
                mini_fridge=True,
                air_conditioning=True
            ),
            models.Room(
                room_id="ROOM_TEST_2",
                room_number="102",
                building_id="BLD_TEST_1",
                view="Bay",
                bathroom_type="En-Suite",
                private_room_rent=2500.00,
                status="AVAILABLE",
                ready_to_rent=True,
                bed_size="King",
                maximum_people_in_room=1,
                sink=True,
                work_desk=True
            ),
            models.Room(
                room_id="ROOM_TEST_3",
                room_number="201",
                building_id="BLD_TEST_1",
                view="Garden",
                bathroom_type="Shared",
                private_room_rent=1500.00,
                shared_room_rent_2=900.00,
                status="AVAILABLE",
                ready_to_rent=True,
                bed_size="Twin",
                maximum_people_in_room=2,
                heating=True
            ),
            models.Room(
                room_id="ROOM_TEST_4",
                room_number="202",
                building_id="BLD_TEST_1",
                view="Street",
                bathroom_type="Private",
                private_room_rent=1800.00,
                status="OCCUPIED",
                ready_to_rent=True,
                bed_size="Full",
                maximum_people_in_room=1,
                work_desk=True,
                work_chair=True
            )
        ]
        for room in rooms:
            db_session.add(room)
        
        # Create operators
        operator = models.Operator(
            operator_id=1,
            name="Test Operator",
            email="test_operator@example.com",
            role="Leasing Agent",
            active=True
        )
        db_session.add(operator)
        
        # Create leads
        lead = models.Lead(
            lead_id="LEAD_TEST_1",
            email="test_lead@example.com",
            status="EXPLORING"
        )
        db_session.add(lead)
        
        # Create tenants
        tenant = models.Tenant(
            tenant_id="TENANT_TEST_1",
            tenant_name="Test Tenant",
            room_id="ROOM_TEST_4",
            building_id="BLD_TEST_1",
            tenant_email="test_tenant@example.com",
            status="ACTIVE",
            lease_start_date=datetime.now().date() - timedelta(days=30),
            lease_end_date=datetime.now().date() + timedelta(days=335)
        )
        db_session.add(tenant)
        
        db_session.commit()
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

# Mock Gemini API Response
def mock_gemini_generate_content(*args, **kwargs):
    """Mocks Gemini API response for testing AI functions."""
    model = args[0] if args else kwargs.get('model', '')
    contents = args[1] if len(args) > 1 else kwargs.get('contents', '')
    
    # Default mock response
    response_mock = mock.Mock(text="Test response from Gemini API")
    
    # Different responses based on the function being tested
    if "filter_rooms" in contents.lower() or "room" in contents.lower():
        response_mock.text = "Found several rooms matching your criteria. Prices range from $1500 to $2500."
    elif "schedule" in contents.lower() or "event" in contents.lower() or "showing" in contents.lower():
        response_mock.text = "Your showing has been scheduled for tomorrow at 10:00 AM."
    elif "maintenance" in contents.lower() or "repair" in contents.lower():
        response_mock.text = "Your maintenance request has been submitted and will be addressed soon."
    elif "analytics" in contents.lower() or "metrics" in contents.lower() or "insights" in contents.lower():
        response_mock.text = "Property performance analysis shows 80% occupancy rate with an average rent of $2000."
    elif "message" in contents.lower() or "notification" in contents.lower() or "communication" in contents.lower():
        response_mock.text = "Your message has been sent successfully."
    elif "document" in contents.lower() or "lease" in contents.lower() or "application" in contents.lower():
        response_mock.text = "The document has been generated and is ready for review."
    elif "checklist" in contents.lower() or "move in" in contents.lower() or "move out" in contents.lower():
        response_mock.text = "Move-in checklist has been created with standard items."
    
    return response_mock

@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    """Fixture to mock Gemini API for all tests in this file."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    yield

def test_filter_rooms_function(db):
    """Tests filtering rooms based on user preferences."""
    # Test with basic query
    result = filter_rooms_function(query="I want a room with a private bathroom", db=db)
    
    assert "success" not in result  # No error
    assert "response" in result
    assert "data" in result
    assert isinstance(result["data"], list)
    
    # Verify private bathroom rooms are returned
    private_bathroom_count = 0
    for room in result["data"]:
        if room["bathroom_type"] == "Private":
            private_bathroom_count += 1
    
    assert private_bathroom_count > 0
    
    # Test with more specific parameters
    result = filter_rooms_function(
        query="Looking for a nice room",
        min_price=1800,
        max_price=3000,
        bathroom_type="Private",
        db=db
    )
    
    assert "data" in result
    assert isinstance(result["data"], list)
    
    # Verify price and bathroom filters
    for room in result["data"]:
        assert room["private_room_rent"] >= 1800
        assert room["private_room_rent"] <= 3000
        assert room["bathroom_type"] == "Private"
    
    # Test amenities filter
    result = filter_rooms_function(
        query="Room with desk",
        amenities=["work desk"],
        db=db
    )
    
    assert "data" in result
    assert isinstance(result["data"], list)
    
    # Verify rooms with work desk are returned
    for room in result["data"]:
        assert room["features"]["work_desk"] is True

def test_schedule_event_function(db):
    """Tests scheduling an event."""
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    result = schedule_event_function(
        event_type="SHOWING",
        title="Test Showing",
        start_time=start_time.isoformat(),
        end_time=end_time.isoformat(),
        room_id="ROOM_TEST_1",
        building_id="BLD_TEST_1",
        operator_id="1",
        lead_id="LEAD_TEST_1",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "event_id" in result
    assert result["event_id"].startswith("EVENT_")
    assert "status" in result
    assert result["status"] == "SCHEDULED"
    assert "response" in result

def test_process_maintenance_request_function_create(db):
    """Tests creating a maintenance request."""
    result = process_maintenance_request_function(
        action="CREATE",
        title="Test Maintenance Request",
        description="This is a test maintenance request",
        room_id="ROOM_TEST_4",
        building_id="BLD_TEST_1",
        tenant_id="TENANT_TEST_1",
        priority="MEDIUM",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "request_id" in result
    assert result["request_id"].startswith("MAINT_")
    assert "status" in result
    assert result["status"] == "PENDING"
    assert "priority" in result
    assert result["priority"] == "MEDIUM"
    assert "response" in result

def test_process_maintenance_request_function_update(db):
    """Tests updating a maintenance request status."""
    # First create a request
    create_result = process_maintenance_request_function(
        action="CREATE",
        title="Request to Update",
        description="This request will be updated",
        room_id="ROOM_TEST_4",
        building_id="BLD_TEST_1",
        tenant_id="TENANT_TEST_1",
        priority="LOW",
        db=db
    )
    
    request_id = create_result["request_id"]
    
    # Now update it
    update_result = process_maintenance_request_function(
        action="UPDATE",
        request_id=request_id,
        status="IN_PROGRESS",
        db=db
    )
    
    assert "success" in update_result
    assert update_result["success"] is True
    assert "request_id" in update_result
    assert update_result["request_id"] == request_id
    assert "status" in update_result
    assert update_result["status"] == "IN_PROGRESS"
    assert "response" in update_result

def test_process_maintenance_request_function_assign(db):
    """Tests assigning a maintenance request."""
    # First create a request
    create_result = process_maintenance_request_function(
        action="CREATE",
        title="Request to Assign",
        description="This request will be assigned",
        room_id="ROOM_TEST_4",
        building_id="BLD_TEST_1",
        tenant_id="TENANT_TEST_1",
        priority="HIGH",
        db=db
    )
    
    request_id = create_result["request_id"]
    
    # Now assign it
    assign_result = process_maintenance_request_function(
        action="ASSIGN",
        request_id=request_id,
        assigned_to="1",
        db=db
    )
    
    assert "success" in assign_result
    assert assign_result["success"] is True
    assert "request_id" in assign_result
    assert assign_result["request_id"] == request_id
    assert "assigned_to" in assign_result
    assert assign_result["assigned_to"] == 1
    assert "status" in assign_result
    assert assign_result["status"] == "ASSIGNED"
    assert "response" in assign_result

def test_generate_insights_function(db):
    """Tests generating analytics insights."""
    result = generate_insights_function(
        insight_type="OCCUPANCY",
        building_id="BLD_TEST_1",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "insight_type" in result
    assert result["insight_type"] == "OCCUPANCY"
    assert "data" in result
    assert "occupancy_rate" in result["data"]
    assert "summary" in result
    assert "analysis" in result
    assert "response" in result
    
    # Test dashboard insights
    dashboard_result = generate_insights_function(
        insight_type="DASHBOARD",
        building_id="BLD_TEST_1",
        db=db
    )
    
    assert "success" in dashboard_result
    assert dashboard_result["success"] is True
    assert "data" in dashboard_result
    assert "occupancy_metrics" in dashboard_result["data"]
    assert "financial_metrics" in dashboard_result["data"]
    assert "lead_metrics" in dashboard_result["data"]
    assert "response" in dashboard_result

def test_create_communication_function_message(db):
    """Tests creating a message."""
    result = create_communication_function(
        communication_type="MESSAGE",
        content="This is a test message",
        sender_type="OPERATOR",
        sender_id="1",
        recipient_type="TENANT",
        recipient_id="TENANT_TEST_1",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "message_id" in result or "message_count" in result
    assert "response" in result

def test_create_communication_function_bulk(db):
    """Tests sending a bulk message."""
    result = create_communication_function(
        communication_type="MESSAGE",
        content="This is a bulk test message",
        sender_type="OPERATOR",
        sender_id="1",
        recipient_type="TENANT",
        recipient_ids=["TENANT_TEST_1", "OTHER_TENANT"], # Only first will exist in test DB
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "message_count" in result
    assert result["message_count"] >= 1
    assert "response" in result

def test_create_communication_function_notification(db):
    """Tests creating a notification."""
    result = create_communication_function(
        communication_type="NOTIFICATION",
        content="This is a test notification",
        user_type="TENANT",
        user_id="TENANT_TEST_1",
        title="Test Notification",
        notification_type="TEST",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "notification_id" in result
    assert result["notification_id"].startswith("NOTIF_")
    assert "status" in result
    assert "response" in result

def test_create_communication_function_announcement(db):
    """Tests creating an announcement."""
    result = create_communication_function(
        communication_type="ANNOUNCEMENT",
        content="This is a test announcement",
        building_id="BLD_TEST_1",
        title="Test Announcement",
        priority="HIGH",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "announcement_id" in result
    assert result["announcement_id"].startswith("ANN_")
    assert "building_id" in result
    assert result["building_id"] == "BLD_TEST_1"
    assert "response" in result

def test_generate_document_function_lease(db):
    """Tests generating a lease document."""
    result = generate_document_function(
        document_type="LEASE",
        tenant_id="TENANT_TEST_1",
        room_id="ROOM_TEST_4",
        building_id="BLD_TEST_1",
        lease_start_date=datetime.now().date().isoformat(),
        lease_end_date=(datetime.now().date() + timedelta(days=365)).isoformat(),
        monthly_rent=1800.00,
        deposit_amount=3600.00,
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "document_id" in result
    assert result["document_id"].startswith("DOC_")
    assert "document_type" in result
    assert result["document_type"] == "LEASE"
    assert "status" in result
    assert "response" in result

def test_generate_document_function_application(db):
    """Tests generating an application document."""
    result = generate_document_function(
        document_type="APPLICATION",
        lead_id="LEAD_TEST_1",
        room_id="ROOM_TEST_1",
        building_id="BLD_TEST_1",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "document_id" in result
    assert result["document_id"].startswith("DOC_")
    assert "document_type" in result
    assert result["document_type"] == "APPLICATION"
    assert "status" in result
    assert "response" in result

def test_manage_checklist_function_create(db):
    """Tests creating a checklist."""
    result = manage_checklist_function(
        action="CREATE",
        checklist_type="INSPECTION",
        room_id="ROOM_TEST_4",
        building_id="BLD_TEST_1",
        tenant_id="TENANT_TEST_1",
        operator_id="1",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "checklist_id" in result
    assert result["checklist_id"].startswith("CHKL_")
    assert "checklist_type" in result
    assert result["checklist_type"] == "INSPECTION"
    assert "status" in result
    assert "response" in result

def test_manage_checklist_function_move_in(db):
    """Tests creating a move-in checklist."""
    result = manage_checklist_function(
        action="CREATE",
        checklist_type="MOVE_IN",
        room_id="ROOM_TEST_4",
        building_id="BLD_TEST_1",
        tenant_id="TENANT_TEST_1",
        db=db
    )
    
    assert "success" in result
    assert result["success"] is True
    assert "checklist_id" in result
    assert result["checklist_id"].startswith("CHKL_")
    assert "checklist_type" in result
    assert result["checklist_type"] == "MOVE_IN"
    assert "status" in result
    assert "response" in result

def test_manage_checklist_function_update_status(db):
    """Tests updating a checklist status."""
    # First create a checklist
    create_result = manage_checklist_function(
        action="CREATE",
        checklist_type="MOVE_OUT",
        room_id="ROOM_TEST_4",
        building_id="BLD_TEST_1",
        tenant_id="TENANT_TEST_1",
        db=db
    )
    
    checklist_id = create_result["checklist_id"]
    
    # Now update its status
    update_result = manage_checklist_function(
        action="UPDATE_STATUS",
        checklist_id=checklist_id,
        status="IN_PROGRESS",
        db=db
    )
    
    assert "success" in update_result
    assert update_result["success"] is True
    assert "checklist_id" in update_result
    assert update_result["checklist_id"] == checklist_id
    assert "status" in update_result
    assert update_result["status"] == "IN_PROGRESS"
    assert "response" in update_result