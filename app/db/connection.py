from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB_URL")
DATABASE_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")

if not DATABASE_URL:
    raise EnvironmentError("SUPABASE_DB_URL not set.")
if not DATABASE_PASSWORD:
    raise EnvironmentError("SUPABASE_DB_PASSWORD not set.")

SQLALCHEMY_DATABASE_URL = f"{DATABASE_URL}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    try:
        db_test = SessionLocal()
        db_test.execute(text("SELECT 1"))
        db_test.close()
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Check .env and Supabase details.")