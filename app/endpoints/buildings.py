# app/endpoints/buildings.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import building_service
from ..db.connection import get_db
from ..models import building as building_models  # Import Pydantic models

router = APIRouter()

@router.post("/buildings/", response_model=building_models.Building, status_code=201)
def create_building(building: building_models.BuildingCreate, db: Session = Depends(get_db)):
    """
    Create a new building.
    """
    db_building = building_service.create_building(db=db, building=building)
    return db_building

@router.get("/buildings/{building_id}", response_model=building_models.Building)
def read_building(building_id: str, db: Session = Depends(get_db)):
    """
    Get building by ID.
    """
    db_building = building_service.get_building_by_id(db, building_id=building_id)
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return db_building

@router.put("/buildings/{building_id}", response_model=building_models.Building)
def update_building(building_id: str, building_update: building_models.BuildingUpdate, db: Session = Depends(get_db)):
    """
    Update building by ID.
    """
    db_building = building_service.update_building(db, building_id=building_id, building_update=building_update)
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return db_building

@router.delete("/buildings/{building_id}", status_code=204)
def delete_building(building_id: str, db: Session = Depends(get_db)):
    """
    Delete building by ID.
    """
    db_building = building_service.get_building_by_id(db, building_id=building_id)
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    building_service.delete_building(db, building_id=building_id)
    return {"ok": True}

@router.get("/buildings/", response_model=List[building_models.Building])
def read_buildings(db: Session = Depends(get_db)):
    """
    Get all buildings.
    """
    buildings_list = building_service.get_all_buildings(db)
    return buildings_list