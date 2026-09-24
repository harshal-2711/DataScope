"""Deep verification of actual Supabase PostgreSQL tables, schemas, relationships, and data."""
from __future__ import annotations

import json
import urllib.request
import urllib.error

SUPABASE_URL = "https://wvbozonxguapddgrbitz.supabase.co"
ANON_KEY = "sb_publishable_C-De4bkO-fUjauTg_GGGLg_IMot1AnQ"

ALL_TABLES = [
    "profiles",
    "companies",
    "company_memberships",
    "data_sources",
    "datasets",
    "dataset_versions",
    "data_records",
    "data_sync_jobs",
    "reports",
    "audit_logs",
]

def supabase_get(endpoint: str):
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    req = urllib.request.Request(
        url,
        headers={
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
            "Content-Type": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            return res.getcode(), data
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, body
    except Exception as e:
        return 500, str(e)

def verify_tables():
    print("======================================================================")
    print("DATASCOPE REAL SUPABASE CLOUD DATABASE TABLE AUDIT")
    print(f"Supabase Project URL: {SUPABASE_URL}")
    print("======================================================================")

    for tbl in ALL_TABLES:
        code, data = supabase_get(f"{tbl}?select=*&limit=5")
        if code == 200:
            count = len(data) if isinstance(data, list) else 0
            sample_keys = list(data[0].keys()) if count > 0 and isinstance(data[0], dict) else []
            print(f"[EXISTS 200 OK] Table: public.{tbl.ljust(22)} | Rows returned: {count} | Columns: {sample_keys[:6]}")
        elif code in (401, 403):
            print(f"[RLS ACTIVE   ] Table: public.{tbl.ljust(22)} | Protected by Row Level Security (Code {code})")
        elif code == 404:
            print(f"[MISSING 404  ] Table: public.{tbl.ljust(22)} | Table not found in PostgREST schema")
        else:
            print(f"[STATUS {code}   ] Table: public.{tbl.ljust(22)} | {data}")

if __name__ == "__main__":
    verify_tables()
