# app/ai_services/intelligent_building_room_finder.py

import json
import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.ai_services.gemini_sql_generator import GeminiSQLGenerator
from app.ai_services.sql_executor import SQLExecutor
from app.db.database_constants import DATABASE_DISTINCT_VALUES, validate_value, get_valid_values
from app.ai_services.text_response_formatter import TextResponseFormatter

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_room_and_building_criteria(query: str) -> Dict[str, Any]:
    """
    Extract both room and building criteria from natural language query using LLM.
    Now includes valid database values in the prompt and validates extracted values.
    """
    print(f"🔍 Extracting criteria from: '{query}'")
    
    # Build valid values text for the prompt
    valid_values_text = _build_valid_values_prompt()
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Extract room and building search criteria from this query: "{query}"
            
            {valid_values_text}
            
            Room criteria to look for:
            - Price range (min/max) - interpret keywords:
              * "budget"/"cheap" = $500-$1500
              * "affordable" = $1000-$2000  
              * "mid-range"/"moderate" = $1500-$2500
              * "premium"/"expensive" = $2000-$3500
              * "luxury" = $3000+
            - Room type: "private" (maximum_people_in_room = 1) or "shared" (maximum_people_in_room > 1)
            - Bathroom type: MUST use exact values (Private/Shared/En-Suite)
            - Bed size: MUST use exact values (Twin/Full/Queen/King/Bunk)
            - View preferences: MUST use exact values from list
            - Room amenities: boolean values stored as 'true'/'false' strings (mini_fridge/sink/work_desk/heating/air_conditioning)
            - Floor preferences (numeric range)
            - Room size (sq_footage min/max)
            - Status: default to "Available" unless specified otherwise
            
            Building criteria to look for:
            - Location/area: MUST use exact values (SOMA/North Beach/Mission etc.)
            - Building amenities: boolean values stored as 'true'/'false' strings (wifi_included/laundry_onsite/fitness_area)
            - Pet policy: MUST use exact values (No/Yes/Cats Only/Small Dogs Only)
            - Parking (parking_available boolean)
            - Utilities included (boolean)
            - Lease terms (min_lease_term_max numeric)
            
            Return a JSON object with two sections:
            {{
                "room_filters": {{
                    "price_min": null,
                    "price_max": null,
                    "room_type": null,
                    "bathroom_type": null,
                    "bed_size": null,
                    "view_types": [],
                    "room_amenities": {{
                        "mini_fridge": null,
                        "sink": null,
                        "work_desk": null,
                        "work_chair": null,
                        "heating": null,
                        "air_conditioning": null,
                        "cable_tv": null
                    }},
                    "floor_min": null,
                    "floor_max": null,
                    "sq_footage_min": null,
                    "availability_date": null,
                    "status": "Available"
                }},
                "building_filters": {{
                    "area": null,
                    "building_amenities": {{
                        "wifi_included": null,
                        "laundry_onsite": null,
                        "fitness_area": null,
                        "work_study_area": null,
                        "secure_access": null,
                        "bike_storage": null,
                        "rooftop_access": null
                    }},
                    "pet_friendly": null,
                    "utilities_included": null,
                    "min_lease_term_max": null,
                    "parking_available": null
                }},
                "requires_join": false
            }}
            
            CRITICAL RULES:
            1. Use ONLY the exact valid values provided above - case sensitive!
            2. For price keywords, map to actual numeric ranges
            3. For boolean amenities, use true/false or null
            4. Set requires_join to true if query mentions BOTH room AND building features
            5. Only include non-null values in the response
            6. Default status to "Available" unless user specifies otherwise
            
            Return ONLY valid JSON.
            """,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=500
            )
        )
        
        # Parse response
        response_text = response.text.strip()
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            criteria = json.loads(json_match.group(0))
            
            # Validate and correct extracted values
            criteria = _validate_extracted_criteria(criteria)
            
            print(f"✅ Criteria extracted and validated successfully")
            return criteria
        else:
            print(f"⚠️ Failed to extract JSON, using defaults")
            return {"room_filters": {}, "building_filters": {}, "requires_join": False}
            
    except Exception as e:
        print(f"❌ Error extracting criteria: {e}")
        return {"room_filters": {}, "building_filters": {}, "requires_join": False}


def _build_valid_values_prompt() -> str:
    """Build a concise prompt section with valid database values."""
    prompt_parts = ["VALID DATABASE VALUES (use these EXACT values):"]
    
    # Room values
    room_values = DATABASE_DISTINCT_VALUES.get("rooms", {}).get("text_columns", {})
    prompt_parts.append("\nRoom values:")
    prompt_parts.append(f"- Status: {', '.join(room_values.get('status', []))}")
    prompt_parts.append(f"- Bathroom types: {', '.join(room_values.get('bathroom_type', []))}")
    prompt_parts.append(f"- Bed sizes: {', '.join(room_values.get('bed_size', []))}")
    prompt_parts.append(f"- Views: {', '.join(room_values.get('view', []))}")
    
    # Building values
    building_values = DATABASE_DISTINCT_VALUES.get("buildings", {}).get("text_columns", {})
    prompt_parts.append("\nBuilding values:")
    prompt_parts.append(f"- Areas: {', '.join(building_values.get('area', []))}")
    prompt_parts.append(f"- Pet policies: {', '.join(building_values.get('pet_friendly', []))}")
    
    return '\n'.join(prompt_parts)


def _validate_extracted_criteria(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and correct extracted criteria against known valid values."""
    
    # Validate room filters
    room_filters = criteria.get('room_filters', {})
    if room_filters:
        # Validate text columns
        for column in ['status', 'bathroom_type', 'bed_size']:
            if room_filters.get(column):
                is_valid, corrected = validate_value('rooms', column, room_filters[column])
                if not is_valid and corrected:
                    print(f"  Corrected room {column}: '{room_filters[column]}' -> '{corrected}'")
                    room_filters[column] = corrected
        
        # Validate view_types array
        if room_filters.get('view_types'):
            corrected_views = []
            for view in room_filters['view_types']:
                is_valid, corrected = validate_value('rooms', 'view', view)
                if corrected:
                    corrected_views.append(corrected)
            room_filters['view_types'] = corrected_views
    
    # Validate building filters
    building_filters = criteria.get('building_filters', {})
    if building_filters:
        # Validate area
        if building_filters.get('area'):
            is_valid, corrected = validate_value('buildings', 'area', building_filters['area'])
            if not is_valid and corrected:
                print(f"  Corrected building area: '{building_filters['area']}' -> '{corrected}'")
                building_filters['area'] = corrected
        
        # Validate pet_friendly
        if building_filters.get('pet_friendly'):
            is_valid, corrected = validate_value('buildings', 'pet_friendly', building_filters['pet_friendly'])
            if not is_valid and corrected:
                print(f"  Corrected pet_friendly: '{building_filters['pet_friendly']}' -> '{corrected}'")
                building_filters['pet_friendly'] = corrected
    
    # Update criteria with validated values
    criteria['room_filters'] = room_filters
    criteria['building_filters'] = building_filters
    
    return criteria


def prepare_sql_requirements(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert extracted criteria into SQL generator requirements.
    Updated to ensure proper filter naming for SQL generation.
    """
    room_filters = criteria.get('room_filters', {})
    building_filters = criteria.get('building_filters', {})
    requires_join = criteria.get('requires_join', False)
    
    # ALWAYS include buildings table for room searches to get building info
    # This is the key change - force join for any room search
    tables = ['rooms', 'buildings']
    requires_join = True  # Always join to get building info
    
    # Prepare filters for SQL generator
    all_filters = {}
    
    # Room filters
    for key, value in room_filters.items():
        if value is not None:
            if key == 'room_amenities':
                # Flatten amenities - prefix with 'room_' for clarity
                for amenity, enabled in value.items():
                    if enabled is not None:
                        all_filters[f'room_{amenity}'] = enabled
            elif key == 'view_types' and isinstance(value, list) and value:
                # Handle multiple view types
                all_filters['view_types'] = value
            else:
                all_filters[key] = value
    
    # Building filters  
    for key, value in building_filters.items():
        if value is not None:
            if key == 'building_amenities':
                # Flatten amenities - prefix with 'building_'
                for amenity, enabled in value.items():
                    if enabled is not None:
                        all_filters[f'building_{amenity}'] = enabled
            else:
                all_filters[f'building_{key}'] = value
    
    # Prepare joins - ALWAYS include this for room searches
    joins = [{
        "from": "rooms",
        "to": "buildings",
        "on": "building_id",
        "type": "INNER"
    }]
    
    # Default ordering
    order_by = [
        {"column": "private_room_rent", "direction": "ASC"},
        {"column": "room_number", "direction": "ASC"}
    ]
    
    return {
        "filters": all_filters,
        "query_type": "search",
        "tables": tables,
        "joins": joins,
        "order_by": order_by,
        "limit": 15
    }


def unified_room_search_function(query: str, **kwargs) -> Dict[str, Any]:
    """
    Unified room search function that handles both room and building criteria.
    Replaces v1 and v2 room finders.
    """
    print(f"🏠 UNIFIED ROOM SEARCH: '{query}'")
    print("=" * 70)
    
    try:
        # Step 1: Extract criteria using LLM
        criteria = extract_room_and_building_criteria(query)
        
        # Step 2: Prepare SQL requirements
        sql_requirements = prepare_sql_requirements(criteria)
        
        # Step 3: Generate SQL
        sql_generator = GeminiSQLGenerator()
        sql_result = sql_generator.generate_sql(**sql_requirements)
        
        if not sql_result.get('success') or not sql_result.get('sql'):
            return {
                "success": False,
                "response": f"Failed to generate search query: {sql_result.get('explanation', 'Unknown error')}",
                "data": [],
                "query": query
            }
        
        print(f"📝 Generated SQL: {sql_result['sql']}")
        
        # Step 4: Execute SQL
        executor = SQLExecutor()
        results = executor.execute_query(sql_result['sql'])
        
        if results['success']:
            data = results['data']
            
            # Format response
            if len(data) == 0:
                response_text = f"No rooms found matching '{query}'. Try adjusting your criteria."
            else:
                # Get price range
                prices = [r.get('private_room_rent', 0) for r in data if r.get('private_room_rent')]
                if prices:
                    price_range = f"${min(prices):,.0f} - ${max(prices):,.0f}"
                    response_text = f"Found {len(data)} rooms matching '{query}'. Price range: {price_range}."
                else:
                    response_text = f"Found {len(data)} rooms matching '{query}'."
            
            return {
                "success": True,
                "response": response_text,
                "data": data,
                "total_results": len(data),
                "search_criteria": criteria,
                "sql_query": sql_result['sql'],
                "query": query
            }
        else:
            return {
                "success": False,
                "response": f"Error executing search: {results.get('error', 'Unknown error')}",
                "data": [],
                "query": query
            }
            
    except Exception as e:
        print(f"❌ UNIFIED SEARCH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "response": f"Search failed: {str(e)}",
            "data": [],
            "query": query
        }


def extract_bed_search_criteria(query: str) -> Dict[str, Any]:
    """
    Extract bed-specific search criteria from natural language query.
    Handles queries like "find a bed under $800" or "available beds in SOMA".
    """
    print(f"🛏️ Extracting bed criteria from: '{query}'")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Extract BED search criteria from this query: "{query}"

            This is for searching individual BEDS within rooms, not entire rooms.
            Each room can have multiple beds, each with its own:
            - rent (price per bed)
            - status (Available, Reserved, Occupied)
            - availableFrom/availableUntil dates
            - bedType (Single, Double, Queen, King, Bunk)
            - view

            Extract:
            {{
                "max_rent": null,           // Maximum bed rent (e.g., "under $800" -> 800)
                "min_rent": null,           // Minimum bed rent
                "status": "Available",       // Bed status filter (default: Available)
                "bed_type": null,           // Specific bed type
                "available_from": null,     // Date bed should be available from
                "city": null,               // City filter from building
                "area": null,               // Area filter (SOMA, Mission, etc.)
                "building_id": null         // Specific building
            }}

            Price keywords:
            - "cheap"/"budget" = max $800
            - "affordable" = max $1000
            - "under $X" = max X
            - "around $X" = min X-200, max X+200

            Return ONLY valid JSON.
            """,
            config=GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=300
            )
        )

        response_text = response.text.strip()
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

        if json_match:
            criteria = json.loads(json_match.group(0))
            print(f"✅ Bed criteria extracted: {criteria}")
            return criteria
        else:
            print(f"⚠️ Failed to extract bed criteria JSON")
            return {"status": "Available"}

    except Exception as e:
        print(f"❌ Error extracting bed criteria: {e}")
        return {"status": "Available"}


def unified_bed_search_function(query: str, **kwargs) -> Dict[str, Any]:
    """
    Unified bed search function that searches for individual BEDS within rooms.
    Handles queries like "find a bed under $800" or "available beds".

    Returns bed-level results with room and building context.
    """
    print(f"🛏️ UNIFIED BED SEARCH: '{query}'")
    print("=" * 70)

    try:
        # Step 1: Extract bed-specific criteria
        criteria = extract_bed_search_criteria(query)

        # Step 2: Build SQL to get rooms with bed configuration
        # Note: Bed-level fields (min_rent, max_rent, etc.) are stored inside beds_configuration JSON
        # We fetch all rooms with beds_configuration and do filtering in Python
        sql_parts = [
            """
            SELECT
                r.room_id,
                r.room_number,
                r.room_type,
                r.floor_number,
                r.bathroom_type,
                r.beds_configuration,
                r.private_room_rent,
                b.building_id,
                b.building_name,
                b.city,
                b.full_address,
                b.state,
                b.area
            FROM rooms r
            INNER JOIN buildings b ON r.building_id = b.building_id
            WHERE r.ready_to_rent = true
            AND r.beds_configuration IS NOT NULL
            """
        ]

        # Add building-level pre-filters (these columns exist)
        # Using parameterized-style filtering to prevent SQL injection
        # Note: Values are sanitized by removing dangerous characters
        def sanitize_sql_value(value: str) -> str:
            """Remove characters that could be used for SQL injection"""
            if not value:
                return ''
            # Remove quotes, semicolons, and SQL comment markers
            dangerous_chars = ["'", '"', ';', '--', '/*', '*/', '\\']
            sanitized = str(value)
            for char in dangerous_chars:
                sanitized = sanitized.replace(char, '')
            return sanitized.strip()

        if criteria.get('city'):
            safe_city = sanitize_sql_value(criteria['city'])
            sql_parts.append(f"AND LOWER(b.city) LIKE LOWER('%{safe_city}%')")
        if criteria.get('area'):
            safe_area = sanitize_sql_value(criteria['area'])
            sql_parts.append(f"AND LOWER(b.area) LIKE LOWER('%{safe_area}%')")
        if criteria.get('building_id'):
            safe_building_id = sanitize_sql_value(criteria['building_id'])
            sql_parts.append(f"AND r.building_id = '{safe_building_id}'")

        # Order by private_room_rent as proxy (bed filtering happens in Python)
        sql_parts.append("ORDER BY r.private_room_rent ASC NULLS LAST LIMIT 100")

        sql = '\n'.join(sql_parts)
        print(f"📝 Generated SQL: {sql}")

        # Step 3: Execute SQL
        executor = SQLExecutor()
        results = executor.execute_query(sql)

        if not results['success']:
            return {
                "success": False,
                "response": f"Error searching beds: {results.get('error', 'Unknown error')}",
                "data": [],
                "beds": [],
                "query": query
            }

        # Step 4: Parse beds from each room and filter at bed level
        beds = []
        for room in results['data']:
            # Try beds_configuration first, then bed_configurations
            beds_config = room.get('beds_configuration') or room.get('bed_configurations')

            if not beds_config:
                continue

            # Parse JSON if string
            if isinstance(beds_config, str):
                try:
                    beds_config = json.loads(beds_config)
                except:
                    continue

            # Handle both old format (list) and new format (object with beds array)
            beds_list = []
            if isinstance(beds_config, list):
                # Old format: direct list of beds
                beds_list = beds_config
            elif isinstance(beds_config, dict):
                # New format: {beds: [...], min_rent: ..., max_rent: ..., ...}
                beds_list = beds_config.get('beds', [])
            else:
                continue

            if not beds_list:
                continue

            # Filter and collect individual beds
            for bed in beds_list:
                # Apply bed-level filters
                bed_rent = bed.get('rent')
                bed_status = bed.get('status', 'Available')

                # Price filter
                if criteria.get('max_rent') and bed_rent and bed_rent > criteria['max_rent']:
                    continue
                if criteria.get('min_rent') and bed_rent and bed_rent < criteria['min_rent']:
                    continue

                # Status filter
                if criteria.get('status') and bed_status != criteria['status']:
                    continue

                # Bed type filter
                if criteria.get('bed_type') and bed.get('bedType') != criteria['bed_type']:
                    continue

                # Build bed result with room and building context
                floor_num = room.get('floor_number')
                room_num = room['room_number']
                bathroom = room.get('bathroom_type', '')

                # Create unique room display name to differentiate same room numbers
                # Format: "Room 12 (Floor 1, Private Bath)" or "Room 12 (Floor 2, Shared Bath)"
                room_display_parts = [f"Room {room_num}"]
                differentiators = []
                if floor_num:
                    differentiators.append(f"Floor {floor_num}")
                if bathroom:
                    differentiators.append(f"{bathroom} Bath")
                if differentiators:
                    room_display_name = f"Room {room_num} ({', '.join(differentiators)})"
                else:
                    room_display_name = f"Room {room_num}"

                beds.append({
                    # Bed details
                    "bed_id": bed.get('bed_id', f"{room['room_id']}_BED_unknown"),
                    "bedName": bed.get('bedName', 'Unnamed Bed'),
                    "bedType": bed.get('bedType'),
                    "rent": bed_rent,
                    "status": bed_status,
                    "availableFrom": bed.get('availableFrom'),
                    "availableUntil": bed.get('availableUntil'),
                    "view": bed.get('view'),
                    "maxOccupancy": bed.get('maxOccupancy', 1),
                    # Room context
                    "room_id": room['room_id'],
                    "room_number": room_num,
                    "room_display_name": room_display_name,  # NEW: Unique display name
                    "room_type": room.get('room_type'),
                    "floor_number": floor_num,
                    "bathroom_type": bathroom,
                    # Building context
                    "building_id": room.get('building_id'),
                    "building_name": room.get('building_name'),
                    "building_city": room.get('city'),
                    "building_address": room.get('full_address'),
                    "building_state": room.get('state'),
                    "building_area": room.get('area')
                })

        # Sort by rent (cheapest first)
        beds.sort(key=lambda x: x.get('rent') or float('inf'))

        print(f"✅ Found {len(beds)} beds")

        # Step 5: Format response using TextResponseFormatter for rich markdown
        format_type = kwargs.get('format_type', 'web')

        if len(beds) == 0:
            response_text = f"No beds found matching '{query}'. Try adjusting your search criteria."
        else:
            # Use TextResponseFormatter for rich markdown response
            try:
                formatter = TextResponseFormatter()

                # Run async formatter in sync context
                def run_formatter():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        return loop.run_until_complete(
                            formatter.format_response(
                                data=beds,
                                original_query=query,
                                result_type="bed_search",
                                format_type=format_type
                            )
                        )
                    finally:
                        loop.close()

                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(run_formatter)
                    response_text = future.result()

                print(f"✅ TextResponseFormatter generated response ({len(response_text)} chars)")

            except Exception as format_error:
                print(f"⚠️ TextResponseFormatter failed, using fallback: {format_error}")
                # Fallback to basic response
                prices = [b['rent'] for b in beds if b.get('rent')]
                if prices:
                    price_range = f"${min(prices):,.0f} - ${max(prices):,.0f}"
                    response_text = f"🛏️ Found {len(beds)} beds matching '{query}'. Price range: {price_range}/month."
                else:
                    response_text = f"🛏️ Found {len(beds)} beds matching '{query}'."

        return {
            "success": True,
            "response": response_text,
            "data": beds,  # For compatibility
            "beds": beds,  # Explicit bed results
            "total_results": len(beds),
            "search_criteria": criteria,
            "query": query,
            "search_type": "beds"  # Indicate this is a bed search
        }

    except Exception as e:
        print(f"❌ BED SEARCH ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "response": f"Bed search failed: {str(e)}",
            "data": [],
            "beds": [],
            "query": query
        }


def is_bed_search_query(query: str) -> bool:
    """
    Determine if a query is asking about individual beds vs rooms.
    """
    query_lower = query.lower()

    # Keywords that indicate bed-level search
    bed_keywords = [
        'bed under', 'bed below', 'bed for', 'beds under', 'beds below',
        'cheapest bed', 'affordable bed', 'budget bed',
        'single bed', 'available bed', 'find a bed', 'find bed',
        'bed in', 'beds in', 'bed at', 'beds at',
        'individual bed', 'one bed', 'per bed'
    ]

    for keyword in bed_keywords:
        if keyword in query_lower:
            return True

    # Check for price + bed pattern
    if re.search(r'\$?\d+.*bed|bed.*\$?\d+', query_lower):
        return True

    return False