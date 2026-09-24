import sqlite3

conn = sqlite3.connect("datascope.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
print("Local SQLite (datascope.db) table row counts:")
for t in tables:
    cursor.execute(f"SELECT count(*) FROM {t}")
    cnt = cursor.fetchone()[0]
    print(f"  - {t.ljust(25)}: {cnt} rows")

cursor.execute("SELECT id, name, source_type, company_id, dataset_id FROM data_sources LIMIT 5;")
sources = cursor.fetchall()
print("\nSample local data_sources:")
for s in sources:
    print(" ", s)
