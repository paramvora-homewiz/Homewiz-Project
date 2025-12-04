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



def get_building_with_images(db: Session, building_id: str):
    """
    Retrieves a building with parsed image URLs
    """
    try:
        building = get_building_by_id(db, building_id)
        if not building:
            return None
            
        # Convert SQLAlchemy model to dict
        building_dict = {
            "building_id": building.building_id,
            "building_name": building.building_name,
            "full_address": building.full_address,
            "operator_id": building.operator_id,
            "available": building.available,
            "street": building.street,
            "area": building.area,
            "city": building.city,
            "state": building.state,
            "zip": building.zip,
            "floors": building.floors,
            "total_rooms": building.total_rooms,
            "total_bathrooms": building.total_bathrooms,
            "bathrooms_on_each_floor": building.bathrooms_on_each_floor,
            "common_kitchen": building.common_kitchen,
            "min_lease_term": building.min_lease_term,
            "pref_min_lease_term": building.pref_min_lease_term,
            "wifi_included": building.wifi_included,
            "laundry_onsite": building.laundry_onsite,
            "common_area": building.common_area,
            "secure_access": building.secure_access,
            "bike_storage": building.bike_storage,
            "rooftop_access": building.rooftop_access,
            "pet_friendly": building.pet_friendly,
            "cleaning_common_spaces": building.cleaning_common_spaces,
            "utilities_included": building.utilities_included,
            "fitness_area": building.fitness_area,
            "work_study_area": building.work_study_area,
            "social_events": building.social_events,
            "nearby_conveniences_walk": building.nearby_conveniences_walk,
            "nearby_transportation": building.nearby_transportation,
            "priority": building.priority,
            "created_at": building.created_at,
            "last_modified": building.last_modified,
            "virtual_tour_url": building.virtual_tour_url,
            # NEW: Multiple video/tour URLs
            "virtual_tour_urls": building.virtual_tour_urls,
            # NEW: WalkScore data
            "walkscore_data": building.walkscore_data,
            "walkscore": building.walkscore,
            "walkscore_transit": building.walkscore_transit,
            "walkscore_bike": building.walkscore_bike,
            # NEW: Security features
            "security_cameras": building.security_cameras,
            "keycard_access": building.keycard_access,
            "keycode_entry": building.keycode_entry,
            "security_guard": building.security_guard,
            "onsite_manager": building.onsite_manager,
            "gated_community": building.gated_community,
            "intercom_system": building.intercom_system,
            "building_alarm": building.building_alarm,
            # NEW: Accessibility features
            "wheelchair_ramp": building.wheelchair_ramp,
            "elevator_access": building.elevator_access,
            "wide_doorways": building.wide_doorways,
            "accessible_bathroom": building.accessible_bathroom,
            "hearing_assistance": building.hearing_assistance,
            "visual_assistance": building.visual_assistance,
            "accessible_parking": building.accessible_parking,
            "grab_bars": building.grab_bars,
            "lowered_counters": building.lowered_counters,
            "accessible_entrance": building.accessible_entrance,
            "service_animal_friendly": building.service_animal_friendly,
            "accessible_emergency": building.accessible_emergency,
            "accessibility_details": building.accessibility_details,
            # NEW: Parking options
            "covered_parking": building.covered_parking,
            "garage_parking": building.garage_parking,
            "street_parking": building.street_parking,
            "visitor_parking": building.visitor_parking,
            "handicap_parking": building.handicap_parking,
            "electric_charging": building.electric_charging,
        }
        
        # Parse building images
        if building.building_images:
            import json
            try:
                building_dict["building_images"] = json.loads(building.building_images)
            except:
                building_dict["building_images"] = []
        else:
            building_dict["building_images"] = []
            
        return building_dict
        
    except Exception as e:
        print(f"Error fetching building with images: {str(e)}")
        return None

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



def get_buildings_by_operator(db: Session, operator_id: int) -> List[models.Building]:
    """
    Retrieves all buildings managed by a specific operator.
    """
    return db.query(models.Building).filter(models.Building.operator_id == operator_id).all()

def get_available_buildings(db: Session) -> List[models.Building]:
    """
    Retrieves all available buildings.
    """
    return db.query(models.Building).filter(models.Building.available == True).all()

def search_buildings(db: Session, search_term: str) -> List[models.Building]:
    """
    Search buildings by name, address, or area.
    """
    return db.query(models.Building).filter(
        models.Building.building_name.ilike(f"%{search_term}%") |
        models.Building.full_address.ilike(f"%{search_term}%") |
        models.Building.area.ilike(f"%{search_term}%") |
        models.Building.city.ilike(f"%{search_term}%")
    ).all()