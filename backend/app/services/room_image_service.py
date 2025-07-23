# app/services/room_image_service.py
# Room image service using SQLAlchemy + Supabase Storage

import os
import uuid
import json
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from ..db.supabase_storage import get_storage_client
from ..db import models

# Configuration
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
BUCKET_NAME = "building-images"  # Same bucket as buildings

def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    
    # Check file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: JPEG, PNG, WebP, GIF"
        )
    
    return True

async def upload_room_image(db: Session, building_id: str, room_id: str, file: UploadFile) -> dict:
    """Upload a single room image to Supabase Storage"""
    
    try:
        # Verify room exists and belongs to the building
        room = db.query(models.Room).filter(
            models.Room.room_id == room_id,
            models.Room.building_id == building_id
        ).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found in specified building")
        
        # Validate file
        validate_image_file(file)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        if not file_extension:
            file_extension = '.jpg'  # Default extension
            
        unique_filename = f"{room_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Read file content
        file_content = await file.read()
        
        # Get Supabase storage client
        storage_client = get_storage_client()
        
        # Upload to Supabase Storage with buildings/building_id/rooms/room_id folder structure
        storage_path = f"buildings/{building_id}/rooms/{room_id}/{unique_filename}"
        
        result = storage_client.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Check if upload was successful
        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Upload failed: {result.error}")
        
        # Get public URL
        public_url = storage_client.storage.from_(BUCKET_NAME).get_public_url(storage_path)
        
        return {
            "image_url": public_url,
            "image_path": storage_path,
            "file_name": unique_filename,
            "original_name": file.filename,
            "room_id": room_id,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def upload_multiple_room_images(db: Session, building_id: str, room_id: str, files: List[UploadFile]) -> List[dict]:
    """Upload multiple room images"""
    
    if len(files) > 10:  # Limit number of images
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed at once")
    
    uploaded_images = []
    failed_uploads = []
    
    for file in files:
        try:
            result = await upload_room_image(db, building_id, room_id, file)
            uploaded_images.append(result)
        except Exception as e:
            failed_uploads.append({"file": file.filename, "error": str(e)})
            continue
    
    return uploaded_images

def get_room_images(db: Session, room_id: str) -> List[str]:
    """Get all image URLs for a room from SQLAlchemy database"""
    
    try:
        # Query your existing SQLAlchemy Room model
        room = db.query(models.Room).filter(models.Room.room_id == room_id).first()
        
        if room and hasattr(room, 'room_images') and room.room_images:
            # Handle both JSON string and direct list
            images = room.room_images
            if isinstance(images, str):
                try:
                    return json.loads(images)
                except:
                    return []
            elif isinstance(images, list):
                return images
        return []
        
    except Exception as e:
        print(f"Error getting room images: {str(e)}")
        return []

def update_room_images_in_db(db: Session, room_id: str, image_urls: List[str]) -> bool:
    """Update room record with new image URLs in SQLAlchemy database"""
    
    try:
        # Query your existing SQLAlchemy Room model
        room = db.query(models.Room).filter(models.Room.room_id == room_id).first()
        
        if not room:
            print(f"Room {room_id} not found")
            return False
        
        # Convert list to JSON string for storage
        images_json = json.dumps(image_urls)
        
        # Update the room record - add room_images field if it doesn't exist
        if hasattr(room, 'room_images'):
            room.room_images = images_json
        else:
            # If room_images field doesn't exist in your model, you'll need to add it
            print(f"Warning: room_images field not found in Room model")
            return False
        
        # Commit the changes
        db.commit()
        db.refresh(room)
        
        return True
        
    except Exception as e:
        print(f"Failed to update room images in DB: {str(e)}")
        db.rollback()
        return False

def delete_room_image(building_id: str, room_id: str, image_path: str) -> bool:
    """Delete an image from Supabase Storage"""
    
    try:
        storage_client = get_storage_client()
        result = storage_client.storage.from_(BUCKET_NAME).remove([image_path])
        
        # Check if deletion was successful
        if hasattr(result, 'error') and result.error:
            print(f"Failed to delete image: {result.error}")
            return False
            
        return True
    except Exception as e:
        print(f"Failed to delete image {image_path}: {str(e)}")
        return False

def delete_all_room_images(db: Session, building_id: str, room_id: str) -> bool:
    """Delete all images for a specific room from storage"""
    
    try:
        storage_client = get_storage_client()
        
        # List all files in the room's folder
        folder_path = f"buildings/{building_id}/rooms/{room_id}"
        result = storage_client.storage.from_(BUCKET_NAME).list(folder_path)
        
        if hasattr(result, 'error') and result.error:
            print(f"Failed to list images for room {room_id}: {result.error}")
            return False
        
        if not result or len(result) == 0:
            return True  # No images to delete
        
        # Create list of file paths to delete
        file_paths = [f"{folder_path}/{file['name']}" for file in result]
        
        # Delete all files
        delete_result = storage_client.storage.from_(BUCKET_NAME).remove(file_paths)
        
        if hasattr(delete_result, 'error') and delete_result.error:
            print(f"Failed to delete images: {delete_result.error}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Failed to delete all room images: {str(e)}")
        return False

def get_room_image_count(building_id: str, room_id: str) -> int:
    """Get count of images for a room from storage"""
    
    try:
        storage_client = get_storage_client()
        folder_path = f"buildings/{building_id}/rooms/{room_id}"
        result = storage_client.storage.from_(BUCKET_NAME).list(folder_path)
        
        if hasattr(result, 'error') and result.error:
            return 0
            
        return len(result) if result else 0
        
    except Exception as e:
        print(f"Failed to get image count: {str(e)}")
        return 0

def get_room_with_images(db: Session, room_id: str) -> Optional[dict]:
    """Get room with parsed image URLs"""
    
    try:
        room = db.query(models.Room).filter(models.Room.room_id == room_id).first()
        if not room:
            return None
            
        # Convert SQLAlchemy model to dict (simplified version)
        room_dict = {
            "room_id": room.room_id,
            "room_number": room.room_number,
            "building_id": room.building_id,
            "status": room.status,
            "private_room_rent": room.private_room_rent,
            "bed_count": room.bed_count,
            "bathroom_type": room.bathroom_type,
            "sq_footage": room.sq_footage,
            # Add other fields as needed
        }
        
        # Parse room images
        if hasattr(room, 'room_images') and room.room_images:
            import json
            try:
                room_dict["room_images"] = json.loads(room.room_images)
            except:
                room_dict["room_images"] = []
        else:
            room_dict["room_images"] = []
            
        return room_dict
        
    except Exception as e:
        print(f"Error fetching room with images: {str(e)}")
        return None