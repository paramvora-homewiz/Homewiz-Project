from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import lead_service
from ..db.connection import get_db
from ..models import lead as lead_models  # Import Pydantic models
# from app.db import models as db_models # If you need to refer to SQLAlchemy models directly in endpoints (less common)


router = APIRouter()


@router.post("/leads/", response_model=lead_models.Lead, status_code=201)
def create_lead(lead: lead_models.LeadCreate, db: Session = Depends(get_db)):
    """
    Create a new lead.
    """
    db_lead = lead_service.get_lead_by_email(db, email=lead.email)
    if db_lead:
        raise HTTPException(status_code=400, detail="Lead with this email already registered")
    
    created_db_lead = lead_service.create_lead(db=db, email=lead.email, status=lead.status) # Capture returned db_lead

    # Manual datetime to string conversion before returning (for POST)
    created_db_lead.created_at = created_db_lead.created_at.isoformat() if created_db_lead.created_at else None
    created_db_lead.last_modified = created_db_lead.last_modified.isoformat() if created_db_lead.last_modified else None

    return created_db_lead # Return the modified db_lead


@router.get("/leads/{lead_id}", response_model=lead_models.Lead)
def read_lead(lead_id: str, db: Session = Depends(get_db)):
    """
    Get lead by ID.
    """
    db_lead = lead_service.get_lead_by_id(db, lead_id=lead_id)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Manual datetime to string conversion before returning (for GET by ID)
    db_lead.created_at = db_lead.created_at.isoformat() if db_lead.created_at else None
    db_lead.last_modified = db_lead.last_modified.isoformat() if db_lead.last_modified else None

    return db_lead


@router.put("/leads/{lead_id}/status", response_model=lead_models.Lead)
def update_lead_status(lead_id: str, status_update: lead_models.LeadUpdateStatus, db: Session = Depends(get_db)):
    """
    Update lead status.
    """
    db_lead = lead_service.update_lead_status(db, lead_id=lead_id, status=status_update.status)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Manual datetime to string conversion before returning (for PUT status - just in case)
    db_lead.created_at = db_lead.created_at.isoformat() if db_lead.created_at else None
    db_lead.last_modified = db_lead.last_modified.isoformat() if db_lead.last_modified else None

    return db_lead


@router.put("/leads/{lead_id}/wishlist", response_model=lead_models.Lead)
def update_lead_wishlist(lead_id: str, wishlist_update: lead_models.LeadUpdateWishlist, db: Session = Depends(get_db)):
    """
    Update lead wishlist.
    """
    db_lead = lead_service.update_lead_wishlist(db, lead_id=lead_id, wishlist=wishlist_update.wishlist)
    if db_lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Manual datetime to string conversion before returning (for PUT wishlist - just in case)
    db_lead.created_at = db_lead.created_at.isoformat() if db_lead.created_at else None
    db_lead.last_modified = db_lead.last_modified.isoformat() if db_lead.last_modified else None

    return db_lead


@router.get("/leads/", response_model=List[lead_models.Lead])
def read_leads(db: Session = Depends(get_db)):
    """
    Get all leads.
    """
    leads_list = lead_service.get_all_leads(db)

    # Manual datetime to string conversion for each lead in the list (for GET all)
    for db_lead in leads_list:
        db_lead.created_at = db_lead.created_at.isoformat() if db_lead.created_at else None
        db_lead.last_modified = db_lead.last_modified.isoformat() if db_lead.last_modified else None

    return leads_list