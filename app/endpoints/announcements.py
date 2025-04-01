from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import announcement_service
from ..db.connection import get_db
from ..models import announcement as announcement_models

router = APIRouter()

@router.post("/announcements/", response_model=announcement_models.Announcement, status_code=201)
def create_announcement(announcement: announcement_models.AnnouncementCreate, db: Session = Depends(get_db)):
    """
    Create a new building announcement.
    """
    db_announcement = announcement_service.create_announcement(
        db=db,
        building_id=announcement.building_id,
        title=announcement.title,
        content=announcement.content,
        priority=announcement.priority,
        expires_at=announcement.expires_at,
        send_notifications=True
    )
    return db_announcement

@router.get("/announcements/{announcement_id}", response_model=announcement_models.Announcement)
def read_announcement(announcement_id: str, db: Session = Depends(get_db)):
    """
    Get announcement by ID.
    """
    db_announcement = announcement_service.get_announcement_by_id(db, announcement_id=announcement_id)
    if db_announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return db_announcement

@router.put("/announcements/{announcement_id}", response_model=announcement_models.Announcement)
def update_announcement(
    announcement_id: str, 
    announcement_update: announcement_models.AnnouncementUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update announcement details.
    """
    db_announcement = announcement_service.update_announcement(
        db=db,
        announcement_id=announcement_id,
        title=announcement_update.title,
        content=announcement_update.content,
        priority=announcement_update.priority,
        expires_at=announcement_update.expires_at
    )
    if db_announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return db_announcement

@router.delete("/announcements/{announcement_id}", status_code=204)
def delete_announcement(announcement_id: str, db: Session = Depends(get_db)):
    """
    Delete announcement by ID.
    """
    success = announcement_service.delete_announcement(db, announcement_id=announcement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"ok": True}

@router.get("/buildings/{building_id}/announcements/", response_model=List[announcement_models.Announcement])
def read_building_announcements(
    building_id: str,
    include_expired: bool = False,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get announcements for a specific building.
    """
    announcements = announcement_service.get_building_announcements(
        db=db,
        building_id=building_id,
        include_expired=include_expired,
        limit=limit
    )
    return announcements

@router.post("/announcements/{announcement_id}/send", status_code=200)
def send_announcement_as_message(
    announcement_id: str,
    sender_type: str,
    sender_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Send an announcement as a message to all tenants in the building.
    """
    result = announcement_service.send_announcement_message(
        db=db,
        announcement_id=announcement_id,
        sender_type=sender_type,
        sender_id=sender_id
    )
    return {
        "announcement_id": announcement_id,
        "messages_sent": result["messages_sent"],
        "tenant_count": result["tenant_count"]
    }

@router.get("/tenants/{tenant_id}/announcements/active", response_model=List[announcement_models.Announcement])
def get_active_announcements_for_tenant(tenant_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get active announcements relevant to a specific tenant.
    """
    announcements = announcement_service.get_active_announcements_for_tenant(
        db=db,
        tenant_id=tenant_id,
        limit=limit
    )
    return announcements