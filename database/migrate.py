import sqlite3
import os

DB_PATH = r'c:\Users\DAG\Downloads\PROJECT\feedback intelligence system\database\comments.db'

def migrate():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('ALTER TABLE comments ADD COLUMN user_handle TEXT DEFAULT "Anonymous"')
        conn.commit()
        conn.close()
        print("Migration successful: added user_handle column.")
    except Exception as e:
        print(f"Migration error (might already exist): {e}")

if __name__ == "__main__":
    migrate()
