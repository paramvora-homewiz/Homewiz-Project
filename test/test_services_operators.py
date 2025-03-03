import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import date

from app.db.connection import Base
from app.services import operator_service
from app.db import models
from app.models import operator as operator_models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for operators."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_operator(db):
    """Tests creating a new operator."""
    operator_data = {
        "name": "Test Operator",
        "email": f"test_operator_{uuid.uuid4()}@example.com",
        "role": "Leasing Agent"
    }
    operator_create = operator_models.OperatorCreate(**operator_data)
    created_operator = operator_service.create_operator(db, operator_create)
    assert created_operator.operator_id is not None
    assert created_operator.name == operator_data["name"]
    assert created_operator.email == operator_data["email"]
    assert created_operator.role == operator_data["role"]

def test_get_operator_by_id(db):
    """Tests retrieving an operator by ID."""
    operator_data = {
        "name": "Operator to Get",
        "email": f"get_operator_{uuid.uuid4()}@example.com",
        "role": "Property Manager"
    }
    operator_create = operator_models.OperatorCreate(**operator_data)
    created_operator = operator_service.create_operator(db, operator_create)
    retrieved_operator = operator_service.get_operator_by_id(db, operator_id=created_operator.operator_id)
    assert retrieved_operator.operator_id == created_operator.operator_id
    assert retrieved_operator.name == operator_data["name"]

def test_get_operator_by_id_not_found(db):
    """Tests retrieving a non-existent operator."""
    non_existent_operator_id = 9999
    retrieved_operator = operator_service.get_operator_by_id(db, operator_id=non_existent_operator_id)
    assert retrieved_operator is None

def test_update_operator(db):
    """Tests updating operator details."""
    operator_data = {
        "name": "Operator to Update",
        "email": f"update_operator_{uuid.uuid4()}@example.com",
        "role": "Maintenance"
    }
    operator_create = operator_models.OperatorCreate(**operator_data)
    created_operator = operator_service.create_operator(db, operator_create)

    operator_update_data = {
        "role": "Assistant Manager",
        "active": False
    }
    operator_update_model = operator_models.OperatorUpdate(**operator_update_data)
    updated_operator = operator_service.update_operator(db, operator_id=created_operator.operator_id, operator_update=operator_update_model)
    assert updated_operator.operator_id == created_operator.operator_id
    assert updated_operator.role == operator_update_data["role"]
    assert updated_operator.active == operator_update_data["active"]

def test_delete_operator(db):
    """Tests deleting an operator."""
    operator_data = {
        "name": "Operator to Delete",
        "email": f"delete_operator_{uuid.uuid4()}@example.com",
        "role": "Leasing Agent"
    }
    operator_create = operator_models.OperatorCreate(**operator_data)
    created_operator = operator_service.create_operator(db, operator_create)
    deletion_successful = operator_service.delete_operator(db, operator_id=created_operator.operator_id)
    assert deletion_successful
    retrieved_operator = operator_service.get_operator_by_id(db, operator_id=created_operator.operator_id)
    assert retrieved_operator is None

def test_get_all_operators(db):
    """Tests retrieving all operators."""
    # Create a few operators
    operator_data1 = {
        "name": "Operator One",
        "email": f"operator1_{uuid.uuid4()}@example.com",
        "role": "Leasing Agent"
    }
    operator_create1 = operator_models.OperatorCreate(**operator_data1)
    operator_service.create_operator(db, operator_create1)

    operator_data2 = {
        "name": "Operator Two",
        "email": f"operator2_{uuid.uuid4()}@example.com",
        "role": "Maintenance"
    }
    operator_create2 = operator_models.OperatorCreate(**operator_data2)
    operator_service.create_operator(db, operator_create2)

    operators_list = operator_service.get_all_operators(db)
    assert isinstance(operators_list, list)
    assert len(operators_list) >= 2
    operator_ids_in_response = {operator.operator_id for operator in operators_list}
    assert operator_create1.dict()['email'] in [operator.email for operator in operators_list] #cannot access operator_create1.email directly
    assert operator_create2.dict()['email'] in [operator.email for operator in operators_list] #cannot access operator_create2.email directly