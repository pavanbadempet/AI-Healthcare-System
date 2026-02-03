from sqlalchemy import create_engine, text
import sys
import os

# Add local path
sys.path.append(os.getcwd())

from backend.database import engine

from backend import models

def fix_db():
    print("Attempting to initialize/fix database...")
    try:
        # 1. Create tables if they don't exist
        models.Base.metadata.create_all(bind=engine)
        print("[OK] Verified/Created DB Tables.")
        
        # 2. Double check created_at just in case (for existing tables)
        with engine.connect() as conn:
            try:
                 conn.execute(text("SELECT created_at FROM users LIMIT 1"))
                 print("[OK] created_at column verified.")
            except Exception:
                 print("[WARN] created_at column missing in existing table. Adding it...")
                 conn.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))
                 conn.commit()
                 print("[OK] Fixed created_at column.")
                 
    except Exception as e:
        print(f"[ERROR] DB Init Failed: {e}")

if __name__ == "__main__":
    fix_db()
