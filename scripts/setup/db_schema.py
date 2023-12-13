import sqlite3
import os

try:
    conn = sqlite3.connect("healthcare.db")
    cursor = conn.cursor()
    
    print("Users Columns:")
    import json
    data = cursor.execute("PRAGMA table_info(users)").fetchall()
    print(data)

except Exception as e:
    print(f"DB Error: {e}")
