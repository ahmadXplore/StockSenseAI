import sqlite3

conn = sqlite3.connect('stocksense.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables found:", [t[0] for t in tables])
print()

for t in tables:
    table_name = t[0]
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cur.fetchone()[0]
    print(f"  {table_name}: {count} rows")

conn.close()
