# app/endpoints/rooms.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from ..services import room_service
from ..services.room_image_service import (
    upload_room_image, 
    upload_multiple_room_images,
    delete_room_image,
    delete_all_room_images,
    update_room_images_in_db,
    get_room_images,
    get_room_image_count
)
from ..db.connection import get_db
from ..models import room as room_models  # Import Pydantic models

router = APIRouter()

# ===== EXISTING ROOM CRUD ENDPOINTS (Unchanged) =====

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

@router.get("/rooms/{room_id}/details")
def read_room_with_details(room_id: str, db: Session = Depends(get_db)):
    """
    Get room with parsed image URLs and other details.
    """
    db_room = room_service.get_room_with_images(db, room_id=room_id)
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
    
    # Get building_id for image cleanup
    building_id = db_room.building_id
    
    # Delete all associated images first
    delete_all_room_images(db, building_id, room_id)
    
    # Delete room record
    room_service.delete_room(db, room_id=room_id)
    return {"ok": True}

@router.get("/rooms/", response_model=List[room_models.Room])
def read_rooms(db: Session = Depends(get_db)):
    """
    Get all rooms.
    """
    rooms_list = room_service.get_all_rooms(db)
    return rooms_list

# ===== ADDITIONAL ROOM ENDPOINTS =====

@router.get("/rooms/building/{building_id}")
def read_rooms_by_building(building_id: str, db: Session = Depends(get_db)):
    """Get all rooms in a specific building."""
    rooms_list = room_service.get_rooms_by_building(db, building_id=building_id)
    return rooms_list

@router.get("/rooms/available/")
def read_available_rooms(building_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Get all available rooms, optionally filtered by building."""
    rooms_list = room_service.get_available_rooms(db, building_id=building_id)
    return rooms_list

@router.post("/rooms/search/")
def search_rooms(filters: dict, db: Session = Depends(get_db)):
    """Search rooms based on various criteria."""
    rooms_list = room_service.search_rooms(db, filters=filters)
    return rooms_list

# ===== NEW ROOM IMAGE MANAGEMENT ENDPOINTS =====

@router.post("/buildings/{building_id}/rooms/{room_id}/images/upload")
async def upload_room_images(
    building_id: str,
    room_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload multiple images for a room in a specific building"""
    
    # Check if room exists and belongs to building
    if not confirm_room_exists_in_building(db, building_id, room_id):
        raise HTTPException(status_code=404, detail="Room not found in specified building")
    
    try:
        # Upload images to Supabase Storage
        uploaded_images = await upload_multiple_room_images(db, building_id, room_id, files)
        
        if not uploaded_images:
            raise HTTPException(status_code=400, detail="No images were uploaded successfully")
        
        # Get current images from database
        current_images = get_room_images(db, room_id)
        
        # Add new image URLs to existing ones
        new_image_urls = [img["image_url"] for img in uploaded_images]
        all_image_urls = current_images + new_image_urls
        
        # Update room record with new image URLs
        success = update_room_images_in_db(db, room_id, all_image_urls)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update room with image URLs")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_images)} images",
            "uploaded_images": uploaded_images,
            "total_images": len(all_image_urls),
            "room_id": room_id,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/buildings/{building_id}/rooms/{room_id}/images/single")
async def upload_single_room_image(
    building_id: str,
    room_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a single image for a room in a specific building"""
    
    # Check if room exists and belongs to building
    if not confirm_room_exists_in_building(db, building_id, room_id):
        raise HTTPException(status_code=404, detail="Room not found in specified building")
    
    try:
        # Upload single image
        uploaded_image = await upload_room_image(db, building_id, room_id, file)
        
        # Get current images and add new one
        current_images = get_room_images(db, room_id)
        updated_images = current_images + [uploaded_image["image_url"]]
        
        # Update room record
        success = update_room_images_in_db(db, room_id, updated_images)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update room with image URL")
        
        return {
            "message": "Image uploaded successfully",
            "uploaded_image": uploaded_image,
            "total_images": len(updated_images),
            "room_id": room_id,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/buildings/{building_id}/rooms/{room_id}/images")
def get_room_images_endpoint(building_id: str, room_id: str, db: Session = Depends(get_db)):
    """Get all images for a room in a specific building"""
    
    # Check if room exists and belongs to building
    if not confirm_room_exists_in_building(db, building_id, room_id):
        raise HTTPException(status_code=404, detail="Room not found in specified building")
    
    try:
        images = get_room_images(db, room_id)
        storage_count = get_room_image_count(building_id, room_id)
        
        return {
            "room_id": room_id,
            "building_id": building_id,
            "images": images,
            "total_count": len(images),
            "storage_count": storage_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buildings/{building_id}/rooms/{room_id}/images")
async def delete_room_image_endpoint(
    building_id: str,
    room_id: str,
    image_url: str = Form(...),
    db: Session = Depends(get_db)
):
    """Delete a specific image from a room in a specific building"""
    
    # Check if room exists and belongs to building
    if not confirm_room_exists_in_building(db, building_id, room_id):
        raise HTTPException(status_code=404, detail="Room not found in specified building")
    
    try:
        # Get current images
        current_images = get_room_images(db, room_id)
        
        if image_url not in current_images:
            raise HTTPException(status_code=404, detail="Image not found for this room")
        
        # Extract storage path from URL
        # URL format: https://xxx.supabase.co/storage/v1/object/public/building-images/buildings/BLD001/rooms/ROOM001/filename.jpg
        if f'/buildings/{building_id}/rooms/{room_id}/' in image_url:
            # Extract the path after building-images/
            image_path = image_url.split('building-images/')[-1]
        else:
            raise HTTPException(status_code=400, detail="Invalid image URL format")
        
        # Delete from Supabase storage
        deleted = delete_room_image(building_id, room_id, image_path)
        
        if not deleted:
            print(f"Warning: Could not delete image from storage: {image_path}")
            # Continue anyway to remove from database
        
        # Remove from room record
        updated_images = [img for img in current_images if img != image_url]
        success = update_room_images_in_db(db, room_id, updated_images)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update room record")
        
        return {
            "message": "Image deleted successfully",
            "remaining_images": len(updated_images),
            "room_id": room_id,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buildings/{building_id}/rooms/{room_id}/images/all")
async def delete_all_room_images_endpoint(
    building_id: str,
    room_id: str,
    db: Session = Depends(get_db)
):
    """Delete ALL images for a room in a specific building"""
    
    if not confirm_room_exists_in_building(db, building_id, room_id):
        raise HTTPException(status_code=404, detail="Room not found in specified building")
    
    try:
        # Delete all images from storage
        deleted = delete_all_room_images(db, building_id, room_id)
        
        if not deleted:
            print(f"Warning: Could not delete all images from storage for room {room_id}")
        
        # Clear room_images field in database
        success = update_room_images_in_db(db, room_id, [])
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update room record")
        
        return {
            "message": f"All images deleted for room {room_id}",
            "remaining_images": 0,
            "room_id": room_id,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/buildings/{building_id}/rooms/{room_id}/images/reorder")
async def reorder_room_images(
    building_id: str,
    room_id: str,
    image_urls: List[str],
    db: Session = Depends(get_db)
):
    """Reorder room images"""
    
    if not confirm_room_exists_in_building(db, building_id, room_id):
        raise HTTPException(status_code=404, detail="Room not found in specified building")
    
    try:
        # Verify all provided URLs belong to this room
        current_images = get_room_images(db, room_id)
        
        for url in image_urls:
            if url not in current_images:
                raise HTTPException(status_code=400, detail=f"Image URL not found: {url}")
        
        # Update with new order
        success = update_room_images_in_db(db, room_id, image_urls)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reorder images")
        
        return {
            "message": "Images reordered successfully",
            "new_order": image_urls,
            "total_images": len(image_urls),
            "room_id": room_id,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== HELPER FUNCTIONS =====

def confirm_room_exists_in_building(db: Session, building_id: str, room_id: str) -> bool:
    """Helper function to check if room exists in specified building"""
    from ..db import models
    room = db.query(models.Room).filter(
        models.Room.room_id == room_id,
        models.Room.building_id == building_id
    ).first()
    return room is not None