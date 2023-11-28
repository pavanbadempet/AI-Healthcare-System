
import os
import shutil

DB_FILE = "healthcare.db"
WAL_FILE = "healthcare.db-wal"
SHM_FILE = "healthcare.db-shm"

def reset_db():
    print("Stopping any running processes (if needed)...")
    # In a real scenario we might kill processes, here we just delete files
    
    files = [DB_FILE, WAL_FILE, SHM_FILE]
    for f in files:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f"Deleted {f}")
            except Exception as e:
                print(f"Error deleting {f}: {e}")
        else:
            print(f"{f} not found.")

    print("Database reset complete. Restart the app to recreate tables.")

if __name__ == "__main__":
    reset_db()
