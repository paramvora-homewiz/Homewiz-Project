# app/endpoints/buildings.py

from typing import List, Optional
from fastapi import UploadFile, File, Form

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..services import building_service
from ..services.image_service import (
    upload_building_image, 
    upload_multiple_building_images,
    delete_building_image,
    delete_all_building_images,
    update_building_images_in_db,
    get_building_images,
    get_building_image_count
)

from ..services.video_service import (
    upload_building_video,
    upload_multiple_building_videos,
    delete_building_video,
    delete_all_building_videos,
    update_building_videos_in_db,
    get_building_videos,
    get_building_video_count,
    get_videos_by_category,
    get_videos_in_category_from_storage,
    get_all_videos_from_storage,
    VIDEO_CATEGORIES
)
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


    # ===== NEW IMAGE MANAGEMENT ENDPOINTS =====

def confirm_building_exists(db: Session, building_id: str) -> bool:
    """Helper function to check if building exists"""
    building = building_service.get_building_by_id(db, building_id)
    return building is not None

@router.post("/buildings/{building_id}/images/upload")
async def upload_building_images(
    building_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload multiple images for a building"""
    
    # Check if building exists first
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    try:
        # Upload images to Supabase Storage
        uploaded_images = await upload_multiple_building_images(db, building_id, files)
        
        if not uploaded_images:
            raise HTTPException(status_code=400, detail="No images were uploaded successfully")
        
        # Get current images from database
        current_images = get_building_images(db, building_id)
        
        # Add new image URLs to existing ones
        new_image_urls = [img["image_url"] for img in uploaded_images]
        all_image_urls = current_images + new_image_urls
        
        # Update building record with new image URLs
        success = update_building_images_in_db(db, building_id, all_image_urls)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building with image URLs")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_images)} images",
            "uploaded_images": uploaded_images,
            "total_images": len(all_image_urls),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/buildings/{building_id}/images/single")
async def upload_single_building_image(
    building_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a single image for a building"""
    
    # Check if building exists
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    try:
        # Upload single image
        uploaded_image = await upload_building_image(db, building_id, file)
        
        # Get current images and add new one
        current_images = get_building_images(db, building_id)
        updated_images = current_images + [uploaded_image["image_url"]]
        
        # Update building record
        success = update_building_images_in_db(db, building_id, updated_images)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building with image URL")
        
        return {
            "message": "Image uploaded successfully",
            "uploaded_image": uploaded_image,
            "total_images": len(updated_images),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/buildings/{building_id}", response_model=building_models.Building)
def read_building(building_id: str, db: Session = Depends(get_db)):
    """
    Get building by ID.
    """
    db_building = building_service.get_building_by_id(db, building_id=building_id)
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    return db_building

@router.get("/buildings/{building_id}/details")
def read_building_with_details(building_id: str, db: Session = Depends(get_db)):
    """Get building with parsed image URLs and other details."""
    db_building = building_service.get_building_with_images(db, building_id=building_id)
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
    """Delete building by ID."""
    db_building = building_service.get_building_by_id(db, building_id=building_id)
    if db_building is None:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Delete all associated images first
    delete_all_building_images(building_id)
    
    # Delete building record
    building_service.delete_building(db, building_id=building_id)
    return {"ok": True}

@router.get("/buildings/", response_model=List[building_models.Building])
def read_buildings(db: Session = Depends(get_db)):
    """
    Get all buildings.
    """
    buildings_list = building_service.get_all_buildings(db)
    return buildings_list

@router.get("/buildings/operator/{operator_id}")
def read_buildings_by_operator(operator_id: int, db: Session = Depends(get_db)):
    """Get all buildings managed by a specific operator."""
    buildings_list = building_service.get_buildings_by_operator(db, operator_id=operator_id)
    return buildings_list

@router.get("/buildings/available/")
def read_available_buildings(db: Session = Depends(get_db)):
    """Get all available buildings."""
    buildings_list = building_service.get_available_buildings(db)
    return buildings_list

@router.get("/buildings/search/{search_term}")
def search_buildings(search_term: str, db: Session = Depends(get_db)):
    """Search buildings by name, address, or area."""
    buildings_list = building_service.search_buildings(db, search_term=search_term)
    return buildings_list
    
@router.get("/buildings/{building_id}/images")
def get_building_images_endpoint(building_id: str, db: Session = Depends(get_db)):
    """Get all images for a building"""
    
    try:
        images = get_building_images(db, building_id)
        storage_count = get_building_image_count(building_id)
        
        return {
            "building_id": building_id,
            "images": images,
            "total_count": len(images),
            "storage_count": storage_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buildings/{building_id}/images")
async def delete_building_image_endpoint(
    building_id: str,
    image_url: str = Form(...),
    db: Session = Depends(get_db)
):
    """Delete a specific image from a building"""
    
    try:
        # Get current images
        current_images = get_building_images(db, building_id)
        
        if image_url not in current_images:
            raise HTTPException(status_code=404, detail="Image not found for this building")
        
        # Extract storage path from URL
        if f'building-images/{building_id}/' in image_url:
            # Extract just the building_id/filename part
            image_path = image_url.split(f'building-images/')[-1]
        else:
            raise HTTPException(status_code=400, detail="Invalid image URL format")
        
        # Delete from Supabase storage
        deleted = delete_building_image(building_id, image_path)
        
        if not deleted:
            print(f"Warning: Could not delete image from storage: {image_path}")
            # Continue anyway to remove from database
        
        # Remove from building record
        updated_images = [img for img in current_images if img != image_url]
        success = update_building_images_in_db(db, building_id, updated_images)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building record")
        
        return {
            "message": "Image deleted successfully",
            "remaining_images": len(updated_images),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buildings/{building_id}/images/all")
async def delete_all_building_images_endpoint(
    building_id: str,
    db: Session = Depends(get_db)
):
    """Delete ALL images for a building"""
    
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    try:
        # Delete all images from storage
        deleted = delete_all_building_images(building_id)
        
        if not deleted:
            print(f"Warning: Could not delete all images from storage for building {building_id}")
        
        # Clear building_images field in database
        success = update_building_images_in_db(db, building_id, [])
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building record")
        
        return {
            "message": f"All images deleted for building {building_id}",
            "remaining_images": 0,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/buildings/{building_id}/images/reorder")
async def reorder_building_images(
    building_id: str,
    image_urls: List[str],
    db: Session = Depends(get_db)
):
    """Reorder building images"""
    
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    try:
        # Verify all provided URLs belong to this building
        current_images = get_building_images(db, building_id)
        
        for url in image_urls:
            if url not in current_images:
                raise HTTPException(status_code=400, detail=f"Image URL not found: {url}")
        
        # Update with new order
        success = update_building_images_in_db(db, building_id, image_urls)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reorder images")
        
        return {
            "message": "Images reordered successfully",
            "new_order": image_urls,
            "total_images": len(image_urls),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

    # ===== VIDEO MANAGEMENT ENDPOINTS =====

@router.post("/buildings/{building_id}/videos/upload")
async def upload_building_videos(
    building_id: str,
    files: List[UploadFile] = File(...),
    video_categories: Optional[List[str]] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload multiple videos for a building"""
    
    # Check if building exists first
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    try:
        # Parse video categories if provided as form data
        if video_categories and isinstance(video_categories[0], str) and ',' in video_categories[0]:
            video_categories = video_categories[0].split(',')
        
        # Validate categories
        if video_categories:
            for category in video_categories:
                if category not in VIDEO_CATEGORIES:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Invalid category: {category}. Allowed: {', '.join(VIDEO_CATEGORIES)}"
                    )
        
        # Upload videos to Supabase Storage
        uploaded_videos = await upload_multiple_building_videos(db, building_id, files, video_categories)
        
        if not uploaded_videos:
            raise HTTPException(status_code=400, detail="No videos were uploaded successfully")
        
        # Get current videos from database
        current_videos = get_building_videos(db, building_id)
        
        # Add new video data to existing ones
        all_videos = current_videos + uploaded_videos
        
        # Update building record with new video data
        success = update_building_videos_in_db(db, building_id, all_videos)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building with video data")
        
        return {
            "message": f"Successfully uploaded {len(uploaded_videos)} videos",
            "uploaded_videos": uploaded_videos,
            "total_videos": len(all_videos),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/buildings/{building_id}/videos/single")
async def upload_single_building_video(
    building_id: str,
    file: UploadFile = File(...),
    video_category: str = Form("general"),
    db: Session = Depends(get_db)
):
    """Upload a single video for a building"""
    
    # Check if building exists
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Validate category
    if video_category not in VIDEO_CATEGORIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category: {video_category}. Allowed: {', '.join(VIDEO_CATEGORIES)}"
        )
    
    try:
        # Upload single video
        uploaded_video = await upload_building_video(db, building_id, file, video_category)
        
        # Get current videos and add new one
        current_videos = get_building_videos(db, building_id)
        updated_videos = current_videos + [uploaded_video]
        
        # Update building record
        success = update_building_videos_in_db(db, building_id, updated_videos)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building with video data")
        
        return {
            "message": "Video uploaded successfully",
            "uploaded_video": uploaded_video,
            "total_videos": len(updated_videos),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/buildings/{building_id}/videos")
def get_building_videos_endpoint(building_id: str, db: Session = Depends(get_db)):
    """Get all videos for a building"""
    
    try:
        videos = get_building_videos(db, building_id)
        storage_count = get_building_video_count(building_id)
        
        return {
            "building_id": building_id,
            "videos": videos,
            "total_count": len(videos),
            "storage_count": storage_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/buildings/{building_id}/videos/category/{video_category}")
def get_building_video_by_category(
    building_id: str, 
    video_category: str,
    db: Session = Depends(get_db)
):
    """Get videos by category for a building"""
    
    # Validate category
    if video_category not in VIDEO_CATEGORIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category: {video_category}. Allowed: {', '.join(VIDEO_CATEGORIES)}"
        )
    
    try:
        videos = get_videos_by_category(db, building_id, video_category)
        
        # Also get actual files from storage for this category
        storage_files = get_videos_in_category_from_storage(building_id, video_category)
        
        return {
            "building_id": building_id,
            "category": video_category,
            "videos": videos,
            "storage_files": storage_files,
            "count": len(videos)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/buildings/{building_id}/videos/categories")
def get_building_videos_by_categories(
    building_id: str,
    db: Session = Depends(get_db)
):
    """Get all videos organized by categories"""
    
    try:
        all_videos = get_building_videos(db, building_id)
        
        # Organize videos by category
        videos_by_category = {category: [] for category in VIDEO_CATEGORIES}
        
        for video in all_videos:
            category = video.get('video_category', 'general')
            if category in videos_by_category:
                videos_by_category[category].append(video)
        
        # Get storage counts for each category
        storage_data = get_all_videos_from_storage(building_id)
        storage_counts = {category: len(files) for category, files in storage_data.items()}
        
        return {
            "building_id": building_id,
            "videos_by_category": videos_by_category,
            "storage_counts": storage_counts,
            "total_videos": len(all_videos)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buildings/{building_id}/videos")
async def delete_building_video_endpoint(
    building_id: str,
    video_url: str = Form(...),
    db: Session = Depends(get_db)
):
    """Delete a specific video from a building"""
    
    try:
        # Get current videos
        current_videos = get_building_videos(db, building_id)
        
        # Find the video to delete
        video_to_delete = None
        for video in current_videos:
            if video.get('video_url') == video_url:
                video_to_delete = video
                break
        
        if not video_to_delete:
            raise HTTPException(status_code=404, detail="Video not found for this building")
        
        # Extract storage path from video data
        video_path = video_to_delete.get('video_path')
        
        if not video_path:
            # Try to extract from URL if path not stored
            # The URL structure should contain the full path after the bucket name
            if f'building-images/' in video_url:
                video_path = video_url.split(f'building-images/')[-1]
            else:
                raise HTTPException(status_code=400, detail="Invalid video URL format")
        
        # Delete from Supabase storage
        deleted = delete_building_video(building_id, video_path)
        
        if not deleted:
            print(f"Warning: Could not delete video from storage: {video_path}")
            # Continue anyway to remove from database
        
        # Remove from building record
        updated_videos = [video for video in current_videos if video.get('video_url') != video_url]
        success = update_building_videos_in_db(db, building_id, updated_videos)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building record")
        
        return {
            "message": "Video deleted successfully",
            "remaining_videos": len(updated_videos),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/buildings/{building_id}/videos/all")
async def delete_all_building_videos_endpoint(
    building_id: str,
    db: Session = Depends(get_db)
):
    """Delete ALL videos for a building"""
    
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    try:
        # Delete all videos from storage
        deleted = delete_all_building_videos(building_id)
        
        if not deleted:
            print(f"Warning: Could not delete all videos from storage for building {building_id}")
        
        # Clear building_videos field in database
        success = update_building_videos_in_db(db, building_id, [])
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update building record")
        
        return {
            "message": f"All videos deleted for building {building_id}",
            "remaining_videos": 0,
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/buildings/{building_id}/videos/reorder")
async def reorder_building_videos(
    building_id: str,
    video_data: List[dict],
    db: Session = Depends(get_db)
):
    """Reorder building videos"""
    
    if not confirm_building_exists(db, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
    
    try:
        # Verify all provided videos belong to this building
        current_videos = get_building_videos(db, building_id)
        current_urls = {video.get('video_url') for video in current_videos}
        
        for video in video_data:
            if video.get('video_url') not in current_urls:
                raise HTTPException(status_code=400, detail=f"Video URL not found: {video.get('video_url')}")
        
        # Update with new order
        success = update_building_videos_in_db(db, building_id, video_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reorder videos")
        
        return {
            "message": "Videos reordered successfully",
            "new_order": video_data,
            "total_videos": len(video_data),
            "building_id": building_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/buildings/{building_id}/media/summary")
def get_building_media_summary(
    building_id: str,
    db: Session = Depends(get_db)
):
    """Get summary of all media (images and videos) for a building"""
    
    try:
        images = get_building_images(db, building_id)
        videos = get_building_videos(db, building_id)
        
        return {
            "building_id": building_id,
            "media_summary": {
                "total_images": len(images),
                "total_videos": len(videos),
                "total_media": len(images) + len(videos),
                "storage_usage": {
                    "images_count": get_building_image_count(building_id),
                    "videos_count": get_building_video_count(building_id)
                }
            },
            "images": images,
            "videos": videos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))