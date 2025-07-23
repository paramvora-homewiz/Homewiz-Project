# app/db/supabase_connection.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

load_dotenv()
Base = declarative_base()
# Get Supabase credentials
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise EnvironmentError("SUPABASE_URL or SUPABASE_ANON_KEY not set in .env file.")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def get_supabase() -> Client:
    """Get Supabase client instance"""
    return supabase

# Test connection
if __name__ == "__main__":
    try:
        # Test query
        response = supabase.table('rooms').select('count', count='exact').limit(1).execute()
        print(f"✅ Connected to Supabase! Total rooms: {response.count}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")