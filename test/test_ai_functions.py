import pytest
from unittest import mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.connection import Base
from app.db import models
from app.ai_functions import find_buildings_rooms_function  # Import the function to test
from fastapi import Depends
import json  # Import json module
import uuid # Import uuid for generating test room_ids


TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture, seeded with test rooms."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # --- Seed test data ---
        building_test = models.Building(building_id="BLD_TEST_1", building_name="Test Building 1") # Create a test building
        db_session.add(building_test)

        room_data = [ # Test rooms with different views and bathroom types
            {"room_id": "ROOM_TEST_1", "room_number": "101", "building_id": "BLD_TEST_1", "view": "City", "bathroom_type": "Private", "private_room_rent": 2000.00},
            {"room_id": "ROOM_TEST_2", "room_number": "102", "building_id": "BLD_TEST_1", "view": "Bay", "bathroom_type": "En-Suite", "private_room_rent": 2500.00},
            {"room_id": "ROOM_TEST_3", "room_number": "201", "building_id": "BLD_TEST_1", "view": "Garden", "bathroom_type": "Shared", "private_room_rent": 1500.00},
            {"room_id": "ROOM_TEST_4", "room_number": "202", "building_id": "BLD_TEST_1", "view": "Street", "bathroom_type": "Private", "private_room_rent": 1800.00},
        ]
        for room_item in room_data:
            room = models.Room(**room_item)
            db_session.add(room)
        db_session.commit()
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)


# --- Mock Gemini API Response ---
def mock_gemini_generate_content(model, contents, config=None):
    """Mocks Gemini API response based on prompt content, now returns structured data in 'data'."""
    if "error" in contents.lower():
        raise Exception("Simulated Gemini API error")
    if "mars_query" in contents.lower():
        response_mock = mock.Mock(text="Gemini: No matching rooms found based on your criteria.", function_calls=[]) # Simulate no rooms - empty function_calls
        # Mock 'data' to be an empty list for no matches scenario
        response_mock.data = [] # Mock empty data list
        return response_mock # Return modified response_mock with empty data

    # --- Simulate Gemini returning structured function call with arguments ---
    function_call_mock = mock.Mock()
    function_call_mock.name = "find_buildings_rooms_function" # Function name Gemini is expected to call
    function_call_mock.args = {"query": contents} # Pass the prompt as the 'query' argument

    response_mock = mock.Mock()
    response_mock.function_calls = [function_call_mock] # Return function call in function_calls list

    return response_mock # Return response mock with function_calls


def test_find_rooms_city_view_filter(db, monkeypatch):
    """Tests find_buildings_rooms_function with 'city view' filter."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    query_text = "find me a room with a city view"
    result = find_buildings_rooms_function(query=query_text, db=db)

    assert "error" not in result
    assert "response" in result
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) >= 1 # Expect at least one room with city view from test data
    for room in result["data"]:
        assert room["view"] == "City" # Verify all returned rooms have city view

def test_find_rooms_private_bathroom_filter(db, monkeypatch):
    """Tests find_buildings_rooms_function with 'private bathroom' filter."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    query_text = "I want a room with a private bathroom"
    result = find_buildings_rooms_function(query=query_text, db=db)

    assert "error" not in result
    assert "response" in result
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) == 2 # Expect 2 rooms with private bathroom in test data
    for room in result["data"]:
        assert room["bathroom_type"] == "Private"

def test_find_rooms_city_view_and_private_bathroom_filter(db, monkeypatch):
    """Tests combined filters: 'city view' and 'private bathroom'."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    query_text = "city view and private bathroom"
    result = find_buildings_rooms_function(query=query_text, db=db)

    assert "error" not in result
    assert "response" in result
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) >= 1 # Expect at least one room matching both criteria
    for room in result["data"]:
        assert room["view"] == "City"
        assert room["bathroom_type"] == "Private"

def test_find_rooms_no_matches(db, monkeypatch):
    """Tests scenario with no matching rooms (using 'mars_query' trigger)."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    query_text = "find me a room on Mars mars_query" # "mars_query" triggers no-match mock
    result = find_buildings_rooms_function(query=query_text, db=db)

    assert "error" not in result
    assert "response" in result
    assert "data" in result
    assert isinstance(result["data"], list)
    assert not result["data"] # Data list should be empty

def test_find_rooms_gemini_api_error(db, monkeypatch):
    """Tests handling of simulated Gemini API error."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    query_text = "trigger gemini error" # Triggers error mock
    result = find_buildings_rooms_function(query=query_text, db=db)

    assert "error" in result
    assert "Gemini API call" in result["error"]
    assert "response" in result
    assert "Error in room search - Function Calling V3 - No Dispatch Call in AI Functions" in result["response"] 