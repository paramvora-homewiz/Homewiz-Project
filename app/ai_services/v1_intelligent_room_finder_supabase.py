# app/ai_services/v1_intelligent_room_finder_supabase.py
# Enhanced: ALL room-level filtering using Supabase client

import json
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
from google import genai
from app.config import GEMINI_API_KEY
from app.db.supabase_connection import get_supabase
from google.genai.types import GenerateContentConfig

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_all_room_criteria_with_llm(query: str) -> Dict[str, Any]:
    """
    Extract ALL room-level criteria (basic + advanced) using LLM
    """
    print(f"🤖 EXTRACTING ALL ROOM CRITERIA: '{query}'")
    
    # Default criteria structure
    default_criteria = {
        "price_min": None, "price_max": None, "view_types": [], "bathroom_type": None,
        "bed_size": None, "bed_type": None, "room_type": None, "amenities_required": [],
        "budget_level": None, "floor_preferences": {}, "size_requirements": {},
        "availability": {}, "occupancy": {}, "special_requirements": []
    }
    
    try:
        # Use simpler prompt to reduce JSON errors
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Extract room search criteria from this query: "{query}"
            
            Look for:
            - Price range (min/max)
            - Room type (private/shared)
            - Bathroom type (Private/Shared/En-Suite)
            - Bed size (Twin/Full/Queen/King)
            - View preferences (city/bay/garden/street)
            - Amenities (fridge/sink/desk/chair/heating/ac/tv/storage/bedding)
            - Floor preferences
            - Special requirements (quiet/furnished/ready to rent)
            
            Return a simple JSON object with only the criteria found in the query.
            Example: {{"price_max": 2000, "bathroom_type": "Private", "view_types": ["city"]}}
            
            IMPORTANT: Return ONLY valid JSON, no other text.
            """,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=200
            )
        )
        
        # Parse response with fallback handling
        response_text = response.text.strip()
        
        # Try to extract and clean JSON
        if '{' in response_text and '}' in response_text:
            # Extract JSON portion
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_text = response_text[start:end]
            
            # Clean common issues
            json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)  # Remove trailing commas
            
            try:
                extracted = json.loads(json_text)
                # Merge with defaults
                criteria = default_criteria.copy()
                criteria.update(extracted)
                print(f"✅ Room criteria extracted successfully")
                return criteria
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse error: {e}, using fallback parsing")
        
        # Fallback: Basic keyword extraction
        query_lower = query.lower()
        criteria = default_criteria.copy()
        
        # Price extraction
        price_match = re.search(r'under\s*\$?(\d+)', query_lower)
        if price_match:
            criteria["price_max"] = int(price_match.group(1))
        
        # Bathroom type
        if "private bathroom" in query_lower:
            criteria["bathroom_type"] = "Private"
        elif "shared bathroom" in query_lower:
            criteria["bathroom_type"] = "Shared"
        
        # Room type
        if "private room" in query_lower:
            criteria["room_type"] = "private"
        elif "shared room" in query_lower:
            criteria["room_type"] = "shared"
        
        # Bed size
        for bed in ["twin", "full", "queen", "king"]:
            if bed in query_lower:
                criteria["bed_size"] = bed.capitalize()
                break
        
        # View types
        views = []
        for view in ["city", "bay", "garden", "street"]:
            if f"{view} view" in query_lower:
                views.append(view)
        if views:
            criteria["view_types"] = views
        
        print(f"✅ Room criteria extracted via fallback")
        return criteria
        
    except Exception as e:
        print(f"❌ LLM extraction failed: {e}, using defaults")
        return default_criteria

def build_supabase_room_query(criteria: Dict[str, Any], original_query: str):
    """
    Build Supabase query with comprehensive room filters
    """
    print(f"🔧 BUILDING SUPABASE QUERY")
    
    supabase = get_supabase()
    query = supabase.table('rooms').select('*, buildings(*)')
    query_lower = original_query.lower()
    
    # === PRICE FILTERS ===
    if criteria.get("price_min"):
        query = query.gte('private_room_rent', criteria["price_min"])
        print(f"   💰 Min price: ${criteria['price_min']}")
    
    if criteria.get("price_max"):
        query = query.lte('private_room_rent', criteria["price_max"])
        print(f"   💰 Max price: ${criteria['price_max']}")
    
    # Budget level
    if criteria.get("budget_level") and not criteria.get("price_max"):
        if criteria["budget_level"] == "budget":
            query = query.lte('private_room_rent', 1800)
            print("   💰 Budget: <= $1800")
        elif criteria["budget_level"] == "luxury":
            query = query.gte('private_room_rent', 3500)
            print("   💰 Luxury: >= $3500")
    
    # === VIEW FILTERS ===
    view_types = criteria.get("view_types", [])
    if view_types:
        view_filters = []
        for view in view_types:
            view_filters.append(f"view.ilike.%{view}%")
        if view_filters:
            query = query.or_(','.join(view_filters))
            print(f"   🏞️ Views: {', '.join(view_types)}")
    
    # === BATHROOM FILTERS ===
    if criteria.get("bathroom_type"):
        query = query.eq('bathroom_type', criteria["bathroom_type"])
        print(f"   🚿 Bathroom: {criteria['bathroom_type']}")
    
    # === BED FILTERS ===
    if criteria.get("bed_size"):
        query = query.eq('bed_size', criteria["bed_size"])
        print(f"   🛏️ Bed size: {criteria['bed_size']}")
    
    if criteria.get("bed_type"):
        query = query.eq('bed_type', criteria["bed_type"])
        print(f"   🛏️ Bed type: {criteria['bed_type']}")
    
    # === ROOM TYPE FILTERS ===
    room_type = criteria.get("room_type")
    if room_type:
        if room_type == "private":
            query = query.eq('maximum_people_in_room', 1)
            print("   🏠 Private room")
        elif room_type == "shared":
            query = query.gt('maximum_people_in_room', 1)
            print("   🏠 Shared room")
    
    # === AMENITY FILTERS ===
    amenity_column_map = {
        'fridge': 'mini_fridge',
        'sink': 'sink',
        'desk': 'work_desk',
        'chair': 'work_chair',
        'heating': 'heating',
        'ac': 'air_conditioning',
        'tv': 'cable_tv',
        'storage': 'room_storage',
        'bedding': 'bedding_provided'
    }
    
    amenities_required = criteria.get("amenities_required", [])
    for amenity in amenities_required:
        if amenity in amenity_column_map:
            query = query.eq(amenity_column_map[amenity], True)
            print(f"   🔧 Required amenity: {amenity}")
    
    # === FLOOR PREFERENCES ===
    floor_prefs = criteria.get("floor_preferences", {})
    if floor_prefs.get("min_floor"):
        query = query.gte('floor_number', floor_prefs["min_floor"])
        print(f"   🏢 Min floor: {floor_prefs['min_floor']}")
    
    if floor_prefs.get("max_floor"):
        query = query.lte('floor_number', floor_prefs["max_floor"])
        print(f"   🏢 Max floor: {floor_prefs['max_floor']}")
    
    if floor_prefs.get("prefer_high_floors"):
        query = query.gte('floor_number', 5)
        print("   🏢 High floors (5+)")
    
    # === SIZE REQUIREMENTS ===
    size_reqs = criteria.get("size_requirements", {})
    if size_reqs.get("min_sq_footage"):
        query = query.gte('sq_footage', size_reqs["min_sq_footage"])
        print(f"   📐 Min sq ft: {size_reqs['min_sq_footage']}")
    
    if size_reqs.get("spacious"):
        query = query.gte('sq_footage', 280)
        print("   📐 Spacious rooms (280+ sq ft)")
    
    # === AVAILABILITY FILTERS ===
    availability = criteria.get("availability", {})
    if availability.get("immediate"):
        query = query.eq('ready_to_rent', True)
        today = datetime.now().date().isoformat()
        query = query.or_(f'booked_till.lt.{today},booked_till.is.null')
        print("   📅 Immediate availability")
    
    move_in_date = availability.get("move_in_date")
    if move_in_date:
        query = query.eq('ready_to_rent', True)
        query = query.or_(f'booked_till.lt.{move_in_date},booked_till.is.null')
        print(f"   📅 Available by: {move_in_date}")
    
    # === OCCUPANCY FILTERS ===
    occupancy = criteria.get("occupancy", {})
    if occupancy.get("single_only"):
        query = query.eq('maximum_people_in_room', 1)
        print("   👤 Single occupancy only")
    
    # === SPECIAL REQUIREMENTS ===
    special_reqs = criteria.get("special_requirements", [])
    for req in special_reqs:
        if req == "quiet":
            query = query.not_.ilike('view', '%street%')
            print("   🤫 Quiet (non-street facing)")
        elif req == "furnished":
            query = query.eq('work_desk', True).eq('work_chair', True).eq('bedding_provided', True)
            print("   🪑 Furnished")
        elif req == "ready_to_rent":
            query = query.eq('ready_to_rent', True)
            print("   ✅ Ready to rent")
    
    print(f"✅ Built comprehensive Supabase query")
    return query

def score_rooms_comprehensively(rooms: List[Dict], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Score rooms based on all criteria
    """
    print(f"📊 COMPREHENSIVE ROOM SCORING")
    
    scored_rooms = []
    
    for room in rooms:
        score = 0
        reasons = []
        
        # Floor scoring
        floor_prefs = criteria.get("floor_preferences", {})
        if floor_prefs.get("prefer_high_floors") and room.get('floor_number'):
            floor_score = min(room['floor_number'] * 4, 40)
            score += floor_score
            if room['floor_number'] >= 5:
                reasons.append(f"high floor ({room['floor_number']})")
        
        # Size scoring
        if room.get('sq_footage'):
            if room['sq_footage'] >= 280:
                score += 30
                reasons.append("spacious")
            elif room['sq_footage'] >= 250:
                score += 20
                reasons.append("good size")
        
        # Availability scoring
        if not room.get('booked_till') or (room.get('booked_till') and room['booked_till'] < datetime.now().date().isoformat()):
            if room.get('ready_to_rent'):
                score += 25
                reasons.append("available now")
        
        # Furnished scoring
        if room.get('work_desk') and room.get('work_chair') and room.get('bedding_provided'):
            score += 30
            reasons.append("furnished")
        
        # Quiet scoring
        if room.get('view') and "street" not in room['view'].lower():
            score += 20
            reasons.append("quiet location")
        
        # Premium amenities scoring
        amenity_score = 0
        if room.get('mini_fridge'): amenity_score += 8
        if room.get('sink'): amenity_score += 6
        if room.get('air_conditioning'): amenity_score += 10
        if room.get('heating'): amenity_score += 8
        if room.get('cable_tv'): amenity_score += 5
        
        if amenity_score > 15:
            score += amenity_score
            reasons.append("well-equipped")
        
        # Bathroom bonus
        if room.get('bathroom_type') == "Private":
            score += 35
            reasons.append("private bathroom")
        elif room.get('bathroom_type') == "En-Suite":
            score += 25
            reasons.append("en-suite")
        
        # View bonus
        if room.get('view'):
            view_lower = room['view'].lower()
            if "city" in view_lower or "bay" in view_lower:
                score += 25
                reasons.append("premium view")
            elif "garden" in view_lower:
                score += 15
                reasons.append("garden view")
        
        # Bed size bonus
        bed_scores = {"King": 20, "Queen": 15, "Full": 10, "Twin": 5}
        if room.get('bed_size') in bed_scores:
            score += bed_scores[room['bed_size']]
            if room['bed_size'] in ["King", "Queen"]:
                reasons.append(f"{room['bed_size'].lower()} bed")
        
        scored_rooms.append({
            "room": room,
            "score": score,
            "reasons": reasons
        })
    
    scored_rooms.sort(key=lambda x: x["score"], reverse=True)
    print(f"   📈 Scored {len(scored_rooms)} rooms comprehensively")
    return scored_rooms

def execute_comprehensive_room_search(query: str) -> Dict[str, Any]:
    """
    Comprehensive room search with all room-level criteria using Supabase
    """
    print(f"🚀 COMPREHENSIVE ROOM SEARCH: '{query}'")
    print("=" * 70)
    
    try:
        # Step 1: Extract all room criteria
        criteria = extract_all_room_criteria_with_llm(query)
        
        # Step 2: Build and execute Supabase query
        supabase_query = build_supabase_room_query(criteria, query)
        
        # Step 3: Execute query
        print("💾 EXECUTING SUPABASE QUERY")
        response = supabase_query.order('private_room_rent', desc=False).limit(50).execute()
        rooms = response.data
        
        print(f"✅ Found {len(rooms)} rooms before scoring")
        
        # Step 4: Score and rank rooms
        scored_rooms = score_rooms_comprehensively(rooms, criteria)
        
        # Step 5: Format results (limit to 5 best matches)
        final_rooms = scored_rooms[:5]
        room_data = []
        
        for scored_room in final_rooms:
            room = scored_room["room"]
            building = room.get('buildings', {})
            
            room_data.append({
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
                "active_tenants": room.get('active_tenants'),
                "last_check": room.get('last_check'),
                "match_score": scored_room["score"],
                "match_reasons": scored_room["reasons"],
                "amenities": {
                    "mini_fridge": room.get('mini_fridge'),
                    "sink": room.get('sink'),
                    "work_desk": room.get('work_desk'),
                    "work_chair": room.get('work_chair'),
                    "heating": room.get('heating'),
                    "air_conditioning": room.get('air_conditioning'),
                    "cable_tv": room.get('cable_tv'),
                    "room_storage": room.get('room_storage'),
                    "bedding_provided": room.get('bedding_provided')
                }
            })
        
        # Step 6: Generate simple response
        if len(room_data) == 0:
            response_text = f"No rooms found matching '{query}'. Try different criteria."
        else:
            prices = [r['private_room_rent'] for r in room_data if r['private_room_rent']]
            if prices:
                price_range = f"${min(prices)} - ${max(prices)}"
                top_match = room_data[0]
                
                # Build match reasons (limit to 2)
                reasons = top_match['match_reasons'][:2]
                reasons_text = ', '.join(reasons) if reasons else 'good match'
                
                response_text = f"Found {len(room_data)} rooms matching '{query}'. Price: {price_range}. Top: Room {top_match['room_number']} (Score: {top_match['match_score']}) - {reasons_text}."
            else:
                response_text = f"Found {len(room_data)} rooms matching '{query}'."
        
        return {
            "response": response_text,
            "data": room_data,
            "total_results": len(room_data),
            "search_criteria": criteria,
            "query": query,
            "search_type": "comprehensive_room_search"
        }
        
    except Exception as e:
        print(f"❌ COMPREHENSIVE SEARCH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "response": "Comprehensive room search failed. Please try again.",
            "data": [],
            "total_results": 0,
            "query": query
        }

# Main function export
def find_buildings_rooms_function(query: str, **kwargs) -> Dict[str, Any]:
    """
    Enhanced room search with ALL room-level criteria (v1) - Supabase version
    Note: db parameter removed as we use Supabase client directly
    """
    return execute_comprehensive_room_search(query)