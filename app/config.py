import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set in .env file.")

# Supabase Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise EnvironmentError("SUPABASE_URL or SUPABASE_ANON_KEY not set in .env file.")

if __name__ == "__main__":
    print("✅ Gemini API Key loaded:", GEMINI_API_KEY is not None)
    print("✅ Supabase URL loaded:", SUPABASE_URL is not None)
    print("✅ Supabase Anon Key loaded:", SUPABASE_ANON_KEY is not None)
    
    if GEMINI_API_KEY:
        masked_key = GEMINI_API_KEY[:4] + "..." + GEMINI_API_KEY[-4:]
        print("   Masked Gemini API Key:", masked_key)
    if SUPABASE_URL:
        print("   Supabase URL:", SUPABASE_URL)