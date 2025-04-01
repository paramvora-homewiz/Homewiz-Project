import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from ..db import models
from ..models import notification as notification_models

def create_notification(
    db: Session, 
    user_type: str, 
    user_id: str, 
    title: str, 
    content: str, 
    notification_type: str,
    priority: str = "NORMAL"
) -> models.Notification:
    """
    Creates a new notification in the database.
    """
    notification_id = f"NOTIF_{uuid.uuid4()}"
    db_notification = models.Notification(
        notification_id=notification_id,
        user_type=user_type,
        user_id=user_id,
        title=title,
        content=content,
        type=notification_type,
        priority=priority,
        status="UNREAD"
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notification_by_id(db: Session, notification_id: str) -> Optional[models.Notification]:
    """
    Retrieves a notification from the database by its notification_id.
    """
    return db.query(models.Notification).filter(models.Notification.notification_id == notification_id).first()

def get_user_notifications(
    db: Session, 
    user_type: str, 
    user_id: str, 
    status: Optional[str] = None,
    limit: int = 100
) -> List[models.Notification]:
    """
    Retrieves notifications for a specific user.
    """
    query = db.query(models.Notification).filter(
        models.Notification.user_type == user_type,
        models.Notification.user_id == user_id
    )
    
    if status:
        query = query.filter(models.Notification.status == status)
    
    return query.order_by(models.Notification.created_at.desc()).limit(limit).all()

def mark_notification_as_read(db: Session, notification_id: str) -> Optional[models.Notification]:
    """
    Marks a notification as read.
    """
    db_notification = get_notification_by_id(db, notification_id)
    if db_notification:
        db_notification.status = "READ"
        db_notification.read_at = datetime.now()
        db.commit()
        db.refresh(db_notification)
        return db_notification
    return None

def delete_notification(db: Session, notification_id: str) -> bool:
    """
    Deletes a notification from the database.
    """
    db_notification = get_notification_by_id(db, notification_id)
    if db_notification:
        db.delete(db_notification)
        db.commit()
        return True
    return False

def create_bulk_notifications(
    db: Session, 
    user_type: str, 
    user_ids: List[str], 
    title: str, 
    content: str, 
    notification_type: str,
    priority: str = "NORMAL"
) -> List[models.Notification]:
    """
    Creates notifications for multiple users at once.
    """
    notifications = []
    for user_id in user_ids:
        notification = create_notification(
            db=db,
            user_type=user_type,
            user_id=user_id,
            title=title,
            content=content,
            notification_type=notification_type,
            priority=priority
        )
        notifications.append(notification)
    
    return notifications

def mark_all_as_read(db: Session, user_type: str, user_id: str) -> int:
    """
    Marks all unread notifications for a user as read.
    Returns the number of notifications marked as read.
    """
    now = datetime.now()
    result = db.query(models.Notification).filter(
        models.Notification.user_type == user_type,
        models.Notification.user_id == user_id,
        models.Notification.status == "UNREAD"
    ).update({
        "status": "READ",
        "read_at": now
    })
    
    db.commit()
    return result

def count_unread_notifications(db: Session, user_type: str, user_id: str) -> int:
    """
    Counts the number of unread notifications for a user.
    """
    return db.query(models.Notification).filter(
        models.Notification.user_type == user_type,
        models.Notification.user_id == user_id,
        models.Notification.status == "UNREAD"
    ).count()