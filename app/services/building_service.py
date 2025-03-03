# app/services/building_service.py
from typing import List, Optional

from sqlalchemy.orm import Session

from ..db import models
from ..models import building as building_models

def create_building(db: Session, building: building_models.BuildingCreate) -> models.Building:
    """
    Creates a new building in the database.
    """
    db_building = models.Building(**building.dict())
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building

def get_building_by_id(db: Session, building_id: str) -> Optional[models.Building]:
    """
    Retrieves a building from the database by its building_id.
    """
    return db.query(models.Building).filter(models.Building.building_id == building_id).first()

def update_building(db: Session, building_id: str, building_update: building_models.BuildingUpdate) -> Optional[models.Building]:
    """
    Updates the details of a building in the database.
    """
    db_building = get_building_by_id(db, building_id)
    if db_building:
        for key, value in building_update.dict(exclude_unset=True).items():
            setattr(db_building, key, value)
        db.commit()
        db.refresh(db_building)
        return db_building
    return None

def delete_building(db: Session, building_id: str) -> bool:
    """
    Deletes a building from the database by its building_id.
    """
    db_building = get_building_by_id(db, building_id)
    if db_building:
        db.delete(db_building)
        db.commit()
        return True
    return False

def get_all_buildings(db: Session) -> List[models.Building]:
    """
    Retrieves all buildings from the database.
    """
    return db.query(models.Building).all()