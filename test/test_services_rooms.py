import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.connection import Base
from app.services import room_service
from app.db import models
from app.models import room as room_models # Pydantic models
import uuid

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """
    Function-scoped test database fixture. Creates a new in-memory database and session for each test function,
    and drops all tables after the test completes.
    """
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)  # Create tables
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine) # Drop tables


def test_create_room(db):
    """
    Tests creating a new room.
    """
    room_id = f"ROOM_TEST_{uuid.uuid4()}"
    room_data = {
        "room_id": room_id,
        "room_number": "101",
        "building_id": "BLD_TEST",
        "private_room_rent": 1500.00,
        "bathroom_type": "Private",
        "bed_size": "Queen",
        "view": "City"
    }
    room_create = room_models.RoomCreate(**room_data)
    created_room = room_service.create_room(db, room_create)
    assert created_room.room_id == room_id
    assert created_room.room_number == room_data["room_number"]
    assert created_room.private_room_rent == room_data["private_room_rent"]

def test_get_room_by_id(db):
    """
    Tests retrieving a room by its ID.
    """
    room_id = f"ROOM_TEST_{uuid.uuid4()}"
    room_data = {
        "room_id": room_id,
        "room_number": "102",
        "building_id": "BLD_TEST",
        "private_room_rent": 1600.00,
        "bathroom_type": "En-Suite",
        "bed_size": "King",
        "view": "Bay"
    }
    room_create = room_models.RoomCreate(**room_data)
    created_room = room_service.create_room(db, room_create)
    retrieved_room = room_service.get_room_by_id(db, room_id=room_id)
    assert retrieved_room.room_id == room_id
    assert retrieved_room.room_number == room_data["room_number"]

def test_get_room_by_id_not_found(db):
    """
    Tests retrieving a room by an ID that does not exist.
    """
    non_existent_room_id = "NON_EXISTENT_ROOM_ID"
    retrieved_room = room_service.get_room_by_id(db, room_id=non_existent_room_id)
    assert retrieved_room is None

def test_update_room(db):
    """
    Tests updating a room's details.
    """
    room_id = f"ROOM_TEST_{uuid.uuid4()}"
    room_data = {
        "room_id": room_id,
        "room_number": "103",
        "building_id": "BLD_TEST",
        "private_room_rent": 1700.00,
        "bathroom_type": "Shared",
        "bed_size": "Full",
        "view": "Garden"
    }
    room_create = room_models.RoomCreate(**room_data)
    created_room = room_service.create_room(db, room_create)

    room_update_data = {
        "private_room_rent": 1850.00,
        "status": "OCCUPIED"
    }
    room_update_model = room_models.RoomUpdate(**room_update_data)
    updated_room = room_service.update_room(db, room_id=room_id, room_update=room_update_model)
    assert updated_room.room_id == room_id
    assert updated_room.private_room_rent == room_update_data["private_room_rent"]
    assert updated_room.status == room_update_data["status"]

def test_delete_room(db):
    """
    Tests deleting a room.
    """
    room_id = f"ROOM_TEST_{uuid.uuid4()}"
    room_data = {
        "room_id": room_id,
        "room_number": "104",
        "building_id": "BLD_TEST",
        "private_room_rent": 1900.00,
        "bathroom_type": "Private",
        "bed_size": "Queen",
        "view": "Street"
    }
    room_create = room_models.RoomCreate(**room_data)
    created_room = room_service.create_room(db, room_create)
    deletion_successful = room_service.delete_room(db, room_id=room_id)
    assert deletion_successful
    retrieved_room = room_service.get_room_by_id(db, room_id=room_id)
    assert retrieved_room is None # Verify room is actually deleted

def test_get_all_rooms(db):
    """
    Tests retrieving all rooms.
    """
    # Create a few rooms
    room_data1 = {
        "room_id": f"ROOM_TEST_{uuid.uuid4()}",
        "room_number": "201",
        "building_id": "BLD_TEST",
        "private_room_rent": 2000.00,
        "bathroom_type": "En-Suite",
        "bed_size": "King",
        "view": "Bay"
    }
    room_create1 = room_models.RoomCreate(**room_data1)
    room_service.create_room(db, room_create1)

    room_data2 = {
        "room_id": f"ROOM_TEST_{uuid.uuid4()}",
        "room_number": "202",
        "building_id": "BLD_TEST",
        "private_room_rent": 2100.00,
        "bathroom_type": "Shared",
        "bed_size": "Full",
        "view": "Garden"
    }
    room_create2 = room_models.RoomCreate(**room_data2)
    room_service.create_room(db, room_create2)

    rooms_list = room_service.get_all_rooms(db)
    assert isinstance(rooms_list, list)
    assert len(rooms_list) >= 2 # At least 2 rooms should be returned
    room_ids_in_response = {room.room_id for room in rooms_list}
    assert room_data1["room_id"] in room_ids_in_response
    assert room_data2["room_id"] in room_ids_in_response