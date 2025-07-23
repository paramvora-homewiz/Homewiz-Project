# app/services/image_service.py
# Uses SQLAlchemy for database + Supabase for storage

import os
import uuid
import json
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from ..db.supabase_storage import get_storage_client
from ..db import models  # Your existing SQLAlchemy models

# Configuration
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
BUCKET_NAME = "building-images"

def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    
    # Check file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: JPEG, PNG, WebP, GIF"
        )
    
    return True

async def upload_building_image(db: Session, building_id: str, file: UploadFile) -> dict:
    """Upload a single building image to Supabase Storage"""
    
    try:
        # Validate file
        validate_image_file(file)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        if not file_extension:
            file_extension = '.jpg'  # Default extension
            
        unique_filename = f"{building_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Read file content
        file_content = await file.read()
        
        # Get Supabase storage client
        storage_client = get_storage_client()
        
        # Upload to Supabase Storage with building_id folder structure
        storage_path = f"{building_id}/{unique_filename}"
        
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
            "original_name": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def upload_multiple_building_images(db: Session, building_id: str, files: List[UploadFile]) -> List[dict]:
    """Upload multiple building images"""
    
    if len(files) > 10:  # Limit number of images
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed at once")
    
    uploaded_images = []
    failed_uploads = []
    
    for file in files:
        try:
            result = await upload_building_image(db, building_id, file)
            uploaded_images.append(result)
        except Exception as e:
            failed_uploads.append({"file": file.filename, "error": str(e)})
            continue
    
    return uploaded_images

def get_building_images(db: Session, building_id: str) -> List[str]:
    """Get all image URLs for a building from SQLAlchemy database"""
    
    try:
        # Query your existing SQLAlchemy Building model
        building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
        
        if building and building.building_images:
            # Handle both JSON string and direct list
            images = building.building_images
            if isinstance(images, str):
                try:
                    return json.loads(images)
                except:
                    return []
            elif isinstance(images, list):
                return images
        return []
        
    except Exception as e:
        print(f"Error getting building images: {str(e)}")
        return []

def update_building_images_in_db(db: Session, building_id: str, image_urls: List[str]) -> bool:
    """Update building record with new image URLs in SQLAlchemy database"""
    
    try:
        # Query your existing SQLAlchemy Building model
        building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
        
        if not building:
            print(f"Building {building_id} not found")
            return False
        
        # Convert list to JSON string for storage
        images_json = json.dumps(image_urls)
        
        # Update the building record
        building.building_images = images_json
        
        # Commit the changes
        db.commit()
        db.refresh(building)
        
        return True
        
    except Exception as e:
        print(f"Failed to update building images in DB: {str(e)}")
        db.rollback()
        return False

def delete_building_image(building_id: str, image_path: str) -> bool:
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

def delete_all_building_images(building_id: str) -> bool:
    """Delete all images for a specific building from storage"""
    
    try:
        storage_client = get_storage_client()
        
        # List all files in the building's folder
        result = storage_client.storage.from_(BUCKET_NAME).list(building_id)
        
        if hasattr(result, 'error') and result.error:
            print(f"Failed to list images for building {building_id}: {result.error}")
            return False
        
        if not result or len(result) == 0:
            return True  # No images to delete
        
        # Create list of file paths to delete
        file_paths = [f"{building_id}/{file['name']}" for file in result]
        
        # Delete all files
        delete_result = storage_client.storage.from_(BUCKET_NAME).remove(file_paths)
        
        if hasattr(delete_result, 'error') and delete_result.error:
            print(f"Failed to delete images: {delete_result.error}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Failed to delete all building images: {str(e)}")
        return False

def get_building_image_count(building_id: str) -> int:
    """Get count of images for a building from storage"""
    
    try:
        storage_client = get_storage_client()
        result = storage_client.storage.from_(BUCKET_NAME).list(building_id)
        
        if hasattr(result, 'error') and result.error:
            return 0
            
        return len(result) if result else 0
        
    except Exception as e:
        print(f"Failed to get image count: {str(e)}")
        return 0