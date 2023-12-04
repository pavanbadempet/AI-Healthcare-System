import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("password123")

conn = sqlite3.connect("healthcare.db")
cursor = conn.cursor()

cursor.execute("UPDATE users SET hashed_password = ? WHERE username = ?", (hashed, "pavansofts"))
conn.commit()
print("PASSWORD_RESET_SUCCESS")
