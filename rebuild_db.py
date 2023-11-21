import os
import time
import sys
from sqlalchemy import create_engine, MetaData
from backend.database import SQLALCHEMY_DATABASE_URL
from backend import models

def rebuild_database():
    print("Initializing Database Rebuild...")
    
    # 1. Try to connect and drop all tables (Soft Reset)
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        meta = MetaData()
        meta.reflect(bind=engine)
        print(f"Found existing tables: {list(meta.tables.keys())}")
        print("Attempting to DROP all tables...")
        meta.drop_all(bind=engine)
        print("Tables dropped using SQLAlchemy.")
    except Exception as e:
        print(f"Soft reset failed (expected if file locked): {e}")

    # 2. Hard Delete of File
    db_path = "healthcare.db"
    if os.path.exists(db_path):
        print(f"Attempting to delete {db_path}...")
        try:
            os.remove(db_path)
            print("Database file DELETED successfully.")
        except PermissionError:
            print("!!! ERROR: Database file is LOCKED !!!")
            print("Please manually close any 'python.exe' or terminal windows running the app.")
            return False
    
    # 3. Recreate
    print("Creating new schema...")
    try:
        # Re-import to ensure fresh metadata
        from backend.database import engine
        models.Base.metadata.create_all(bind=engine)
        print("SUCCESS: Database schema created!")
        print("You can now run 'run_app.bat'.")
        return True
    except Exception as e:
        print(f"Creation failed: {e}")
        return False

if __name__ == "__main__":
    success = rebuild_database()
    if not success:
        sys.exit(1)
