import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db import models
from ..models import announcement as announcement_models
from . import notification_service, message_service

def create_announcement(
    db: Session,
    building_id: str,
    title: str,
    content: str,
    priority: str = "NORMAL",
    expires_at: Optional[datetime] = None,
    send_notifications: bool = True
) -> models.BuildingAnnouncement:
    """
    Creates a new building announcement.
    """
    announcement_id = f"ANN_{uuid.uuid4()}"
    
    db_announcement = models.BuildingAnnouncement(
        announcement_id=announcement_id,
        building_id=building_id,
        title=title,
        content=content,
        priority=priority,
        expires_at=expires_at
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    
    # Send notifications to all tenants in the building if requested
    if send_notifications:
        # Get all active tenants in the building
        tenants = db.query(models.Tenant).filter(
            models.Tenant.building_id == building_id,
            models.Tenant.status == "ACTIVE"
        ).all()
        
        for tenant in tenants:
            notification_service.create_notification(
                db=db,
                user_type="TENANT",
                user_id=tenant.tenant_id,
                title=f"Building Announcement: {title}",
                content=content[:100] + ("..." if len(content) > 100 else ""),
                notification_type="ANNOUNCEMENT",
                priority=priority
            )
    
    return db_announcement

def get_announcement_by_id(db: Session, announcement_id: str) -> Optional[models.BuildingAnnouncement]:
    """
    Retrieves an announcement from the database by its announcement_id.
    """
    return db.query(models.BuildingAnnouncement).filter(models.BuildingAnnouncement.announcement_id == announcement_id).first()

def update_announcement(
    db: Session,
    announcement_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    priority: Optional[str] = None,
    expires_at: Optional[datetime] = None
) -> Optional[models.BuildingAnnouncement]:
    """
    Updates an announcement with new values.
    """
    db_announcement = get_announcement_by_id(db, announcement_id)
    if db_announcement:
        if title:
            db_announcement.title = title
        
        if content:
            db_announcement.content = content
        
        if priority:
            db_announcement.priority = priority
        
        if expires_at:
            db_announcement.expires_at = expires_at
        
        db.commit()
        db.refresh(db_announcement)
        return db_announcement
    return None

def delete_announcement(db: Session, announcement_id: str) -> bool:
    """
    Deletes an announcement from the database.
    """
    db_announcement = get_announcement_by_id(db, announcement_id)
    if db_announcement:
        db.delete(db_announcement)
        db.commit()
        return True
    return False

def get_building_announcements(
    db: Session,
    building_id: str,
    include_expired: bool = False,
    limit: int = 100
) -> List[models.BuildingAnnouncement]:
    """
    Retrieves announcements for a specific building.
    """
    query = db.query(models.BuildingAnnouncement).filter(models.BuildingAnnouncement.building_id == building_id)
    
    if not include_expired:
        # Only include announcements that haven't expired
        query = query.filter(
            (models.BuildingAnnouncement.expires_at > datetime.now()) | 
            (models.BuildingAnnouncement.expires_at == None)
        )
    
    return query.order_by(desc(models.BuildingAnnouncement.created_at)).limit(limit).all()

def send_announcement_message(
    db: Session,
    announcement_id: str,
    sender_type: str,
    sender_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends the announcement as a message to all tenants in the building.
    """
    db_announcement = get_announcement_by_id(db, announcement_id)
    if not db_announcement:
        raise ValueError("Announcement not found")
    
    # Use the message service to send to all tenants
    result = message_service.send_building_announcement(
        db=db,
        building_id=db_announcement.building_id,
        sender_type=sender_type,
        sender_id=sender_id,
        title=db_announcement.title,
        content=db_announcement.content
    )
    
    return result

def get_active_announcements_for_tenant(
    db: Session,
    tenant_id: str,
    limit: int = 100
) -> List[models.BuildingAnnouncement]:
    """
    Retrieves active announcements relevant to a specific tenant.
    """
    # Get the tenant's building
    tenant = db.query(models.Tenant).filter(models.Tenant.tenant_id == tenant_id).first()
    if not tenant:
        return []
    
    # Get active announcements for the tenant's building
    return get_building_announcements(
        db=db,
        building_id=tenant.building_id,
        include_expired=False,
        limit=limit
    )