# app/services/room_service.py
from typing import List, Optional

from sqlalchemy.orm import Session

from ..db import models
from ..models import room as room_models

def create_room(db: Session, room: room_models.RoomCreate) -> models.Room:
    """
    Creates a new room in the database.
    """
    db_room = models.Room(**room.dict())
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_room_by_id(db: Session, room_id: str) -> Optional[models.Room]:
    """
    Retrieves a room from the database by its room_id.
    """
    return db.query(models.Room).filter(models.Room.room_id == room_id).first()

def update_room(db: Session, room_id: str, room_update: room_models.RoomUpdate) -> Optional[models.Room]:
    """
    Updates the details of a room in the database.
    """
    db_room = get_room_by_id(db, room_id)
    if db_room:
        for key, value in room_update.dict(exclude_unset=True).items():
            setattr(db_room, key, value)
        db.commit()
        db.refresh(db_room)
        return db_room
    return None

def delete_room(db: Session, room_id: str) -> bool:
    """
    Deletes a room from the database by its room_id.
    """
    db_room = get_room_by_id(db, room_id)
    if db_room:
        db.delete(db_room)
        db.commit()
        return True
    return False

def get_all_rooms(db: Session) -> List[models.Room]:
    """
    Retrieves all rooms from the database.
    """
    return db.query(models.Room).all()