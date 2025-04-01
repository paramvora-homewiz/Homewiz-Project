import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

from app.db.connection import Base
from app.services import notification_service
from app.db import models

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """Function-scoped test database fixture for notifications."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(engine)

def test_create_notification(db):
    """Tests creating a new notification."""
    notification = notification_service.create_notification(
        db=db,
        user_type="TENANT",
        user_id="TEST_TENANT_1",
        title="Test Notification",
        content="This is a test notification",
        notification_type="TEST",
        priority="NORMAL"
    )
    
    assert notification.notification_id is not None
    assert notification.notification_id.startswith("NOTIF_")
    assert notification.user_type == "TENANT"
    assert notification.user_id == "TEST_TENANT_1"
    assert notification.title == "Test Notification"
    assert notification.content == "This is a test notification"
    assert notification.type == "TEST"
    assert notification.priority == "NORMAL"
    assert notification.status == "UNREAD"
    assert notification.created_at is not None
    assert notification.read_at is None

def test_get_notification_by_id(db):
    """Tests retrieving a notification by ID."""
    notification = notification_service.create_notification(
        db=db,
        user_type="OPERATOR",
        user_id="1",
        title="Test Get Notification",
        content="This is a retrievable notification",
        notification_type="TEST",
        priority="HIGH"
    )
    
    retrieved_notification = notification_service.get_notification_by_id(db, notification_id=notification.notification_id)
    assert retrieved_notification is not None
    assert retrieved_notification.notification_id == notification.notification_id
    assert retrieved_notification.title == "Test Get Notification"
    assert retrieved_notification.priority == "HIGH"

def test_get_notification_by_id_not_found(db):
    """Tests retrieving a non-existent notification."""
    non_existent_id = f"NOTIF_{uuid.uuid4()}"
    notification = notification_service.get_notification_by_id(db, notification_id=non_existent_id)
    assert notification is None

def test_get_user_notifications(db):
    """Tests retrieving notifications for a specific user."""
    user_type = "LEAD"
    user_id = "TEST_LEAD_1"
    
    # Create several notifications for the user
    for i in range(3):
        notification_service.create_notification(
            db=db,
            user_type=user_type,
            user_id=user_id,
            title=f"Test Notification {i+1}",
            content=f"This is test notification {i+1}",
            notification_type="TEST",
            priority="NORMAL"
        )
    
    # Create a notification for another user
    notification_service.create_notification(
        db=db,
        user_type="TENANT",
        user_id="OTHER_USER",
        title="Other User Notification",
        content="This is for another user",
        notification_type="TEST",
        priority="NORMAL"
    )
    
    # Retrieve notifications for our test user
    notifications = notification_service.get_user_notifications(db, user_type=user_type, user_id=user_id)
    
    assert len(notifications) == 3
    for notification in notifications:
        assert notification.user_type == user_type
        assert notification.user_id == user_id

def test_mark_notification_as_read(db):
    """Tests marking a notification as read."""
    notification = notification_service.create_notification(
        db=db,
        user_type="TENANT",
        user_id="TEST_TENANT_2",
        title="Notification to Mark Read",
        content="This notification will be marked as read",
        notification_type="TEST",
        priority="NORMAL"
    )
    
    assert notification.status == "UNREAD"
    assert notification.read_at is None
    
    updated_notification = notification_service.mark_notification_as_read(db, notification_id=notification.notification_id)
    
    assert updated_notification.status == "READ"
    assert updated_notification.read_at is not None
    
    # Verify changes were persisted
    retrieved_notification = notification_service.get_notification_by_id(db, notification_id=notification.notification_id)
    assert retrieved_notification.status == "READ"
    assert retrieved_notification.read_at is not None

def test_mark_notification_as_read_not_found(db):
    """Tests marking a non-existent notification as read."""
    non_existent_id = f"NOTIF_{uuid.uuid4()}"
    result = notification_service.mark_notification_as_read(db, notification_id=non_existent_id)
    assert result is None

def test_delete_notification(db):
    """Tests deleting a notification."""
    notification = notification_service.create_notification(
        db=db,
        user_type="TENANT",
        user_id="TEST_TENANT_3",
        title="Notification to Delete",
        content="This notification will be deleted",
        notification_type="TEST",
        priority="NORMAL"
    )
    
    success = notification_service.delete_notification(db, notification_id=notification.notification_id)
    assert success is True
    
    # Verify the notification was deleted
    retrieved_notification = notification_service.get_notification_by_id(db, notification_id=notification.notification_id)
    assert retrieved_notification is None

def test_create_bulk_notifications(db):
    """Tests creating notifications for multiple users at once."""
    user_type = "TENANT"
    user_ids = ["TENANT_1", "TENANT_2", "TENANT_3"]
    title = "Bulk Notification"
    content = "This is a bulk notification"
    notification_type = "BULK_TEST"
    
    notifications = notification_service.create_bulk_notifications(
        db=db,
        user_type=user_type,
        user_ids=user_ids,
        title=title,
        content=content,
        notification_type=notification_type
    )
    
    assert len(notifications) == 3
    
    for i, notification in enumerate(notifications):
        assert notification.user_type == user_type
        assert notification.user_id == user_ids[i]
        assert notification.title == title
        assert notification.content == content
        assert notification.type == notification_type

def test_mark_all_as_read(db):
    """Tests marking all notifications for a user as read."""
    user_type = "TENANT"
    user_id = "TEST_TENANT_4"
    
    # Create several notifications for the user
    for i in range(3):
        notification_service.create_notification(
            db=db,
            user_type=user_type,
            user_id=user_id,
            title=f"Test Notification {i+1}",
            content=f"This is test notification {i+1}",
            notification_type="TEST",
            priority="NORMAL"
        )
    
    # Mark all as read
    count = notification_service.mark_all_as_read(db, user_type=user_type, user_id=user_id)
    
    assert count == 3
    
    # Verify all notifications are marked as read
    notifications = notification_service.get_user_notifications(db, user_type=user_type, user_id=user_id)
    
    assert len(notifications) == 3
    for notification in notifications:
        assert notification.status == "READ"
        assert notification.read_at is not None

def test_count_unread_notifications(db):
    """Tests counting unread notifications for a user."""
    user_type = "TENANT"
    user_id = "TEST_TENANT_5"
    
    # Create several notifications for the user
    for i in range(5):
        notification_service.create_notification(
            db=db,
            user_type=user_type,
            user_id=user_id,
            title=f"Test Notification {i+1}",
            content=f"This is test notification {i+1}",
            notification_type="TEST",
            priority="NORMAL"
        )
    
    # Mark some as read
    notifications = notification_service.get_user_notifications(db, user_type=user_type, user_id=user_id)
    notification_service.mark_notification_as_read(db, notification_id=notifications[0].notification_id)
    notification_service.mark_notification_as_read(db, notification_id=notifications[1].notification_id)
    
    # Count unread
    count = notification_service.count_unread_notifications(db, user_type=user_type, user_id=user_id)
    
    assert count == 3