import os
import sys
from pathlib import Path
import psycopg2
from sqlalchemy import text

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

def apply_migration():
    print("--- APPLYING SUPABASE MIGRATION ---")
    migration_path = Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations" / "20260924000000_production_compatibility.sql"
    with open(migration_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Executing additive migration...")
    cursor.execute(sql)
    print("Migration executed successfully!")

    # Check data_records table
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'data_records'
        );
    """)
    records_exists = cursor.fetchone()[0]
    print(f"Verification: public.data_records exists = {records_exists}")

    # Check columns & rows across all tables
    tables = [
        "profiles",
        "companies",
        "company_memberships",
        "data_sources",
        "datasets",
        "dataset_versions",
        "data_records",
        "data_sync_jobs",
        "reports",
        "audit_logs"
    ]
    print("\n--- SUPABASE CLOUD TABLES VERIFICATION ---")
    for tbl in tables:
        cursor.execute(f"SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{tbl}';")
        cols = cursor.fetchone()[0]
        cursor.execute(f"SELECT count(*) FROM public.{tbl};")
        rows = cursor.fetchone()[0]
        print(f"Table public.{tbl.ljust(22)} : {cols} columns | {rows} rows")

    cursor.execute("SELECT current_database(), current_user, version();")
    db_name, db_user, db_ver = cursor.fetchone()
    print(f"\nConnected Database: {db_name}, User: {db_user}")
    print(f"PostgreSQL Version: {db_ver}")

    conn.close()

if __name__ == "__main__":
    apply_migration()
