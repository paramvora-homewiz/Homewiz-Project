#!/usr/bin/env python3
"""
Backend Server Startup Script
This script starts the FastAPI backend server with proper configuration.
"""

import uvicorn
import os
import sys
from pathlib import Path

def setup_environment():
    """Setup environment variables if not already set."""
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  GEMINI_API_KEY not found in environment")
        print("   Please set it: export GEMINI_API_KEY='your_key_here'")
        return False
    
    if not os.getenv("NEXT_PUBLIC_SUPABASE_URL"):
        print("⚠️  NEXT_PUBLIC_SUPABASE_URL not found in environment")
        print("   Please set it: export NEXT_PUBLIC_SUPABASE_URL='your_url_here'")
        return False
    
    if not os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"):
        print("⚠️  NEXT_PUBLIC_SUPABASE_ANON_KEY not found in environment")
        print("   Please set it: export NEXT_PUBLIC_SUPABASE_ANON_KEY='your_key_here'")
        return False
    
    print("✅ Environment variables configured")
    return True

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting HomeWiz Backend Server...")
    print("=" * 50)
    
    # Check environment
    if not setup_environment():
        print("❌ Environment not properly configured")
        return
    
    # Server configuration
    host = "0.0.0.0"  # Allow external connections
    port = 8002  # Use different port to avoid conflicts
    reload = True  # Auto-reload on code changes
    
    print(f"📍 Server will run on: http://{host}:{port}")
    print(f"🔄 Auto-reload: {'Enabled' if reload else 'Disabled'}")
    print(f"📊 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 Alternative docs: http://{host}:{port}/redoc")
    print()
    print("🎯 Available Endpoints:")
    print("   • GET  /                    - Health check")
    print("   • POST /query/              - Legacy query endpoint")
    print("   • POST /universal-query/    - New universal query endpoint")
    print("   • POST /query/suggestions/  - Query suggestions")
    print("   • POST /query/validate/     - Query validation")
    print("   • GET  /query/statistics/   - System statistics")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {str(e)}")

if __name__ == "__main__":
    start_server()
