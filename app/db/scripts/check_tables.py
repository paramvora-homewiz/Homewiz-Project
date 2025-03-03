from sqlalchemy import text

from app.db.connection import get_db

def check_tables():
    db = next(get_db())
    try:
        result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = result.fetchall()

        print("Tables in the database:")
        for table in tables:
            print(table[0])
    except Exception as e:
        print(f"Error fetching tables: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_tables()
