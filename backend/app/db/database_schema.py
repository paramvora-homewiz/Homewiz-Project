# app/ai_services/database_schema.py

"""
Database Schema for HomeWiz Property Management System
This file contains the complete database schema information needed for SQL generation.
Updated to match the actual PostgreSQL database structure.
"""

DATABASE_SCHEMA = {
    "description": "HomeWiz Property Management System - PostgreSQL Database Schema",
    "tables": {
        "operators": {
            "description": "Property management staff and operators",
            "columns": {
                "operator_id": {"type": "BIGINT", "primary_key": True, "nullable": False, "auto_increment": True, "description": "Unique identifier for operator"},
                "name": {"type": "TEXT", "nullable": True, "description": "Full name of the operator"},
                "email": {"type": "TEXT", "nullable": True, "description": "Email address of the operator"},
                "phone": {"type": "TEXT", "nullable": True, "description": "Phone number of the operator"},
                "role": {"type": "TEXT", "nullable": True, "description": "Role of the operator (Property Manager, Assistant Manager, etc.)"},
                "active": {"type": "BOOLEAN", "nullable": True, "description": "Whether the operator is currently active"},
                "date_joined": {"type": "TEXT", "nullable": True, "description": "Date when operator joined"},
                "last_active": {"type": "TEXT", "nullable": True, "description": "Last active date of operator"},
                "operator_type": {"type": "TEXT", "nullable": True, "description": "Type of operator (LEASING_AGENT, MAINTENANCE, BUILDING_MANAGER, ADMIN)"},
                "permissions": {"type": "TEXT", "nullable": True, "description": "JSON string of permission flags"},
                "notification_preferences": {"type": "TEXT", "nullable": True, "description": "Notification preferences (EMAIL, SMS, BOTH, NONE)"},
                "working_hours": {"type": "TEXT", "nullable": True, "description": "JSON string of working hours"},
                "emergency_contact": {"type": "BOOLEAN", "nullable": True, "description": "Whether this operator can be contacted in emergencies"},
                "calendar_sync_enabled": {"type": "BOOLEAN", "nullable": True, "description": "Whether calendar sync is enabled"},
                "calendar_external_id": {"type": "TEXT", "nullable": True, "description": "ID for external calendar integration"}
            },
            "relationships": [
                {"type": "one_to_many", "target": "buildings", "foreign_key": "operator_id"},
                {"type": "one_to_many", "target": "rooms", "foreign_key": "last_check_by"},
                {"type": "one_to_many", "target": "tenants", "foreign_key": "operator_id"}
            ]
        },
        "tour_bookings": {
            "description": "Tour scheduling and booking records",
            "columns": {
                "tour_id": {"type": "TEXT", "primary_key": True},
                "lead_id": {"type": "TEXT", "foreign_key": "leads.lead_id"},
                "room_id": {"type": "TEXT", "foreign_key": "rooms.room_id"},
                "operator_id": {"type": "BIGINT", "foreign_key": "operators.operator_id"},
                "scheduled_date": {"type": "TEXT", "nullable": False},
                "scheduled_time": {"type": "TEXT", "nullable": False},
                "duration_minutes": {"type": "INTEGER", "default": 30},
                "status": {"type": "TEXT", "nullable": False},
                "tour_type": {"type": "TEXT", "default": "Virtual"},
                "google_meet_url": {"type": "TEXT", "nullable": True},
                "google_calendar_link": {"type": "TEXT", "nullable": True},
                "virtual_tour_video_url": {"type": "TEXT", "nullable": True},
                "notes": {"type": "TEXT", "nullable": True},
                "special_requests": {"type": "TEXT", "nullable": True},
                "confirmation_sent": {"type": "BOOLEAN", "default": False},
                "reminder_sent": {"type": "BOOLEAN", "default": False},
                "tour_completed_at": {"type": "TEXT", "nullable": True},
                "feedback_rating": {"type": "INTEGER", "nullable": True},
                "feedback_comments": {"type": "TEXT", "nullable": True},
                "created_at": {"type": "TIMESTAMP WITH TIME ZONE", "default": "NOW()"},
                "last_modified": {"type": "TIMESTAMP WITH TIME ZONE", "default": "NOW()"}
            },
            "relationships": [
                {"type": "belongs_to", "target": "leads", "foreign_key": "lead_id"},
                {"type": "belongs_to", "target": "rooms", "foreign_key": "room_id"},
                {"type": "belongs_to", "target": "operators", "foreign_key": "operator_id"}
            ]
        },

        "tour_availability_slots": {
            "description": "Available time slots for tours",
            "columns": {
                "slot_id": {"type": "TEXT", "primary_key": True},
                "room_id": {"type": "TEXT", "foreign_key": "rooms.room_id"},
                "operator_id": {"type": "BIGINT", "foreign_key": "operators.operator_id"},
                "slot_date": {"type": "TEXT", "nullable": False},
                "slot_time": {"type": "TEXT", "nullable": False},
                "slot_duration": {"type": "INTEGER", "default": 30},
                "is_available": {"type": "BOOLEAN", "default": True},
                "is_booked": {"type": "BOOLEAN", "default": False},
                "created_at": {"type": "TIMESTAMP WITH TIME ZONE", "default": "NOW()"}
            },
            "relationships": [
                {"type": "belongs_to", "target": "rooms", "foreign_key": "room_id"},
                {"type": "belongs_to", "target": "operators", "foreign_key": "operator_id"}
            ]
        },

        "buildings": {
            "description": "Property buildings and their features",
            "columns": {
                "building_id": {"type": "TEXT", "primary_key": True, "nullable": False, "description": "Unique identifier for building"},
                "building_name": {"type": "TEXT", "nullable": True, "description": "Name of the building"},
                "full_address": {"type": "TEXT", "nullable": True, "description": "Complete address of the building"},
                "operator_id": {"type": "BIGINT", "nullable": True, "foreign_key": "operators.operator_id", "description": "ID of the operator managing this building"},
                "available": {"type": "BOOLEAN", "nullable": True, "description": "Whether the building is available for new tenants"},
                "street": {"type": "TEXT", "nullable": True, "description": "Street address"},
                "area": {"type": "TEXT", "nullable": True, "description": "Area/neighborhood (Downtown, SoMA, Mission, Hayes Valley, Marina)"},
                "city": {"type": "TEXT", "nullable": True, "description": "City name"},
                "state": {"type": "TEXT", "nullable": True, "description": "State name"},
                "zip": {"type": "BIGINT", "nullable": True, "description": "ZIP code"},
                "floors": {"type": "BIGINT", "nullable": True, "description": "Number of floors in the building"},
                "total_rooms": {"type": "BIGINT", "nullable": True, "description": "Total number of rooms in the building"},
                "total_bathrooms": {"type": "BIGINT", "nullable": True, "description": "Total number of bathrooms"},
                "bathrooms_on_each_floor": {"type": "BIGINT", "nullable": True, "description": "Number of bathrooms on each floor"},
                "common_kitchen": {"type": "TEXT", "nullable": True, "description": "Common kitchen type (None, Basic, Full, Premium)"},
                "min_lease_term": {"type": "BIGINT", "nullable": True, "description": "Minimum lease term in months"},
                "pref_min_lease_term": {"type": "BIGINT", "nullable": True, "description": "Preferred minimum lease term in months"},
                "wifi_included": {"type": "BOOLEAN", "nullable": True, "description": "Whether WiFi is included in rent"},
                "laundry_onsite": {"type": "BOOLEAN", "nullable": True, "description": "Whether laundry facilities are available on-site"},
                "common_area": {"type": "TEXT", "nullable": True, "description": "Description of common areas"},
                "secure_access": {"type": "BOOLEAN", "nullable": True, "description": "Whether the building has secure access"},
                "bike_storage": {"type": "BOOLEAN", "nullable": True, "description": "Whether bike storage is available"},
                "rooftop_access": {"type": "BOOLEAN", "nullable": True, "description": "Whether rooftop access is available"},
                "pet_friendly": {"type": "TEXT", "nullable": True, "description": "Pet policy (No, Cats Only, Small Pets, All Pets)"},
                "cleaning_common_spaces": {"type": "TEXT", "nullable": True, "description": "Cleaning schedule for common spaces"},
                "utilities_included": {"type": "BOOLEAN", "nullable": True, "description": "Whether utilities are included in rent"},
                "fitness_area": {"type": "BOOLEAN", "nullable": True, "description": "Whether fitness area is available"},
                "work_study_area": {"type": "BOOLEAN", "nullable": True, "description": "Whether work/study area is available"},
                "social_events": {"type": "BOOLEAN", "nullable": True, "description": "Whether social events are organized"},
                "nearby_conveniences_walk": {"type": "TEXT", "nullable": True, "description": "Nearby conveniences within walking distance"},
                "nearby_transportation": {"type": "TEXT", "nullable": True, "description": "Nearby transportation options"},
                "priority": {"type": "BIGINT", "nullable": True, "description": "Priority level of the building"},
                "year_built": {"type": "TEXT", "nullable": True, "description": "Year the building was built"},
                "last_renovation": {"type": "TEXT", "nullable": True, "description": "Year or date of last renovation"},
                "building_rules": {"type": "TEXT", "nullable": True, "description": "Building rules and policies"},
                "amenities_details": {"type": "TEXT", "nullable": True, "description": "JSON string of detailed amenities info"},
                "neighborhood_description": {"type": "TEXT", "nullable": True, "description": "Description of the neighborhood"},
                "building_description": {"type": "TEXT", "nullable": True, "description": "Description of the building"},
                "public_transit_info": {"type": "TEXT", "nullable": True, "description": "Public transit information"},
                "parking_info": {"type": "TEXT", "nullable": True, "description": "Parking information"},
                "security_features": {"type": "TEXT", "nullable": True, "description": "Security features description"},
                "disability_access": {"type": "BOOLEAN", "nullable": True, "description": "Whether the building has disability access"},
                "disability_features": {"type": "TEXT", "nullable": True, "description": "Disability access features"},
                "building_images": {"type": "TEXT", "nullable": True, "description": "JSON array of building image URLs"},
                "virtual_tour_url": {"type": "TEXT", "nullable": True, "description": "URL for virtual tour"},
                "created_at": {"type": "TIMESTAMP WITH TIME ZONE", "nullable": True, "description": "Record creation timestamp"},
                "last_modified": {"type": "TIMESTAMP WITH TIME ZONE", "nullable": True, "description": "Last modification timestamp"}
            },
            "relationships": [
                {"type": "many_to_one", "target": "operators", "foreign_key": "operator_id"},
                {"type": "one_to_many", "target": "rooms", "foreign_key": "building_id"},
                {"type": "one_to_many", "target": "tenants", "foreign_key": "building_id"}
            ]
        },
        
        "rooms": {
            "description": "Individual rooms within buildings",
            "columns": {
                "room_id": {"type": "TEXT", "primary_key": True, "nullable": False, "description": "Unique identifier for room"},
                "room_number": {"type": "BIGINT", "nullable": True, "description": "Room number within the building"},
                "building_id": {"type": "TEXT", "nullable": True, "foreign_key": "buildings.building_id", "description": "ID of the building containing this room"},
                "ready_to_rent": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room is ready to rent"},
                "status": {"type": "TEXT", "nullable": True, "description": "Room status (AVAILABLE, OCCUPIED, MAINTENANCE, RESERVED)"},
                "booked_from": {"type": "TEXT", "nullable": True, "description": "Date from which room is booked"},
                "booked_till": {"type": "TEXT", "nullable": True, "description": "Date until which room is booked"},
                "active_tenants": {"type": "TEXT", "nullable": True, "description": "Number of active tenants in the room (stored as text)"},
                "maximum_people_in_room": {"type": "BIGINT", "nullable": True, "description": "Maximum number of people allowed in the room"},
                "private_room_rent": {"type": "DOUBLE PRECISION", "nullable": True, "description": "Rent for private room occupancy"},
                "shared_room_rent_2": {"type": "TEXT", "nullable": True, "description": "Rent for shared room occupancy (2 people) - stored as text"},
                "last_check": {"type": "TEXT", "nullable": True, "description": "Date of last room check"},
                "last_check_by": {"type": "BIGINT", "nullable": True, "foreign_key": "operators.operator_id", "description": "ID of operator who last checked the room"},
                "current_booking_types": {"type": "TEXT", "nullable": True, "description": "Current booking types for the room"},
                "floor_number": {"type": "BIGINT", "nullable": True, "description": "Floor number where the room is located"},
                "bed_count": {"type": "TEXT", "nullable": True, "description": "Number of beds in the room (stored as text)"},
                "bathroom_type": {"type": "TEXT", "nullable": True, "description": "Bathroom type (Private, Shared, En-Suite)"},
                "bed_size": {"type": "TEXT", "nullable": True, "description": "Size of the bed(s) (Twin, Full, Queen, King)"},
                "bed_type": {"type": "TEXT", "nullable": True, "description": "Type of bed(s)"},
                "view": {"type": "TEXT", "nullable": True, "description": "View from the room (city, bay, garden, street)"},
                "sq_footage": {"type": "BIGINT", "nullable": True, "description": "Square footage of the room"},
                "mini_fridge": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room has a mini fridge"},
                "sink": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room has a sink"},
                "bedding_provided": {"type": "BOOLEAN", "nullable": True, "description": "Whether bedding is provided"},
                "work_desk": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room has a work desk"},
                "work_chair": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room has a work chair"},
                "heating": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room has heating"},
                "air_conditioning": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room has air conditioning"},
                "cable_tv": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room has cable TV"},
                "room_storage": {"type": "TEXT", "nullable": True, "description": "Storage options in the room"},
                "noise_level": {"type": "TEXT", "nullable": True, "description": "Noise level (QUIET, MODERATE, LIVELY)"},
                "sunlight": {"type": "TEXT", "nullable": True, "description": "Sunlight level (BRIGHT, MODERATE, LOW)"},
                "furnished": {"type": "BOOLEAN", "nullable": True, "description": "Whether the room is furnished"},
                "furniture_details": {"type": "TEXT", "nullable": True, "description": "Details about furniture in the room"},
                "last_renovation_date": {"type": "TEXT", "nullable": True, "description": "Date of last renovation"},
                "public_notes": {"type": "TEXT", "nullable": True, "description": "Public notes about the room"},
                "internal_notes": {"type": "TEXT", "nullable": True, "description": "Internal notes for staff only"},
                "virtual_tour_url": {"type": "TEXT", "nullable": True, "description": "URL for virtual tour of the room"},
                "available_from": {"type": "TEXT", "nullable": True, "description": "Date from which room is available"},
                "additional_features": {"type": "TEXT", "nullable": True, "description": "Additional features of the room"},
                "room_images": {"type": "TEXT", "nullable": True, "description": "JSON array of room image URLs"},
                "last_modified": {"type": "TIMESTAMP WITH TIME ZONE", "nullable": True, "description": "Last modification timestamp"}
            },
            "relationships": [
                {"type": "many_to_one", "target": "buildings", "foreign_key": "building_id"},
                {"type": "many_to_one", "target": "operators", "foreign_key": "last_check_by"},
                {"type": "one_to_many", "target": "tenants", "foreign_key": "room_id"},
                {"type": "one_to_many", "target": "leads", "foreign_key": "selected_room_id"}
            ]
        },
        
        "tenants": {
            "description": "Current tenants and their information",
            "columns": {
                "tenant_id": {"type": "TEXT", "primary_key": True, "nullable": False, "description": "Unique identifier for tenant"},
                "tenant_name": {"type": "TEXT", "nullable": True, "description": "Full name of the tenant"},
                "room_id": {"type": "TEXT", "nullable": True, "foreign_key": "rooms.room_id", "description": "ID of the room the tenant occupies"},
                "room_number": {"type": "BIGINT", "nullable": True, "description": "Room number the tenant occupies"},
                "lease_start_date": {"type": "TEXT", "nullable": True, "description": "Start date of the lease"},
                "lease_end_date": {"type": "TEXT", "nullable": True, "description": "End date of the lease"},
                "operator_id": {"type": "BIGINT", "nullable": True, "foreign_key": "operators.operator_id", "description": "ID of the operator managing this tenant"},
                "booking_type": {"type": "TEXT", "nullable": True, "description": "Type of booking (LEASE, AIRBNB, CORPORATE, STUDENT)"},
                "tenant_nationality": {"type": "TEXT", "nullable": True, "description": "Nationality of the tenant"},
                "tenant_email": {"type": "TEXT", "nullable": True, "description": "Email address of the tenant"},
                "phone": {"type": "TEXT", "nullable": True, "description": "Phone number of the tenant"},
                "emergency_contact_name": {"type": "TEXT", "nullable": True, "description": "Name of emergency contact"},
                "emergency_contact_phone": {"type": "TEXT", "nullable": True, "description": "Phone number of emergency contact"},
                "emergency_contact_relation": {"type": "TEXT", "nullable": True, "description": "Relationship to emergency contact"},
                "building_id": {"type": "TEXT", "nullable": True, "foreign_key": "buildings.building_id", "description": "ID of the building where tenant lives"},
                "status": {"type": "TEXT", "nullable": True, "description": "Tenant status (ACTIVE, PENDING, TERMINATED, EXPIRED)"},
                "deposit_amount": {"type": "BIGINT", "nullable": True, "description": "Deposit amount paid by tenant"},
                "payment_status": {"type": "TEXT", "nullable": True, "description": "Payment status (CURRENT, LATE, PENDING)"},
                "special_requests": {"type": "TEXT", "nullable": True, "description": "Special requests from tenant"},
                "payment_reminders_enabled": {"type": "BOOLEAN", "nullable": True, "description": "Whether payment reminders are enabled"},
                "communication_preferences": {"type": "TEXT", "nullable": True, "description": "Communication preferences (EMAIL, SMS, BOTH)"},
                "account_status": {"type": "TEXT", "nullable": True, "description": "Account status (ACTIVE, INACTIVE, PENDING)"},
                "last_payment_date": {"type": "TEXT", "nullable": True, "description": "Date of last payment"},
                "next_payment_date": {"type": "TEXT", "nullable": True, "description": "Date of next payment"},
                "rent_payment_method": {"type": "TEXT", "nullable": True, "description": "Method of rent payment"},
                "has_pets": {"type": "BOOLEAN", "nullable": True, "description": "Whether tenant has pets"},
                "pet_details": {"type": "TEXT", "nullable": True, "description": "Details about pets"},
                "has_vehicles": {"type": "BOOLEAN", "nullable": True, "description": "Whether tenant has vehicles"},
                "vehicle_details": {"type": "TEXT", "nullable": True, "description": "Details about vehicles"},
                "has_renters_insurance": {"type": "BOOLEAN", "nullable": True, "description": "Whether tenant has renters insurance"},
                "insurance_details": {"type": "TEXT", "nullable": True, "description": "Insurance details"},
                "created_at": {"type": "TIMESTAMP WITH TIME ZONE", "nullable": True, "description": "Record creation timestamp"},
                "last_modified": {"type": "TIMESTAMP WITH TIME ZONE", "nullable": True, "description": "Last modification timestamp"}
            },
            "relationships": [
                {"type": "many_to_one", "target": "rooms", "foreign_key": "room_id"},
                {"type": "many_to_one", "target": "buildings", "foreign_key": "building_id"},
                {"type": "many_to_one", "target": "operators", "foreign_key": "operator_id"}
            ]
        },
        
        "leads": {
            "description": "Potential renters and their information",
            "columns": {
                "lead_id": {"type": "TEXT", "primary_key": True, "nullable": False, "description": "Unique identifier for lead"},
                "email": {"type": "TEXT", "nullable": True, "description": "Email address of the lead"},
                "status": {"type": "TEXT", "nullable": True, "description": "Lead status (EXPLORING, SHOWING_SCHEDULED, BACKGROUND_CHECK, LEASE_REQUESTED, APPROVED, REJECTED)"},
                "interaction_count": {"type": "BIGINT", "nullable": True, "description": "Number of interactions with the lead"},
                "rooms_interested": {"type": "JSONB", "nullable": True, "description": "JSON array of room IDs the lead is interested in"},
                "selected_room_id": {"type": "TEXT", "nullable": True, "foreign_key": "rooms.room_id", "description": "ID of the room selected by the lead"},
                "showing_dates": {"type": "TEXT", "nullable": True, "description": "JSON array or text of showing dates"},
                "planned_move_in": {"type": "TEXT", "nullable": True, "description": "Planned move-in date"},
                "planned_move_out": {"type": "TEXT", "nullable": True, "description": "Planned move-out date"},
                "visa_status": {"type": "TEXT", "nullable": True, "description": "Visa status of the lead"},
                "notes": {"type": "TEXT", "nullable": True, "description": "Notes about the lead"},
                "lead_score": {"type": "TEXT", "nullable": True, "description": "Lead score for prioritization (stored as text)"},
                "lead_source": {"type": "TEXT", "nullable": True, "description": "Source of the lead (WEBSITE, REFERRAL, ADVERTISEMENT, etc.)"},
                "preferred_communication": {"type": "TEXT", "nullable": True, "description": "Preferred communication method (EMAIL, SMS, PHONE)"},
                "budget_min": {"type": "TEXT", "nullable": True, "description": "Minimum budget of the lead (stored as text)"},
                "budget_max": {"type": "TEXT", "nullable": True, "description": "Maximum budget of the lead (stored as text)"},
                "preferred_move_in_date": {"type": "TEXT", "nullable": True, "description": "Preferred move-in date"},
                "preferred_lease_term": {"type": "TEXT", "nullable": True, "description": "Preferred lease term in months (stored as text)"},
                "additional_preferences": {"type": "TEXT", "nullable": True, "description": "JSON string of additional preferences"},
                "last_contacted": {"type": "TEXT", "nullable": True, "description": "Last contact timestamp (stored as text)"},
                "next_follow_up": {"type": "TEXT", "nullable": True, "description": "Next follow-up timestamp (stored as text)"},
                "created_at": {"type": "TIMESTAMP WITH TIME ZONE", "nullable": True, "description": "Record creation timestamp"},
                "last_modified": {"type": "TIMESTAMP WITH TIME ZONE", "nullable": True, "description": "Last modification timestamp"}
            },
            "relationships": [
                {"type": "many_to_one", "target": "rooms", "foreign_key": "selected_room_id"}
            ]
        }
    },
    
    # "common_values": {
    #     "room_status": ["AVAILABLE", "OCCUPIED", "MAINTENANCE", "RESERVED"],
    #     "tenant_status": ["ACTIVE", "PENDING", "TERMINATED", "EXPIRED"],
    #     "lead_status": ["EXPLORING", "SHOWING_SCHEDULED", "BACKGROUND_CHECK", "LEASE_REQUESTED", "APPROVED", "REJECTED"],
    #     "payment_status": ["CURRENT", "LATE", "PENDING"],
    #     "bathroom_type": ["Private", "Shared", "En-Suite"],
    #     "bed_size": ["Twin", "Full", "Queen", "King"],
    #     "booking_type": ["LEASE", "AIRBNB", "CORPORATE", "STUDENT"],
    #     "operator_type": ["LEASING_AGENT", "MAINTENANCE", "BUILDING_MANAGER", "ADMIN"],
    #     "pet_friendly": ["No", "Cats Only", "Small Pets", "All Pets"],
    #     "common_kitchen": ["None", "Basic", "Full", "Premium"],
    #     "areas": ["Downtown", "SoMA", "Mission", "Hayes Valley", "Marina"]
    # },
    
    # "common_queries": {
    #     "room_search": {
    #         "description": "Search for available rooms with filters",
    #         "example": "Show me available rooms under $2000 in downtown with wifi",
    #         "tables": ["rooms", "buildings"],
    #         "sample_sql": """
    #             SELECT r.*, b.building_name, b.area, b.wifi_included
    #             FROM rooms r
    #             JOIN buildings b ON r.building_id = b.building_id
    #             WHERE r.status = 'AVAILABLE' 
    #             AND r.private_room_rent < 2000
    #             AND b.area = 'Downtown'
    #             AND b.wifi_included = true
    #         """
    #     },
    #     "occupancy_analytics": {
    #         "description": "Calculate occupancy rates",
    #         "example": "What's the occupancy rate by building?",
    #         "tables": ["rooms", "buildings"],
    #         "sample_sql": """
    #             SELECT b.building_name,
    #                    COUNT(r.room_id) as total_rooms,
    #                    SUM(CASE WHEN r.status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied_rooms,
    #                    (SUM(CASE WHEN r.status = 'OCCUPIED' THEN 1 ELSE 0 END)::float / COUNT(r.room_id)::float * 100) as occupancy_rate
    #             FROM buildings b
    #             JOIN rooms r ON b.building_id = r.building_id
    #             GROUP BY b.building_name
    #             ORDER BY occupancy_rate DESC
    #         """
    #     },
    #     "tenant_management": {
    #         "description": "Manage tenant information",
    #         "example": "Show all active tenants with their payment status",
    #         "tables": ["tenants", "rooms", "buildings"],
    #         "sample_sql": """
    #             SELECT t.tenant_name, t.tenant_email, r.room_number, 
    #                    b.building_name, t.payment_status, t.lease_end_date
    #             FROM tenants t
    #             JOIN rooms r ON t.room_id = r.room_id
    #             JOIN buildings b ON r.building_id = b.building_id
    #             WHERE t.status = 'ACTIVE'
    #             ORDER BY t.payment_status, t.lease_end_date
    #         """
    #     },
    #     "lead_tracking": {
    #         "description": "Track and manage leads",
    #         "example": "Show all leads in showing scheduled status",
    #         "tables": ["leads", "rooms"],
    #         "sample_sql": """
    #             SELECT l.lead_id, l.email, l.status, l.selected_room_id,
    #                    r.room_number, l.showing_dates, l.planned_move_in
    #             FROM leads l
    #             LEFT JOIN rooms r ON l.selected_room_id = r.room_id
    #             WHERE l.status = 'SHOWING_SCHEDULED'
    #             ORDER BY l.last_modified DESC
    #         """
    #     },
    #     "revenue_analysis": {
    #         "description": "Analyze revenue metrics",
    #         "example": "Calculate total potential revenue by building",
    #         "tables": ["rooms", "buildings"],
    #         "sample_sql": """
    #             SELECT b.building_name,
    #                    SUM(r.private_room_rent) as total_potential_revenue,
    #                    SUM(CASE WHEN r.status = 'OCCUPIED' THEN r.private_room_rent ELSE 0 END) as actual_revenue,
    #                    AVG(r.private_room_rent) as avg_room_rent
    #             FROM buildings b
    #             JOIN rooms r ON b.building_id = r.building_id
    #             GROUP BY b.building_name
    #             ORDER BY total_potential_revenue DESC
    #         """
    #     }
    # }
}


def get_schema_for_sql_generation():
    """Get formatted schema information for SQL generation."""
    schema_text = f"""
# HomeWiz Property Management Database Schema

## Database Overview
{DATABASE_SCHEMA['description']}

## Tables and Relationships

"""
    
    for table_name, table_info in DATABASE_SCHEMA['tables'].items():
        schema_text += f"""
### Table: {table_name}
**Description:** {table_info['description']}

**Columns:**
"""
        for col_name, col_info in table_info['columns'].items():
            constraints = []
            if col_info.get('primary_key'):
                constraints.append("PRIMARY KEY")
            if col_info.get('foreign_key'):
                constraints.append(f"FOREIGN KEY -> {col_info['foreign_key']}")
            if col_info.get('auto_increment'):
                constraints.append("AUTO INCREMENT")
            
            constraint_text = f" ({', '.join(constraints)})" if constraints else ""
            
            schema_text += f"- {col_name}: {col_info['type']}{constraint_text} - {col_info['description']}\n"
        
        if table_info.get('relationships'):
            schema_text += "\n**Relationships:**\n"
            for rel in table_info['relationships']:
                schema_text += f"- {rel['type']} with {rel['target']} via {rel['foreign_key']}\n"
        
        schema_text += "\n"
    
    # Add SQL generation guidelines without referencing common values
    schema_text += """

## SQL Generation Guidelines

1. **Table Aliases**: Always use aliases for better readability:
   - r for rooms
   - b for buildings
   - t for tenants
   - l for leads
   - o for operators

2. **Data Types**: Be aware of the actual PostgreSQL data types:
   - IDs are typically TEXT (except operator_id which is BIGINT)
   - Dates are stored as TEXT in many cases
   - Some numeric fields like budget_min/max are stored as TEXT
   - rooms_interested in leads table is JSONB

3. **JOIN Patterns**:
   - rooms -> buildings via building_id
   - rooms -> operators via last_check_by
   - tenants -> rooms via room_id
   - tenants -> buildings via building_id
   - leads -> rooms via selected_room_id

4. **Common Filters**:
   - Available rooms: WHERE r.status = 'AVAILABLE'
   - Active tenants: WHERE t.status = 'ACTIVE'
   - Buildings with amenities: WHERE b.wifi_included = true

5. **Aggregate Functions**:
   - Occupancy rate: SUM(CASE WHEN r.status = 'OCCUPIED' THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100
   - Revenue calculations: SUM(r.private_room_rent)
   - Averages: AVG(r.private_room_rent)

6. **Ordering**:
   - Price: ORDER BY r.private_room_rent ASC/DESC
   - Date: ORDER BY created_at DESC
   - Multiple: ORDER BY b.building_name, r.room_number

7. **Limits**: Default to LIMIT 50 unless specified otherwise
"""
    
    return schema_text

def get_table_columns(table_name: str) -> list:
    """Get list of columns for a specific table."""
    if table_name in DATABASE_SCHEMA['tables']:
        return list(DATABASE_SCHEMA['tables'][table_name]['columns'].keys())
    return []

def get_table_relationships(table_name: str) -> list:
    """Get relationships for a specific table."""
    if table_name in DATABASE_SCHEMA['tables']:
        return DATABASE_SCHEMA['tables'][table_name].get('relationships', [])
    return []