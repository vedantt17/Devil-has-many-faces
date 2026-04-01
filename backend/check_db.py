import sys
sys.path.insert(0, ".")
from db.sqlite_client import SQLITE_PATH, get_connection
print("DB path:", SQLITE_PATH)
conn = get_connection()
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t[0] for t in tables])