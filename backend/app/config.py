import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the root directory (two levels up from backend/app/)
root_dir = Path(__file__).parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set in .env file.")

# Supabase Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise EnvironmentError("SUPABASE_URL or SUPABASE_ANON_KEY not set in .env file.")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL not set in .env file.")

# Application Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
API_PORT = int(os.getenv("API_PORT", "8002"))

if __name__ == "__main__":
    print("✅ Configuration loaded successfully!")
    print("✅ Gemini API Key loaded:", GEMINI_API_KEY is not None)
    print("✅ Supabase URL loaded:", SUPABASE_URL is not None)
    print("✅ Supabase Anon Key loaded:", SUPABASE_ANON_KEY is not None)
    print("✅ Database URL loaded:", DATABASE_URL is not None)
    print("✅ Log Level:", LOG_LEVEL)
    print("✅ API Port:", API_PORT)
    
    if GEMINI_API_KEY:
        masked_key = GEMINI_API_KEY[:4] + "..." + GEMINI_API_KEY[-4:]
        print("   Masked Gemini API Key:", masked_key)
    
    if SUPABASE_URL:
        print("   Supabase URL:", SUPABASE_URL)