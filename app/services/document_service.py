import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db import models
from ..models import document as document_models
from . import notification_service

def create_document(
    db: Session,
    title: str,
    document_type: str,
    content: Optional[str] = None,
    tenant_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    room_id: Optional[str] = None,
    building_id: Optional[str] = None,
    status: str = "DRAFT"
) -> models.Document:
    """
    Creates a new document in the database.
    """
    document_id = f"DOC_{uuid.uuid4()}"
    
    db_document = models.Document(
        document_id=document_id,
        title=title,
        document_type=document_type,
        content=content,
        status=status,
        tenant_id=tenant_id,
        lead_id=lead_id,
        room_id=room_id,
        building_id=building_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Notify relevant parties
    if tenant_id and status != "DRAFT":
        notification_service.create_notification(
            db=db,
            user_type="TENANT",
            user_id=tenant_id,
            title=f"New {document_type} Document",
            content=f"A new {document_type.lower()} document '{title}' is available for your review.",
            notification_type="DOCUMENT"
        )
    
    if lead_id and status != "DRAFT":
        notification_service.create_notification(
            db=db,
            user_type="LEAD",
            user_id=lead_id,
            title=f"New {document_type} Document",
            content=f"A new {document_type.lower()} document '{title}' is available for your review.",
            notification_type="DOCUMENT"
        )
    
    return db_document

def get_document_by_id(db: Session, document_id: str) -> Optional[models.Document]:
    """
    Retrieves a document from the database by its document_id.
    """
    return db.query(models.Document).filter(models.Document.document_id == document_id).first()

def update_document_status(
    db: Session,
    document_id: str,
    status: str
) -> Optional[models.Document]:
    """
    Updates the status of a document.
    """
    db_document = get_document_by_id(db, document_id)
    if db_document:
        db_document.status = status
        
        if status == "SIGNED":
            db_document.signed_at = datetime.now()
        
        db.commit()
        db.refresh(db_document)
        
        # Notify relevant parties
        if db_document.tenant_id:
            notification_service.create_notification(
                db=db,
                user_type="TENANT",
                user_id=db_document.tenant_id,
                title=f"Document Status Updated",
                content=f"The document '{db_document.title}' has been updated to status: {status}.",
                notification_type="DOCUMENT"
            )
        
        if db_document.lead_id:
            notification_service.create_notification(
                db=db,
                user_type="LEAD",
                user_id=db_document.lead_id,
                title=f"Document Status Updated",
                content=f"The document '{db_document.title}' has been updated to status: {status}.",
                notification_type="DOCUMENT"
            )
        
        return db_document
    return None

def update_document_content(
    db: Session,
    document_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None
) -> Optional[models.Document]:
    """
    Updates the content of a document.
    """
    db_document = get_document_by_id(db, document_id)
    if db_document:
        if title:
            db_document.title = title
        
        if content:
            db_document.content = content
        
        db_document.updated_at = datetime.now()
        db.commit()
        db.refresh(db_document)
        return db_document
    return None

def delete_document(db: Session, document_id: str) -> bool:
    """
    Deletes a document from the database.
    """
    db_document = get_document_by_id(db, document_id)
    if db_document:
        db.delete(db_document)
        db.commit()
        return True
    return False

def get_tenant_documents(
    db: Session,
    tenant_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Document]:
    """
    Retrieves documents for a specific tenant.
    """
    query = db.query(models.Document).filter(models.Document.tenant_id == tenant_id)
    
    if document_type:
        query = query.filter(models.Document.document_type == document_type)
    
    if status:
        query = query.filter(models.Document.status == status)
    
    return query.order_by(desc(models.Document.created_at)).all()

def get_lead_documents(
    db: Session,
    lead_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Document]:
    """
    Retrieves documents for a specific lead.
    """
    query = db.query(models.Document).filter(models.Document.lead_id == lead_id)
    
    if document_type:
        query = query.filter(models.Document.document_type == document_type)
    
    if status:
        query = query.filter(models.Document.status == status)
    
    return query.order_by(desc(models.Document.created_at)).all()

def get_room_documents(
    db: Session,
    room_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Document]:
    """
    Retrieves documents for a specific room.
    """
    query = db.query(models.Document).filter(models.Document.room_id == room_id)
    
    if document_type:
        query = query.filter(models.Document.document_type == document_type)
    
    if status:
        query = query.filter(models.Document.status == status)
    
    return query.order_by(desc(models.Document.created_at)).all()

def get_building_documents(
    db: Session,
    building_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[models.Document]:
    """
    Retrieves documents for a specific building.
    """
    query = db.query(models.Document).filter(models.Document.building_id == building_id)
    
    if document_type:
        query = query.filter(models.Document.document_type == document_type)
    
    if status:
        query = query.filter(models.Document.status == status)
    
    return query.order_by(desc(models.Document.created_at)).all()

def generate_lease_document(
    db: Session,
    tenant_id: str,
    room_id: str,
    building_id: str,
    lease_start_date: datetime,
    lease_end_date: datetime,
    monthly_rent: float,
    deposit_amount: float
) -> models.Document:
    """
    Generates a standardized lease document.
    """
    # Get tenant, room, and building details
    tenant = db.query(models.Tenant).filter(models.Tenant.tenant_id == tenant_id).first()
    room = db.query(models.Room).filter(models.Room.room_id == room_id).first()
    building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
    
    if not tenant or not room or not building:
        raise ValueError("Tenant, room, or building not found")
    
    # Generate lease title
    title = f"Lease Agreement - {tenant.tenant_name} - {room.room_number} - {lease_start_date.strftime('%Y-%m-%d')}"
    
    # Generate lease content (placeholder for a real template system)
    # In a real implementation, you would use a template engine like Jinja2
    content = f"""
    LEASE AGREEMENT

    THIS LEASE AGREEMENT is made on {datetime.now().strftime('%Y-%m-%d')} between:
    
    LANDLORD: {building.building_name} Management
    TENANT: {tenant.tenant_name}
    
    PROPERTY:
    Building: {building.building_name}
    Address: {building.full_address}
    Unit: {room.room_number}
    
    TERM:
    The lease begins on {lease_start_date.strftime('%Y-%m-%d')} and ends on {lease_end_date.strftime('%Y-%m-%d')}.
    
    RENT:
    Monthly Rent: ${monthly_rent:.2f}
    Security Deposit: ${deposit_amount:.2f}
    
    [Additional lease terms would be inserted here]
    
    By signing below, the Tenant acknowledges having read and agreed to all terms of this lease.
    
    _________________________
    Tenant Signature
    
    _________________________
    Landlord Signature
    """
    
    return create_document(
        db=db,
        title=title,
        document_type="LEASE",
        content=content,
        tenant_id=tenant_id,
        room_id=room_id,
        building_id=building_id,
        status="PENDING_SIGNATURE"
    )

def generate_application_document(
    db: Session,
    lead_id: str,
    room_id: Optional[str] = None,
    building_id: Optional[str] = None
) -> models.Document:
    """
    Generates a standardized rental application document.
    """
    # Get lead details
    lead = db.query(models.Lead).filter(models.Lead.lead_id == lead_id).first()
    
    if not lead:
        raise ValueError("Lead not found")
    
    # Get room and building details if provided
    room_info = ""
    building_info = ""
    
    if room_id:
        room = db.query(models.Room).filter(models.Room.room_id == room_id).first()
        if room:
            room_info = f"Room: {room.room_number}\n"
    
    if building_id:
        building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
        if building:
            building_info = f"Building: {building.building_name}\nAddress: {building.full_address}\n"
    
    # Generate application title
    title = f"Rental Application - {lead.email} - {datetime.now().strftime('%Y-%m-%d')}"
    
    # Generate application content (placeholder for a real template system)
    content = f"""
    RENTAL APPLICATION

    Date: {datetime.now().strftime('%Y-%m-%d')}
    
    PROSPECTIVE TENANT INFORMATION:
    Email: {lead.email}
    
    RENTAL INFORMATION:
    {building_info}
    {room_info}
    Planned Move-in Date: {lead.planned_move_in.strftime('%Y-%m-%d') if lead.planned_move_in else 'TBD'}
    
    PERSONAL INFORMATION:
    Full Name: _________________________
    Phone Number: _________________________
    Current Address: _________________________
    
    EMPLOYMENT INFORMATION:
    Current Employer: _________________________
    Position: _________________________
    Monthly Income: _________________________
    
    EMERGENCY CONTACT:
    Name: _________________________
    Relationship: _________________________
    Phone: _________________________
    
    REFERENCES:
    1. _________________________
    2. _________________________
    
    By signing below, I certify that the information provided is true and complete. I authorize verification of this information.
    
    _________________________
    Applicant Signature
    """
    
    return create_document(
        db=db,
        title=title,
        document_type="APPLICATION",
        content=content,
        lead_id=lead_id,
        room_id=room_id,
        building_id=building_id,
        status="DRAFT"
    )