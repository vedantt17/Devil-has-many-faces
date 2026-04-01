# Written by V
import sqlite3
import os
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

SQLITE_PATH = os.getenv("SQLITE_PATH", os.path.join(ROOT_DIR, "data", "dmf.db"))

if not os.path.isabs(SQLITE_PATH):
    SQLITE_PATH = os.path.join(ROOT_DIR, SQLITE_PATH.lstrip("./"))

def get_connection():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_connection()
    schema_path = os.path.join(ROOT_DIR, "schema.sql")
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"SQLite DB initialized at {SQLITE_PATH}")

if __name__ == "__main__":
    init_db()