from sqlalchemy import create_engine, text
from app.db.connection import get_db

def check_tables():
    db = next(get_db())  # Get a session
    try:
        # Query to check all tables in the 'public' schema
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = result.fetchall()
        
        print("Tables in the database:")
        for table in tables:
            print(table[0])

        # Check if specific tables exist in the database
        required_tables = ['operators', 'buildings', 'rooms', 'tenants', 'leads']
        for table in required_tables:
            if table in [t[0] for t in tables]:
                print(f"Table '{table}' exists in the database.")
            else:
                print(f"Table '{table}' does not exist in the database.")

                # Print 2 rows of data from each table
        print("\nPrinting 2 rows of data from each table...\n")
        print_2_rows(db, 'operators')
        print_2_rows(db, 'buildings')
        print_2_rows(db, 'rooms')
        print_2_rows(db, 'tenants')
        print_2_rows(db, 'leads')


        check_operators_data(db)  # Check data in 'operators' table
        check_buildings_data(db)  # Check data in 'buildings' table
        check_rooms_data(db)      # Check data in 'rooms' table
        check_tenants_data(db)    # Check data in 'tenants' table
        check_leads_data(db)   

    except Exception as e:
        print(f"Error checking tables: {e}")
    finally:
        db.close()


def print_2_rows(db, table_name):
    """Function to print 2 rows from any given table."""
    print(f"\n2 rows from the '{table_name}' table:")
    query = text(f"SELECT * FROM {table_name} LIMIT 2")
    result = db.execute(query).fetchall()
    
    if result:
        for row in result:
            print(row)
    else:
        print(f"No data found in the '{table_name}' table.")


# Function to check if data exists in the 'operators' table
def check_operators_data(db):
    print("\nChecking data in 'operators' table...")
    result = db.execute(text("SELECT COUNT(*) FROM operators")).fetchone()
    if result[0] > 0:
        print(f"Data check passed: {result[0]} operators found.")
    else:
        print("Data check failed: No operators found.")

    # Check if any operator has a specific role (e.g., 'Property Manager')
    result = db.execute(text("SELECT COUNT(*) FROM operators WHERE role = :role"), {"role": "Property Manager"}).fetchone()
    if result[0] > 0:
        print(f"Data check passed: Found {result[0]} Property Managers.")
    else:
        print("Data check failed: No Property Managers found.")

# Function to check if data exists in the 'buildings' table
def check_buildings_data(db):
    print("\nChecking data in 'buildings' table...")
    result = db.execute(text("SELECT COUNT(*) FROM buildings")).fetchone()
    if result[0] > 0:
        print(f"Data check passed: {result[0]} buildings found.")
    else:
        print("Data check failed: No buildings found.")

    # Check if a building exists with a specific name or ID
    result = db.execute(text("SELECT COUNT(*) FROM buildings WHERE building_name = :name"), {"name": "Market Street Residences"}).fetchone()
    if result[0] > 0:
        print(f"Data check passed: Found building 'Market Street Residences'.")
    else:
        print("Data check failed: 'Market Street Residences' not found.")

# Function to check if data exists in the 'rooms' table
def check_rooms_data(db):
    print("\nChecking data in 'rooms' table...")
    result = db.execute(text("SELECT COUNT(*) FROM rooms")).fetchone()
    if result[0] > 0:
        print(f"Data check passed: {result[0]} rooms found.")
    else:
        print("Data check failed: No rooms found.")

    # Check if any room has a certain rent amount (e.g., private room rent > 2000)
    result = db.execute(text("SELECT COUNT(*) FROM rooms WHERE private_room_rent > :rent"), {"rent": 2000}).fetchone()
    if result[0] > 0:
        print(f"Data check passed: Found {result[0]} rooms with rent greater than $2000.")
    else:
        print("Data check failed: No rooms with rent greater than $2000.")

# Function to check if data exists in the 'tenants' table
def check_tenants_data(db):
    print("\nChecking data in 'tenants' table...")
    result = db.execute(text("SELECT COUNT(*) FROM tenants")).fetchone()
    if result[0] > 0:
        print(f"Data check passed: {result[0]} tenants found.")
    else:
        print("Data check failed: No tenants found.")

    # Check if any tenant has a specific status (e.g., 'ACTIVE')
    result = db.execute(text("SELECT COUNT(*) FROM tenants WHERE status = :status"), {"status": "ACTIVE"}).fetchone()
    if result[0] > 0:
        print(f"Data check passed: Found {result[0]} active tenants.")
    else:
        print("Data check failed: No active tenants found.")

# Function to check if data exists in the 'leads' table
def check_leads_data(db):
    print("\nChecking data in 'leads' table...")
    result = db.execute(text("SELECT COUNT(*) FROM leads")).fetchone()
    if result[0] > 0:
        print(f"Data check passed: {result[0]} leads found.")
    else:
        print("Data check failed: No leads found.")

    # Check if any lead has a specific status (e.g., 'EXPLORING')
    result = db.execute(text("SELECT COUNT(*) FROM leads WHERE status = :status"), {"status": "EXPLORING"}).fetchone()
    if result[0] > 0:
        print(f"Data check passed: Found {result[0]} leads in 'EXPLORING' status.")
    else:
        print("Data check failed: No leads in 'EXPLORING' status.")

if __name__ == "__main__":
    check_tables()
