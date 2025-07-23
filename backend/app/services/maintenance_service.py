import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..db import models
from ..models import maintenance_request as maintenance_models
from . import notification_service

def create_maintenance_request(
    db: Session,
    title: str,
    description: str,
    room_id: str,
    building_id: str,
    tenant_id: str,
    priority: str = "MEDIUM",
    assigned_to: Optional[int] = None
) -> models.MaintenanceRequest:
    """
    Creates a new maintenance request in the database.
    """
    request_id = f"MAINT_{uuid.uuid4()}"
    status = "ASSIGNED" if assigned_to else "PENDING"
    
    db_request = models.MaintenanceRequest(
        request_id=request_id,
        title=title,
        description=description,
        priority=priority,
        status=status,
        room_id=room_id,
        building_id=building_id,
        tenant_id=tenant_id,
        assigned_to=assigned_to
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    # Send notification to the tenant
    notification_service.create_notification(
        db=db,
        user_type="TENANT",
        user_id=tenant_id,
        title="Maintenance Request Received",
        content=f"Your maintenance request '{title}' has been received and is {status.lower()}.",
        notification_type="MAINTENANCE"
    )
    
    # If assigned, notify the maintenance operator
    if assigned_to:
        notification_service.create_notification(
            db=db,
            user_type="OPERATOR",
            user_id=str(assigned_to),
            title="New Maintenance Request Assigned",
            content=f"A new maintenance request '{title}' has been assigned to you.",
            notification_type="MAINTENANCE",
            priority=priority
        )
    
    return db_request

def get_maintenance_request_by_id(db: Session, request_id: str) -> Optional[models.MaintenanceRequest]:
    """
    Retrieves a maintenance request from the database by its request_id.
    """
    return db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.request_id == request_id).first()

def update_maintenance_request_status(
    db: Session, 
    request_id: str, 
    status: str,
    notes: Optional[str] = None
) -> Optional[models.MaintenanceRequest]:
    """
    Updates the status of a maintenance request.
    """
    db_request = get_maintenance_request_by_id(db, request_id)
    if db_request:
        old_status = db_request.status
        db_request.status = status
        
        if status == "COMPLETED":
            db_request.resolved_at = datetime.now()
        
        db.commit()
        db.refresh(db_request)
        
        # Notify the tenant about the status change
        notification_service.create_notification(
            db=db,
            user_type="TENANT",
            user_id=db_request.tenant_id,
            title=f"Maintenance Request {status}",
            content=f"Your maintenance request '{db_request.title}' has been {status.lower()}." + 
                    (f" Notes: {notes}" if notes else ""),
            notification_type="MAINTENANCE"
        )
        
        return db_request
    return None

def assign_maintenance_request(
    db: Session,
    request_id: str,
    operator_id: int
) -> Optional[models.MaintenanceRequest]:
    """
    Assigns a maintenance request to an operator.
    """
    db_request = get_maintenance_request_by_id(db, request_id)
    if db_request:
        db_request.assigned_to = operator_id
        if db_request.status == "PENDING":
            db_request.status = "ASSIGNED"
        
        db.commit()
        db.refresh(db_request)
        
        # Notify the assigned operator
        notification_service.create_notification(
            db=db,
            user_type="OPERATOR",
            user_id=str(operator_id),
            title="Maintenance Request Assigned",
            content=f"A maintenance request '{db_request.title}' has been assigned to you.",
            notification_type="MAINTENANCE",
            priority=db_request.priority
        )
        
        return db_request
    return None

def update_maintenance_request(
    db: Session,
    request_id: str,
    update_data: Dict[str, Any]
) -> Optional[models.MaintenanceRequest]:
    """
    Updates a maintenance request with new values.
    """
    db_request = get_maintenance_request_by_id(db, request_id)
    if db_request:
        for key, value in update_data.items():
            if value is not None and hasattr(db_request, key):
                setattr(db_request, key, value)
        
        db.commit()
        db.refresh(db_request)
        return db_request
    return None

def delete_maintenance_request(db: Session, request_id: str) -> bool:
    """
    Deletes a maintenance request from the database.
    """
    db_request = get_maintenance_request_by_id(db, request_id)
    if db_request:
        db.delete(db_request)
        db.commit()
        return True
    return False

def get_tenant_maintenance_requests(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    limit: int = 100
) -> List[models.MaintenanceRequest]:
    """
    Retrieves maintenance requests for a specific tenant.
    """
    query = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.tenant_id == tenant_id)
    
    if status:
        query = query.filter(models.MaintenanceRequest.status == status)
    
    return query.order_by(desc(models.MaintenanceRequest.created_at)).limit(limit).all()

def get_building_maintenance_requests(
    db: Session,
    building_id: str,
    status: Optional[str] = None,
    limit: int = 100
) -> List[models.MaintenanceRequest]:
    """
    Retrieves maintenance requests for a specific building.
    """
    query = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.building_id == building_id)
    
    if status:
        query = query.filter(models.MaintenanceRequest.status == status)
    
    return query.order_by(desc(models.MaintenanceRequest.created_at)).limit(limit).all()

def get_operator_maintenance_requests(
    db: Session,
    operator_id: int,
    status: Optional[str] = None,
    limit: int = 100
) -> List[models.MaintenanceRequest]:
    """
    Retrieves maintenance requests assigned to a specific operator.
    """
    query = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.assigned_to == operator_id)
    
    if status:
        query = query.filter(models.MaintenanceRequest.status == status)
    
    return query.order_by(desc(models.MaintenanceRequest.created_at)).limit(limit).all()

def get_maintenance_requests_by_priority(
    db: Session,
    priority: str,
    status: Optional[str] = None,
    limit: int = 100
) -> List[models.MaintenanceRequest]:
    """
    Retrieves maintenance requests by priority.
    """
    query = db.query(models.MaintenanceRequest).filter(models.MaintenanceRequest.priority == priority)
    
    if status:
        query = query.filter(models.MaintenanceRequest.status == status)
    
    return query.order_by(desc(models.MaintenanceRequest.created_at)).limit(limit).all()

def get_unassigned_maintenance_requests(
    db: Session,
    building_id: Optional[str] = None,
    limit: int = 100
) -> List[models.MaintenanceRequest]:
    """
    Retrieves unassigned maintenance requests.
    """
    query = db.query(models.MaintenanceRequest).filter(
        or_(
            models.MaintenanceRequest.assigned_to == None,
            models.MaintenanceRequest.status == "PENDING"
        )
    )
    
    if building_id:
        query = query.filter(models.MaintenanceRequest.building_id == building_id)
    
    return query.order_by(desc(models.MaintenanceRequest.created_at)).limit(limit).all()