from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import message_service
from ..db.connection import get_db
from ..models import message as message_models

router = APIRouter()

@router.post("/messages/", response_model=message_models.Message, status_code=201)
def create_message(message: message_models.MessageCreate, db: Session = Depends(get_db)):
    """
    Create a new message.
    """
    db_message = message_service.create_message(
        db=db,
        content=message.content,
        message_type=message.message_type,
        sender_type=message.sender_type,
        sender_id=message.sender_id,
        recipient_type=message.recipient_type,
        recipient_id=message.recipient_id
    )
    return db_message

@router.post("/messages/bulk/", status_code=201)
def send_bulk_message(request: message_models.BulkMessageRequest, db: Session = Depends(get_db)):
    """
    Send a message to multiple recipients.
    """
    messages = message_service.send_bulk_message(
        db=db,
        content=request.content,
        message_type=request.message_type,
        sender_type=request.sender_type,
        sender_id=request.sender_id,
        recipient_type=request.recipient_type,
        recipient_ids=request.recipient_ids
    )
    return {"sent_count": len(messages)}

@router.get("/messages/{message_id}", response_model=message_models.Message)
def read_message(message_id: str, db: Session = Depends(get_db)):
    """
    Get message by ID.
    """
    db_message = message_service.get_message_by_id(db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return db_message

@router.post("/messages/{message_id}/delivered", response_model=message_models.Message)
def mark_message_as_delivered(message_id: str, db: Session = Depends(get_db)):
    """
    Mark a message as delivered.
    """
    db_message = message_service.mark_message_as_delivered(db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return db_message

@router.post("/messages/{message_id}/read", response_model=message_models.Message)
def mark_message_as_read(message_id: str, db: Session = Depends(get_db)):
    """
    Mark a message as read.
    """
    db_message = message_service.mark_message_as_read(db, message_id=message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return db_message

@router.get("/users/{user_type}/{user_id}/messages/", response_model=List[message_models.Message])
def read_user_messages(
    user_type: str,
    user_id: str,
    conversation_with_type: Optional[str] = None,
    conversation_with_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get messages for a specific user.
    """
    messages = message_service.get_user_messages(
        db=db,
        user_type=user_type,
        user_id=user_id,
        conversation_with_type=conversation_with_type,
        conversation_with_id=conversation_with_id,
        limit=limit
    )
    return messages

@router.get("/users/{user_type}/{user_id}/conversations/", response_model=List[Dict[str, Any]])
def get_conversation_partners(user_type: str, user_id: str, db: Session = Depends(get_db)):
    """
    Get a list of users that the specified user has had conversations with.
    """
    partners = message_service.get_conversation_partners(
        db=db,
        user_type=user_type,
        user_id=user_id
    )
    return partners

@router.get("/users/{user_type}/{user_id}/messages/unread/count", status_code=200)
def count_unread_messages(user_type: str, user_id: str, db: Session = Depends(get_db)):
    """
    Count unread messages for a user.
    """
    count = message_service.count_unread_messages(
        db=db,
        recipient_type=user_type,
        recipient_id=user_id
    )
    return {"unread_count": count}

@router.get("/messages/history/{user1_type}/{user1_id}/{user2_type}/{user2_id}", response_model=List[message_models.Message])
def get_message_history(
    user1_type: str,
    user1_id: str,
    user2_type: str,
    user2_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get the message history between two users.
    """
    messages = message_service.get_message_history(
        db=db,
        user1_type=user1_type,
        user1_id=user1_id,
        user2_type=user2_type,
        user2_id=user2_id,
        limit=limit
    )
    return messages

@router.post("/buildings/{building_id}/announcements/send", status_code=201)
def send_building_announcement(
    building_id: str,
    sender_type: str,
    title: str,
    content: str,
    sender_id: Optional[str] = None,
    message_type: str = "TEXT",
    db: Session = Depends(get_db)
):
    """
    Send a message to all tenants in a building.
    """
    result = message_service.send_building_announcement(
        db=db,
        building_id=building_id,
        sender_type=sender_type,
        sender_id=sender_id,
        title=title,
        content=content,
        message_type=message_type
    )
    return {
        "building_id": building_id,
        "messages_sent": result["messages_sent"],
        "tenant_count": result["tenant_count"],
        "announcement_id": result["announcement"].announcement_id if "announcement" in result else None
    }