"""Run this once to create & seed the SQLite database."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "neataura.db")
SQL_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def init():
    with open(SQL_PATH, "r") as f:
        sql = f.read()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(sql)
    conn.commit()
    conn.close()
    print(f"✅ Database created at {DB_PATH}")

if __name__ == "__main__":
    init()