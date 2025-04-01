import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..db import models
from ..models import checklist as checklist_models
from . import notification_service

def create_checklist(
    db: Session,
    checklist_type: str,
    room_id: str,
    building_id: str,
    tenant_id: Optional[str] = None,
    operator_id: Optional[int] = None,
    items: Optional[List[Dict[str, Any]]] = None
) -> models.Checklist:
    """
    Creates a new checklist in the database along with its items.
    """
    checklist_id = f"CHKL_{uuid.uuid4()}"
    
    db_checklist = models.Checklist(
        checklist_id=checklist_id,
        checklist_type=checklist_type,
        status="PENDING",
        room_id=room_id,
        building_id=building_id,
        tenant_id=tenant_id,
        operator_id=operator_id
    )
    db.add(db_checklist)
    db.commit()
    db.refresh(db_checklist)
    
    # Create checklist items if provided
    if items:
        for item in items:
            create_checklist_item(
                db=db,
                checklist_id=checklist_id,
                description=item.get("description"),
                status=item.get("status", "PENDING"),
                notes=item.get("notes")
            )
    
    # Notify the operator if assigned
    if operator_id:
        notification_service.create_notification(
            db=db,
            user_type="OPERATOR",
            user_id=str(operator_id),
            title=f"New {checklist_type} Checklist Assigned",
            content=f"A new {checklist_type.lower()} checklist has been assigned to you for room {room_id}.",
            notification_type="CHECKLIST"
        )
    
    # Notify the tenant if applicable
    if tenant_id:
        notification_service.create_notification(
            db=db,
            user_type="TENANT",
            user_id=tenant_id,
            title=f"{checklist_type} Checklist Created",
            content=f"A {checklist_type.lower()} checklist has been created for your room.",
            notification_type="CHECKLIST"
        )
    
    return db_checklist

def create_checklist_item(
    db: Session,
    checklist_id: str,
    description: str,
    status: str = "PENDING",
    notes: Optional[str] = None
) -> models.ChecklistItem:
    """
    Creates a new checklist item in the database.
    """
    item_id = f"ITEM_{uuid.uuid4()}"
    
    db_item = models.ChecklistItem(
        item_id=item_id,
        checklist_id=checklist_id,
        description=description,
        status=status,
        notes=notes
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_checklist_by_id(db: Session, checklist_id: str) -> Optional[models.Checklist]:
    """
    Retrieves a checklist from the database by its checklist_id.
    """
    return db.query(models.Checklist).filter(models.Checklist.checklist_id == checklist_id).first()

def get_checklist_item_by_id(db: Session, item_id: str) -> Optional[models.ChecklistItem]:
    """
    Retrieves a checklist item from the database by its item_id.
    """
    return db.query(models.ChecklistItem).filter(models.ChecklistItem.item_id == item_id).first()

def get_checklist_items(db: Session, checklist_id: str) -> List[models.ChecklistItem]:
    """
    Retrieves all items for a checklist.
    """
    return db.query(models.ChecklistItem).filter(models.ChecklistItem.checklist_id == checklist_id).all()

def update_checklist_status(
    db: Session,
    checklist_id: str,
    status: str
) -> Optional[models.Checklist]:
    """
    Updates the status of a checklist.
    """
    db_checklist = get_checklist_by_id(db, checklist_id)
    if db_checklist:
        db_checklist.status = status
        if status == "COMPLETED":
            db_checklist.completed_at = datetime.now()
        
        db.commit()
        db.refresh(db_checklist)
        
        # Notify relevant parties
        if db_checklist.operator_id:
            notification_service.create_notification(
                db=db,
                user_type="OPERATOR",
                user_id=str(db_checklist.operator_id),
                title=f"Checklist {status}",
                content=f"The {db_checklist.checklist_type.lower()} checklist for room {db_checklist.room_id} has been marked as {status.lower()}.",
                notification_type="CHECKLIST"
            )
        
        if db_checklist.tenant_id:
            notification_service.create_notification(
                db=db,
                user_type="TENANT",
                user_id=db_checklist.tenant_id,
                title=f"Checklist {status}",
                content=f"The {db_checklist.checklist_type.lower()} checklist for your room has been marked as {status.lower()}.",
                notification_type="CHECKLIST"
            )
        
        return db_checklist
    return None

def update_checklist_item_status(
    db: Session,
    item_id: str,
    status: str,
    notes: Optional[str] = None
) -> Optional[models.ChecklistItem]:
    """
    Updates the status of a checklist item.
    """
    db_item = get_checklist_item_by_id(db, item_id)
    if db_item:
        db_item.status = status
        if notes:
            db_item.notes = notes
        
        if status == "COMPLETED":
            db_item.completed_at = datetime.now()
        
        db.commit()
        db.refresh(db_item)
        
        # Check if all items are completed to update the checklist status
        if status == "COMPLETED":
            checklist = get_checklist_by_id(db, db_item.checklist_id)
            all_items = get_checklist_items(db, db_item.checklist_id)
            all_completed = all(item.status == "COMPLETED" for item in all_items)
            
            if all_completed and checklist.status != "COMPLETED":
                update_checklist_status(db, db_item.checklist_id, "COMPLETED")
        
        return db_item
    return None

def delete_checklist(db: Session, checklist_id: str) -> bool:
    """
    Deletes a checklist and all its items from the database.
    """
    # First, delete all checklist items
    db.query(models.ChecklistItem).filter(models.ChecklistItem.checklist_id == checklist_id).delete()
    
    # Then delete the checklist itself
    deleted = db.query(models.Checklist).filter(models.Checklist.checklist_id == checklist_id).delete()
    db.commit()
    return deleted > 0

def get_room_checklists(
    db: Session,
    room_id: str,
    checklist_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Checklist]:
    """
    Retrieves checklists for a specific room.
    """
    query = db.query(models.Checklist).filter(models.Checklist.room_id == room_id)
    
    if checklist_type:
        query = query.filter(models.Checklist.checklist_type == checklist_type)
    
    if status:
        query = query.filter(models.Checklist.status == status)
    
    return query.order_by(desc(models.Checklist.created_at)).all()

def get_tenant_checklists(
    db: Session,
    tenant_id: str,
    checklist_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Checklist]:
    """
    Retrieves checklists for a specific tenant.
    """
    query = db.query(models.Checklist).filter(models.Checklist.tenant_id == tenant_id)
    
    if checklist_type:
        query = query.filter(models.Checklist.checklist_type == checklist_type)
    
    if status:
        query = query.filter(models.Checklist.status == status)
    
    return query.order_by(desc(models.Checklist.created_at)).all()

def get_operator_checklists(
    db: Session,
    operator_id: int,
    checklist_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Checklist]:
    """
    Retrieves checklists assigned to a specific operator.
    """
    query = db.query(models.Checklist).filter(models.Checklist.operator_id == operator_id)
    
    if checklist_type:
        query = query.filter(models.Checklist.checklist_type == checklist_type)
    
    if status:
        query = query.filter(models.Checklist.status == status)
    
    return query.order_by(desc(models.Checklist.created_at)).all()

def get_building_checklists(
    db: Session,
    building_id: str,
    checklist_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Checklist]:
    """
    Retrieves checklists for a specific building.
    """
    query = db.query(models.Checklist).filter(models.Checklist.building_id == building_id)
    
    if checklist_type:
        query = query.filter(models.Checklist.checklist_type == checklist_type)
    
    if status:
        query = query.filter(models.Checklist.status == status)
    
    return query.order_by(desc(models.Checklist.created_at)).all()

def create_move_in_checklist(
    db: Session,
    room_id: str,
    building_id: str,
    tenant_id: str,
    operator_id: Optional[int] = None
) -> models.Checklist:
    """
    Creates a standardized move-in checklist.
    """
    standard_items = [
        {"description": "Verify all keys work properly", "status": "PENDING"},
        {"description": "Inspect walls and ceilings for damage", "status": "PENDING"},
        {"description": "Check all lights and fixtures", "status": "PENDING"},
        {"description": "Verify plumbing is working properly", "status": "PENDING"},
        {"description": "Test all appliances", "status": "PENDING"},
        {"description": "Inspect floors and carpets", "status": "PENDING"},
        {"description": "Verify windows open/close properly", "status": "PENDING"},
        {"description": "Check smoke and CO detectors", "status": "PENDING"},
        {"description": "Confirm heating/cooling systems work", "status": "PENDING"},
        {"description": "Inspect for pest issues", "status": "PENDING"}
    ]
    
    return create_checklist(
        db=db,
        checklist_type="MOVE_IN",
        room_id=room_id,
        building_id=building_id,
        tenant_id=tenant_id,
        operator_id=operator_id,
        items=standard_items
    )

def create_move_out_checklist(
    db: Session,
    room_id: str,
    building_id: str,
    tenant_id: str,
    operator_id: Optional[int] = None
) -> models.Checklist:
    """
    Creates a standardized move-out checklist.
    """
    standard_items = [
        {"description": "Collect all keys", "status": "PENDING"},
        {"description": "Inspect walls and ceilings for damage", "status": "PENDING"},
        {"description": "Check all lights and fixtures", "status": "PENDING"},
        {"description": "Verify plumbing is working properly", "status": "PENDING"},
        {"description": "Test all appliances", "status": "PENDING"},
        {"description": "Inspect floors and carpets for damage", "status": "PENDING"},
        {"description": "Verify windows are intact", "status": "PENDING"},
        {"description": "Check smoke and CO detectors", "status": "PENDING"},
        {"description": "Confirm heating/cooling systems work", "status": "PENDING"},
        {"description": "Verify tenant has removed all belongings", "status": "PENDING"},
        {"description": "Assess cleaning needs", "status": "PENDING"},
        {"description": "Document any damages for deposit deduction", "status": "PENDING"}
    ]
    
    return create_checklist(
        db=db,
        checklist_type="MOVE_OUT",
        room_id=room_id,
        building_id=building_id,
        tenant_id=tenant_id,
        operator_id=operator_id,
        items=standard_items
    )