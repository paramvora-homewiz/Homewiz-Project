import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

from app.db.connection import Base
from app.services import message_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for messages."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        # Create a test building, tenant, lead, and operator
        building = models.Building(
            building_id="TEST_BUILDING_1",
            building_name="Test Building"
        )
        tenant1 = models.Tenant(
            tenant_id="TEST_TENANT_1",
            tenant_name="Test Tenant 1",
            room_id="TEST_ROOM_1",
            building_id="TEST_BUILDING_1",
            tenant_email="test_tenant1@example.com",
            status="ACTIVE"
        )
        tenant2 = models.Tenant(
            tenant_id="TEST_TENANT_2",
            tenant_name="Test Tenant 2",
            room_id="TEST_ROOM_2",
            building_id="TEST_BUILDING_1",
            tenant_email="test_tenant2@example.com",
            status="ACTIVE"
        )
        lead = models.Lead(
            lead_id="TEST_LEAD_1",
            email="test_lead@example.com",
            status="EXPLORING"
        )
        operator = models.Operator(
            name="Test Operator",
            email="test_operator@example.com"
        )
        
        db_session.add(building)
        db_session.add(tenant1)
        db_session.add(tenant2)
        db_session.add(lead)
        db_session.add(operator)
        db_session.commit()
        
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_message(db):
    """Tests creating a new message."""
    content = "This is a test message"
    sender_type = "OPERATOR"
    sender_id = "1"
    recipient_type = "TENANT"
    recipient_id = "TEST_TENANT_1"
    message_type = "TEXT"
    
    message = message_service.create_message(
        db=db,
        content=content,
        sender_type=sender_type,
        sender_id=sender_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        message_type=message_type
    )
    
    assert message.message_id is not None
    assert message.message_id.startswith("MSG_")
    assert message.content == content
    assert message.sender_type == sender_type
    assert message.sender_id == sender_id
    assert message.recipient_type == recipient_type
    assert message.recipient_id == recipient_id
    assert message.message_type == message_type
    assert message.status == "SENT"
    assert message.created_at is not None
    assert message.delivered_at is None
    assert message.read_at is None

def test_get_message_by_id(db):
    """Tests retrieving a message by ID."""
    # Create a message
    message = message_service.create_message(
        db=db,
        content="Message to Retrieve",
        sender_type="OPERATOR",
        sender_id="1",
        recipient_type="TENANT",
        recipient_id="TEST_TENANT_1",
        message_type="TEXT"
    )
    
    # Retrieve the message
    retrieved_message = message_service.get_message_by_id(db, message_id=message.message_id)
    
    assert retrieved_message is not None
    assert retrieved_message.message_id == message.message_id
    assert retrieved_message.content == "Message to Retrieve"

def test_get_message_by_id_not_found(db):
    """Tests retrieving a non-existent message."""
    non_existent_id = f"MSG_{uuid.uuid4()}"
    message = message_service.get_message_by_id(db, message_id=non_existent_id)
    assert message is None

def test_mark_message_as_delivered(db):
    """Tests marking a message as delivered."""
    # Create a message
    message = message_service.create_message(
        db=db,
        content="Message to Mark Delivered",
        sender_type="OPERATOR",
        sender_id="1",
        recipient_type="TENANT",
        recipient_id="TEST_TENANT_1",
        message_type="TEXT"
    )
    
    assert message.status == "SENT"
    assert message.delivered_at is None
    
    # Mark as delivered
    updated_message = message_service.mark_message_as_delivered(db, message_id=message.message_id)
    
    assert updated_message.status == "DELIVERED"
    assert updated_message.delivered_at is not None
    
    # Verify changes were persisted
    retrieved_message = message_service.get_message_by_id(db, message_id=message.message_id)
    assert retrieved_message.status == "DELIVERED"
    assert retrieved_message.delivered_at is not None

def test_mark_message_as_read(db):
    """Tests marking a message as read."""
    # Create a message
    message = message_service.create_message(
        db=db,
        content="Message to Mark Read",
        sender_type="OPERATOR",
        sender_id="1",
        recipient_type="TENANT",
        recipient_id="TEST_TENANT_1",
        message_type="TEXT"
    )
    
    assert message.status == "SENT"
    assert message.read_at is None
    
    # Mark as read
    updated_message = message_service.mark_message_as_read(db, message_id=message.message_id)
    
    assert updated_message.status == "READ"
    assert updated_message.read_at is not None
    
    # Verify changes were persisted
    retrieved_message = message_service.get_message_by_id(db, message_id=message.message_id)
    assert retrieved_message.status == "READ"
    assert retrieved_message.read_at is not None

def test_get_user_messages(db):
    """Tests retrieving messages for a specific user."""
    user_type = "TENANT"
    user_id = "TEST_TENANT_1"
    
    # Create outgoing messages from the user
    for i in range(2):
        message_service.create_message(
            db=db,
            content=f"Outgoing message {i+1}",
            sender_type=user_type,
            sender_id=user_id,
            recipient_type="OPERATOR",
            recipient_id="1",
            message_type="TEXT"
        )
    
    # Create incoming messages to the user
    for i in range(3):
        message_service.create_message(
            db=db,
            content=f"Incoming message {i+1}",
            sender_type="OPERATOR",
            sender_id="1",
            recipient_type=user_type,
            recipient_id=user_id,
            message_type="TEXT"
        )
    
    # Create messages for another user
    message_service.create_message(
        db=db,
        content="Other user message",
        sender_type="OPERATOR",
        sender_id="1",
        recipient_type="TENANT",
        recipient_id="TEST_TENANT_2",
        message_type="TEXT"
    )
    
    # Retrieve all messages for our test user
    messages = message_service.get_user_messages(db, user_type=user_type, user_id=user_id)
    
    assert len(messages) == 5  # 2 outgoing + 3 incoming
    
    # Count incoming and outgoing messages
    outgoing_count = sum(1 for msg in messages if msg.sender_type == user_type and msg.sender_id == user_id)
    incoming_count = sum(1 for msg in messages if msg.recipient_type == user_type and msg.recipient_id == user_id)
    
    assert outgoing_count == 2
    assert incoming_count == 3

def test_get_user_messages_with_conversation_partner(db):
    """Tests retrieving messages between a user and a specific conversation partner."""
    # Setup user and partner
    user_type = "TENANT"
    user_id = "TEST_TENANT_1"
    partner_type = "OPERATOR"
    partner_id = "1"
    
    # Create messages between user and partner
    for i in range(2):
        message_service.create_message(
            db=db,
            content=f"User to partner {i+1}",
            sender_type=user_type,
            sender_id=user_id,
            recipient_type=partner_type,
            recipient_id=partner_id,
            message_type="TEXT"
        )
    
    for i in range(3):
        message_service.create_message(
            db=db,
            content=f"Partner to user {i+1}",
            sender_type=partner_type,
            sender_id=partner_id,
            recipient_type=user_type,
            recipient_id=user_id,
            message_type="TEXT"
        )
    
    # Create messages with another partner
    message_service.create_message(
        db=db,
        content="User to another partner",
        sender_type=user_type,
        sender_id=user_id,
        recipient_type="LEAD",
        recipient_id="TEST_LEAD_1",
        message_type="TEXT"
    )
    
    # Retrieve messages between user and specific partner
    messages = message_service.get_user_messages(
        db=db,
        user_type=user_type,
        user_id=user_id,
        conversation_with_type=partner_type,
        conversation_with_id=partner_id
    )
    
    assert len(messages) == 5  # 2 from user to partner + 3 from partner to user
    
    # Verify all messages are between the user and partner
    for msg in messages:
        assert (msg.sender_type == user_type and msg.sender_id == user_id and 
                msg.recipient_type == partner_type and msg.recipient_id == partner_id) or \
               (msg.sender_type == partner_type and msg.sender_id == partner_id and 
                msg.recipient_type == user_type and msg.recipient_id == user_id)

def test_get_conversation_partners(db):
    """Tests retrieving conversation partners for a user."""
    user_type = "TENANT"
    user_id = "TEST_TENANT_1"
    
    # Create conversations with different partners
    partners = [
        {"type": "OPERATOR", "id": "1"},
        {"type": "LEAD", "id": "TEST_LEAD_1"},
        {"type": "TENANT", "id": "TEST_TENANT_2"}
    ]
    
    for partner in partners:
        # User sends message to partner
        message_service.create_message(
            db=db,
            content=f"Message to {partner['type']} {partner['id']}",
            sender_type=user_type,
            sender_id=user_id,
            recipient_type=partner["type"],
            recipient_id=partner["id"],
            message_type="TEXT"
        )
        
        # Partner sends message to user
        message_service.create_message(
            db=db,
            content=f"Message from {partner['type']} {partner['id']}",
            sender_type=partner["type"],
            sender_id=partner["id"],
            recipient_type=user_type,
            recipient_id=user_id,
            message_type="TEXT"
        )
    
    # Get conversation partners
    conversation_partners = message_service.get_conversation_partners(db, user_type=user_type, user_id=user_id)
    
    assert len(conversation_partners) == 3
    
    # Check that all partners are included
    partner_identifiers = [(p["partner_type"], p["partner_id"]) for p in conversation_partners]
    for partner in partners:
        assert (partner["type"], partner["id"]) in partner_identifiers

def test_count_unread_messages(db):
    """Tests counting unread messages for a recipient."""
    recipient_type = "TENANT"
    recipient_id = "TEST_TENANT_1"
    
    # Create several messages for the recipient
    for i in range(5):
        message_service.create_message(
            db=db,
            content=f"Test message {i+1}",
            sender_type="OPERATOR",
            sender_id="1",
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            message_type="TEXT"
        )
    
    # Get all messages
    messages = message_service.get_user_messages(
        db=db,
        user_type=recipient_type,
        user_id=recipient_id,
        conversation_with_type="OPERATOR",
        conversation_with_id="1"
    )
    
    # Mark some as read
    message_service.mark_message_as_read(db, message_id=messages[0].message_id)
    message_service.mark_message_as_read(db, message_id=messages[1].message_id)
    
    # Count unread
    count = message_service.count_unread_messages(db, recipient_type=recipient_type, recipient_id=recipient_id)
    
    assert count == 3

def test_send_bulk_message(db):
    """Tests sending a message to multiple recipients."""
    content = "Bulk message test"
    sender_type = "OPERATOR"
    sender_id = "1"
    recipient_type = "TENANT"
    recipient_ids = ["TEST_TENANT_1", "TEST_TENANT_2"]
    message_type = "TEXT"
    
    messages = message_service.send_bulk_message(
        db=db,
        content=content,
        message_type=message_type,
        sender_type=sender_type,
        sender_id=sender_id,
        recipient_type=recipient_type,
        recipient_ids=recipient_ids
    )
    
    assert len(messages) == 2
    
    for i, message in enumerate(messages):
        assert message.content == content
        assert message.sender_type == sender_type
        assert message.sender_id == sender_id
        assert message.recipient_type == recipient_type
        assert message.recipient_id == recipient_ids[i]
        assert message.message_type == message_type
        assert message.status == "SENT"

def test_get_message_history(db):
    """Tests retrieving message history between two users."""
    user1_type = "TENANT"
    user1_id = "TEST_TENANT_1"
    user2_type = "OPERATOR"
    user2_id = "1"
    
    # Create message history
    messages_data = [
        # User1 to User2
        {"content": "Hello", "sender_type": user1_type, "sender_id": user1_id, 
         "recipient_type": user2_type, "recipient_id": user2_id},
        # User2 to User1
        {"content": "Hi there", "sender_type": user2_type, "sender_id": user2_id, 
         "recipient_type": user1_type, "recipient_id": user1_id},
        # User1 to User2
        {"content": "How are you?", "sender_type": user1_type, "sender_id": user1_id, 
         "recipient_type": user2_type, "recipient_id": user2_id},
        # User2 to User1
        {"content": "I'm good, thanks", "sender_type": user2_type, "sender_id": user2_id, 
         "recipient_type": user1_type, "recipient_id": user1_id},
    ]
    
    for msg_data in messages_data:
        message_service.create_message(
            db=db,
            content=msg_data["content"],
            sender_type=msg_data["sender_type"],
            sender_id=msg_data["sender_id"],
            recipient_type=msg_data["recipient_type"],
            recipient_id=msg_data["recipient_id"],
            message_type="TEXT"
        )
    
    # Get message history
    history = message_service.get_message_history(
        db=db,
        user1_type=user1_type,
        user1_id=user1_id,
        user2_type=user2_type,
        user2_id=user2_id
    )
    
    assert len(history) == 4
    
    # Verify all messages are between user1 and user2
    for msg in history:
        assert (msg.sender_type == user1_type and msg.sender_id == user1_id and 
                msg.recipient_type == user2_type and msg.recipient_id == user2_id) or \
               (msg.sender_type == user2_type and msg.sender_id == user2_id and 
                msg.recipient_type == user1_type and msg.recipient_id == user1_id)
    
    # Messages should be in reverse chronological order (newest first)
    assert history[0].content == "I'm good, thanks"
    assert history[1].content == "How are you?"
    assert history[2].content == "Hi there"
    assert history[3].content == "Hello"