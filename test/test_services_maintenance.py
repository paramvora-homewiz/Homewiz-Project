import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

from app.db.connection import Base
from app.services import maintenance_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for maintenance requests."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create a test building, room, operator, and tenant
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
        db_session.add(tenant)
        db_session.commit()
        
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_maintenance_request(db):
    """Tests creating a new maintenance request."""
    title = "Test Maintenance Request"
    description = "This is a test maintenance request"
    
    request = maintenance_service.create_maintenance_request(
        db=db,
        title=title,
        description=description,
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    assert request.request_id is not None
    assert request.request_id.startswith("MAINT_")
    assert request.title == title
    assert request.description == description
    assert request.priority == "MEDIUM"
    assert request.status == "PENDING"
    assert request.room_id == "TEST_ROOM_1"
    assert request.building_id == "TEST_BUILDING_1"
    assert request.tenant_id == "TEST_TENANT_1"
    assert request.assigned_to is None
    assert request.created_at is not None
    assert request.updated_at is not None
    assert request.resolved_at is None

def test_create_maintenance_request_with_assignment(db):
    """Tests creating a maintenance request with immediate assignment."""
    title = "Assigned Maintenance Request"
    description = "This request is assigned immediately"
    
    request = maintenance_service.create_maintenance_request(
        db=db,
        title=title,
        description=description,
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="HIGH",
        assigned_to=1
    )
    
    assert request.request_id is not None
    assert request.title == title
    assert request.priority == "HIGH"
    assert request.status == "ASSIGNED"
    assert request.assigned_to == 1

def test_get_maintenance_request_by_id(db):
    """Tests retrieving a maintenance request by ID."""
    # Create a request
    request = maintenance_service.create_maintenance_request(
        db=db,
        title="Request to Retrieve",
        description="This request will be retrieved",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    # Retrieve the request
    retrieved_request = maintenance_service.get_maintenance_request_by_id(db, request_id=request.request_id)
    
    assert retrieved_request is not None
    assert retrieved_request.request_id == request.request_id
    assert retrieved_request.title == "Request to Retrieve"

def test_get_maintenance_request_by_id_not_found(db):
    """Tests retrieving a non-existent maintenance request."""
    non_existent_id = f"MAINT_{uuid.uuid4()}"
    request = maintenance_service.get_maintenance_request_by_id(db, request_id=non_existent_id)
    assert request is None

def test_update_maintenance_request_status(db):
    """Tests updating a maintenance request's status."""
    # Create a request
    request = maintenance_service.create_maintenance_request(
        db=db,
        title="Request to Update Status",
        description="This request's status will be updated",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    assert request.status == "PENDING"
    
    # Update the status
    updated_request = maintenance_service.update_maintenance_request_status(
        db=db,
        request_id=request.request_id,
        status="IN_PROGRESS",
        notes="Work has started"
    )
    
    assert updated_request.status == "IN_PROGRESS"
    
    # Verify changes were persisted
    retrieved_request = maintenance_service.get_maintenance_request_by_id(db, request_id=request.request_id)
    assert retrieved_request.status == "IN_PROGRESS"

def test_update_maintenance_request_status_to_completed(db):
    """Tests updating a maintenance request's status to completed."""
    # Create a request
    request = maintenance_service.create_maintenance_request(
        db=db,
        title="Request to Complete",
        description="This request will be completed",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    # Update the status to completed
    updated_request = maintenance_service.update_maintenance_request_status(
        db=db,
        request_id=request.request_id,
        status="COMPLETED",
        notes="Work is done"
    )
    
    assert updated_request.status == "COMPLETED"
    assert updated_request.resolved_at is not None
    
    # Verify changes were persisted
    retrieved_request = maintenance_service.get_maintenance_request_by_id(db, request_id=request.request_id)
    assert retrieved_request.status == "COMPLETED"
    assert retrieved_request.resolved_at is not None

def test_update_maintenance_request_status_not_found(db):
    """Tests updating status of a non-existent maintenance request."""
    non_existent_id = f"MAINT_{uuid.uuid4()}"
    result = maintenance_service.update_maintenance_request_status(
        db=db,
        request_id=non_existent_id,
        status="IN_PROGRESS"
    )
    assert result is None

def test_assign_maintenance_request(db):
    """Tests assigning a maintenance request to an operator."""
    # Create a request
    request = maintenance_service.create_maintenance_request(
        db=db,
        title="Request to Assign",
        description="This request will be assigned",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    assert request.assigned_to is None
    assert request.status == "PENDING"
    
    # Assign the request
    assigned_request = maintenance_service.assign_maintenance_request(
        db=db,
        request_id=request.request_id,
        operator_id=1
    )
    
    assert assigned_request.assigned_to == 1
    assert assigned_request.status == "ASSIGNED"
    
    # Verify changes were persisted
    retrieved_request = maintenance_service.get_maintenance_request_by_id(db, request_id=request.request_id)
    assert retrieved_request.assigned_to == 1
    assert retrieved_request.status == "ASSIGNED"

def test_assign_maintenance_request_not_found(db):
    """Tests assigning a non-existent maintenance request."""
    non_existent_id = f"MAINT_{uuid.uuid4()}"
    result = maintenance_service.assign_maintenance_request(
        db=db,
        request_id=non_existent_id,
        operator_id=1
    )
    assert result is None

def test_update_maintenance_request(db):
    """Tests updating maintenance request details."""
    # Create a request
    request = maintenance_service.create_maintenance_request(
        db=db,
        title="Request to Update",
        description="This request will be updated",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    # Prepare update data
    update_data = {
        "title": "Updated Request Title",
        "description": "Updated request description",
        "priority": "HIGH"
    }
    
    # Update the request
    updated_request = maintenance_service.update_maintenance_request(
        db=db,
        request_id=request.request_id,
        update_data=update_data
    )
    
    assert updated_request.title == update_data["title"]
    assert updated_request.description == update_data["description"]
    assert updated_request.priority == update_data["priority"]
    
    # Verify changes were persisted
    retrieved_request = maintenance_service.get_maintenance_request_by_id(db, request_id=request.request_id)
    assert retrieved_request.title == update_data["title"]
    assert retrieved_request.description == update_data["description"]
    assert retrieved_request.priority == update_data["priority"]

def test_delete_maintenance_request(db):
    """Tests deleting a maintenance request."""
    # Create a request
    request = maintenance_service.create_maintenance_request(
        db=db,
        title="Request to Delete",
        description="This request will be deleted",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    # Delete the request
    success = maintenance_service.delete_maintenance_request(db, request_id=request.request_id)
    
    assert success is True
    
    # Verify the request was deleted
    retrieved_request = maintenance_service.get_maintenance_request_by_id(db, request_id=request.request_id)
    assert retrieved_request is None

def test_get_tenant_maintenance_requests(db):
    """Tests retrieving maintenance requests for a specific tenant."""
    tenant_id = "TEST_TENANT_1"
    
    # Create several requests for the tenant
    for i in range(3):
        maintenance_service.create_maintenance_request(
            db=db,
            title=f"Tenant Request {i+1}",
            description=f"This is tenant request {i+1}",
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            tenant_id=tenant_id,
            priority="MEDIUM"
        )
    
    # Create a request for another tenant
    maintenance_service.create_maintenance_request(
        db=db,
        title="Other Tenant Request",
        description="This is for another tenant",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="OTHER_TENANT",
        priority="MEDIUM"
    )
    
    # Retrieve requests for our test tenant
    requests = maintenance_service.get_tenant_maintenance_requests(db, tenant_id=tenant_id)
    
    assert len(requests) == 3
    for request in requests:
        assert request.tenant_id == tenant_id

def test_get_building_maintenance_requests(db):
    """Tests retrieving maintenance requests for a specific building."""
    building_id = "TEST_BUILDING_1"
    
    # Create several requests for the building
    for i in range(3):
        maintenance_service.create_maintenance_request(
            db=db,
            title=f"Building Request {i+1}",
            description=f"This is building request {i+1}",
            room_id="TEST_ROOM_1",
            building_id=building_id,
            tenant_id="TEST_TENANT_1",
            priority="MEDIUM"
        )
    
    # Create a request for another building
    maintenance_service.create_maintenance_request(
        db=db,
        title="Other Building Request",
        description="This is for another building",
        room_id="OTHER_ROOM",
        building_id="OTHER_BUILDING",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM"
    )
    
    # Retrieve requests for our test building
    requests = maintenance_service.get_building_maintenance_requests(db, building_id=building_id)
    
    assert len(requests) == 3
    for request in requests:
        assert request.building_id == building_id

def test_get_operator_maintenance_requests(db):
    """Tests retrieving maintenance requests assigned to a specific operator."""
    operator_id = 1
    
    # Create several requests assigned to the operator
    for i in range(3):
        maintenance_service.create_maintenance_request(
            db=db,
            title=f"Operator Request {i+1}",
            description=f"This is operator request {i+1}",
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            tenant_id="TEST_TENANT_1",
            priority="MEDIUM",
            assigned_to=operator_id
        )
    
    # Create a request assigned to another operator
    maintenance_service.create_maintenance_request(
        db=db,
        title="Other Operator Request",
        description="This is for another operator",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM",
        assigned_to=2
    )
    
    # Retrieve requests for our test operator
    requests = maintenance_service.get_operator_maintenance_requests(db, operator_id=operator_id)
    
    assert len(requests) == 3
    for request in requests:
        assert request.assigned_to == operator_id

def test_get_unassigned_maintenance_requests(db):
    """Tests retrieving unassigned maintenance requests."""
    # Create several unassigned requests
    for i in range(3):
        maintenance_service.create_maintenance_request(
            db=db,
            title=f"Unassigned Request {i+1}",
            description=f"This is unassigned request {i+1}",
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            tenant_id="TEST_TENANT_1",
            priority="MEDIUM"
        )
    
    # Create an assigned request
    maintenance_service.create_maintenance_request(
        db=db,
        title="Assigned Request",
        description="This request is assigned",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        priority="MEDIUM",
        assigned_to=1
    )
    
    # Retrieve unassigned requests
    requests = maintenance_service.get_unassigned_maintenance_requests(db)
    
    assert len(requests) == 3
    for request in requests:
        assert request.assigned_to is None
        assert request.status == "PENDING"