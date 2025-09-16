# app/db/database_constants.py

from typing import Any
DATABASE_DISTINCT_VALUES = {
    "buildings": {
        # Text columns with distinct values (from CSV)
        "text_columns": {
            "amenities_details": [],  # Complex JSON/varied data
            "area": ["North Beach", "SOMA"],
            "building_description": [],  # Too varied to list
            "building_name": [
                "1080 Folsom Residences",
                "221 7th Street Residences", 
                "251 9th Street Residences",
                "371 Columbus Residences",
                "524 Columbus Residences",
                "UpMarket Residences"
            ],
            "building_rules": ["No smoking, quiet hours 10 PM - 8 AM, guests must be registered"],
            "city": ["San Francisco"],
            "cleaning_common_spaces": ["Daily cleaning of common areas"],
            "common_area": ["Shared lounge, kitchen, and dining areas"],
            "common_kitchen": ["Fully equipped with modern appliances"],
            "disability_features": ["Elevator access, ADA compliant bathrooms"],
            "full_address": [],  # Too varied
            "last_renovation": ["2023", "2024", "2025"],
            "nearby_conveniences_walk": [
                "Restaurants, Cafes, Nightlife, Cultural Sites",
                "Union Square, Financial District, Tech Companies"
            ],
            "nearby_transportation": [
                "MUNI Lines, Walking Distance to Downtown",
                "MUNI, BART, Highway Access"
            ],
            "neighborhood_description": [],  # Too varied
            "parking_info": ["Limited street parking", "Street parking available"],
            "pet_friendly": ["Cats only", "No pets", "No pets allowed"],
            "public_transit_info": [],  # Too varied
            "security_features": ["Key card access, security cameras"],
            "state": ["CA"],
            "street": [],  # Too varied
            "year_built": ["2018", "2019", "2021"],
        },
        
        # Boolean columns (stored as "true"/"false" strings in database)
        "boolean_string_columns": [
            "available", "bike_storage", "disability_access", "fitness_area",
            "laundry_onsite", "rooftop_access", "secure_access", "social_events",
            "utilities_included", "wifi_included", "work_study_area"
        ],
        
        # Numeric columns (if any)
        "numeric_columns": {}
    },
    
    "rooms": {
        # Text columns with distinct values (from CSV)
        "text_columns": {
            "additional_features": ["Balcony access", "Corner room", "Extra storage"],
            "available_from": [],  # Date field - too many values
            "bathroom_type": ["Private", "Semi-Private", "Shared"],
            "bed_size": ["Full", "Queen", "Twin"],
            "bed_type": ["Bunk", "Loft", "Standard"],
            "booked_from": [],  # Date field - too many values
            "booked_till": [],  # Date field - too many values
            "building_id": [
                "BLDG_1080_FOLSOM",
                "BLDG_221_7TH",
                "BLDG_251_9TH",
                "BLDG_371_COLUMBUS",
                "BLDG_524_COLUMBUS",
                "BLDG_UPMARKET"
            ],
            "current_booking_types": ["Both", "Long-term", "Short-term"],
            "furniture_details": ["Bed, desk, chair, dresser, closet"],
            "internal_notes": ["Popular room", "Quiet location", "Recently renovated"],
            "last_check": [],  # Date field
            "last_renovation_date": [],  # Date field - too many values
            "noise_level": ["Lively", "Moderate", "Quiet"],
            "public_notes": ["Fully furnished with all amenities included"],
            "room_images": [],  # URLs - too many to list
            "room_storage": ["Closet + shelving", "Closet only", "Under-bed storage"],
            "status": ["Available", "Maintenance", "Occupied"],
            "sunlight": ["Bright", "Limited", "Moderate"],
            "view": ["City View", "Courtyard", "Limited View", "Street View"],
            "virtual_tour_url": [],  # URLs - too many to list
        },
        
        # Boolean columns (stored as "true"/"false" strings)
        "boolean_string_columns": [
            "air_conditioning", "bedding_provided", "cable_tv", "furnished",
            "heating", "mini_fridge", "ready_to_rent", "sink", 
            "work_chair", "work_desk"
        ],
        
        # Numeric columns
        "numeric_columns": {
            "active_tenants": {"min": 0, "max": 3},
            "bed_count": {"min": 1, "max": 3},
            "shared_room_rent_2": {"min": 600, "max": 695},
        }
    },
    
    # Placeholder for other tables - to be filled when you provide CSVs
    "tenants": {
        # Text columns with distinct values
        "text_columns": {
            "account_status": ["Active", "Closed", "Pending", "Suspended"],
            "booking_type": ["Long-term", "Month-to-month", "Short-term"],
            "building_id": [
                "BLDG_1080_FOLSOM",
                "BLDG_221_7TH",
                "BLDG_251_9TH",
                "BLDG_371_COLUMBUS",
                "BLDG_524_COLUMBUS",
                "BLDG_UPMARKET"
            ],
            "communication_preferences": ["App", "Email", "Phone", "Text"],
            "emergency_contact_name": [],  # Too many to list
            "emergency_contact_phone": [],  # Too many to list
            "emergency_contact_relation": ["Friend", "Parent", "Partner", "Sibling", "Spouse"],
            "insurance_details": [],  # Too many policy numbers
            "last_payment_date": [],  # Date field
            "lease_end_date": [],  # Date field
            "lease_start_date": [],  # Date field
            "next_payment_date": [],  # Date field
            "payment_status": ["Current", "Late", "Overdue", "Pending"],
            "pet_details": ["Cat, Large", "Cat, Medium", "Cat, Small", "Dog, Large", "Dog, Medium", "Dog, Small", "Fish, Large", "Fish, Medium", "Fish, Small"],
            "phone": [],  # Too many to list
            "rent_payment_method": ["ACH", "Bank Transfer", "Check", "Credit Card"],
            "special_requests": ["Extra storage", "Lower floor", "Pet-friendly", "Quiet room"],
            "status": ["Active", "Inactive", "Moving Out", "Pending Move-in"],
            "tenant_email": [],  # Too many to list
            "tenant_name": [],  # Too many to list
            "tenant_nationality": ["American", "Brazilian", "British", "Canadian", "Chinese", "French", "German", "Indian", "Italian", "Japanese", "Korean", "Mexican"],
            "vehicle_details": ["Bike, Hatchback", "Bike, Sedan", "Bike, SUV", "Car, Hatchback", "Car, Sedan", "Car, SUV", "Motorcycle, Hatchback", "Motorcycle, Sedan", "Motorcycle, SUV"],
        },
        
        # Boolean columns (stored as "true"/"false" strings)
        "boolean_string_columns": [
            "has_pets", "has_renters_insurance", "has_vehicles", "payment_reminders_enabled"
        ],
        
        # Numeric columns
        "numeric_columns": {}
    },
    
    "leads": {
        # Text columns with distinct values
        "text_columns": {
            "additional_preferences": ["Good internet speed", "Kitchen access important", "Near public transport", "Non-smoking building", "Parking needed"],
            "budget_max": [],  # Too many values (numeric range)
            "budget_min": ["1000", "1100", "600", "700", "800", "900"],
            "email": [],  # Too many to list
            "last_contacted": [],  # Date field
            "lead_score": ["Cold", "Hot", "Qualified", "Unqualified", "Warm"],
            "lead_source": ["Email Campaign", "Google Ads", "Partner", "Referral", "Social Media", "Walk-in", "Website"],
            "next_follow_up": [],  # Date field
            "notes": ["Budget conscious", "Graduate student", "Interested in private room", "Looking for quiet space", "Needs pet-friendly room", "Prefers lower floor", "Tech professional"],
            "planned_move_in": [],  # Date field
            "planned_move_out": [],  # Date field
            "preferred_communication": ["Email", "Phone", "Text", "Video Call"],
            "preferred_lease_term": ["12 months", "3 months", "6 months", "9 months", "Flexible"],
            "preferred_move_in_date": [],  # Date field
            "rooms_interested": [],  # JSONB field with room IDs
            "selected_room_id": [],  # Too many room IDs to list
            "showing_dates": [],  # Date field
            "status": ["Application Submitted", "Contacted", "Converted", "Interested", "Lost", "New", "Viewing Scheduled"],
            "visa_status": ["F-1 Student", "H-1B", "J-1", "Other", "Permanent Resident", "Tourist", "US Citizen"],
        },
        
        # Boolean columns
        "boolean_string_columns": [],
        
        # Numeric columns
        "numeric_columns": {
            "budget_max": {"min": 800, "max": 1600},
            "budget_min": {"min": 600, "max": 1100}
        }
    },
    
    "operators": {
        # Text columns with distinct values
        "text_columns": {
            "calendar_external_id": [],  # Calendar IDs
            "date_joined": [],  # Date field
            "email": [],  # Too many to list
            "last_active": [],  # Date field
            "name": [
                "David Kim", "Emily Rodriguez", "James Martinez", "John Manager",
                "Kausha", "Kaushs", "Lisa Leasing", "Lisa Wong", "Michael Chen",
                "Mike Maintenance", "Sarah Admin", "Sarah Johnson", "Tom Support"
            ],
            "notification_preferences": ["Both", "Email", "EMAIL", "SMS"],
            "operator_type": [
                "ADMIN", "BUILDING_MANAGER", "Community Manager", "Leasing Agent",
                "LEASING_AGENT", "Maintenance Coordinator", "Marketing Specialist",
                "Operations Manager", "Property Manager"
            ],
            "permissions": ["Full", "Limited"],
            "phone": [],  # Too many to list
            "role": ["Agent", "Assistant Manager", "Coordinator", "Leasing Agent", "Maintenance", "Manager", "Property Manager", "Specialist"],
            "working_hours": ["9:00 AM - 6:00 PM"],
        },
        
        # Boolean columns (stored as "true"/"false" strings)
        "boolean_string_columns": [
            "active", "calendar_sync_enabled", "emergency_contact"
        ],
        
        # Numeric columns
        "numeric_columns": {}
    }
}

# Helper functions remain the same but updated for actual structure

def get_column_type(table: str, column: str) -> str:
    """Determine if a column is text, boolean, or numeric."""
    if table not in DATABASE_DISTINCT_VALUES:
        return "unknown"
    
    table_data = DATABASE_DISTINCT_VALUES[table]
    
    if column in table_data.get("boolean_string_columns", []):
        return "boolean_string"
    elif column in table_data.get("numeric_columns", {}):
        return "numeric"
    elif column in table_data.get("text_columns", {}):
        return "text"
    else:
        return "unknown"

def get_valid_values(table: str, column: str) -> list:
    """Get valid values for a text column."""
    if table in DATABASE_DISTINCT_VALUES:
        text_columns = DATABASE_DISTINCT_VALUES[table].get("text_columns", {})
        return text_columns.get(column, [])
    return []

def validate_value(table: str, column: str, value: Any) -> tuple[bool, Any]:
    """
    Validate and potentially correct a value for a column.
    Returns (is_valid, corrected_value)
    """
    column_type = get_column_type(table, column)
    
    if column_type == "boolean_string":
        # Boolean values stored as strings "true"/"false"
        if isinstance(value, bool):
            return True, "true" if value else "false"
        elif isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ["true", "yes", "1", "on"]:
                return True, "true"
            elif value_lower in ["false", "no", "0", "off"]:
                return True, "false"
        return False, value
    
    elif column_type == "numeric":
        # Check if within range
        try:
            num_value = float(value)
            range_info = get_numeric_range(table, column)
            if range_info:
                min_val = range_info.get("min", float("-inf"))
                max_val = range_info.get("max", float("inf"))
                if min_val <= num_value <= max_val:
                    return True, num_value
                else:
                    # Clamp to range
                    return False, max(min_val, min(num_value, max_val))
            return True, num_value
        except (TypeError, ValueError):
            return False, None
    
    elif column_type == "text":
        # Check against valid values if they exist
        valid_values = get_valid_values(table, column)
        if not valid_values:  # No validation needed
            return True, value
        
        # Exact match check (case sensitive as in DB)
        value_str = str(value)
        if value_str in valid_values:
            return True, value_str
        
        # Try case-insensitive match and return DB version
        for valid in valid_values:
            if valid.lower() == value_str.lower():
                return True, valid
        
        return False, value_str
    
    return True, value  # Unknown type, pass through

def get_numeric_range(table: str, column: str) -> dict:
    """Get min/max range for a numeric column."""
    if table in DATABASE_DISTINCT_VALUES:
        numeric_columns = DATABASE_DISTINCT_VALUES[table].get("numeric_columns", {})
        return numeric_columns.get(column, {})
    return {}

def format_values_for_prompt() -> str:
    """Format database values for inclusion in LLM prompts."""
    output = ["## Valid Database Values (EXACT column names and values from database)\n"]
    
    for table, data in DATABASE_DISTINCT_VALUES.items():
        output.append(f"\n### {table.upper()} Table:\n")
        
        # Text columns with values
        text_columns = data.get("text_columns", {})
        if text_columns:
            output.append("**Text columns with specific values:**")
            for column, values in text_columns.items():
                if values:  # Only show if we have specific values
                    if len(values) > 5:
                        output.append(f"- {column}: {', '.join(values[:3])} ... (and more)")
                    else:
                        output.append(f"- {column}: {', '.join(values)}")
        
        # Boolean string columns
        boolean_cols = data.get("boolean_string_columns", [])
        if boolean_cols:
            output.append(f"\n**Boolean columns** (stored as 'true'/'false' strings): {', '.join(boolean_cols[:10])}")
            if len(boolean_cols) > 10:
                output.append(f"  ... and {len(boolean_cols)-10} more")
        
        # Numeric columns
        numeric_cols = data.get("numeric_columns", {})
        if numeric_cols:
            output.append(f"\n**Numeric columns with ranges**:")
            for column, range_info in list(numeric_cols.items())[:5]:
                output.append(f"  - {column}: {range_info.get('min', 0)} to {range_info.get('max', 'unlimited')}")
    
    return '\n'.join(output)

    # ----------------------------------------------------------------------
# Date & Timestamp column metadata and helpers (added for LLM SQL accuracy)
# ----------------------------------------------------------------------

# Columns that are stored as TEXT but represent dates.
# Format assumes ISO 'YYYY-MM-DD' unless otherwise noted. Provide concrete examples
# so the LLM copies the pattern and uses CASTs in SQL.
DATE_TEXT_COLUMNS = {
    "leads": {
        "last_contacted": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-06-18", "2025-07-25", "2025-06-13"],
            "notes": "Stored as TEXT; cast to DATE for filtering."
        },
        "next_follow_up": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-10-05", "2025-10-12"],
            "notes": "Stored as TEXT; cast to DATE for filtering."
        },
        "planned_move_in": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-10-20", "2025-10-03", "2025-10-08"],
            "notes": "Stored as TEXT; cast to DATE for filtering."
        },
        "planned_move_out": {
            "format": "YYYY-MM-DD",
            "examples": ["2026-06-04", "2026-07-06", "2026-05-04"],
            "notes": "Stored as TEXT; cast to DATE for filtering."
        },
        "preferred_move_in_date": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-09-30"],
            "notes": "Stored as TEXT; cast to DATE for filtering."
        },
        "showing_dates": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-09-18"],
            "notes": "Stored as TEXT; may contain multiple dates separated by commas; split and cast each to DATE for filtering."
        }
    },
    "buildings": {
        "last_renovation": {
            "format": "YYYY-MM-DD",
            "examples": ["2020", "2018"],
            "notes": "Year only as TEXT. Cast to INTEGER for comparisons."
        },
        "year_built": {
            "format": "YYYY",
            "examples": ["1995", "2008"],
            "notes": "Stored as TEXT; year only. Cast to INTEGER for comparisons or build DATE literal like DATE(CONCAT(year_built,'-01-01'))."
        }
    },
    "rooms": {
        "available_from": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-09-01", "2025-10-15"],
            "notes": "Stored as TEXT; room availability date. Cast to DATE for filtering."
        },
        "booked_from": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-02-10", "2025-03-01"],
            "notes": "Stored as TEXT; booking start date. Cast to DATE for filtering."
        },
        "booked_till": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-03-15", "2025-04-01"],
            "notes": "Stored as TEXT; booking end date. Cast to DATE for filtering."
        },
        "last_check": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-08-20", "2025-09-10"],
            "notes": "Stored as TEXT; last room inspection date. Cast to DATE for filtering."
        },
        "last_renovation_date": {
            "format": "YYYY-MM-DD",
            "examples": ["2024-11-30", "2019-06-15"],
            "notes": "Stored as TEXT; last renovation date. Cast to DATE for filtering."
        }
    },
    "tenants": {
        "last_payment_date": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-09-01", "2025-08-01"],
            "notes": "Stored as TEXT; last rent payment. Cast to DATE for filtering."
        },
        "lease_start_date": {
            "format": "YYYY-MM-DD",
            "examples": ["2024-06-01", "2025-01-15"],
            "notes": "Stored as TEXT; lease start date. Cast to DATE for filtering."
        },
        "lease_end_date": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-05-31", "2026-06-01"],
            "notes": "Stored as TEXT; lease end date. Cast to DATE for filtering."
        },
        "next_payment_date": {
            "format": "YYYY-MM-DD",
            "examples": ["2025-10-01", "2025-11-01"],
            "notes": "Stored as TEXT; next scheduled rent payment. Cast to DATE for filtering."
        }
    }
}

# Columns that are native TIMESTAMP / TIMESTAMPTZ in the DB (no casting needed for comparisons).
TIMESTAMP_COLUMNS = {
    "leads": {
        "created_at": {
            "type": "timestamptz",
            "examples": ["2025-02-01 12:30:00+00"],
            "notes": "Timestamp with time zone; compare directly."
        },
        "last_modified": {
            "type": "timestamptz",
            "examples": ["2025-07-22 09:15:00+00"],
            "notes": "Timestamp with time zone; compare directly."
        }
    },
    "buildings": {
        "created_at": {
            "type": "timestamptz",
            "examples": ["2025-01-12 10:30:00+00"],
            "notes": "Timestamp with time zone; compare directly."
        },
        "last_modified": {
            "type": "timestamptz",
            "examples": ["2025-07-16 11:00:00+00"],
            "notes": "Timestamp with time zone; compare directly."
        }
    },
    "rooms": {
        "last_modified": {
            "type": "timestamptz",
            "examples": ["2025-07-16 11:00:00+00"],
            "notes": "Timestamp with time zone; compare directly."
        }
    },
    "tenants": {
        "created_at": {
            "type": "timestamptz",
            "examples": ["2025-02-01 12:30:00+00"],
            "notes": "Timestamp with time zone; compare directly."
        },
        "last_modified": {
            "type": "timestamptz",
            "examples": ["2025-07-22 09:15:00+00"],
            "notes": "Timestamp with time zone; compare directly."
        }
    }
}

def format_date_values_for_prompt() -> str:
    """A cheatsheet section the LLM can copy for date handling."""
    lines = ["\n## Date columns stored as TEXT (cast before filtering)\n"]
    for table, cols in DATE_TEXT_COLUMNS.items():
        lines.append(f"- {table}:")
        for col, meta in cols.items():
            ex = ", ".join(meta.get("examples", [])[:3]) or "e.g., 2025-09-01"
            lines.append(f"  - {col} (format {meta['format']}; examples: {ex})")
    lines.append("""\
\n### SQL date filtering cheatsheet
PostgreSQL:
  WHERE TO_DATE(<col>,'YYYY-MM-DD') >= DATE '2025-09-01'
MySQL:
  WHERE STR_TO_DATE(<col>,'%Y-%m-%d') < DATE '2025-10-01'
SQLite:
  WHERE DATE(<col>) BETWEEN DATE('2025-09-01') AND DATE('2025-09-30')
""")
    lines.append("\n## Native timestamp columns (compare directly)\n")
    for table, cols in TIMESTAMP_COLUMNS.items():
        names = ", ".join(cols.keys())
        if names:
            lines.append(f"- {table}: {names}")
    return "\n".join(lines)