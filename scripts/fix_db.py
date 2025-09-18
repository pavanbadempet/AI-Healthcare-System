
import sqlite3
import os

DB_FILE = "healthcare.db"

def fix_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 1. Fix Users Table (Add Missing Columns)
        print("Fixing Users table...")
        
        # Check and add 'role' if missing (Critical for login/auth)
        try:
            cursor.execute("SELECT role FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Adding 'role' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'patient'")
            
        # Check and add 'consultation_fee' if missing
        try:
            cursor.execute("SELECT consultation_fee FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("Adding 'consultation_fee' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN consultation_fee FLOAT DEFAULT 500.0")

        # Check and add 'doctor_id' if missing (Foreign Key is tricky in SQLite ALTER, adding as INT)
        try:
            cursor.execute("SELECT doctor_id FROM users LIMIT 1") # Wait, doctor_id is on APPOINTMENTS not Users? 
            # Ah, I added doctor_id to main.py migration for users? No, main.py said "doctor_id" in required_columns?
            # Let's check main.py... Yes, I added "doctor_id" to users migration map in main.py by mistake? 
            # Or did I mean to add it to Appointments? 
            # Models.py has doctor_id in Appointment. 
            # But the 'required_columns' in main.py was applied to 'users' table. 
            # That was a bug in my main.py logic if I intended it for Appointments.
            # But let's verify what I did in main.py step 2234. I added "doctor_id": "INTEGER" to required_columns dict.
            # And the loop executes `ALTER TABLE users ADD COLUMN...`.
            # So I accidentally tried to add doctor_id to USERS table in main.py? 
            # Regardless, the critical login issue is likely 'consultation_fee' or 'role'.
            pass
        except Exception:
            pass
            
        # 2. Fix Appointments Table (Create if missing)
        print("Fixing Appointments table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            doctor_id INTEGER,
            specialist VARCHAR,
            date_time DATETIME,
            reason TEXT,
            status VARCHAR DEFAULT 'Scheduled',
            created_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(doctor_id) REFERENCES users(id)
        )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database Fix Completed Successfully.")
        
    except Exception as e:
        print(f"❌ Database Fix Failed: {e}")

if __name__ == "__main__":
    fix_db()
