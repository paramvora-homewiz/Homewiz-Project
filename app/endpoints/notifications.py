from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import notification_service
from ..db.connection import get_db
from ..models import notification as notification_models

router = APIRouter()

@router.post("/notifications/", response_model=notification_models.Notification, status_code=201)
def create_notification(notification: notification_models.NotificationCreate, db: Session = Depends(get_db)):
    """
    Create a new notification.
    """
    db_notification = notification_service.create_notification(
        db=db,
        user_type=notification.user_type,
        user_id=notification.user_id,
        title=notification.title,
        content=notification.content,
        notification_type=notification.type,
        priority=notification.priority
    )
    return db_notification

@router.get("/notifications/{notification_id}", response_model=notification_models.Notification)
def read_notification(notification_id: str, db: Session = Depends(get_db)):
    """
    Get notification by ID.
    """
    db_notification = notification_service.get_notification_by_id(db, notification_id=notification_id)
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification

@router.post("/notifications/{notification_id}/read", response_model=notification_models.Notification)
def mark_notification_as_read(notification_id: str, db: Session = Depends(get_db)):
    """
    Mark a notification as read.
    """
    db_notification = notification_service.mark_notification_as_read(db, notification_id=notification_id)
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification

@router.delete("/notifications/{notification_id}", status_code=204)
def delete_notification(notification_id: str, db: Session = Depends(get_db)):
    """
    Delete notification by ID.
    """
    success = notification_service.delete_notification(db, notification_id=notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}

@router.get("/users/{user_type}/{user_id}/notifications/", response_model=List[notification_models.Notification])
def read_user_notifications(
    user_type: str,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get notifications for a specific user.
    """
    notifications = notification_service.get_user_notifications(
        db=db,
        user_type=user_type,
        user_id=user_id,
        status=status,
        limit=limit
    )
    return notifications

@router.post("/users/{user_type}/{user_id}/notifications/mark-all-read", status_code=200)
def mark_all_notifications_as_read(user_type: str, user_id: str, db: Session = Depends(get_db)):
    """
    Mark all notifications for a user as read.
    """
    count = notification_service.mark_all_as_read(db, user_type=user_type, user_id=user_id)
    return {"marked_read": count}

@router.get("/users/{user_type}/{user_id}/notifications/count", status_code=200)
def count_unread_notifications(user_type: str, user_id: str, db: Session = Depends(get_db)):
    """
    Count unread notifications for a user.
    """
    count = notification_service.count_unread_notifications(db, user_type=user_type, user_id=user_id)
    return {"unread_count": count}

@router.post("/bulk-notifications/", status_code=201)
def create_bulk_notifications(
    user_type: str,
    user_ids: List[str],
    title: str,
    content: str,
    notification_type: str,
    priority: str = "NORMAL",
    db: Session = Depends(get_db)
):
    """
    Create notifications for multiple users at once.
    """
    notifications = notification_service.create_bulk_notifications(
        db=db,
        user_type=user_type,
        user_ids=user_ids,
        title=title,
        content=content,
        notification_type=notification_type,
        priority=priority
    )
    return {"created_count": len(notifications)}