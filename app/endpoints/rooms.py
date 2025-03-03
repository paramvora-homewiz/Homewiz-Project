# app/endpoints/rooms.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import room_service
from ..db.connection import get_db
from ..models import room as room_models  # Import Pydantic models

router = APIRouter()

@router.post("/rooms/", response_model=room_models.Room, status_code=201)
def create_room(room: room_models.RoomCreate, db: Session = Depends(get_db)):
    """
    Create a new room.
    """
    db_room = room_service.create_room(db=db, room=room)
    return db_room

@router.get("/rooms/{room_id}", response_model=room_models.Room)
def read_room(room_id: str, db: Session = Depends(get_db)):
    """
    Get room by ID.
    """
    db_room = room_service.get_room_by_id(db, room_id=room_id)
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return db_room

@router.put("/rooms/{room_id}", response_model=room_models.Room)
def update_room(room_id: str, room_update: room_models.RoomUpdate, db: Session = Depends(get_db)):
    """
    Update room by ID.
    """
    db_room = room_service.update_room(db, room_id=room_id, room_update=room_update)
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return db_room

@router.delete("/rooms/{room_id}", status_code=204)
def delete_room(room_id: str, db: Session = Depends(get_db)):
    """
    Delete room by ID.
    """
    db_room = room_service.get_room_by_id(db, room_id=room_id)
    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    room_service.delete_room(db, room_id=room_id)
    return {"ok": True}

@router.get("/rooms/", response_model=List[room_models.Room])
def read_rooms(db: Session = Depends(get_db)):
    """
    Get all rooms.
    """
    rooms_list = room_service.get_all_rooms(db)
    return rooms_list