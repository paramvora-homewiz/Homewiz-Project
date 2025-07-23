from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
# DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL not set.")
if not DATABASE_PASSWORD:
    raise EnvironmentError("DATABASE_PASSWORD not set.")


engine = create_engine(DATABASE_URL)

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