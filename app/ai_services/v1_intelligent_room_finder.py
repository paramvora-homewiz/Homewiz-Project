# app/ai_services/v1_intelligent_room_finder.py
# Enhanced: ALL room-level filtering (basic + advanced) in one place

import json
from typing import Dict, Any, List
from datetime import datetime
from google import genai
from app.config import GEMINI_API_KEY
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db import models
from google.genai.types import GenerateContentConfig

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_all_room_criteria_with_llm(query: str) -> Dict[str, Any]:
    """
    Extract ALL room-level criteria (basic + advanced) using LLM
    """
    print(f"🤖 EXTRACTING ALL ROOM CRITERIA: '{query}'")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Extract ALL room-level search criteria from: "{query}"
            
            Return JSON with these fields (use null/empty for missing):
            {{
                "price_min": <number or null>,
                "price_max": <number or null>,
                "view_types": [<"city", "bay", "garden", "street">],
                "bathroom_type": <"Private", "Shared", "En-Suite" or null>,
                "bed_size": <"Twin", "Full", "Queen", "King" or null>,
                "bed_type": <"Single", "Double", "Bunk" or null>,
                "room_type": <"private" or "shared" or null>,
                "amenities_required": [<"fridge", "sink", "desk", "chair", "heating", "ac", "tv", "storage", "bedding">],
                "budget_level": <"budget", "luxury" or null>,
                "floor_preferences": {{
                    "min_floor": <number or null>,
                    "max_floor": <number or null>,
                    "avoid_ground_floor": <boolean>,
                    "prefer_high_floors": <boolean>,
                    "specific_floor": <number or null>
                }},
                "size_requirements": {{
                    "min_sq_footage": <number or null>,
                    "max_sq_footage": <number or null>,
                    "spacious": <boolean>
                }},
                "availability": {{
                    "move_in_date": <"YYYY-MM-DD" or null>,
                    "immediate": <boolean>,
                    "flexible_date": <boolean>
                }},
                "occupancy": {{
                    "max_people": <number or null>,
                    "exact_people": <number or null>,
                    "single_only": <boolean>
                }},
                "special_requirements": [<"quiet", "furnished", "ready_to_rent", "recently_checked">],
                "booking_preferences": {{
                    "private_rent_only": <boolean>,
                    "shared_rent_available": <boolean>
                }}
            }}
            
            Examples:
            "spacious private room under $2000 with city view on upper floors" → 
            {{"price_max": 2000, "room_type": "private", "view_types": ["city"], "size_requirements": {{"spacious": true}}, "floor_preferences": {{"prefer_high_floors": true}}}}
            
            "furnished queen bed room, quiet area, move in July, single occupancy" → 
            {{"bed_size": "Queen", "special_requirements": ["furnished", "quiet"], "availability": {{"move_in_date": "2025-07-01"}}, "occupancy": {{"single_only": true}}}}
            
            "shared room under $1500 with fridge and desk, available immediately" →
            {{"price_max": 1500, "room_type": "shared", "amenities_required": ["fridge", "desk"], "availability": {{"immediate": true}}}}
            
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
        print(f"✅ All room criteria extracted: {criteria}")
        return criteria
        
    except Exception as e:
        print(f"❌ LLM failed: {e}")
        return {
            "price_min": None, "price_max": None, "view_types": [], "bathroom_type": None,
            "bed_size": None, "bed_type": None, "room_type": None, "amenities_required": [],
            "budget_level": None, "floor_preferences": {}, "size_requirements": {},
            "availability": {}, "occupancy": {}, "special_requirements": [],
            "booking_preferences": {}
        }

def build_comprehensive_room_filters(criteria: Dict[str, Any], original_query: str) -> List:
    """
    Build comprehensive room database filters (basic + advanced)
    """
    print(f"🔧 BUILDING COMPREHENSIVE ROOM FILTERS")
    
    filters = []
    query_lower = original_query.lower()
    
    # === PRICE FILTERS ===
    if criteria.get("price_min"):
        filters.append(models.Room.private_room_rent >= criteria["price_min"])
        print(f"   💰 Min price: ${criteria['price_min']}")
    
    if criteria.get("price_max"):
        filters.append(models.Room.private_room_rent <= criteria["price_max"])
        print(f"   💰 Max price: ${criteria['price_max']}")
    
    # Budget level
    if criteria.get("budget_level") and not criteria.get("price_max"):
        if criteria["budget_level"] == "budget":
            filters.append(models.Room.private_room_rent <= 1800)
            print("   💰 Budget: <= $1800")
        elif criteria["budget_level"] == "luxury":
            filters.append(models.Room.private_room_rent >= 3500)
            print("   💰 Luxury: >= $3500")
    
    # === VIEW FILTERS ===
    view_types = criteria.get("view_types", [])
    if view_types:
        view_conditions = []
        for view in view_types:
            view_conditions.append(models.Room.view.ilike(f"%{view}%"))
        if view_conditions:
            filters.append(or_(*view_conditions))
            print(f"   🏞️ Views: {', '.join(view_types)}")
    # Fallback to string matching
    elif any(view in query_lower for view in ["city view", "bay view", "garden view", "street view"]):
        if "city view" in query_lower:
            filters.append(models.Room.view.ilike("%city%"))
            print("   🏞️ City view (fallback)")
        if "bay view" in query_lower:
            filters.append(models.Room.view.ilike("%bay%"))
            print("   🏞️ Bay view (fallback)")
        if "garden view" in query_lower:
            filters.append(models.Room.view.ilike("%garden%"))
            print("   🏞️ Garden view (fallback)")
        if "street view" in query_lower:
            filters.append(models.Room.view.ilike("%street%"))
            print("   🏞️ Street view (fallback)")
    
    # === BATHROOM FILTERS ===
    if criteria.get("bathroom_type"):
        filters.append(models.Room.bathroom_type == criteria["bathroom_type"])
        print(f"   🚿 Bathroom: {criteria['bathroom_type']}")
    
    # === BED FILTERS ===
    if criteria.get("bed_size"):
        filters.append(models.Room.bed_size == criteria["bed_size"])
        print(f"   🛏️ Bed size: {criteria['bed_size']}")
    
    if criteria.get("bed_type"):
        filters.append(models.Room.bed_type == criteria["bed_type"])
        print(f"   🛏️ Bed type: {criteria['bed_type']}")
    
    # === ROOM TYPE FILTERS ===
    room_type = criteria.get("room_type")
    if room_type:
        if room_type == "private":
            filters.append(models.Room.maximum_people_in_room == 1)
            print("   🏠 Private room")
        elif room_type == "shared":
            filters.append(models.Room.maximum_people_in_room > 1)
            print("   🏠 Shared room")
    
    # === AMENITY FILTERS ===
    amenity_column_map = {
        'fridge': models.Room.mini_fridge,
        'sink': models.Room.sink,
        'desk': models.Room.work_desk,
        'chair': models.Room.work_chair,
        'heating': models.Room.heating,
        'ac': models.Room.air_conditioning,
        'tv': models.Room.cable_tv,
        'storage': models.Room.room_storage,
        'bedding': models.Room.bedding_provided
    }
    
    amenities_required = criteria.get("amenities_required", [])
    for amenity in amenities_required:
        if amenity in amenity_column_map:
            filters.append(amenity_column_map[amenity] == True)
            print(f"   🔧 Required amenity: {amenity}")
    
    # === FLOOR PREFERENCES ===
    floor_prefs = criteria.get("floor_preferences", {})
    if floor_prefs.get("min_floor"):
        filters.append(models.Room.floor_number >= floor_prefs["min_floor"])
        print(f"   🏢 Min floor: {floor_prefs['min_floor']}")
    
    if floor_prefs.get("max_floor"):
        filters.append(models.Room.floor_number <= floor_prefs["max_floor"])
        print(f"   🏢 Max floor: {floor_prefs['max_floor']}")
    
    if floor_prefs.get("specific_floor"):
        filters.append(models.Room.floor_number == floor_prefs["specific_floor"])
        print(f"   🏢 Specific floor: {floor_prefs['specific_floor']}")
    
    if floor_prefs.get("avoid_ground_floor"):
        filters.append(models.Room.floor_number > 1)
        print("   🏢 Avoiding ground floor")
    
    if floor_prefs.get("prefer_high_floors"):
        filters.append(models.Room.floor_number >= 5)
        print("   🏢 High floors (5+)")
    
    # === SIZE REQUIREMENTS ===
    size_reqs = criteria.get("size_requirements", {})
    if size_reqs.get("min_sq_footage"):
        filters.append(models.Room.sq_footage >= size_reqs["min_sq_footage"])
        print(f"   📐 Min sq ft: {size_reqs['min_sq_footage']}")
    
    if size_reqs.get("max_sq_footage"):
        filters.append(models.Room.sq_footage <= size_reqs["max_sq_footage"])
        print(f"   📐 Max sq ft: {size_reqs['max_sq_footage']}")
    
    if size_reqs.get("spacious"):
        filters.append(models.Room.sq_footage >= 280)
        print("   📐 Spacious rooms (280+ sq ft)")
    
    # === AVAILABILITY FILTERS ===
    availability = criteria.get("availability", {})
    move_in_date = availability.get("move_in_date")
    if move_in_date:
        try:
            move_date = datetime.strptime(move_in_date, "%Y-%m-%d").date()
            filters.append(or_(
                models.Room.booked_till < move_date,
                models.Room.booked_till.is_(None)
            ))
            filters.append(models.Room.ready_to_rent == True)
            print(f"   📅 Available by: {move_in_date}")
        except ValueError:
            print(f"   ❌ Invalid move-in date: {move_in_date}")
    
    if availability.get("immediate"):
        filters.append(or_(
            models.Room.booked_till < datetime.now().date(),
            models.Room.booked_till.is_(None)
        ))
        filters.append(models.Room.ready_to_rent == True)
        print("   📅 Immediate availability")
    
    # === OCCUPANCY FILTERS ===
    occupancy = criteria.get("occupancy", {})
    if occupancy.get("max_people"):
        filters.append(models.Room.maximum_people_in_room <= occupancy["max_people"])
        print(f"   👥 Max occupancy: {occupancy['max_people']}")
    
    if occupancy.get("exact_people"):
        filters.append(models.Room.maximum_people_in_room == occupancy["exact_people"])
        print(f"   👥 Exact occupancy: {occupancy['exact_people']}")
    
    if occupancy.get("single_only"):
        filters.append(models.Room.maximum_people_in_room == 1)
        print("   👤 Single occupancy only")
    
    # === SPECIAL REQUIREMENTS ===
    special_reqs = criteria.get("special_requirements", [])
    for req in special_reqs:
        if req == "quiet":
            filters.append(~models.Room.view.ilike("%street%"))
            print("   🤫 Quiet (non-street facing)")
        elif req == "furnished":
            filters.append(and_(
                models.Room.work_desk == True,
                models.Room.work_chair == True,
                models.Room.bedding_provided == True
            ))
            print("   🪑 Furnished")
        elif req == "ready_to_rent":
            filters.append(models.Room.ready_to_rent == True)
            print("   ✅ Ready to rent")
        elif req == "recently_checked":
            # Rooms checked within last 30 days
            thirty_days_ago = datetime.now().date() - datetime.timedelta(days=30)
            filters.append(models.Room.last_check >= thirty_days_ago)
            print("   🔍 Recently checked")
    
    # === BOOKING PREFERENCES ===
    booking_prefs = criteria.get("booking_preferences", {})
    if booking_prefs.get("shared_rent_available"):
        filters.append(models.Room.shared_room_rent_2.isnot(None))
        print("   🤝 Shared rent option available")
    
    print(f"✅ Built {len(filters)} comprehensive room filters")
    return filters

def score_rooms_comprehensively(rooms: List, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Score rooms based on all criteria (basic + advanced)
    """
    print(f"📊 COMPREHENSIVE ROOM SCORING")
    
    scored_rooms = []
    floor_prefs = criteria.get("floor_preferences", {})
    size_reqs = criteria.get("size_requirements", {})
    special_reqs = criteria.get("special_requirements", [])
    
    for room in rooms:
        score = 0
        reasons = []
        
        # Floor scoring
        if floor_prefs.get("prefer_high_floors") and room.floor_number:
            floor_score = min(room.floor_number * 4, 40)
            score += floor_score
            if room.floor_number >= 5:
                reasons.append(f"high floor ({room.floor_number})")
        
        # Size scoring
        if room.sq_footage:
            if room.sq_footage >= 280:
                score += 30
                reasons.append("spacious")
            elif room.sq_footage >= 250:
                score += 20
                reasons.append("good size")
            
            # Bonus for extra space
            size_bonus = min((room.sq_footage - 200) // 10, 25)
            score += size_bonus
        
        # Availability scoring
        if room.booked_till is None or room.booked_till < datetime.now().date():
            if room.ready_to_rent:
                score += 25
                reasons.append("available now")
        
        # Furnished scoring
        if room.work_desk and room.work_chair and room.bedding_provided:
            score += 30
            reasons.append("furnished")
        
        # Quiet scoring
        if room.view and "street" not in room.view.lower():
            score += 20
            reasons.append("quiet location")
        
        # Premium amenities scoring
        amenity_score = 0
        if room.mini_fridge:
            amenity_score += 8
        if room.sink:
            amenity_score += 6
        if room.air_conditioning:
            amenity_score += 10
        if room.heating:
            amenity_score += 8
        if room.cable_tv:
            amenity_score += 5
        
        if amenity_score > 15:
            score += amenity_score
            reasons.append("well-equipped")
        
        # Bathroom bonus
        if room.bathroom_type == "Private":
            score += 35
            reasons.append("private bathroom")
        elif room.bathroom_type == "En-Suite":
            score += 25
            reasons.append("en-suite")
        
        # View bonus
        if room.view:
            view_lower = room.view.lower()
            if "city" in view_lower or "bay" in view_lower:
                score += 25
                reasons.append("premium view")
            elif "garden" in view_lower:
                score += 15
                reasons.append("garden view")
        
        # Bed size bonus
        bed_scores = {"King": 20, "Queen": 15, "Full": 10, "Twin": 5}
        if room.bed_size in bed_scores:
            score += bed_scores[room.bed_size]
            if room.bed_size in ["King", "Queen"]:
                reasons.append(f"{room.bed_size.lower()} bed")
        
        # Recently maintained
        if room.last_check and room.last_check >= (datetime.now().date() - datetime.timedelta(days=30)):
            score += 10
            reasons.append("recently checked")
        
        scored_rooms.append({
            "room": room,
            "score": score,
            "reasons": reasons
        })
    
    scored_rooms.sort(key=lambda x: x["score"], reverse=True)
    print(f"   📈 Scored {len(scored_rooms)} rooms comprehensively")
    return scored_rooms

def execute_comprehensive_room_search(query: str, db: Session) -> Dict[str, Any]:
    """
    Comprehensive room search with all room-level criteria (basic + advanced)
    """
    print(f"🚀 COMPREHENSIVE ROOM SEARCH: '{query}'")
    print("=" * 70)
    
    try:
        # Step 1: Extract all room criteria
        criteria = extract_all_room_criteria_with_llm(query)
        
        # Step 2: Build comprehensive filters
        filters = build_comprehensive_room_filters(criteria, query)
        
        # Step 3: Execute query
        print("💾 EXECUTING COMPREHENSIVE QUERY")
        rooms_query = db.query(models.Room).join(models.Building)
        
        if filters:
            rooms_query = rooms_query.filter(and_(*filters))
        
        # Order by rent first, then we'll re-sort by score
        rooms_query = rooms_query.order_by(models.Room.private_room_rent.asc())
        rooms = rooms_query.limit(5).all()  # Get more for scoring
        
        print(f"✅ Found {len(rooms)} rooms before scoring")
        
        # Step 4: Score and rank rooms
        scored_rooms = score_rooms_comprehensively(rooms, criteria)
        
        # Step 5: Format results (limit to 5 best matches)
        final_rooms = scored_rooms[:5]
        room_data = []
        
        for scored_room in final_rooms:
            room = scored_room["room"]
            building = room.building
            
            room_data.append({
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
                "active_tenants": room.active_tenants,
                "last_check": room.last_check.isoformat() if room.last_check else None,
                "match_score": scored_room["score"],
                "match_reasons": scored_room["reasons"],
                "amenities": {
                    "mini_fridge": room.mini_fridge,
                    "sink": room.sink,
                    "work_desk": room.work_desk,
                    "work_chair": room.work_chair,
                    "heating": room.heating,
                    "air_conditioning": room.air_conditioning,
                    "cable_tv": room.cable_tv,
                    "room_storage": room.room_storage,
                    "bedding_provided": room.bedding_provided
                }
            })
        
        # Step 6: Generate simple response
        if len(room_data) == 0:
            response_text = f"No rooms found matching '{query}'. Try different criteria."
        else:
            prices = [r['private_room_rent'] for r in room_data]
            price_range = f"${min(prices)} - ${max(prices)}"
            top_match = room_data[0]
            
            # Build match reasons (limit to 2)
            reasons = top_match['match_reasons'][:2]
            reasons_text = ', '.join(reasons) if reasons else 'good match'
            
            response_text = f"Found {len(room_data)} rooms matching '{query}'. Price: {price_range}. Top: Room {top_match['room_number']} (Score: {top_match['match_score']}) - {reasons_text}."
        
        return {
            "response": response_text,
            "data": room_data,
            "total_results": len(room_data),
            "search_criteria": criteria,
            "filters_applied": len(filters),
            "query": query,
            "search_type": "comprehensive_room_search"
        }
        
    except Exception as e:
        print(f"❌ COMPREHENSIVE SEARCH ERROR: {e}")
        return {
            "error": str(e),
            "response": "Comprehensive room search failed. Please try again.",
            "data": [],
            "total_results": 0,
            "query": query
        }

# Main function export
def find_buildings_rooms_function(query: str, db: Session) -> Dict[str, Any]:
    """
    Enhanced room search with ALL room-level criteria (v1)
    """
    return execute_comprehensive_room_search(query, db)