import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from app.db.connection import Base
from app.services import building_service
from app.db import models
from app.models import building as building_models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for buildings."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_building(db):
    """Tests creating a new building."""
    building_id = f"BLD_TEST_{uuid.uuid4()}"
    building_data = {
        "building_id": building_id,
        "building_name": "Test Building",
        "area": "Downtown",
        "priority": 1
    }
    building_create = building_models.BuildingCreate(**building_data)
    created_building = building_service.create_building(db, building_create)
    assert created_building.building_id == building_id
    assert created_building.building_name == building_data["building_name"]
    assert created_building.area == building_data["area"]
    assert created_building.priority == building_data["priority"]

def test_get_building_by_id(db):
    """Tests retrieving a building by ID."""
    building_id = f"BLD_TEST_{uuid.uuid4()}"
    building_data = {
        "building_id": building_id,
        "building_name": "Building to Get",
        "area": "SoMA",
        "priority": 2
    }
    building_create = building_models.BuildingCreate(**building_data)
    created_building = building_service.create_building(db, building_create)
    retrieved_building = building_service.get_building_by_id(db, building_id=building_id)
    assert retrieved_building.building_id == building_id
    assert retrieved_building.building_name == building_data["building_name"]

def test_get_building_by_id_not_found(db):
    """Tests retrieving a non-existent building."""
    non_existent_building_id = "NON_EXISTENT_BUILDING_ID"
    retrieved_building = building_service.get_building_by_id(db, building_id=non_existent_building_id)
    assert retrieved_building is None

def test_update_building(db):
    """Tests updating building details."""
    building_id = f"BLD_TEST_{uuid.uuid4()}"
    building_data = {
        "building_id": building_id,
        "building_name": "Building to Update",
        "area": "Mission",
        "priority": 3
    }
    building_create = building_models.BuildingCreate(**building_data)
    created_building = building_service.create_building(db, building_create)

    building_update_data = {
        "building_id": building_id,
        "building_name": "Updated Building Name",
        "priority": 1
    }
    building_update_model = building_models.BuildingUpdate(**building_update_data)
    updated_building = building_service.update_building(db, building_id=building_id, building_update=building_update_model)
    assert updated_building.building_id == building_id
    assert updated_building.building_name == building_update_data["building_name"]
    assert updated_building.priority == building_update_data["priority"]

def test_delete_building(db):
    """Tests deleting a building."""
    building_id = f"BLD_TEST_{uuid.uuid4()}"
    building_data = {
        "building_id": building_id,
        "building_name": "Building to Delete",
        "area": "Hayes Valley",
        "priority": 4
    }
    building_create = building_models.BuildingCreate(**building_data)
    created_building = building_service.create_building(db, building_create)
    deletion_successful = building_service.delete_building(db, building_id=building_id)
    assert deletion_successful
    retrieved_building = building_service.get_building_by_id(db, building_id=building_id)
    assert retrieved_building is None

def test_get_all_buildings(db):
    """Tests retrieving all buildings."""
    # Create a few buildings
    building_data1 = {
        "building_id": f"BLD_TEST_{uuid.uuid4()}",
        "building_name": "Building One",
        "area": "Marina",
        "priority": 1
    }
    building_create1 = building_models.BuildingCreate(**building_data1)
    building_service.create_building(db, building_create1)

    building_data2 = {
        "building_id": f"BLD_TEST_{uuid.uuid4()}",
        "building_name": "Building Two",
        "area": "Downtown",
        "priority": 2
    }
    building_create2 = building_models.BuildingCreate(**building_data2)
    building_service.create_building(db, building_create2)

    buildings_list = building_service.get_all_buildings(db)
    assert isinstance(buildings_list, list)
    assert len(buildings_list) >= 2
    building_ids_in_response = {building.building_id for building in buildings_list}
    assert building_data1["building_id"] in building_ids_in_response
    assert building_data2["building_id"] in building_ids_in_response