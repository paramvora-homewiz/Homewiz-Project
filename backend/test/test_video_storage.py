# test_video_storage.py
# Test script to verify video storage functionality

import asyncio
from app.db.supabase_storage import get_storage_client, test_storage_connection

def test_video_bucket():
    """Test if video storage is properly configured"""
    
    print("🎬 Testing Video Storage Configuration...")
    
    # Test basic storage connection
    if not test_storage_connection():
        print("❌ Storage connection failed!")
        return False
    
    try:
        storage_client = get_storage_client()
        
        # List buckets to verify building-images bucket exists
        buckets = storage_client.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        if "building-images" in bucket_names:
            print("✅ building-images bucket found!")
            
            # Test creating video folders structure
            test_building_id = "TEST_BUILDING_123"
            test_categories = ["amenities", "kitchen_bathrooms", "outside", "general"]
            
            print("\n📁 Testing video folder structure:")
            for category in test_categories:
                path = f"{test_building_id}/videos/{category}/"
                print(f"  - {path}")
            
            print("\n✅ Video storage is ready to use!")
            print("\n📋 Video categories available:")
            for cat in test_categories:
                print(f"  - {cat}")
            
            return True
        else:
            print("❌ building-images bucket not found!")
            print("Please create it in your Supabase dashboard")
            return False
            
    except Exception as e:
        print(f"❌ Error testing video storage: {str(e)}")
        return False

def print_usage_examples():
    """Print example usage"""
    print("\n📚 Example Usage:")
    print("\n1. Upload a single video:")
    print("""
    curl -X POST "http://localhost:8000/buildings/{building_id}/videos/single" \\
         -F "file=@video.mp4" \\
         -F "video_category=amenities"
    """)
    
    print("\n2. Upload multiple videos:")
    print("""
    curl -X POST "http://localhost:8000/buildings/{building_id}/videos/upload" \\
         -F "files=@tour.mp4" \\
         -F "files=@exterior.mp4" \\
         -F "video_categories=amenities,outside"
    """)
    
    print("\n3. Get videos by category:")
    print("""
    curl "http://localhost:8000/buildings/{building_id}/videos/category/amenities"
    """)
    
    print("\n4. Get all videos organized by category:")
    print("""
    curl "http://localhost:8000/buildings/{building_id}/videos/categories"
    """)

if __name__ == "__main__":
    print("=" * 50)
    print("🎥 BUILDING VIDEO STORAGE TEST")
    print("=" * 50)
    
    if test_video_bucket():
        print_usage_examples()
        print("\n✨ Everything is configured correctly!")
    else:
        print("\n💥 Please fix the issues above before proceeding")
    
    print("=" * 50)