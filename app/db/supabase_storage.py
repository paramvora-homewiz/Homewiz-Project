# app/db/supabase_storage.py
# This file handles ONLY Supabase Storage, not the database

from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase credentials for storage only
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file for image storage")

# Create Supabase client for storage operations only
supabase_storage: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_storage_client():
    """Get Supabase client for storage operations"""
    return supabase_storage

def test_storage_connection():
    """Test Supabase storage connection"""
    try:
        # Test storage connection
        buckets = supabase_storage.storage.list_buckets()
        print("✅ Supabase storage connection successful!")
        
        # Check if building-images bucket exists
        bucket_names = [bucket.name for bucket in buckets]
        if "building-images" in bucket_names:
            print("✅ building-images bucket found!")
            return True
        else:
            print("⚠️  building-images bucket not found. Please create it in Supabase dashboard.")
            return False
            
    except Exception as e:
        print(f"❌ Supabase storage connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Supabase storage connection...")
    if test_storage_connection():
        print("🎉 Storage connection successful!")
    else:
        print("💥 Storage connection test failed!")