# app/ai_services/v2_intelligent_room_finder_supabase.py
# Enhanced: Building-level filtering + uses v1 for room criteria

import json
import re
from typing import Dict, Any, List
from datetime import datetime
from google import genai
from app.config import GEMINI_API_KEY
from app.db.supabase_connection import get_supabase
from google.genai.types import GenerateContentConfig

# Import v1 for room-level filtering
from app.ai_services.v1_intelligent_room_finder_supabase import execute_comprehensive_room_search

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_building_criteria_with_llm(query: str) -> Dict[str, Any]:
    """
    Extract ONLY building-level criteria using LLM
    """
    print(f"🏢 EXTRACTING BUILDING CRITERIA: '{query}'")
    
    # Default structure
    default_criteria = {
        "building_features": {},
        "location_preferences": {},
        "building_requirements": {}
    }
    
    try:
        # Simpler prompt to reduce JSON errors
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Extract ONLY building-related criteria from: "{query}"
            
            Look for building features like:
            - gym/fitness area
            - wifi
            - laundry
            - pet-friendly
            - utilities included
            - secure access
            - rooftop
            - bike storage
            
            Return simple JSON with found features.
            Example: {{"building_features": {{"fitness_area": true, "wifi_included": true}}}}
            
            Return ONLY valid JSON.
            """,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=150
            )
        )
        
        response_text = response.text.strip()
        
        # Extract and clean JSON
        if '{' in response_text and '}' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_text = response_text[start:end]
            
            # Clean common issues
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
            
            try:
                extracted = json.loads(json_text)
                criteria = default_criteria.copy()
                criteria.update(extracted)
                print(f"✅ Building criteria extracted successfully")
                return criteria
            except:
                pass
        
        # Fallback: keyword matching
        query_lower = query.lower()
        features = {}
        
        # Check for building features
        if "gym" in query_lower or "fitness" in query_lower:
            features["fitness_area"] = True
        if "wifi" in query_lower or "wi-fi" in query_lower:
            features["wifi_included"] = True
        if "laundry" in query_lower:
            features["laundry_onsite"] = True
        if "pet" in query_lower:
            features["pet_friendly"] = "Yes"
        if "utilities" in query_lower:
            features["utilities_included"] = True
        if "secure" in query_lower:
            features["secure_access"] = True
        if "rooftop" in query_lower:
            features["rooftop_access"] = True
        if "bike" in query_lower:
            features["bike_storage"] = True
        
        criteria = default_criteria.copy()
        if features:
            criteria["building_features"] = features
            
        print(f"✅ Building criteria extracted via fallback")
        return criteria
        
    except Exception as e:
        print(f"❌ Building criteria extraction failed: {e}")
        return default_criteria

def get_qualifying_building_ids(criteria: Dict[str, Any]) -> List[str]:
    """
    Get building IDs that match building-level criteria
    """
    print(f"🔧 FINDING QUALIFYING BUILDINGS")
    
    supabase = get_supabase()
    query = supabase.table('buildings').select('building_id')
    
    # === BUILDING FEATURES ===
    building_features = criteria.get("building_features", {})
    
    if building_features.get("wifi_included") is True:
        query = query.eq('wifi_included', True)
        print("   📶 WiFi included")
    
    if building_features.get("laundry_onsite") is True:
        query = query.eq('laundry_onsite', True)
        print("   🧺 Laundry onsite")
    
    if building_features.get("secure_access") is True:
        query = query.eq('secure_access', True)
        print("   🔐 Secure access")
    
    if building_features.get("bike_storage") is True:
        query = query.eq('bike_storage', True)
        print("   🚲 Bike storage")
    
    if building_features.get("rooftop_access") is True:
        query = query.eq('rooftop_access', True)
        print("   🏢 Rooftop access")
    
    if building_features.get("fitness_area") is True:
        query = query.eq('fitness_area', True)
        print("   💪 Fitness area")
    
    if building_features.get("work_study_area") is True:
        query = query.eq('work_study_area', True)
        print("   📚 Work/study area")
    
    if building_features.get("utilities_included") is True:
        query = query.eq('utilities_included', True)
        print("   ⚡ Utilities included")
    
    if building_features.get("social_events") is True:
        query = query.eq('social_events', True)
        print("   🎉 Social events")
    
    # Pet friendly
    pet_friendly = building_features.get("pet_friendly")
    if pet_friendly in ["Yes", "Some"]:
        query = query.in_('pet_friendly', ["Yes", "Some"])
        print(f"   🐕 Pet friendly: {pet_friendly}")
    elif pet_friendly == "No":
        query = query.eq('pet_friendly', "No")
        print("   🚫 No pets")
    
    # Common kitchen
    common_kitchen = building_features.get("common_kitchen")
    if common_kitchen in ["Full", "Basic"]:
        query = query.eq('common_kitchen', common_kitchen)
        print(f"   🍳 Kitchen: {common_kitchen}")
    
    # === LOCATION PREFERENCES ===
    location_prefs = criteria.get("location_preferences", {})
    
    if location_prefs.get("area"):
        query = query.ilike('area', f"%{location_prefs['area']}%")
        print(f"   📍 Area: {location_prefs['area']}")
    
    if location_prefs.get("city"):
        query = query.ilike('city', f"%{location_prefs['city']}%")
        print(f"   🏙️ City: {location_prefs['city']}")
    
    if location_prefs.get("state"):
        query = query.ilike('state', f"%{location_prefs['state']}%")
        print(f"   🗺️ State: {location_prefs['state']}")
    
    if location_prefs.get("nearby_transportation"):
        query = query.not_.is_('nearby_transportation', None)
        print("   🚌 Near transportation")
    
    # === BUILDING REQUIREMENTS ===
    building_reqs = criteria.get("building_requirements", {})
    
    if building_reqs.get("min_lease_term"):
        query = query.gte('min_lease_term', building_reqs["min_lease_term"])
        print(f"   📅 Min lease term: {building_reqs['min_lease_term']} months")
    
    if building_reqs.get("max_lease_term"):
        query = query.lte('min_lease_term', building_reqs["max_lease_term"])
        print(f"   📅 Max acceptable lease term: {building_reqs['max_lease_term']} months")
    
    # Execute query
    response = query.execute()
    building_ids = [b['building_id'] for b in response.data]
    
    print(f"✅ Found {len(building_ids)} qualifying buildings")
    return building_ids

def score_rooms_with_building_features(rooms: List[Dict], building_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Score rooms including building-level features
    """
    print(f"📊 SCORING WITH BUILDING FEATURES")
    
    scored_rooms = []
    building_features = building_criteria.get("building_features", {})
    
    for room in rooms:
        # Start with existing room score if available
        base_score = room.get('match_score', 0)
        score = base_score
        reasons = room.get('match_reasons', []).copy()
        
        building = room.get('buildings', {})
        
        # Premium building amenities (high score)
        if building.get('fitness_area'):
            score += 25
            reasons.append("gym")
        
        if building.get('rooftop_access'):
            score += 20
            reasons.append("rooftop")
        
        if building.get('work_study_area'):
            score += 20
            reasons.append("study area")
        
        # Convenience amenities (medium score)
        if building.get('laundry_onsite'):
            score += 15
            reasons.append("laundry")
        
        if building.get('wifi_included'):
            score += 15
            reasons.append("wifi")
        
        if building.get('utilities_included'):
            score += 15
            reasons.append("utilities")
        
        if building.get('secure_access'):
            score += 15
            reasons.append("secure")
        
        # Nice-to-have amenities (low score)
        if building.get('bike_storage'):
            score += 10
            reasons.append("bike storage")
        
        if building.get('social_events'):
            score += 10
            reasons.append("events")
        
        # Pet friendly scoring
        if building.get('pet_friendly') in ["Yes", "Some"]:
            score += 12
            reasons.append("pet-friendly")
        
        # Kitchen scoring
        if building.get('common_kitchen') == "Full":
            score += 12
            reasons.append("full kitchen")
        elif building.get('common_kitchen') == "Basic":
            score += 8
            reasons.append("kitchen")
        
        # Location scoring
        if building.get('nearby_transportation'):
            score += 18
            reasons.append("transit")
        
        # Lease flexibility
        if building.get('min_lease_term') and building['min_lease_term'] <= 6:
            score += 10
            reasons.append("flexible lease")
        
        # Update room with new score
        room['match_score'] = score
        room['match_reasons'] = reasons
        
        scored_rooms.append({
            "room": room,
            "score": score,
            "reasons": reasons
        })
    
    scored_rooms.sort(key=lambda x: x["score"], reverse=True)
    print(f"   📈 Scored {len(scored_rooms)} rooms with building features")
    return scored_rooms

def execute_room_and_building_search(query: str, **kwargs) -> Dict[str, Any]:
    """
    Combined room + building search using Supabase
    """
    print(f"🚀 ROOM + BUILDING SEARCH: '{query}'")
    print("=" * 80)
    
    try:
        # Step 1: Extract building criteria
        building_criteria = extract_building_criteria_with_llm(query)
        
        # Step 2: Get qualifying buildings if criteria exist
        qualifying_building_ids = None
        if any(building_criteria.values()):
            qualifying_building_ids = get_qualifying_building_ids(building_criteria)
            
            if not qualifying_building_ids:
                return {
                    "success": True,
                    "response": "No buildings found matching your building criteria.",
                    "data": [],
                    "total_results": 0,
                    "query": query,
                    "search_type": "room_and_building"
                }
        
        # Step 3: Get room results from v1
        print("📋 Getting room-level results from v1...")
        room_results = execute_comprehensive_room_search(query)
        
        if not room_results.get("data"):
            return {
                "success": True,
                "response": "No rooms found matching your room criteria.",
                "data": [],
                "total_results": 0,
                "query": query,
                "search_type": "room_and_building"
            }
        
        # Step 4: Filter by qualifying buildings if needed
        if qualifying_building_ids:
            print("🔍 FILTERING V1 RESULTS BY QUALIFYING BUILDINGS")
            qualified_rooms = []
            for room_data in room_results["data"]:
                if room_data["building_id"] in qualifying_building_ids:
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
        else:
            qualified_rooms = room_results["data"]
        
        # Step 5: Score with building features
        scored_rooms = score_rooms_with_building_features(qualified_rooms, building_criteria)
        
        # Step 6: Format final results (limit to 5)
        final_rooms = scored_rooms[:5]
        room_data_list = []
        
        for scored_room in final_rooms:
            room = scored_room["room"]
            building = room.get('buildings', {})
            
            room_data = {
                # Room details
                "room_id": room['room_id'],
                "room_number": room['room_number'],
                "building_id": room['building_id'],
                "building_name": building.get('building_name', 'Unknown'),
                "full_address": building.get('full_address', 'Unknown'),
                "view": room.get('view'),
                "private_room_rent": room.get('private_room_rent'),
                "shared_room_rent_2": room.get('shared_room_rent_2'),
                "status": room.get('status'),
                "bathroom_type": room.get('bathroom_type'),
                "bed_size": room.get('bed_size'),
                "bed_type": room.get('bed_type'),
                "sq_footage": room.get('sq_footage'),
                "floor_number": room.get('floor_number'),
                "maximum_people_in_room": room.get('maximum_people_in_room'),
                "booked_till": room.get('booked_till'),
                "ready_to_rent": room.get('ready_to_rent'),
                "match_score": scored_room["score"],
                "match_reasons": scored_room["reasons"],
                
                # Room amenities
                "room_amenities": {
                    "mini_fridge": room.get('mini_fridge'),
                    "sink": room.get('sink'),
                    "work_desk": room.get('work_desk'),
                    "work_chair": room.get('work_chair'),
                    "heating": room.get('heating'),
                    "air_conditioning": room.get('air_conditioning'),
                    "cable_tv": room.get('cable_tv'),
                    "room_storage": room.get('room_storage'),
                    "bedding_provided": room.get('bedding_provided')
                },
                
                # Building features
                "building_features": {
                    "wifi_included": building.get('wifi_included', False),
                    "laundry_onsite": building.get('laundry_onsite', False),
                    "secure_access": building.get('secure_access', False),
                    "fitness_area": building.get('fitness_area', False),
                    "utilities_included": building.get('utilities_included', False),
                    "pet_friendly": building.get('pet_friendly', "No"),
                    "min_lease_term": building.get('min_lease_term'),
                    "bike_storage": building.get('bike_storage', False),
                    "rooftop_access": building.get('rooftop_access', False),
                    "work_study_area": building.get('work_study_area', False),
                    "social_events": building.get('social_events', False),
                    "common_kitchen": building.get('common_kitchen', "None")
                },
                
                # Location info
                "location": {
                    "area": building.get('area'),
                    "city": building.get('city'),
                    "state": building.get('state'),
                    "street": building.get('street'),
                    "zip": building.get('zip'),
                    "nearby_transportation": building.get('nearby_transportation'),
                    "nearby_conveniences_walk": building.get('nearby_conveniences_walk')
                }
            }
            room_data_list.append(room_data)
        
        # Step 7: Generate response
        if room_data_list:
            prices = [r['private_room_rent'] for r in room_data_list if r['private_room_rent']]
            if prices:
                price_range = f"${min(prices)} - ${max(prices)}"
                top_match = room_data_list[0]
                
                # Build reasons (limit to first 3)
                reasons = top_match['match_reasons'][:3]
                reasons_text = ', '.join(reasons) if reasons else 'good match'
                
                response_text = f"Found {len(room_data_list)} rooms. Price: {price_range}. Top: Room {top_match['room_number']} (Score: {top_match['match_score']}) - {reasons_text}."
            else:
                response_text = f"Found {len(room_data_list)} rooms matching your criteria."
        else:
            response_text = f"No rooms found matching your room and building criteria."
        
        return {
            "success": True,
            "response": response_text,
            "data": room_data_list,
            "total_results": len(room_data_list),
            "building_criteria": building_criteria,
            "qualifying_buildings": len(qualifying_building_ids) if qualifying_building_ids else "all",
            "query": query,
            "search_type": "room_and_building",
            "scoring_enabled": True
        }
        
    except Exception as e:
        print(f"❌ ROOM + BUILDING SEARCH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "response": "Room and building search failed. Please try again.",
            "data": [],
            "total_results": 0,
            "query": query
        }

# Main function export
def filter_rooms_function(query: str, **kwargs) -> Dict[str, Any]:
    """
    Advanced room + building filtering function (v2) - Supabase version
    Note: db parameter removed as we use Supabase client directly
    """
    return execute_room_and_building_search(query, **kwargs)