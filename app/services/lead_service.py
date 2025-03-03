import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from ..db import models


def get_lead_by_id(db: Session, lead_id: str) -> Optional[models.Lead]:
    """
    Retrieves a lead from the database by their lead_id.
    """
    return db.query(models.Lead).filter(models.Lead.lead_id == lead_id).first()


def get_lead_by_email(db: Session, email: str) -> Optional[models.Lead]:
    """
    Retrieves a lead from the database by their email address.
    """
    return db.query(models.Lead).filter(models.Lead.email == email).first()


def create_lead(db: Session, email: str, status: str = "EXPLORING") -> models.Lead:
    """
    Creates a new lead in the database.
    """
    lead_id = f"LEAD_{uuid.uuid4()}"
    db_lead = models.Lead(lead_id=lead_id, email=email, status=status) # Include lead_id when creating Lead object
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


def update_lead_status(db: Session, lead_id: str, status: str) -> Optional[models.Lead]:
    """
    Updates the status of a lead in the database.
    """
    db_lead = get_lead_by_id(db, lead_id)
    if db_lead:
        db_lead.status = status
        db.commit()
        db.refresh(db_lead)
        return db_lead
    return None  # Lead not found


def update_lead_wishlist(db: Session, lead_id: str, wishlist: List[str]) -> Optional[models.Lead]:
    """
    Updates the wishlist of a lead in the database.
    Assumes wishlist is a list of room_ids.
    """
    db_lead = get_lead_by_id(db, lead_id)
    if db_lead:
        db_lead.rooms_interested = str(wishlist)  # Store wishlist as string representation of list
        db.commit()
        db.refresh(db_lead)
        return db_lead
    return None  # Lead not found


def get_all_leads(db: Session) -> List[models.Lead]:
    """
    Retrieves all leads from the database.
    """
    return db.query(models.Lead).all()