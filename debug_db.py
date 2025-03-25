from sqlalchemy import create_engine, inspect
import sys
import os

# Add local path to sys.path to find backend module
sys.path.append(os.getcwd())

try:
    from backend.database import engine
    from backend import models

    inspector = inspect(engine)
    columns = inspector.get_columns('users')
    
    print("Columns in 'users' table:")
    found_created_at = False
    for column in columns:
        print(f"- {column['name']} ({column['type']})")
        if column['name'] == 'created_at':
            found_created_at = True

    if found_created_at:
        print("\n✅ 'created_at' column FOUND.")
    else:
        print("\n❌ 'created_at' column MISSING.")

except Exception as e:
    print(f"Error inspecting DB: {e}")
