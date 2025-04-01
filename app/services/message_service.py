import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from ..db import models
from ..models import message as message_models
from . import notification_service

def create_message(
    db: Session,
    content: str,
    sender_type: str,
    recipient_type: str,
    message_type: str = "TEXT",
    sender_id: Optional[str] = None,
    recipient_id: Optional[str] = None,
) -> models.Message:
    """
    Creates a new message in the database.
    """
    message_id = f"MSG_{uuid.uuid4()}"
    
    db_message = models.Message(
        message_id=message_id,
        content=content,
        message_type=message_type,
        sender_type=sender_type,
        sender_id=sender_id,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        status="SENT"
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Create notification for the recipient
    if recipient_id and recipient_type:
        notification_service.create_notification(
            db=db,
            user_type=recipient_type,
            user_id=recipient_id,
            title=f"New Message from {sender_type.lower().capitalize()}",
            content=content[:100] + ("..." if len(content) > 100 else ""),
            notification_type="MESSAGE"
        )
    
    return db_message

def get_message_by_id(db: Session, message_id: str) -> Optional[models.Message]:
    """
    Retrieves a message from the database by its message_id.
    """
    return db.query(models.Message).filter(models.Message.message_id == message_id).first()

def mark_message_as_delivered(db: Session, message_id: str) -> Optional[models.Message]:
    """
    Marks a message as delivered.
    """
    db_message = get_message_by_id(db, message_id)
    if db_message:
        db_message.status = "DELIVERED"
        db_message.delivered_at = datetime.now()
        db.commit()
        db.refresh(db_message)
        return db_message
    return None

def mark_message_as_read(db: Session, message_id: str) -> Optional[models.Message]:
    """
    Marks a message as read.
    """
    db_message = get_message_by_id(db, message_id)
    if db_message:
        db_message.status = "READ"
        db_message.read_at = datetime.now()
        db.commit()
        db.refresh(db_message)
        return db_message
    return None

def get_user_messages(
    db: Session,
    user_type: str,
    user_id: str,
    conversation_with_type: Optional[str] = None,
    conversation_with_id: Optional[str] = None,
    limit: int = 100
) -> List[models.Message]:
    """
    Retrieves messages sent to or from a specific user.
    If conversation_with_type and conversation_with_id are provided,
    only messages between the user and the specified conversation partner are returned.
    """
    if conversation_with_type and conversation_with_id:
        # Get conversation between two specific users
        query = db.query(models.Message).filter(
            or_(
                and_(
                    models.Message.sender_type == user_type,
                    models.Message.sender_id == user_id,
                    models.Message.recipient_type == conversation_with_type,
                    models.Message.recipient_id == conversation_with_id
                ),
                and_(
                    models.Message.sender_type == conversation_with_type,
                    models.Message.sender_id == conversation_with_id,
                    models.Message.recipient_type == user_type,
                    models.Message.recipient_id == user_id
                )
            )
        )
    else:
        # Get all messages for the user
        query = db.query(models.Message).filter(
            or_(
                and_(
                    models.Message.sender_type == user_type,
                    models.Message.sender_id == user_id
                ),
                and_(
                    models.Message.recipient_type == user_type,
                    models.Message.recipient_id == user_id
                )
            )
        )
    
    return query.order_by(desc(models.Message.created_at)).limit(limit).all()

def get_conversation_partners(
    db: Session,
    user_type: str,
    user_id: str
) -> List[Dict[str, Any]]:
    """
    Gets a list of unique entities the user has had conversations with.
    Returns a list of dicts with partner_type and partner_id.
    """
    # Get all unique senders who sent messages to this user
    sender_query = db.query(
        models.Message.sender_type,
        models.Message.sender_id
    ).distinct().filter(
        models.Message.recipient_type == user_type,
        models.Message.recipient_id == user_id
    )
    
    # Get all unique recipients who received messages from this user
    recipient_query = db.query(
        models.Message.recipient_type,
        models.Message.recipient_id
    ).distinct().filter(
        models.Message.sender_type == user_type,
        models.Message.sender_id == user_id
    )
    
    # Combine and deduplicate results
    partners = []
    seen = set()
    
    for partner_type, partner_id in sender_query.all():
        if (partner_type, partner_id) not in seen and partner_id is not None:
            seen.add((partner_type, partner_id))
            partners.append({"partner_type": partner_type, "partner_id": partner_id})
    
    for partner_type, partner_id in recipient_query.all():
        if (partner_type, partner_id) not in seen and partner_id is not None:
            seen.add((partner_type, partner_id))
            partners.append({"partner_type": partner_type, "partner_id": partner_id})
    
    return partners

def count_unread_messages(
    db: Session,
    recipient_type: str,
    recipient_id: str
) -> int:
    """
    Counts the number of unread messages for a recipient.
    """
    return db.query(models.Message).filter(
        models.Message.recipient_type == recipient_type,
        models.Message.recipient_id == recipient_id,
        models.Message.status.in_(["SENT", "DELIVERED"])
    ).count()

def send_bulk_message(
    db: Session,
    content: str,
    sender_type: str,
    recipient_type: str,
    recipient_ids: List[str],
    message_type: str = "TEXT",
    sender_id: Optional[str] = None
) -> List[models.Message]:
    """
    Sends a message to multiple recipients.
    """
    messages = []
    for recipient_id in recipient_ids:
        message = create_message(
            db=db,
            content=content,
            message_type=message_type,
            sender_type=sender_type,
            sender_id=sender_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id
        )
        messages.append(message)
    
    return messages

def send_building_announcement(
    db: Session,
    building_id: str,
    sender_type: str,
    sender_id: Optional[str],
    title: str,
    content: str,
    message_type: str = "TEXT"
) -> Dict[str, Any]:
    """
    Sends a message to all tenants in a building.
    """
    # Get all active tenants in the building
    tenants = db.query(models.Tenant).filter(
        models.Tenant.building_id == building_id,
        models.Tenant.status == "ACTIVE"
    ).all()
    
    tenant_ids = [tenant.tenant_id for tenant in tenants]
    
    # Create an announcement record
    announcement_id = f"ANN_{uuid.uuid4()}"
    db_announcement = models.BuildingAnnouncement(
        announcement_id=announcement_id,
        building_id=building_id,
        title=title,
        content=content
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    
    # Send messages to all tenants
    messages = send_bulk_message(
        db=db,
        content=content,
        sender_type=sender_type,
        sender_id=sender_id,
        recipient_type="TENANT",
        recipient_ids=tenant_ids,
        message_type=message_type
    )
    
    return {
        "announcement": db_announcement,
        "messages_sent": len(messages),
        "tenant_count": len(tenant_ids)
    }

def get_message_history(
    db: Session,
    user1_type: str,
    user1_id: str,
    user2_type: str,
    user2_id: str,
    limit: int = 50
) -> List[models.Message]:
    """
    Gets the message history between two users, sorted by time (newest first).
    """
    query = db.query(models.Message).filter(
        or_(
            and_(
                models.Message.sender_type == user1_type,
                models.Message.sender_id == user1_id,
                models.Message.recipient_type == user2_type,
                models.Message.recipient_id == user2_id
            ),
            and_(
                models.Message.sender_type == user2_type,
                models.Message.sender_id == user2_id,
                models.Message.recipient_type == user1_type,
                models.Message.recipient_id == user1_id
            )
        )
    )
    
    return query.order_by(desc(models.Message.created_at)).limit(limit).all()