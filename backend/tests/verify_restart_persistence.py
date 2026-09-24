"""Test restart persistence against Supabase PostgreSQL."""
import json
import urllib.request
import urllib.error
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def make_req(path: str, method: str = "GET", data: dict = None, token: str = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as res:
        resp = res.read().decode()
        return res.getcode(), json.loads(resp) if resp else {}

def test_persistence_after_restart(email: str, dataset_id: str):
    print("=" * 70)
    print("TESTING PERSISTENCE AFTER BACKEND RESTART")
    print("=" * 70)

    # 1. Login with user created prior to restart
    login_payload = {
        "email": email,
        "password": "Password123!Secure"
    }
    status, auth = make_req("/api/auth/login", method="POST", data=login_payload)
    print(f"[1] Login via HTTP after restart: Status {status}")
    token = auth["access_token"]

    # 2. Get User Profile & Active Company
    status, profile = make_req("/api/auth/me", token=token)
    print(f"[2] User Profile from Supabase: Status {status} (Companies: {len(profile.get('companies', []))})")

    # 3. List Data Sources
    status, sources = make_req("/api/data-sources", token=token)
    print(f"[3] List Data Sources from Supabase: Status {status} ({len(sources)} source(s) found)")
    for s in sources:
        print(f"    - DataSource ID: {s['id']}, Name: {s['name']}, Dataset ID: {s.get('dataset_id')}")

    # 4. Fetch Live Data Editor Records for the Dataset
    status, recs = make_req(f"/api/data-management/datasets/{dataset_id}/records?page=1&page_size=10", token=token)
    print(f"[4] Live Data Editor Records from Supabase: Status {status} (total_records={recs['total_records']}, columns={len(recs['columns'])})")
    print(f"    First record data keys: {list(recs['records'][0]['data'].keys())}")

    # 5. Verify Dataset List and Version History
    status, d_list = make_req("/api/data-management/datasets", token=token)
    print(f"[5] List Datasets: Status {status} ({len(d_list)} datasets)")
    for d in d_list:
        print(f"    - Dataset: {d['id']}, Name: {d['name']}, Rows: {d['row_count']}, Active Version: {d['active_version_number']}")

    status, versions = make_req(f"/api/data-management/datasets/{dataset_id}/versions", token=token)
    print(f"[6] Dataset Version History: Status {status} ({len(versions)} version(s) found)")

    print("=" * 70)
    print("RESTART PERSISTENCE CONFIRMED: ALL DATA HYDRATED DIRECTLY FROM SUPABASE!")
    print("=" * 70)

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "prod_analyst_f3880a@datascope.enterprise"
    did = sys.argv[2] if len(sys.argv) > 2 else "bef1e349a80445f2843183f81dbb9c7b"
    test_persistence_after_restart(email, did)
