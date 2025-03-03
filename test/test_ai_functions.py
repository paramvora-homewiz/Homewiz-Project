import pytest
from unittest import mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.connection import Base
from app.db import models
from app.ai_functions import find_buildings_rooms_function # Import the function to test
from fastapi import Depends

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

# --- Mock Gemini API Response ---
def mock_gemini_generate_content(model, contents): # model argument is not used
    """Mocks Gemini API response based on prompt content."""
    if "error" in contents.lower(): # Simulate error case
        raise Exception("Simulated Gemini API error")
    if "mars_query" in contents.lower(): # Simulate no rooms found case - TRIGGERED BY "mars_query" KEYWORD NOW
        return mock.Mock(text="Gemini: No matching rooms found based on your criteria.")
    # Default successful mock response
    return mock.Mock(text="Gemini: Successfully searched for rooms based on your query.")


def test_find_rooms_basic_query(db, monkeypatch):
    """Tests find_buildings_rooms_function with a basic query."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content) # Apply the mock
    query_text = "find me a room with a city view"
    result = find_buildings_rooms_function(query=query_text, db=db) # Call the function with test db

    assert "error" not in result # No error should be returned
    assert "response" in result # Response field should be present
    assert "data" in result # Data field should be present
    assert "Gemini: Successfully searched" in result["response"] # Check mocked Gemini response text (basic keyword check)
    assert isinstance(result["data"], list) # Data should be a list (even if empty)
    # Further assertions can be added to check 'data' content if you seed specific test data in the db fixture

def test_find_rooms_no_matching_rooms(db, monkeypatch):
    """Tests find_buildings_rooms_function when no rooms should match."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    query_text = "find me a room on Mars mars_query" # Include "mars_query" to trigger no-match mock
    result = find_buildings_rooms_function(query=query_text, db=db)

    assert "error" not in result
    assert "response" in result
    assert "data" in result
    assert "Gemini: No matching rooms found" in result["response"] # Check mocked Gemini no-match response
    assert isinstance(result["data"], list) # Data should be a list
    assert not result["data"] # Data list should be empty when no matches

def test_find_rooms_gemini_api_error(db, monkeypatch):
    """Tests find_buildings_rooms_function handles Gemini API error."""
    monkeypatch.setattr("app.ai_functions.client.models.generate_content", mock_gemini_generate_content)
    query_text = "trigger gemini error" # Query to trigger simulated Gemini error (see mock_gemini_generate_content)
    result = find_buildings_rooms_function(query=query_text, db=db)

    assert "error" in result # Error field should be present in response
    assert "Gemini API call" in result["error"] # Check error message content
    assert "response" in result # Response field should still be present (for error message)
    assert "Error searching" in result["response"] # Check error response text