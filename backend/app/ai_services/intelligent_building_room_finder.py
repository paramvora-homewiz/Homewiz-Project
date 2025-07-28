# app/ai_services/unified_room_finder.py

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from google import genai
from app.config import GEMINI_API_KEY
from google.genai.types import GenerateContentConfig
from app.ai_services.gemini_sql_generator import GeminiSQLGenerator
from app.ai_services.sql_executor import SQLExecutor  # We'll create this next

client = genai.Client(api_key=GEMINI_API_KEY)

def extract_room_and_building_criteria(query: str) -> Dict[str, Any]:
    """
    Extract both room and building criteria from natural language query using LLM.
    """
    print(f"🔍 Extracting criteria from: '{query}'")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Extract room and building search criteria from this query: "{query}"
            
            Room criteria to look for:
            - Price range (min/max)
            - Room type (private/shared)
            - Bathroom type (Private/Shared/En-Suite)
            - Bed size (Twin/Full/Queen/King)
            - View preferences (Street View/Courtyard/Limited View)
            - Room amenities (mini_fridge/sink/work_desk/work_chair/heating/air_conditioning/cable_tv)
            - Floor preferences
            - Room size (sq_footage)
            - Availability dates
            
            Building criteria to look for:
            - Location/area (SOMA/North Beach/Mission/etc)
            - Building amenities (wifi_included/laundry_onsite/fitness_area/work_study_area/secure_access)
            - Pet policy
            - Parking
            - Utilities included
            - Lease terms
            
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
            
            Set requires_join to true if query mentions both room and building features.
            Only include non-null values in the response.
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
            print(f"✅ Criteria extracted successfully")
            return criteria
        else:
            print(f"⚠️ Failed to extract JSON, using defaults")
            return {"room_filters": {}, "building_filters": {}, "requires_join": False}
            
    except Exception as e:
        print(f"❌ Error extracting criteria: {e}")
        return {"room_filters": {}, "building_filters": {}, "requires_join": False}


def prepare_sql_requirements(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert extracted criteria into SQL generator requirements.
    """
    room_filters = criteria.get('room_filters', {})
    building_filters = criteria.get('building_filters', {})
    requires_join = criteria.get('requires_join', False)
    
    # Determine tables needed
    tables = ['rooms']
    if requires_join or any(building_filters.values()):
        tables.append('buildings')
        requires_join = True
    
    # Prepare filters for SQL generator
    all_filters = {}
    
    # Room filters
    for key, value in room_filters.items():
        if value is not None:
            if key == 'room_amenities':
                # Flatten amenities
                for amenity, enabled in value.items():
                    if enabled is not None:
                        all_filters[f'room_{amenity}'] = enabled
            else:
                all_filters[key] = value
    
    # Building filters
    for key, value in building_filters.items():
        if value is not None:
            if key == 'building_amenities':
                # Flatten amenities
                for amenity, enabled in value.items():
                    if enabled is not None:
                        all_filters[f'building_{amenity}'] = enabled
            else:
                all_filters[f'building_{key}'] = value
    
    # Prepare joins if needed
    joins = []
    if requires_join:
        joins.append({
            "from": "rooms",
            "to": "buildings",
            "on": "building_id",
            "type": "INNER"
        })
    
    # Default ordering
    order_by = [
        {"column": "private_room_rent", "direction": "ASC"},
        {"column": "room_number", "direction": "ASC"}
    ]
    
    return {
        "filters": all_filters,
        "query_type": "search",
        "tables": tables,
        "joins": joins if joins else None,
        "order_by": order_by,
        "limit": 50
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


# Test function
def test_unified_search():
    """Test the unified room search with various queries."""
    
    test_queries = [
        "Show me available rooms under $2000 with private bathroom",
        "Find rooms in SOMA with wifi and laundry in the building",
        "I need a room with street view, gym in building, and parking",
        "Rooms under $1800 with mini fridge and work desk"
    ]
    
    print("🧪 Testing Unified Room Search")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n📍 Query: {query}")
        result = unified_room_search_function(query)
        
        print(f"Success: {result['success']}")
        print(f"Response: {result['response']}")
        if result.get('search_criteria'):
            print(f"Criteria: {json.dumps(result['search_criteria'], indent=2)}")
        print("-" * 50)


if __name__ == "__main__":
    test_unified_search()