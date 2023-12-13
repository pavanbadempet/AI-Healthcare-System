import sqlite3
import os

if not os.path.exists("healthcare.db"):
    print("NO_DB_FILE")
    exit()

try:
    conn = sqlite3.connect("healthcare.db")
    cursor = conn.cursor()
    
    print("Tables:")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print(tables)
    
    print("\nUsers:")
    try:
        users = cursor.execute("SELECT username FROM users").fetchall()
        print(users)
    except Exception as e:
        print(f"Error reading users: {e}")

except Exception as e:
    print(f"DB Error: {e}")
