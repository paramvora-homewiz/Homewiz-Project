# app/services/video_service.py
# Uses SQLAlchemy for database + Supabase for storage

import os
import uuid
import json
from typing import List, Optional, Dict
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from ..db.supabase_storage import get_storage_client
from ..db import models  # Your existing SQLAlchemy models

# Configuration
ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo",
    "video/x-ms-wmv", "video/webm", "video/ogg"
}
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB (adjust based on your needs)
VIDEO_BUCKET_NAME = "building-images"  # Using same bucket as images

# Define standard video categories based on your storage structure
VIDEO_CATEGORIES = [
    "amenities",
    "kitchen_bathrooms",
    "outside",
    "general"  # fallback category
]

def validate_video_file(file: UploadFile) -> bool:
    """Validate uploaded video file"""
    
    # Check file type
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: MP4, MPEG, MOV, AVI, WMV, WebM, OGG"
        )
    
    return True

async def upload_building_video(db: Session, building_id: str, file: UploadFile, video_category: str = "general") -> dict:
    """Upload a single building video to Supabase Storage"""
    
    try:
        # Validate file
        validate_video_file(file)
        
        # Validate category
        if video_category not in VIDEO_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category: {video_category}. Allowed: {', '.join(VIDEO_CATEGORIES)}"
            )
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        if not file_extension:
            file_extension = '.mp4'  # Default extension
            
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Read file content
        file_content = await file.read()
        
        # Check file size
        if len(file_content) > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size: {MAX_VIDEO_SIZE // (1024*1024)}MB"
            )
        
        # Get Supabase storage client
        storage_client = get_storage_client()
        
        # Upload to Supabase Storage with building_id/videos/category folder structure
        storage_path = f"{building_id}/videos/{video_category}/{unique_filename}"
        
        result = storage_client.storage.from_(VIDEO_BUCKET_NAME).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )
        
        # Check if upload was successful
        if hasattr(result, 'error') and result.error:
            raise HTTPException(status_code=500, detail=f"Upload failed: {result.error}")
        
        # Get public URL
        public_url = storage_client.storage.from_(VIDEO_BUCKET_NAME).get_public_url(storage_path)
        
        return {
            "video_url": public_url,
            "video_path": storage_path,
            "file_name": unique_filename,
            "original_name": file.filename,
            "video_category": video_category,
            "file_size": len(file_content),
            "content_type": file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def upload_multiple_building_videos(
    db: Session, 
    building_id: str, 
    files: List[UploadFile],
    video_categories: Optional[List[str]] = None
) -> List[dict]:
    """Upload multiple building videos"""
    
    if len(files) > 5:  # Limit number of videos (adjust as needed)
        raise HTTPException(status_code=400, detail="Maximum 5 videos allowed at once")
    
    # If video_categories not provided, default to "general" for all
    if not video_categories:
        video_categories = ["general"] * len(files)
    elif len(video_categories) != len(files):
        raise HTTPException(status_code=400, detail="Number of video categories must match number of files")
    
    uploaded_videos = []
    failed_uploads = []
    
    for file, video_category in zip(files, video_categories):
        try:
            result = await upload_building_video(db, building_id, file, video_category)
            uploaded_videos.append(result)
        except Exception as e:
            failed_uploads.append({"file": file.filename, "error": str(e)})
            continue
    
    if failed_uploads:
        # Log failed uploads but continue with successful ones
        print(f"Failed uploads: {failed_uploads}")
    
    return uploaded_videos

def get_building_videos(db: Session, building_id: str) -> List[dict]:
    """Get all video URLs and metadata for a building from SQLAlchemy database"""
    
    try:
        # Query your existing SQLAlchemy Building model
        building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
        
        if building and building.building_videos:
            # Handle both JSON string and direct list
            videos = building.building_videos
            if isinstance(videos, str):
                try:
                    return json.loads(videos)
                except:
                    return []
            elif isinstance(videos, list):
                return videos
        return []
        
    except Exception as e:
        print(f"Error getting building videos: {str(e)}")
        return []

def update_building_videos_in_db(db: Session, building_id: str, video_data: List[dict]) -> bool:
    """Update building record with new video data in SQLAlchemy database"""
    
    try:
        # Query your existing SQLAlchemy Building model
        building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
        
        if not building:
            print(f"Building {building_id} not found")
            return False
        
        # Convert list to JSON string for storage
        videos_json = json.dumps(video_data)
        
        # Update the building record
        building.building_videos = videos_json
        
        # Commit the changes
        db.commit()
        db.refresh(building)
        
        return True
        
    except Exception as e:
        print(f"Failed to update building videos in DB: {str(e)}")
        db.rollback()
        return False

def delete_building_video(building_id: str, video_path: str) -> bool:
    """Delete a video from Supabase Storage"""
    
    try:
        storage_client = get_storage_client()
        result = storage_client.storage.from_(VIDEO_BUCKET_NAME).remove([video_path])
        
        # Check if deletion was successful
        if hasattr(result, 'error') and result.error:
            print(f"Failed to delete video: {result.error}")
            return False
            
        return True
    except Exception as e:
        print(f"Failed to delete video {video_path}: {str(e)}")
        return False

def delete_all_building_videos(building_id: str) -> bool:
    """Delete all videos for a specific building from storage"""
    
    try:
        storage_client = get_storage_client()
        
        # Delete videos from each category
        for category in VIDEO_CATEGORIES:
            try:
                # List files in this category
                result = storage_client.storage.from_(VIDEO_BUCKET_NAME).list(f"{building_id}/videos/{category}")
                
                if result and not hasattr(result, 'error'):
                    # Get file paths
                    file_paths = [f"{building_id}/videos/{category}/{file['name']}" 
                                for file in result if file.get('name')]
                    
                    if file_paths:
                        # Delete files
                        delete_result = storage_client.storage.from_(VIDEO_BUCKET_NAME).remove(file_paths)
                        
                        if hasattr(delete_result, 'error') and delete_result.error:
                            print(f"Failed to delete videos in {category}: {delete_result.error}")
                            
            except Exception as e:
                print(f"Error processing category {category}: {str(e)}")
                continue
        
        return True
        
    except Exception as e:
        print(f"Failed to delete all building videos: {str(e)}")
        return False

def get_building_video_count(building_id: str) -> int:
    """Get count of videos for a building from storage"""
    
    try:
        storage_client = get_storage_client()
        count = 0
        
        # Count files in each category
        for category in VIDEO_CATEGORIES:
            try:
                result = storage_client.storage.from_(VIDEO_BUCKET_NAME).list(f"{building_id}/videos/{category}")
                
                if result and not hasattr(result, 'error'):
                    # Count only actual files
                    count += len([f for f in result if f.get('name')])
                    
            except Exception as e:
                print(f"Error counting videos in {category}: {str(e)}")
                continue
        
        return count
        
    except Exception as e:
        print(f"Failed to get video count: {str(e)}")
        return 0

def get_videos_by_category(db: Session, building_id: str, video_category: str) -> List[dict]:
    """Get videos by category for a building"""
    
    try:
        videos = get_building_videos(db, building_id)
        
        return [video for video in videos if video.get('video_category') == video_category]
        
    except Exception as e:
        print(f"Error getting videos by category: {str(e)}")
        return []

def get_videos_in_category_from_storage(building_id: str, category: str) -> List[str]:
    """Get all video filenames in a specific category from storage"""
    
    try:
        storage_client = get_storage_client()
        result = storage_client.storage.from_(VIDEO_BUCKET_NAME).list(f"{building_id}/videos/{category}")
        
        if hasattr(result, 'error') and result.error:
            return []
        
        if not result:
            return []
        
        # Return only actual files
        return [file['name'] for file in result if file.get('name')]
        
    except Exception as e:
        print(f"Error getting videos in category: {str(e)}")
        return []

def get_all_videos_from_storage(building_id: str) -> Dict[str, List[str]]:
    """Get all videos organized by category from storage"""
    
    videos_by_category = {}
    
    for category in VIDEO_CATEGORIES:
        videos_by_category[category] = get_videos_in_category_from_storage(building_id, category)
    
    return videos_by_category