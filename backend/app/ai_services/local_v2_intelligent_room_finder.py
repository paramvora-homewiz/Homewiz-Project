# app/ai_services/v2_intelligent_room_finder.py
# Enhanced: Building-level filtering + uses v1 for room criteria

import json
from typing import Dict, Any, List
from datetime import datetime
from google import genai
from app.config import GEMINI_API_KEY
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db import models
from google.genai.types import GenerateContentConfig

# Import v1 for room-level filtering
from app.ai_services.v1_intelligent_room_finder import execute_comprehensive_room_search

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_building_criteria_with_llm(query: str) -> Dict[str, Any]:
    """
    Extract ONLY building-level criteria using LLM
    """
    print(f"🏢 EXTRACTING BUILDING CRITERIA: '{query}'")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Extract ONLY building-level criteria from: "{query}"
            
            Ignore room-specific criteria (price, view, bathroom, bed size, floor, sq footage, etc.)
            Focus ONLY on building features and location:
            
            {{
                "building_features": {{
                    "wifi_included": <boolean or null>,
                    "laundry_onsite": <boolean or null>,
                    "secure_access": <boolean or null>,
                    "bike_storage": <boolean or null>,
                    "rooftop_access": <boolean or null>,
                    "fitness_area": <boolean or null>,
                    "work_study_area": <boolean or null>,
                    "utilities_included": <boolean or null>,
                    "pet_friendly": <"Yes", "No", "Some" or null>,
                    "common_kitchen": <"Full", "Basic", "None" or null>,
                    "social_events": <boolean or null>,
                    "common_area": <string or null>,
                    "cleaning_common_spaces": <string or null>
                }},
                "location_preferences": {{
                    "area": <string or null>,
                    "city": <string or null>,
                    "state": <string or null>,
                    "street": <string or null>,
                    "zip": <string or null>,
                    "nearby_transportation": <boolean or null>,
                    "walkable_conveniences": <boolean or null>
                }},
                "building_requirements": {{
                    "min_lease_term": <number or null>,
                    "max_lease_term": <number or null>,
                    "max_floors": <number or null>,
                    "min_floors": <number or null>,
                    "min_total_rooms": <number or null>,
                    "max_total_rooms": <number or null>,
                    "available_building": <boolean or null>
                }}
            }}
            
            Examples:
            "building with gym and laundry, pet-friendly, utilities included" → 
            {{"building_features": {{"fitness_area": true, "laundry_onsite": true, "pet_friendly": "Yes", "utilities_included": true}}}}
            
            "downtown San Francisco with secure access, work area, short lease terms" → 
            {{"location_preferences": {{"area": "downtown", "city": "San Francisco"}}, "building_features": {{"secure_access": true, "work_study_area": true}}, "building_requirements": {{"max_lease_term": 6}}}}
            
            "near public transport, bike storage, social events, rooftop access" →
            {{"location_preferences": {{"nearby_transportation": true}}, "building_features": {{"bike_storage": true, "social_events": true, "rooftop_access": true}}}}
            
            Return ONLY JSON.
            """,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=100
            )
        )
        
        criteria_text = response.text.strip()
        if criteria_text.startswith('```json'):
            criteria_text = criteria_text.replace('```json', '').replace('```', '').strip()
        
        criteria = json.loads(criteria_text)
        print(f"✅ Building criteria extracted: {criteria}")
        return criteria
        
    except Exception as e:
        print(f"❌ Building criteria extraction failed: {e}")
        return {
            "building_features": {},
            "location_preferences": {},
            "building_requirements": {}
        }

def build_building_filters(criteria: Dict[str, Any]) -> List:
    """
    Build building-level database filters only
    """
    print(f"🔧 BUILDING BUILDING-LEVEL FILTERS")
    
    filters = []
    
    # === BUILDING FEATURES ===
    building_features = criteria.get("building_features", {})
    
    if building_features.get("wifi_included") is True:
        filters.append(models.Building.wifi_included == True)
        print("   📶 WiFi included")
    
    if building_features.get("laundry_onsite") is True:
        filters.append(models.Building.laundry_onsite == True)
        print("   🧺 Laundry onsite")
    
    if building_features.get("secure_access") is True:
        filters.append(models.Building.secure_access == True)
        print("   🔐 Secure access")
    
    if building_features.get("bike_storage") is True:
        filters.append(models.Building.bike_storage == True)
        print("   🚲 Bike storage")
    
    if building_features.get("rooftop_access") is True:
        filters.append(models.Building.rooftop_access == True)
        print("   🏢 Rooftop access")
    
    if building_features.get("fitness_area") is True:
        filters.append(models.Building.fitness_area == True)
        print("   💪 Fitness area")
    
    if building_features.get("work_study_area") is True:
        filters.append(models.Building.work_study_area == True)
        print("   📚 Work/study area")
    
    if building_features.get("utilities_included") is True:
        filters.append(models.Building.utilities_included == True)
        print("   ⚡ Utilities included")
    
    if building_features.get("social_events") is True:
        filters.append(models.Building.social_events == True)
        print("   🎉 Social events")
    
    # Pet friendly
    pet_friendly = building_features.get("pet_friendly")
    if pet_friendly:
        if pet_friendly in ["Yes", "Some"]:
            filters.append(models.Building.pet_friendly.in_(["Yes", "Some"]))
            print(f"   🐕 Pet friendly: {pet_friendly}")
        elif pet_friendly == "No":
            filters.append(models.Building.pet_friendly == "No")
            print("   🚫 No pets")
    
    # Common kitchen
    common_kitchen = building_features.get("common_kitchen")
    if common_kitchen and common_kitchen != "None":
        if common_kitchen in ["Full", "Basic"]:
            filters.append(models.Building.common_kitchen == common_kitchen)
            print(f"   🍳 Kitchen: {common_kitchen}")
    
    # Common area
    if building_features.get("common_area"):
        filters.append(models.Building.common_area.isnot(None))
        print("   🛋️ Common area available")
    
    # Cleaning services
    if building_features.get("cleaning_common_spaces"):
        filters.append(models.Building.cleaning_common_spaces.isnot(None))
        print("   🧹 Cleaning services")
    
    # === LOCATION PREFERENCES ===
    location_prefs = criteria.get("location_preferences", {})
    
    if location_prefs.get("area"):
        filters.append(models.Building.area.ilike(f"%{location_prefs['area']}%"))
        print(f"   📍 Area: {location_prefs['area']}")
    
    if location_prefs.get("city"):
        filters.append(models.Building.city.ilike(f"%{location_prefs['city']}%"))
        print(f"   🏙️ City: {location_prefs['city']}")
    
    if location_prefs.get("state"):
        filters.append(models.Building.state.ilike(f"%{location_prefs['state']}%"))
        print(f"   🗺️ State: {location_prefs['state']}")
    
    if location_prefs.get("street"):
        filters.append(models.Building.street.ilike(f"%{location_prefs['street']}%"))
        print(f"   🛣️ Street: {location_prefs['street']}")
    
    if location_prefs.get("zip"):
        filters.append(models.Building.zip == location_prefs["zip"])
        print(f"   📮 ZIP: {location_prefs['zip']}")
    
    if location_prefs.get("nearby_transportation"):
        filters.append(models.Building.nearby_transportation.isnot(None))
        print("   🚌 Near transportation")
    
    if location_prefs.get("walkable_conveniences"):
        filters.append(models.Building.nearby_conveniences_walk.isnot(None))
        print("   🚶 Walkable conveniences")
    
    # === BUILDING REQUIREMENTS ===
    building_reqs = criteria.get("building_requirements", {})
    
    if building_reqs.get("min_lease_term"):
        filters.append(models.Building.min_lease_term >= building_reqs["min_lease_term"])
        print(f"   📅 Min lease term: {building_reqs['min_lease_term']} months")
    
    if building_reqs.get("max_lease_term"):
        filters.append(models.Building.min_lease_term <= building_reqs["max_lease_term"])
        print(f"   📅 Max acceptable lease term: {building_reqs['max_lease_term']} months")
    
    if building_reqs.get("max_floors"):
        filters.append(models.Building.floors <= building_reqs["max_floors"])
        print(f"   🏢 Max floors: {building_reqs['max_floors']}")
    
    if building_reqs.get("min_floors"):
        filters.append(models.Building.floors >= building_reqs["min_floors"])
        print(f"   🏢 Min floors: {building_reqs['min_floors']}")
    
    if building_reqs.get("min_total_rooms"):
        filters.append(models.Building.total_rooms >= building_reqs["min_total_rooms"])
        print(f"   🏠 Min total rooms: {building_reqs['min_total_rooms']}")
    
    if building_reqs.get("max_total_rooms"):
        filters.append(models.Building.total_rooms <= building_reqs["max_total_rooms"])
        print(f"   🏠 Max total rooms: {building_reqs['max_total_rooms']}")
    
    if building_reqs.get("available_building"):
        filters.append(models.Building.available == True)
        print("   ✅ Available buildings only")
    
    print(f"✅ Built {len(filters)} building-level filters")
    return filters

def score_rooms_with_building_features(rooms: List, building_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Score rooms including building-level features
    """
    print(f"📊 SCORING WITH BUILDING FEATURES")
    
    scored_rooms = []
    building_features = building_criteria.get("building_features", {})
    
    for room in rooms:
        # Start with existing room score if available
        base_score = getattr(room, 'match_score', 0)
        score = base_score
        reasons = getattr(room, 'match_reasons', []).copy() if hasattr(room, 'match_reasons') else []
        
        building = room.building
        if building:
            # Premium building amenities (high score)
            if building.fitness_area:
                score += 25
                reasons.append("gym")
            
            if building.rooftop_access:
                score += 20
                reasons.append("rooftop")
            
            if building.work_study_area:
                score += 20
                reasons.append("study area")
            
            # Convenience amenities (medium score)
            if building.laundry_onsite:
                score += 15
                reasons.append("laundry")
            
            if building.wifi_included:
                score += 15
                reasons.append("wifi")
            
            if building.utilities_included:
                score += 15
                reasons.append("utilities")
            
            if building.secure_access:
                score += 15
                reasons.append("secure")
            
            # Nice-to-have amenities (low score)
            if building.bike_storage:
                score += 10
                reasons.append("bike storage")
            
            if building.social_events:
                score += 10
                reasons.append("events")
            
            if building.common_area:
                score += 8
                reasons.append("common area")
            
            # Pet friendly scoring
            if building.pet_friendly in ["Yes", "Some"]:
                score += 12
                reasons.append("pet-friendly")
            
            # Kitchen scoring
            if building.common_kitchen == "Full":
                score += 12
                reasons.append("full kitchen")
            elif building.common_kitchen == "Basic":
                score += 8
                reasons.append("kitchen")
            
            # Location scoring
            if building.nearby_transportation:
                score += 18
                reasons.append("transit")
            
            if building.nearby_conveniences_walk:
                score += 12
                reasons.append("walkable")
            
            # Lease flexibility
            if building.min_lease_term and building.min_lease_term <= 6:
                score += 10
                reasons.append("flexible lease")
        
        scored_rooms.append({
            "room": room,
            "score": score,
            "reasons": reasons
        })
    
    scored_rooms.sort(key=lambda x: x["score"], reverse=True)
    print(f"   📈 Scored {len(scored_rooms)} rooms with building features")
    return scored_rooms

# Fixed execute_room_and_building_search function in v2_intelligent_room_finder.py

def execute_room_and_building_search(query: str, db: Session, **kwargs) -> Dict[str, Any]:
    """
    Combined room + building search - FIXED APPROACH
    """
    print(f"🚀 ROOM + BUILDING SEARCH: '{query}'")
    print("=" * 80)
    
    try:
        # Step 1: Extract building criteria FIRST
        building_criteria = extract_building_criteria_with_llm(query)
        building_filters = build_building_filters(building_criteria)
        
        # Step 2: Apply building filters to get qualifying buildings
        if building_filters:
            print("💾 APPLYING BUILDING FILTERS FIRST")
            
            # Get buildings that match criteria
            qualifying_buildings = db.query(models.Building)\
                .filter(and_(*building_filters))\
                .all()
            
            building_ids = [b.building_id for b in qualifying_buildings]
            print(f"   🏢 Found {len(building_ids)} qualifying buildings")
            
            if not building_ids:
                return {
                    "success": True,
                    "response": "No buildings found matching your building criteria.",
                    "data": [],
                    "total_results": 0,
                    "query": query,
                    "search_type": "room_and_building"
                }
            
            # Step 3: Get room results from v1 BUT limit to qualifying buildings
            print("📋 Getting room-level results from v1 for qualifying buildings...")
            room_results = execute_comprehensive_room_search(query, db)
            
            if not room_results.get("data"):
                return {
                    "success": True,
                    "response": "No rooms found matching your room criteria in qualifying buildings.",
                    "data": [],
                    "total_results": 0,
                    "query": query,
                    "search_type": "room_and_building"
                }
            
            # Step 4: Filter v1 results to only include rooms from qualifying buildings
            print("🔍 FILTERING V1 RESULTS BY QUALIFYING BUILDINGS")
            qualified_rooms = []
            for room_data in room_results["data"]:
                if room_data["building_id"] in building_ids:
                    qualified_rooms.append(room_data)
            
            print(f"   📋 {len(qualified_rooms)} rooms from qualifying buildings")
            
            if not qualified_rooms:
                return {
                    "success": True,
                    "response": "No rooms found matching both room and building criteria.",
                    "data": [],
                    "total_results": 0,
                    "query": query,
                    "search_type": "room_and_building"
                }
            
            # Step 5: Get Room objects for scoring
            filtered_rooms = []
            for room_data in qualified_rooms:
                room = db.query(models.Room).filter(models.Room.room_id == room_data["room_id"]).first()
                if room:
                    # Preserve v1 scoring
                    room.match_score = room_data.get("match_score", 0)
                    room.match_reasons = room_data.get("match_reasons", [])
                    filtered_rooms.append(room)
        
        else:
            # No building filters, use regular v1 flow
            print("📋 No building filters, getting regular v1 results...")
            room_results = execute_comprehensive_room_search(query, db)
            
            if not room_results.get("data"):
                return {
                    "success": True,
                    "response": "No rooms found matching your criteria.",
                    "data": [],
                    "total_results": 0,
                    "query": query,
                    "search_type": "room_and_building"
                }
            
            # Get Room objects from v1 results
            filtered_rooms = []
            for room_data in room_results["data"]:
                room = db.query(models.Room).filter(models.Room.room_id == room_data["room_id"]).first()
                if room:
                    room.match_score = room_data.get("match_score", 0)
                    room.match_reasons = room_data.get("match_reasons", [])
                    filtered_rooms.append(room)
        
        # Step 6: Score with building features (same as before)
        scored_rooms = score_rooms_with_building_features(filtered_rooms, building_criteria)
        
        # Step 7: Format final results (limit to 5) - same as before
        final_rooms = scored_rooms[:5]
        room_data_list = []
        
        for scored_room in final_rooms:
            room = scored_room["room"]
            building = room.building
            
            room_data = {
                # Room details
                "room_id": room.room_id,
                "room_number": room.room_number,
                "building_id": room.building_id,
                "building_name": building.building_name if building else "Unknown",
                "full_address": building.full_address if building else "Unknown",
                "view": room.view,
                "private_room_rent": room.private_room_rent,
                "shared_room_rent_2": room.shared_room_rent_2,
                "status": room.status,
                "bathroom_type": room.bathroom_type,
                "bed_size": room.bed_size,
                "bed_type": room.bed_type,
                "sq_footage": room.sq_footage,
                "floor_number": room.floor_number,
                "maximum_people_in_room": room.maximum_people_in_room,
                "booked_till": room.booked_till.isoformat() if room.booked_till else None,
                "ready_to_rent": room.ready_to_rent,
                "match_score": scored_room["score"],
                "match_reasons": scored_room["reasons"],
                
                # Room amenities
                "room_amenities": {
                    "mini_fridge": room.mini_fridge,
                    "sink": room.sink,
                    "work_desk": room.work_desk,
                    "work_chair": room.work_chair,
                    "heating": room.heating,
                    "air_conditioning": room.air_conditioning,
                    "cable_tv": room.cable_tv,
                    "room_storage": room.room_storage,
                    "bedding_provided": room.bedding_provided
                },
                
                # Building features
                "building_features": {
                    "wifi_included": building.wifi_included if building else False,
                    "laundry_onsite": building.laundry_onsite if building else False,
                    "secure_access": building.secure_access if building else False,
                    "fitness_area": building.fitness_area if building else False,
                    "utilities_included": building.utilities_included if building else False,
                    "pet_friendly": building.pet_friendly if building else "No",
                    "min_lease_term": building.min_lease_term if building else None,
                    "bike_storage": building.bike_storage if building else False,
                    "rooftop_access": building.rooftop_access if building else False,
                    "work_study_area": building.work_study_area if building else False,
                    "social_events": building.social_events if building else False,
                    "common_kitchen": building.common_kitchen if building else "None"
                },
                
                # Location info
                "location": {
                    "area": building.area if building else None,
                    "city": building.city if building else None,
                    "state": building.state if building else None,
                    "street": building.street if building else None,
                    "zip": building.zip if building else None,
                    "nearby_transportation": building.nearby_transportation if building else None,
                    "nearby_conveniences_walk": building.nearby_conveniences_walk if building else None
                }
            }
            room_data_list.append(room_data)
        
        # Step 8: Generate response
        if room_data_list:
            prices = [r['private_room_rent'] for r in room_data_list]
            price_range = f"${min(prices)} - ${max(prices)}"
            top_match = room_data_list[0]
            
            # Build reasons (limit to first 3)
            reasons = top_match['match_reasons'][:3]
            reasons_text = ', '.join(reasons) if reasons else 'good match'
            
            response_text = f"Found {len(room_data_list)} rooms. Price: {price_range}. Top: Room {top_match['room_number']} (Score: {top_match['match_score']}) - {reasons_text}."
        else:
            response_text = f"No rooms found matching your room and building criteria."
        
        return {
            "success": True,
            "response": response_text,
            "data": room_data_list,
            "total_results": len(room_data_list),
            "building_criteria": building_criteria,
            "building_filters_applied": len(building_filters) if building_filters else 0,
            "qualifying_buildings": len(building_ids) if building_filters else "all",
            "query": query,
            "search_type": "room_and_building",
            "scoring_enabled": True
        }
        
    except Exception as e:
        print(f"❌ ROOM + BUILDING SEARCH ERROR: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "Room and building search failed. Please try again.",
            "data": [],
            "total_results": 0,
            "query": query
        }

# Main function export
def filter_rooms_function(query: str, db: Session, **kwargs) -> Dict[str, Any]:
    """
    Advanced room + building filtering function (v2)
    """
    return execute_room_and_building_search(query, db, **kwargs)