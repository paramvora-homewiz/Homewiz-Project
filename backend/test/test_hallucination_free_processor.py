# test/test_hallucination_free_processor.py

import pytest
import asyncio
from app.ai_services.hallucination_free_query_processor import HallucinationFreeQueryProcessor
from app.ai_services.hallucination_free_sql_generator import HallucinationFreeSQLGenerator
from app.ai_services.result_verifier import ResultVerifier

@pytest.mark.asyncio
async def test_property_search():
    """Test property search with hallucination prevention."""
    processor = HallucinationFreeQueryProcessor()
    
    result = await processor.process_query(
        "Find available rooms under $2000 in downtown",
        {"user_id": "test_user", "permissions": ["basic"]}
    )
    
    assert result.success == True
    assert len(result.data) >= 0
    assert "rooms" in result.metadata.get("tables_used", [])
    assert len(result.errors) == 0
    assert result.message is not None

@pytest.mark.asyncio
async def test_analytics_query():
    """Test analytics query with hallucination prevention."""
    processor = HallucinationFreeQueryProcessor()
    
    result = await processor.process_query(
        "Show occupancy rates by building",
        {"user_id": "manager", "permissions": ["manager"]}
    )
    
    assert result.success == True
    assert result.metadata.get("result_type") == "analytics"
    assert len(result.errors) == 0

@pytest.mark.asyncio
async def test_tenant_management_query():
    """Test tenant management query."""
    processor = HallucinationFreeQueryProcessor()
    
    result = await processor.process_query(
        "Show all active tenants with their payment status",
        {"user_id": "manager", "permissions": ["manager"]}
    )
    
    assert result.success == True
    assert result.metadata.get("result_type") == "tenant_management"
    assert len(result.errors) == 0

@pytest.mark.asyncio
async def test_lead_management_query():
    """Test lead management query."""
    processor = HallucinationFreeQueryProcessor()
    
    result = await processor.process_query(
        "Show leads in showing scheduled status",
        {"user_id": "agent", "permissions": ["agent"]}
    )
    
    assert result.success == True
    assert result.metadata.get("result_type") == "lead_management"
    assert len(result.errors) == 0

@pytest.mark.asyncio
async def test_hallucination_prevention():
    """Test that hallucination is prevented."""
    processor = HallucinationFreeQueryProcessor()
    
    # This should fail validation due to non-existent table
    result = await processor.process_query(
        "Find rooms in non_existent_table",
        {"user_id": "test_user", "permissions": ["basic"]}
    )
    
    # Should either fail gracefully or return empty results
    assert result.success == False or len(result.data) == 0

@pytest.mark.asyncio
async def test_sql_generator_schema_constraints():
    """Test SQL generator schema constraints."""
    generator = HallucinationFreeSQLGenerator()
    
    # Test with basic user permissions
    result = await generator.generate_sql(
        "Find available rooms",
        {"permissions": ["basic"]}
    )
    
    assert result.get("success") == True
    assert result.get("sql") is not None
    assert "rooms" in result.get("tables_used", [])
    assert "buildings" in result.get("tables_used", [])

@pytest.mark.asyncio
async def test_sql_generator_permission_restrictions():
    """Test SQL generator respects permission restrictions."""
    generator = HallucinationFreeSQLGenerator()
    
    # Test with basic user permissions (should not access tenants table)
    result = await generator.generate_sql(
        "Show all tenants",
        {"permissions": ["basic"]}
    )
    
    # Should either fail or not include tenants table
    if result.get("success"):
        assert "tenants" not in result.get("tables_used", [])

@pytest.mark.asyncio
async def test_result_verifier_data_integrity():
    """Test result verifier data integrity checks."""
    verifier = ResultVerifier()
    
    # Test with valid data
    valid_data = {
        "success": True,
        "data": [
            {
                "room_id": "RM_001",
                "room_number": "101",
                "building_name": "Test Building",
                "private_room_rent": 1500.0,
                "status": "AVAILABLE"
            }
        ]
    }
    
    result = await verifier.verify_and_structure(
        valid_data,
        "Find available rooms",
        "SELECT * FROM rooms WHERE status = 'AVAILABLE'",
        {"permissions": ["basic"]}
    )
    
    assert result.success == True
    assert len(result.data) == 1
    assert result.data[0]["id"] == "RM_001"

@pytest.mark.asyncio
async def test_result_verifier_invalid_data():
    """Test result verifier with invalid data."""
    verifier = ResultVerifier()
    
    # Test with invalid column name
    invalid_data = {
        "success": True,
        "data": [
            {
                "non_existent_column": "value",
                "room_id": "RM_001"
            }
        ]
    }
    
    result = await verifier.verify_and_structure(
        invalid_data,
        "Find available rooms",
        "SELECT * FROM rooms",
        {"permissions": ["basic"]}
    )
    
    # Should detect the invalid column
    assert result.success == False
    assert len(result.errors) > 0

@pytest.mark.asyncio
async def test_query_suggestions():
    """Test query suggestions functionality."""
    processor = HallucinationFreeQueryProcessor()
    
    # Test basic suggestions
    suggestions = await processor.get_query_suggestions(
        "",
        {"permissions": ["basic"]}
    )
    
    assert len(suggestions) > 0
    assert all(isinstance(s, str) for s in suggestions)
    
    # Test filtered suggestions
    filtered_suggestions = await processor.get_query_suggestions(
        "room",
        {"permissions": ["basic"]}
    )
    
    assert len(filtered_suggestions) > 0
    assert all("room" in s.lower() for s in filtered_suggestions)

@pytest.mark.asyncio
async def test_query_validation():
    """Test query validation functionality."""
    processor = HallucinationFreeQueryProcessor()
    
    # Test valid query
    validation = await processor.validate_query(
        "Find available rooms",
        {"permissions": ["basic"]}
    )
    
    assert validation.get("valid") == True
    assert validation.get("sql_preview") is not None
    
    # Test invalid query
    invalid_validation = await processor.validate_query(
        "Find rooms in non_existent_table",
        {"permissions": ["basic"]}
    )
    
    assert invalid_validation.get("valid") == False
    assert len(invalid_validation.get("errors", [])) > 0

@pytest.mark.asyncio
async def test_batch_queries():
    """Test batch query processing."""
    processor = HallucinationFreeQueryProcessor()
    
    queries = [
        "Find available rooms",
        "Show building information",
        "Count total rooms"
    ]
    
    results = await processor.process_batch_queries(
        queries,
        {"permissions": ["basic"]}
    )
    
    assert len(results) == 3
    assert all(hasattr(result, 'success') for result in results)

@pytest.mark.asyncio
async def test_query_statistics():
    """Test query statistics functionality."""
    processor = HallucinationFreeQueryProcessor()
    
    stats = await processor.get_query_statistics(
        {"permissions": ["basic"]}
    )
    
    assert stats.get("success") == True
    assert "statistics" in stats
    assert isinstance(stats["statistics"], dict)

@pytest.mark.asyncio
async def test_frontend_response_structure():
    """Test that responses are properly structured for frontend."""
    processor = HallucinationFreeQueryProcessor()
    
    result = await processor.process_query(
        "Find available rooms",
        {"permissions": ["basic"]}
    )
    
    # Check response structure
    assert hasattr(result, 'success')
    assert hasattr(result, 'data')
    assert hasattr(result, 'message')
    assert hasattr(result, 'metadata')
    assert hasattr(result, 'errors')
    assert hasattr(result, 'warnings')
    
    # Check data types
    assert isinstance(result.success, bool)
    assert isinstance(result.data, list)
    assert isinstance(result.message, str)
    assert isinstance(result.metadata, dict)
    assert isinstance(result.errors, list)
    assert isinstance(result.warnings, list)

@pytest.mark.asyncio
async def test_permission_based_access():
    """Test that different permission levels have different access."""
    processor = HallucinationFreeQueryProcessor()
    
    # Basic user query
    basic_result = await processor.process_query(
        "Show all tenants",
        {"permissions": ["basic"]}
    )
    
    # Manager user query
    manager_result = await processor.process_query(
        "Show all tenants",
        {"permissions": ["manager"]}
    )
    
    # Results should be different based on permissions
    # (Either different data or different error messages)
    assert basic_result.success != manager_result.success or len(basic_result.data) != len(manager_result.data)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
