# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set in .env file.")

if __name__ == "__main__":
    print("Gemini API Key loaded from environment:", GEMINI_API_KEY is not None)
    # You can optionally print a masked key for verification (e.g., first 4 and last 4 chars)
    if GEMINI_API_KEY:
        masked_key = GEMINI_API_KEY[:4] + "..." + GEMINI_API_KEY[-4:]
        print("Masked Gemini API Key:", masked_key)