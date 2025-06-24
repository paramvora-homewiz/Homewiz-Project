# app/endpoints/buildings.py

from typing import List
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