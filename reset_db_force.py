import os
import time
import shutil

DB_FILE = "healthcare.db"
BACKUP_NAME = f"healthcare_old_{int(time.time())}.db"

def reset_db():
    if os.path.exists(DB_FILE):
        print(f"Attempting to reset database: {DB_FILE}")
        try:
            os.rename(DB_FILE, BACKUP_NAME)
            print(f"SUCCESS: Database renamed to {BACKUP_NAME}")
            print("Please restart run_app.bat now.")
        except PermissionError:
            print("ERROR: Database is locked by the running application.")
            print("ACTION REQUIRED: Please CLOSE the running terminal window (Backend) and run this script again, or simply delete 'healthcare.db' manually.")
    else:
        print("Database file not found. It might have been deleted already. You are good to go!")

if __name__ == "__main__":
    reset_db()
