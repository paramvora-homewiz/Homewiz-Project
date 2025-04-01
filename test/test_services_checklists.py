import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

from app.db.connection import Base
from app.services import checklist_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for checklists."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create test building, room, tenant, operator
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
        tenant = models.Tenant(
            tenant_id="TEST_TENANT_1",
            tenant_name="Test Tenant",
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            tenant_email="test_tenant@example.com"
        )
        operator = models.Operator(
            name="Test Operator",
            email="test_operator@example.com"
        )
        
        db_session.add(building)
        db_session.add(room)
        db_session.add(tenant)
        db_session.add(operator)
        db_session.commit()
        
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_checklist_item(db):
    """Tests creating a new checklist item."""
    # First create a checklist
    checklist = models.Checklist(
        checklist_id="TEST_CHECKLIST_1",
        checklist_type="MOVE_IN",
        status="PENDING",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1"
    )
    db.add(checklist)
    db.commit()
    
    # Create a checklist item
    item = checklist_service.create_checklist_item(
        db=db,
        checklist_id="TEST_CHECKLIST_1",
        description="Test Item",
        status="PENDING",
        notes="Test notes"
    )
    
    assert item.item_id is not None
    assert item.item_id.startswith("ITEM_")
    assert item.checklist_id == "TEST_CHECKLIST_1"
    assert item.description == "Test Item"
    assert item.status == "PENDING"
    assert item.notes == "Test notes"
    assert item.created_at is not None
    assert item.completed_at is None

def test_create_checklist(db):
    """Tests creating a new checklist."""
    checklist_type = "INSPECTION"
    room_id = "TEST_ROOM_1"
    building_id = "TEST_BUILDING_1"
    tenant_id = "TEST_TENANT_1"
    operator_id = 1
    
    # Define items to create with the checklist
    items = [
        {"description": "Check plumbing", "status": "PENDING"},
        {"description": "Check electricity", "status": "PENDING"},
        {"description": "Check heating", "status": "PENDING"}
    ]
    
    checklist = checklist_service.create_checklist(
        db=db,
        checklist_type=checklist_type,
        room_id=room_id,
        building_id=building_id,
        tenant_id=tenant_id,
        operator_id=operator_id,
        items=items
    )
    
    assert checklist.checklist_id is not None
    assert checklist.checklist_id.startswith("CHKL_")
    assert checklist.checklist_type == checklist_type
    assert checklist.status == "PENDING"
    assert checklist.room_id == room_id
    assert checklist.building_id == building_id
    assert checklist.tenant_id == tenant_id
    assert checklist.operator_id == operator_id
    assert checklist.created_at is not None
    assert checklist.completed_at is None
    
    # Verify items were created
    db_items = checklist_service.get_checklist_items(db, checklist_id=checklist.checklist_id)
    assert len(db_items) == 3
    
    item_descriptions = [item.description for item in db_items]
    assert "Check plumbing" in item_descriptions
    assert "Check electricity" in item_descriptions
    assert "Check heating" in item_descriptions

def test_get_checklist_by_id(db):
    """Tests retrieving a checklist by ID."""
    # Create a checklist
    checklist = checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_OUT",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1"
    )
    
    # Retrieve the checklist
    retrieved_checklist = checklist_service.get_checklist_by_id(db, checklist_id=checklist.checklist_id)
    
    assert retrieved_checklist is not None
    assert retrieved_checklist.checklist_id == checklist.checklist_id
    assert retrieved_checklist.checklist_type == "MOVE_OUT"

def test_get_checklist_by_id_not_found(db):
    """Tests retrieving a non-existent checklist."""
    non_existent_id = f"CHKL_{uuid.uuid4()}"
    checklist = checklist_service.get_checklist_by_id(db, checklist_id=non_existent_id)
    assert checklist is None

def test_get_checklist_items(db):
    """Tests retrieving items for a checklist."""
    # Create a checklist with items
    checklist = checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_IN",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        items=[
            {"description": "Item 1", "status": "PENDING"},
            {"description": "Item 2", "status": "PENDING"},
            {"description": "Item 3", "status": "PENDING"}
        ]
    )
    
    # Retrieve items
    items = checklist_service.get_checklist_items(db, checklist_id=checklist.checklist_id)
    
    assert len(items) == 3
    item_descriptions = [item.description for item in items]
    assert "Item 1" in item_descriptions
    assert "Item 2" in item_descriptions
    assert "Item 3" in item_descriptions

def test_update_checklist_status(db):
    """Tests updating a checklist's status."""
    # Create a checklist
    checklist = checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_IN",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1"
    )
    
    assert checklist.status == "PENDING"
    assert checklist.completed_at is None
    
    # Update the status
    updated_checklist = checklist_service.update_checklist_status(
        db=db,
        checklist_id=checklist.checklist_id,
        status="IN_PROGRESS"
    )
    
    assert updated_checklist.status == "IN_PROGRESS"
    assert updated_checklist.completed_at is None
    
    # Update to completed
    completed_checklist = checklist_service.update_checklist_status(
        db=db,
        checklist_id=checklist.checklist_id,
        status="COMPLETED"
    )
    
    assert completed_checklist.status == "COMPLETED"
    assert completed_checklist.completed_at is not None
    
    # Verify changes were persisted
    retrieved_checklist = checklist_service.get_checklist_by_id(db, checklist_id=checklist.checklist_id)
    assert retrieved_checklist.status == "COMPLETED"
    assert retrieved_checklist.completed_at is not None

def test_update_checklist_item_status(db):
    """Tests updating a checklist item's status."""
    # Create a checklist with an item
    checklist = checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_IN",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        items=[
            {"description": "Item to update", "status": "PENDING"}
        ]
    )
    
    # Get the item
    items = checklist_service.get_checklist_items(db, checklist_id=checklist.checklist_id)
    item = items[0]
    
    assert item.status == "PENDING"
    assert item.completed_at is None
    
    # Update the item status
    updated_item = checklist_service.update_checklist_item_status(
        db=db,
        item_id=item.item_id,
        status="COMPLETED",
        notes="Completed with notes"
    )
    
    assert updated_item.status == "COMPLETED"
    assert updated_item.notes == "Completed with notes"
    assert updated_item.completed_at is not None
    
    # Verify changes were persisted
    retrieved_item = checklist_service.get_checklist_item_by_id(db, item_id=item.item_id)
    assert retrieved_item.status == "COMPLETED"
    assert retrieved_item.notes == "Completed with notes"
    assert retrieved_item.completed_at is not None

def test_update_all_items_completes_checklist(db):
    """Tests that completing all items automatically updates the checklist status."""
    # Create a checklist with multiple items
    checklist = checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_IN",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        items=[
            {"description": "Item 1", "status": "PENDING"},
            {"description": "Item 2", "status": "PENDING"},
            {"description": "Item 3", "status": "PENDING"}
        ]
    )
    
    assert checklist.status == "PENDING"
    
    # Get items
    items = checklist_service.get_checklist_items(db, checklist_id=checklist.checklist_id)
    
    # Complete each item
    for item in items:
        checklist_service.update_checklist_item_status(
            db=db,
            item_id=item.item_id,
            status="COMPLETED"
        )
    
    # Verify checklist was automatically marked as completed
    updated_checklist = checklist_service.get_checklist_by_id(db, checklist_id=checklist.checklist_id)
    assert updated_checklist.status == "COMPLETED"
    assert updated_checklist.completed_at is not None

def test_delete_checklist(db):
    """Tests deleting a checklist and its items."""
    # Create a checklist with items
    checklist = checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_OUT",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1",
        items=[
            {"description": "Item 1", "status": "PENDING"},
            {"description": "Item 2", "status": "PENDING"}
        ]
    )
    
    # Verify items exist
    items = checklist_service.get_checklist_items(db, checklist_id=checklist.checklist_id)
    assert len(items) == 2
    
    # Delete the checklist
    success = checklist_service.delete_checklist(db, checklist_id=checklist.checklist_id)
    
    assert success is True
    
    # Verify checklist was deleted
    retrieved_checklist = checklist_service.get_checklist_by_id(db, checklist_id=checklist.checklist_id)
    assert retrieved_checklist is None
    
    # Verify items were deleted
    items_after = db.query(models.ChecklistItem).filter(
        models.ChecklistItem.checklist_id == checklist.checklist_id
    ).all()
    assert len(items_after) == 0

def test_create_move_in_checklist(db):
    """Tests creating a standardized move-in checklist."""
    room_id = "TEST_ROOM_1"
    building_id = "TEST_BUILDING_1"
    tenant_id = "TEST_TENANT_1"
    operator_id = 1
    
    checklist = checklist_service.create_move_in_checklist(
        db=db,
        room_id=room_id,
        building_id=building_id,
        tenant_id=tenant_id,
        operator_id=operator_id
    )
    
    assert checklist.checklist_id is not None
    assert checklist.checklist_type == "MOVE_IN"
    assert checklist.status == "PENDING"
    assert checklist.room_id == room_id
    assert checklist.building_id == building_id
    assert checklist.tenant_id == tenant_id
    assert checklist.operator_id == operator_id
    
    # Verify standard items were created
    items = checklist_service.get_checklist_items(db, checklist_id=checklist.checklist_id)
    
    # Should have the standard move-in items
    assert len(items) > 0
    
    # Check for some expected standard items
    item_descriptions = [item.description.lower() for item in items]
    assert any("key" in desc for desc in item_descriptions)
    assert any("inspect" in desc for desc in item_descriptions)
    assert any("smoke" in desc for desc in item_descriptions)

def test_create_move_out_checklist(db):
    """Tests creating a standardized move-out checklist."""
    room_id = "TEST_ROOM_1"
    building_id = "TEST_BUILDING_1"
    tenant_id = "TEST_TENANT_1"
    
    checklist = checklist_service.create_move_out_checklist(
        db=db,
        room_id=room_id,
        building_id=building_id,
        tenant_id=tenant_id
    )
    
    assert checklist.checklist_id is not None
    assert checklist.checklist_type == "MOVE_OUT"
    assert checklist.status == "PENDING"
    assert checklist.room_id == room_id
    assert checklist.building_id == building_id
    assert checklist.tenant_id == tenant_id
    
    # Verify standard items were created
    items = checklist_service.get_checklist_items(db, checklist_id=checklist.checklist_id)
    
    # Should have the standard move-out items
    assert len(items) > 0
    
    # Check for some expected standard items
    item_descriptions = [item.description.lower() for item in items]
    assert any("key" in desc for desc in item_descriptions)
    assert any("damage" in desc for desc in item_descriptions)
    assert any("clean" in desc for desc in item_descriptions)

def test_get_room_checklists(db):
    """Tests retrieving checklists for a specific room."""
    room_id = "TEST_ROOM_1"
    
    # Create several checklists for the room
    for checklist_type in ["MOVE_IN", "INSPECTION", "MOVE_OUT"]:
        checklist_service.create_checklist(
            db=db,
            checklist_type=checklist_type,
            room_id=room_id,
            building_id="TEST_BUILDING_1",
            tenant_id="TEST_TENANT_1"
        )
    
    # Create a checklist for another room
    checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_IN",
        room_id="OTHER_ROOM",
        building_id="TEST_BUILDING_1",
        tenant_id="TEST_TENANT_1"
    )
    
    # Retrieve checklists for our test room
    checklists = checklist_service.get_room_checklists(db, room_id=room_id)
    
    assert len(checklists) == 3
    for checklist in checklists:
        assert checklist.room_id == room_id
    
    # Test filtering by type
    move_in_checklists = checklist_service.get_room_checklists(
        db, 
        room_id=room_id, 
        checklist_type="MOVE_IN"
    )
    
    assert len(move_in_checklists) == 1
    assert move_in_checklists[0].checklist_type == "MOVE_IN"

def test_get_tenant_checklists(db):
    """Tests retrieving checklists for a specific tenant."""
    tenant_id = "TEST_TENANT_1"
    
    # Create several checklists for the tenant
    for checklist_type in ["MOVE_IN", "INSPECTION", "MOVE_OUT"]:
        checklist_service.create_checklist(
            db=db,
            checklist_type=checklist_type,
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            tenant_id=tenant_id
        )
    
    # Create a checklist for another tenant
    checklist_service.create_checklist(
        db=db,
        checklist_type="MOVE_IN",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1",
        tenant_id="OTHER_TENANT"
    )
    
    # Retrieve checklists for our test tenant
    checklists = checklist_service.get_tenant_checklists(db, tenant_id=tenant_id)
    
    assert len(checklists) == 3
    for checklist in checklists:
        assert checklist.tenant_id == tenant_id