import sqlite3

def run():
    conn = sqlite3.connect("healthcare.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'pavan_badempet'")
    conn.commit()
    print(f"Updated {cursor.rowcount} rows. pavan_badempet is now an admin.")
    conn.close()

if __name__ == "__main__":
    run()
