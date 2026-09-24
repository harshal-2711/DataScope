import urllib.request
import urllib.error
import json
import os

SUPABASE_URL = "https://wvbozonxguapddgrbitz.supabase.co"
ANON_KEY = "sb_publishable_C-De4bkO-fUjauTg_GGGLg_IMot1AnQ"

TABLES_TO_CHECK = [
    "profiles",
    "companies",
    "company_memberships",
    "datasets",
    "dataset_versions",
    "data_sources",
    "data_sync_jobs",
    "reports",
    "audit_logs"
]

def check_tables():
    print(f"Checking tables on Supabase: {SUPABASE_URL}\n")
    results = {}
    for table in TABLES_TO_CHECK:
        url = f"{SUPABASE_URL}/rest/v1/{table}?select=*&limit=1"
        req = urllib.request.Request(url, headers={
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}"
        })
        try:
            with urllib.request.urlopen(req) as res:
                results[table] = f"EXISTS (Status: {res.getcode()})"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                results[table] = "NOT CREATED YET (404 Not Found)"
            elif e.code in (401, 403, 200):
                results[table] = f"EXISTS (Status: {e.code} Protected by RLS)"
            else:
                results[table] = f"Status {e.code}: {e.read().decode()}"
        except Exception as e:
            results[table] = f"Error: {e}"

    print("-" * 60)
    for tbl, stat in results.items():
        print(f"Table public.{tbl.ljust(22)} : {stat}")
    print("-" * 60)

if __name__ == "__main__":
    check_tables()
