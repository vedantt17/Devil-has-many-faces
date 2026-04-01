import sqlite3
conn = sqlite3.connect("data/dmf.db")
sample = conn.execute("SELECT * FROM documents_fts LIMIT 1").fetchone()
print("Sample:", sample)
results = conn.execute("SELECT * FROM documents_fts WHERE documents_fts MATCH 'Epstein' LIMIT 3").fetchall()
print("Search results:", len(results))
for r in results:
    print(" ", r)
conn.close()