
import sqlite3
import os

# Connect to the local database
try:
    conn = sqlite3.connect("healthcare.db")
    cursor = conn.cursor()
    
    print("--- Users Table Schema ---")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    found_fee = False
    for col in columns:
        print(col)
        if col[1] == 'consultation_fee':
            found_fee = True
            
    print(f"\nHas 'consultation_fee': {found_fee}")
    
    print("\n--- Appointments Table Schema ---")
    try:
        cursor.execute("PRAGMA table_info(appointments)")
        appt_cols = cursor.fetchall()
        for col in appt_cols:
            print(col)
    except Exception as e:
        print(f"Error checking appointments: {e}")

    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
