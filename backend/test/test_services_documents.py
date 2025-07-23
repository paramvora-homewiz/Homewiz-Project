import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime, date

from app.db.connection import Base
from app.services import document_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for documents."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create a test building, room, tenant, and lead
        building = models.Building(
            building_id="TEST_BUILDING_1",
            building_name="Test Building",
            full_address="123 Test St, Testville, CA 90210"
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
            tenant_email="test_tenant@example.com",
            lease_start_date=date(2023, 1, 1),
            lease_end_date=date(2023, 12, 31)
        )
        lead = models.Lead(
            lead_id="TEST_LEAD_1",
            email="test_lead@example.com",
            status="EXPLORING",
            planned_move_in=date(2023, 6, 1)
        )
        
        db_session.add(building)
        db_session.add(room)
        db_session.add(tenant)
        db_session.add(lead)
        db_session.commit()
        
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_document(db):
    """Tests creating a new document."""
    title = "Test Document"
    document_type = "TEST"
    content = "This is a test document content"
    
    document = document_service.create_document(
        db=db,
        title=title,
        document_type=document_type,
        content=content,
        tenant_id="TEST_TENANT_1",
        room_id="TEST_ROOM_1",
        building_id="TEST_BUILDING_1"
    )
    
    assert document.document_id is not None
    assert document.document_id.startswith("DOC_")
    assert document.title == title
    assert document.document_type == document_type
    assert document.content == content
    assert document.status == "DRAFT"
    assert document.tenant_id == "TEST_TENANT_1"
    assert document.room_id == "TEST_ROOM_1"
    assert document.building_id == "TEST_BUILDING_1"
    assert document.created_at is not None
    assert document.updated_at is not None
    assert document.signed_at is None

def test_get_document_by_id(db):
    """Tests retrieving a document by ID."""
    # Create a document
    document = document_service.create_document(
        db=db,
        title="Document to Retrieve",
        document_type="TEST",
        content="This document will be retrieved",
        tenant_id="TEST_TENANT_1"
    )
    
    # Retrieve the document
    retrieved_document = document_service.get_document_by_id(db, document_id=document.document_id)
    
    assert retrieved_document is not None
    assert retrieved_document.document_id == document.document_id
    assert retrieved_document.title == "Document to Retrieve"

def test_get_document_by_id_not_found(db):
    """Tests retrieving a non-existent document."""
    non_existent_id = f"DOC_{uuid.uuid4()}"
    document = document_service.get_document_by_id(db, document_id=non_existent_id)
    assert document is None

def test_update_document_status(db):
    """Tests updating a document's status."""
    # Create a document
    document = document_service.create_document(
        db=db,
        title="Document to Update Status",
        document_type="TEST",
        content="This document's status will be updated",
        tenant_id="TEST_TENANT_1"
    )
    
    assert document.status == "DRAFT"
    
    # Update the status
    updated_document = document_service.update_document_status(
        db=db,
        document_id=document.document_id,
        status="PENDING_SIGNATURE"
    )
    
    assert updated_document.status == "PENDING_SIGNATURE"
    assert updated_document.signed_at is None
    
    # Verify changes were persisted
    retrieved_document = document_service.get_document_by_id(db, document_id=document.document_id)
    assert retrieved_document.status == "PENDING_SIGNATURE"

def test_update_document_status_to_signed(db):
    """Tests updating a document's status to signed."""
    # Create a document
    document = document_service.create_document(
        db=db,
        title="Document to Sign",
        document_type="TEST",
        content="This document will be signed",
        tenant_id="TEST_TENANT_1"
    )
    
    # Update the status to signed
    updated_document = document_service.update_document_status(
        db=db,
        document_id=document.document_id,
        status="SIGNED"
    )
    
    assert updated_document.status == "SIGNED"
    assert updated_document.signed_at is not None
    
    # Verify changes were persisted
    retrieved_document = document_service.get_document_by_id(db, document_id=document.document_id)
    assert retrieved_document.status == "SIGNED"
    assert retrieved_document.signed_at is not None

def test_update_document_status_not_found(db):
    """Tests updating status of a non-existent document."""
    non_existent_id = f"DOC_{uuid.uuid4()}"
    result = document_service.update_document_status(
        db=db,
        document_id=non_existent_id,
        status="PENDING_SIGNATURE"
    )
    assert result is None

def test_update_document_content(db):
    """Tests updating a document's content."""
    # Create a document
    document = document_service.create_document(
        db=db,
        title="Document to Update Content",
        document_type="TEST",
        content="This document's content will be updated",
        tenant_id="TEST_TENANT_1"
    )
    
    # Update the content
    new_title = "Updated Document Title"
    new_content = "This is the updated document content"
    
    updated_document = document_service.update_document_content(
        db=db,
        document_id=document.document_id,
        title=new_title,
        content=new_content
    )
    
    assert updated_document.title == new_title
    assert updated_document.content == new_content
    assert updated_document.updated_at > document.updated_at
    
    # Verify changes were persisted
    retrieved_document = document_service.get_document_by_id(db, document_id=document.document_id)
    assert retrieved_document.title == new_title
    assert retrieved_document.content == new_content

def test_update_document_content_not_found(db):
    """Tests updating content of a non-existent document."""
    non_existent_id = f"DOC_{uuid.uuid4()}"
    result = document_service.update_document_content(
        db=db,
        document_id=non_existent_id,
        title="New Title",
        content="New Content"
    )
    assert result is None

def test_delete_document(db):
    """Tests deleting a document."""
    # Create a document
    document = document_service.create_document(
        db=db,
        title="Document to Delete",
        document_type="TEST",
        content="This document will be deleted",
        tenant_id="TEST_TENANT_1"
    )
    
    # Delete the document
    success = document_service.delete_document(db, document_id=document.document_id)
    
    assert success is True
    
    # Verify the document was deleted
    retrieved_document = document_service.get_document_by_id(db, document_id=document.document_id)
    assert retrieved_document is None

def test_get_tenant_documents(db):
    """Tests retrieving documents for a specific tenant."""
    tenant_id = "TEST_TENANT_1"
    
    # Create several documents for the tenant
    for i in range(3):
        document_service.create_document(
            db=db,
            title=f"Tenant Document {i+1}",
            document_type="TEST",
            content=f"This is tenant document {i+1}",
            tenant_id=tenant_id
        )
    
    # Create a document for another tenant
    document_service.create_document(
        db=db,
        title="Other Tenant Document",
        document_type="TEST",
        content="This is for another tenant",
        tenant_id="OTHER_TENANT"
    )
    
    # Retrieve documents for our test tenant
    documents = document_service.get_tenant_documents(db, tenant_id=tenant_id)
    
    assert len(documents) == 3
    for document in documents:
        assert document.tenant_id == tenant_id

def test_get_lead_documents(db):
    """Tests retrieving documents for a specific lead."""
    lead_id = "TEST_LEAD_1"
    
    # Create several documents for the lead
    for i in range(3):
        document_service.create_document(
            db=db,
            title=f"Lead Document {i+1}",
            document_type="APPLICATION",
            content=f"This is lead document {i+1}",
            lead_id=lead_id
        )
    
    # Create a document for another lead
    document_service.create_document(
        db=db,
        title="Other Lead Document",
        document_type="APPLICATION",
        content="This is for another lead",
        lead_id="OTHER_LEAD"
    )
    
    # Retrieve documents for our test lead
    documents = document_service.get_lead_documents(db, lead_id=lead_id)
    
    assert len(documents) == 3
    for document in documents:
        assert document.lead_id == lead_id

def test_generate_lease_document(db):
    """Tests generating a lease document."""
    tenant_id = "TEST_TENANT_1"
    room_id = "TEST_ROOM_1"
    building_id = "TEST_BUILDING_1"
    lease_start_date = datetime(2023, 6, 1)
    lease_end_date = datetime(2024, 5, 31)
    monthly_rent = 1500.0
    deposit_amount = 2000.0
    
    document = document_service.generate_lease_document(
        db=db,
        tenant_id=tenant_id,
        room_id=room_id,
        building_id=building_id,
        lease_start_date=lease_start_date,
        lease_end_date=lease_end_date,
        monthly_rent=monthly_rent,
        deposit_amount=deposit_amount
    )
    
    assert document.document_id is not None
    assert document.document_type == "LEASE"
    assert document.status == "PENDING_SIGNATURE"
    assert document.tenant_id == tenant_id
    assert document.room_id == room_id
    assert document.building_id == building_id
    assert "LEASE AGREEMENT" in document.content
    assert f"${monthly_rent:.2f}" in document.content
    assert f"${deposit_amount:.2f}" in document.content
    assert lease_start_date.strftime("%Y-%m-%d") in document.content
    assert lease_end_date.strftime("%Y-%m-%d") in document.content

def test_generate_application_document(db):
    """Tests generating an application document."""
    lead_id = "TEST_LEAD_1"
    room_id = "TEST_ROOM_1"
    building_id = "TEST_BUILDING_1"
    
    document = document_service.generate_application_document(
        db=db,
        lead_id=lead_id,
        room_id=room_id,
        building_id=building_id
    )
    
    assert document.document_id is not None
    assert document.document_type == "APPLICATION"
    assert document.status == "DRAFT"
    assert document.lead_id == lead_id
    assert document.room_id == room_id
    assert document.building_id == building_id
    assert "RENTAL APPLICATION" in document.content
    assert "test_lead@example.com" in document.content