# test_supabase_client.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

# Get credentials
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

print("=" * 50)
print("SUPABASE CLIENT TEST")
print("=" * 50)

# Check if credentials exist
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Missing credentials!")
    print(f"SUPABASE_URL: {'Set' if SUPABASE_URL else 'Not set'}")
    print(f"SUPABASE_ANON_KEY: {'Set' if SUPABASE_ANON_KEY else 'Not set'}")
    print("\nMake sure your .env file contains:")
    print("NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co")
    print("NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...")
    exit(1)

print(f"✅ URL: {SUPABASE_URL}")
print(f"✅ Key: {SUPABASE_ANON_KEY[:20]}...")

# Create client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    print("✅ Supabase client created successfully!")
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    exit(1)

print("\n" + "=" * 50)
print("TESTING CONNECTION")
print("=" * 50)

# Test 1: Check if we can access the rooms table
try:
    # Count total rooms
    count_response = supabase.table('rooms').select('*', count='exact').limit(1).execute()
    total_rooms = count_response.count
    print(f"✅ Connected to database! Total rooms: {total_rooms}")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    print("\nPossible issues:")
    print("- Table 'rooms' might not exist")
    print("- RLS (Row Level Security) might be blocking access")
    print("- Anon key might not have permissions")
    exit(1)

print("\n" + "=" * 50)
print("FETCHING 10 ROOMS WITH 2 FILTERS")
print("=" * 50)

# Filter criteria
MAX_PRICE = 2500
BATHROOM_TYPE = "Private"

print(f"Filters:")
print(f"1. Price <= ${MAX_PRICE}")
print(f"2. Bathroom Type = {BATHROOM_TYPE}")
print()

try:
    # Query with 2 filters
    response = (
        supabase.table('rooms')
        .select('room_id, room_number, private_room_rent, bathroom_type, bed_size, view, floor_number')
        .lte('private_room_rent', MAX_PRICE)  # Filter 1: price <= 2500
        .eq('bathroom_type', BATHROOM_TYPE)    # Filter 2: bathroom = "Private"
        .limit(10)
        .execute()
    )
    
    rooms = response.data
    
    if not rooms:
        print("❌ No rooms found matching the criteria")
    else:
        print(f"✅ Found {len(rooms)} rooms matching criteria:\n")
        
        # Display results in a nice format
        for i, room in enumerate(rooms, 1):
            print(f"Room {i}:")
            print(f"  ID: {room['room_id']}")
            print(f"  Number: {room['room_number']}")
            print(f"  Price: ${room['private_room_rent']}")
            print(f"  Bathroom: {room['bathroom_type']}")
            print(f"  Bed Size: {room['bed_size']}")
            print(f"  View: {room['view']}")
            print(f"  Floor: {room['floor_number']}")
            print("-" * 30)
    
    # Try another query with different filters
    print("\n" + "=" * 50)
    print("TRYING ANOTHER QUERY")
    print("=" * 50)
    print("Filters: Bed Size = 'Queen' AND Price <= $3000")
    
    response2 = (
        supabase.table('rooms')
        .select('room_number, private_room_rent, bed_size, view')
        .eq('bed_size', 'Queen')
        .lte('private_room_rent', 3000)
        .limit(5)
        .execute()
    )
    
    if response2.data:
        print(f"\n✅ Found {len(response2.data)} Queen bed rooms:")
        for room in response2.data:
            print(f"  Room {room['room_number']}: ${room['private_room_rent']} - {room['view']}")
    
except Exception as e:
    print(f"❌ Query failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check if RLS is enabled on the 'rooms' table")
    print("2. If RLS is enabled, you might need to:")
    print("   - Disable RLS for testing, OR")
    print("   - Create a policy that allows anon users to read")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)