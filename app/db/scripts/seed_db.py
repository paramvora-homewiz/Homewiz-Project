from datetime import datetime, timedelta
import random
import json

from sqlalchemy import func  # Import func for random ordering
from dotenv import load_dotenv

from app.db.connection import Base, get_db, engine  # Import Base, get_db, and engine from your connection.py
from app.db import models  # Import your SQLAlchemy models

load_dotenv()

# Room features for different areas (from your original database_manager.py)
room_features = {
    'Downtown': {'base_rent': 2200, 'premium': 1.3},
    'SoMA': {'base_rent': 1900, 'premium': 1.2},
    'Mission': {'base_rent': 1700, 'premium': 1.1},
    'Hayes Valley': {'base_rent': 2000, 'premium': 1.25},
    'Marina': {'base_rent': 2400, 'premium': 1.4}
}
room_distribution = {
    'BLD_MARKET': 5,  # Reduced for seed data
    'BLD_SOMA': 4,   # Reduced for seed data
    'BLD_MISSION': 4, # Reduced for seed data
    'BLD_HAYES': 4,   # Reduced for seed data
    'BLD_MARINA': 4   # Reduced for seed data
}


def populate_operators(db): # Pass db session as argument
    operators = [
        {'name': 'John Manager', 'email': 'john.manager@homewiz.com', 'phone': '(415)555-0101', 'role': 'Property Manager'},
        {'name': 'Sarah Admin', 'email': 'sarah.admin@homewiz.com', 'phone': '(415)555-0102', 'role': 'Assistant Manager'},
        {'name': 'Mike Maintenance', 'email': 'mike.maintenance@homewiz.com', 'phone': '(415)555-0103', 'role': 'Maintenance'},
        {'name': 'Lisa Leasing', 'email': 'lisa.leasing@homewiz.com', 'phone': '(415)555-0104', 'role': 'Leasing Agent'},
        {'name': 'Tom Support', 'email': 'tom.support@homewiz.com', 'phone': '(415)555-0105', 'role': 'Leasing Agent'}
    ]
    for operator_data in operators:
        operator = models.Operator(**operator_data, date_joined=datetime.now().date() - timedelta(days=180), last_active=datetime.now().date())
        db.add(operator)
    db.commit()
    print("Operators populated.")


def populate_buildings(db): # Pass db session as argument
    buildings = [
        {'building_id': 'BLD_MARKET', 'building_name': 'Market Street Residences', 'full_address': '1000 Market St', 'operator_id': 1, 'street': 'Market St', 'area': 'Downtown', 'city': 'San Francisco', 'state': 'CA', 'zip': '94102', 'floors': 8, 'total_rooms': 20, 'total_bathrooms': 16, 'bathrooms_on_each_floor': 2, 'common_kitchen': 'Premium', 'min_lease_term': 6, 'pref_min_lease_term': 12, 'wifi_included': True, 'laundry_onsite': True, 'common_area': 'Modern Lounge', 'secure_access': True, 'bike_storage': True, 'rooftop_access': True, 'pet_friendly': 'Small Pets', 'cleaning_common_spaces': 'Daily', 'utilities_included': True, 'fitness_area': True, 'work_study_area': True, 'social_events': True, 'nearby_conveniences_walk': 'Shops, Restaurants', 'nearby_transportation': 'BART, MUNI', 'priority': 1},
        {'building_id': 'BLD_SOMA', 'building_name': 'SoMA Commons', 'full_address': '500 Harrison St', 'operator_id': 2, 'street': 'Harrison St', 'area': 'SoMA', 'city': 'San Francisco', 'state': 'CA', 'zip': '94105', 'floors': 6, 'total_rooms': 15, 'total_bathrooms': 12, 'bathrooms_on_each_floor': 2, 'common_kitchen': 'Full', 'min_lease_term': 3, 'pref_min_lease_term': 6, 'wifi_included': True, 'laundry_onsite': True, 'common_area': 'Community Hub', 'secure_access': True, 'bike_storage': True, 'rooftop_access': False, 'pet_friendly': 'Cats Only', 'cleaning_common_spaces': 'Weekly', 'utilities_included': True, 'fitness_area': True, 'work_study_area': False, 'social_events': True, 'nearby_conveniences_walk': 'Cafes, Bars', 'nearby_transportation': 'Caltrain, MUNI', 'priority': 2},
        {'building_id': 'BLD_MISSION', 'building_name': 'Mission Heights', 'full_address': '2500 Mission St', 'operator_id': 3, 'street': 'Mission St', 'area': 'Mission', 'city': 'San Francisco', 'state': 'CA', 'zip': '94110', 'floors': 5, 'total_rooms': 15, 'total_bathrooms': 10, 'bathrooms_on_each_floor': 2, 'common_kitchen': 'Basic', 'min_lease_term': 3, 'pref_min_lease_term': 6, 'wifi_included': True, 'laundry_onsite': True, 'common_area': 'Social Space', 'secure_access': True, 'bike_storage': True, 'rooftop_access': False, 'pet_friendly': 'No', 'cleaning_common_spaces': 'Weekly', 'utilities_included': False, 'fitness_area': False, 'work_study_area': True, 'social_events': True, 'nearby_conveniences_walk': 'Restaurants, Shops', 'nearby_transportation': 'BART, Bus Lines', 'priority': 2},
        {'building_id': 'BLD_HAYES', 'building_name': 'Hayes Valley Suites', 'full_address': '400 Hayes St', 'operator_id': 4, 'street': 'Hayes St', 'area': 'Hayes Valley', 'city': 'San Francisco', 'state': 'CA', 'zip': '94102', 'floors': 4, 'total_rooms': 15, 'total_bathrooms': 8, 'bathrooms_on_each_floor': 2, 'common_kitchen': 'Full', 'min_lease_term': 3, 'pref_min_lease_term': 6, 'wifi_included': True, 'laundry_onsite': True, 'common_area': 'Cozy Commons', 'secure_access': True, 'bike_storage': True, 'rooftop_access': False, 'pet_friendly': 'Small Pets', 'cleaning_common_spaces': 'Weekly', 'utilities_included': True, 'fitness_area': True, 'work_study_area': False, 'social_events': True, 'nearby_conveniences_walk': 'Boutiques, Cafes', 'nearby_transportation': 'MUNI, Bus Lines', 'priority': 2},
        {'building_id': 'BLD_MARINA', 'building_name': 'Marina Bay Views', 'full_address': '2100 Chestnut St', 'operator_id': 5, 'street': 'Chestnut St', 'area': 'Marina', 'city': 'San Francisco', 'state': 'CA', 'zip': '94123', 'floors': 6, 'total_rooms': 15, 'total_bathrooms': 12, 'bathrooms_on_each_floor': 2, 'common_kitchen': 'Premium', 'min_lease_term': 6, 'pref_min_lease_term': 12, 'wifi_included': True, 'laundry_onsite': True, 'common_area': 'Luxury Lounge', 'secure_access': True, 'bike_storage': True, 'rooftop_access': True, 'pet_friendly': 'All Pets', 'cleaning_common_spaces': 'Daily', 'utilities_included': True, 'fitness_area': True, 'work_study_area': True, 'social_events': True, 'nearby_conveniences_walk': 'Whole Foods, Shops', 'nearby_transportation': 'MUNI, Bus Lines', 'priority': 1}
    ]
    for building_data in buildings:
        building = models.Building(**building_data)
        db.add(building)
    db.commit()
    print("Buildings populated.")


def populate_rooms(db): # Pass db session as argument
    for building_id, num_rooms in room_distribution.items():
        building = db.query(models.Building).filter(models.Building.building_id == building_id).first()
        area = building.area
        floors = building.floors
        base_rent = room_features[area]['base_rent']
        premium = room_features[area]['premium']
        for floor in range(1, floors + 1):
            rooms_on_floor = num_rooms // floors + (1 if floor <= num_rooms % floors else 0)
            for room_num in range(1, rooms_on_floor + 1):
                room_number = f"{floor}{str(room_num).zfill(2)}"
                room_id = f"{building_id}_R{room_number}"
                floor_premium = 1 + (floor - 1) * 0.05
                private_rent = base_rent * premium * floor_premium
                room_data = {
                    'room_id': room_id, 'room_number': room_number, 'building_id': building_id, 'floor_number': floor,
                    'maximum_people_in_room': random.choice([1, 2]), 'private_room_rent': private_rent,
                    'bathroom_type': random.choice(['Private', 'En-Suite', 'Shared']),
                    'bed_size': random.choice(['Twin', 'Full', 'Queen']), 'bed_type': random.choice(['Single', 'Platform']),
                    'view': random.choice(['Street', 'City', 'Bay', 'Garden']), 'sq_footage': random.randint(200, 400),
                    'mini_fridge': True, 'sink': True, 'bedding_provided': True, 'work_desk': True, 'work_chair': True,
                    'heating': True, 'air_conditioning': True, 'cable_tv': True,
                    'room_storage': random.choice(['Built-in Closet', 'Walk-in Closet'])
                }
                room = models.Room(**room_data)
                db.add(room)
    db.commit()
    print("Rooms populated.")


def populate_tenants(db): # Pass db session as argument
    current_date = datetime.now().date()
    available_rooms = db.query(models.Room).filter(models.Room.status == 'AVAILABLE').order_by(func.random()).limit(15).all() # Reduced limit for seed data
    for i, room in enumerate(available_rooms, 1):
        lease_type = random.choices(['past', 'current', 'future'], weights=[0.3, 0.4, 0.3], k=1)[0]
        if lease_type == 'past':
            lease_end = current_date - timedelta(days=random.randint(1, 180))
            lease_length = random.choice([6, 12])
            lease_start = lease_end - timedelta(days=lease_length * 30)
        elif lease_type == 'current':
            lease_start = current_date - timedelta(days=random.randint(0, 180))
            lease_length = random.choice([6, 12])
            lease_end = lease_start + timedelta(days=lease_length * 30)
        else:  # future
            lease_start = current_date + timedelta(days=random.randint(1, 180))
            lease_length = random.choice([6, 12])
            lease_end = lease_start + timedelta(days=lease_length * 30)

        tenant_id = f"TNT_{str(i).zfill(3)}"
        email = f"tenant{i}@example.com"
        private_rent = room.private_room_rent

        if lease_end < current_date:
            status = 'EXPIRED'
        elif lease_start > current_date:
            status = 'PENDING'
        else:
            status = 'ACTIVE'

        payment_status = 'PENDING' if status == 'PENDING' else random.choice(['CURRENT'] * 9 + ['LATE'])

        tenant_data = {
            'tenant_id': tenant_id, 'tenant_name': f"Tenant {i}", 'room_id': room.room_id, 'room_number': room.room_number,
            'lease_start_date': lease_start, 'lease_end_date': lease_end, 'operator_id': random.randint(1, 5),
            'booking_type': random.choice(['LEASE', 'CORPORATE', 'STUDENT']),
            'tenant_nationality': random.choice(['US-CITIZEN', 'PERMANENT-RESIDENT', 'F1-VISA']), 'tenant_email': email,
            'phone': f"(415)555-{str(1000 + i).zfill(4)}", 'emergency_contact_name': f"Emergency Contact {i}",
            'emergency_contact_phone': f"(415)555-{str(2000 + i).zfill(4)}", 'emergency_contact_relation': random.choice(['Parent', 'Sibling', 'Spouse']),
            'building_id': room.building_id, 'status': status, 'deposit_amount': private_rent * 2, 'payment_status': payment_status
        }
        tenant = models.Tenant(**tenant_data)
        db.add(tenant)
    db.commit()
    print("Tenants populated.")


def populate_leads(db): # Pass db session as argument
    available_rooms = db.query(models.Room).filter(models.Room.status == 'AVAILABLE').order_by(func.random()).limit(5).all() # Reduced limit
    leads_data = [
        {'lead_id': 'LEAD_001', 'email': 'sarah.smith@email.com', 'status': 'EXPLORING', 'interaction_count': 2, 'rooms_interested': json.dumps([available_rooms[0].room_id if available_rooms else None]), 'visa_status': 'US-CITIZEN'},
        {'lead_id': 'LEAD_002', 'email': 'john.doe@email.com', 'status': 'EXPLORING', 'interaction_count': 5, 'rooms_interested': json.dumps([r.room_id for r in available_rooms[0:3] if available_rooms]), 'visa_status': 'F1-VISA'},
        {'lead_id': 'LEAD_003', 'email': 'emily.wong@email.com', 'status': 'SHOWING_SCHEDULED', 'interaction_count': 8, 'rooms_interested': json.dumps([r.room_id for r in available_rooms[1:3]if available_rooms]), 'selected_room_id': available_rooms[1].room_id if len(available_rooms) > 1 else None, 'showing_dates': json.dumps(['2024-12-20 14:00:00', '2024-12-21 11:00:00']), 'planned_move_in': '2025-01-15', 'planned_move_out': '2025-07-15', 'visa_status': 'H1B-VISA'},
        {'lead_id': 'LEAD_004', 'email': 'michael.chen@email.com', 'status': 'BACKGROUND_CHECK', 'interaction_count': 10, 'rooms_interested': json.dumps([available_rooms[3].room_id if len(available_rooms) > 3 else None]), 'selected_room_id': available_rooms[3].room_id if len(available_rooms) > 3 else None, 'showing_dates': json.dumps(['2024-12-18 15:00:00']), 'planned_move_in': '2025-01-01', 'planned_move_out': '2025-12-31', 'visa_status': 'PERMANENT-RESIDENT'},
        {'lead_id': 'LEAD_005', 'email': 'anna.garcia@email.com', 'status': 'LEASE_REQUESTED', 'interaction_count': 12, 'rooms_interested': json.dumps([available_rooms[4].room_id if len(available_rooms) > 4 else None]), 'selected_room_id': available_rooms[4].room_id if len(available_rooms) > 4 else None, 'showing_dates': json.dumps(['2024-12-17 10:00:00']), 'planned_move_in': '2025-02-01', 'planned_move_out': '2026-01-31', 'visa_status': 'US-CITIZEN'},
        {'lead_id': 'LEAD_006', 'email': 'david.kim@email.com', 'status': 'APPROVED', 'interaction_count': 15, 'rooms_interested': json.dumps([available_rooms[0].room_id if available_rooms else None]), 'selected_room_id': available_rooms[0].room_id if available_rooms else None, 'showing_dates': json.dumps(['2024-12-15 13:00:00']), 'planned_move_in': '2025-01-10', 'planned_move_out': '2025-07-10', 'visa_status': 'F1-VISA'},
        {'lead_id': 'LEAD_007', 'email': 'lisa.taylor@email.com', 'status': 'REJECTED', 'interaction_count': 6, 'rooms_interested': json.dumps([available_rooms[1].room_id if len(available_rooms) > 1 else None]), 'selected_room_id': available_rooms[1].room_id if len(available_rooms) > 1 else None, 'showing_dates': json.dumps(['2024-12-14 16:00:00']), 'planned_move_in': '2025-01-05', 'planned_move_out': '2025-06-05', 'visa_status': 'OTHER'}
    ]
    for lead_data in leads_data:
        lead = models.Lead(**lead_data)
        db.add(lead)
    db.commit()
    print("Leads populated.")


if __name__ == "__main__":
    print("Starting database seeding...")
    Base.metadata.create_all(engine) # Ensure tables are created in Supabase using engine from connection.py
    db_gen = get_db() # Get generator
    db_session = next(db_gen) # Get actual session
    try:
        populate_operators(db_session) # Pass session to populate functions
        populate_buildings(db_session) # Pass session to populate functions
        populate_rooms(db_session) # Pass session to populate functions
        populate_tenants(db_session) # Pass session to populate functions
        populate_leads(db_session) # Pass session to populate functions
    finally:
        db_session.close() # Ensure session is closed
    print("Database seeding completed successfully!")