from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import document_service
from ..db.connection import get_db
from ..models import document as document_models

router = APIRouter()

@router.post("/documents/", response_model=document_models.Document, status_code=201)
def create_document(document: document_models.DocumentCreate, db: Session = Depends(get_db)):
    """
    Create a new document.
    """
    db_document = document_service.create_document(
        db=db,
        title=document.title,
        document_type=document.document_type,
        content=document.content,
        tenant_id=document.tenant_id,
        lead_id=document.lead_id,
        room_id=document.room_id,
        building_id=document.building_id
    )
    return db_document

@router.post("/documents/generate/lease", response_model=document_models.Document, status_code=201)
def generate_lease_document(request: document_models.DocumentGenerationRequest, db: Session = Depends(get_db)):
    """
    Generate a lease document.
    """
    params = request.parameters or {}
    
    if not request.tenant_id or not request.room_id or not request.building_id:
        raise HTTPException(status_code=400, detail="tenant_id, room_id, and building_id are required")
    
    if "lease_start_date" not in params or "lease_end_date" not in params:
        raise HTTPException(status_code=400, detail="lease_start_date and lease_end_date are required in parameters")
    
    if "monthly_rent" not in params or "deposit_amount" not in params:
        raise HTTPException(status_code=400, detail="monthly_rent and deposit_amount are required in parameters")
    
    try:
        lease_start = datetime.strptime(params["lease_start_date"], "%Y-%m-%d")
        lease_end = datetime.strptime(params["lease_end_date"], "%Y-%m-%d")
        monthly_rent = float(params["monthly_rent"])
        deposit_amount = float(params["deposit_amount"])
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter format: {str(e)}")
    
    db_document = document_service.generate_lease_document(
        db=db,
        tenant_id=request.tenant_id,
        room_id=request.room_id,
        building_id=request.building_id,
        lease_start_date=lease_start,
        lease_end_date=lease_end,
        monthly_rent=monthly_rent,
        deposit_amount=deposit_amount
    )
    return db_document

@router.post("/documents/generate/application", response_model=document_models.Document, status_code=201)
def generate_application_document(request: document_models.DocumentGenerationRequest, db: Session = Depends(get_db)):
    """
    Generate an application document.
    """
    if not request.lead_id:
        raise HTTPException(status_code=400, detail="lead_id is required")
    
    db_document = document_service.generate_application_document(
        db=db,
        lead_id=request.lead_id,
        room_id=request.room_id,
        building_id=request.building_id
    )
    return db_document

@router.get("/documents/{document_id}", response_model=document_models.Document)
def read_document(document_id: str, db: Session = Depends(get_db)):
    """
    Get document by ID.
    """
    db_document = document_service.get_document_by_id(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.put("/documents/{document_id}/status", response_model=document_models.Document)
def update_document_status(document_id: str, status: str, db: Session = Depends(get_db)):
    """
    Update document status.
    """
    db_document = document_service.update_document_status(
        db=db,
        document_id=document_id,
        status=status
    )
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.put("/documents/{document_id}/content", response_model=document_models.Document)
def update_document_content(
    document_id: str, 
    update: document_models.DocumentUpdate, 
    db: Session = Depends(get_db)
):
    """
    Update document content.
    """
    db_document = document_service.update_document_content(
        db=db,
        document_id=document_id,
        title=update.title,
        content=update.content
    )
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete document by ID.
    """
    success = document_service.delete_document(db, document_id=document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"ok": True}

@router.get("/tenants/{tenant_id}/documents/", response_model=List[document_models.Document])
def read_tenant_documents(
    tenant_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get documents for a specific tenant.
    """
    documents = document_service.get_tenant_documents(
        db=db,
        tenant_id=tenant_id,
        document_type=document_type,
        status=status
    )
    return documents

@router.get("/leads/{lead_id}/documents/", response_model=List[document_models.Document])
def read_lead_documents(
    lead_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get documents for a specific lead.
    """
    documents = document_service.get_lead_documents(
        db=db,
        lead_id=lead_id,
        document_type=document_type,
        status=status
    )
    return documents

@router.get("/rooms/{room_id}/documents/", response_model=List[document_models.Document])
def read_room_documents(
    room_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get documents for a specific room.
    """
    documents = document_service.get_room_documents(
        db=db,
        room_id=room_id,
        document_type=document_type,
        status=status
    )
    return documents

@router.get("/buildings/{building_id}/documents/", response_model=List[document_models.Document])
def read_building_documents(
    building_id: str,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get documents for a specific building.
    """
    documents = document_service.get_building_documents(
        db=db,
        building_id=building_id,
        document_type=document_type,
        status=status
    )
    return documents