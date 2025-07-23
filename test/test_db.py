import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # Get from .env file
    # DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/postgres"
    # conn = psycopg2.connect(DATABASE_URL)
    Databse_URL = os.getenv("DATABASE_URL")
    print(Databse_URL)
    conn = psycopg2.connect(Databse_URL)
    
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"✅ Connected! PostgreSQL version: {version}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")