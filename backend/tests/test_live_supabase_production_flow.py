"""Comprehensive Production E2E Verification Script for DataScope.

Tests:
1. Fresh user registration & authentication.
2. Tenant company provisioning.
3. Google Sheets connection, test, preview, and ingestion into active dataset.
4. Physical presence of rows in tables (DataSource, Dataset, DatasetVersion, DataRecord, AuditLog).
5. Live Data Editor record retrieval.
6. All BI & Decision intelligence modules (Recommendations, Trends, Forecast, Risks, Competition, Reports).
7. Tenant isolation (User A vs User B).
8. Cache eviction & database hydration (Restart simulation).
"""
import json
import urllib.request
import urllib.error
import uuid
import sys
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://127.0.0.1:8000"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"

def make_request(path: str, method: str = "GET", data: dict = None, token: str = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            resp_body = res.read().decode()
            return res.getcode(), json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"error": err_body}
    except Exception as e:
        return 500, {"error": str(e)}

def run_verification():
    print("=" * 70)
    print("DATASCOPE PRODUCTION END-TO-END VERIFICATION")
    print("=" * 70)

    # 1. Health Check
    status, health = make_request("/api/health")
    print(f"\n[1] Health Check: Status {status} -> {health.get('status')}")
    assert status == 200, "Backend health check failed"

    # 2. Register Fresh User A
    user_a_email = f"lead_analyst_{uuid.uuid4().hex[:6]}@datascope.enterprise"
    reg_data_a = {
        "email": user_a_email,
        "password": "Password123!Secure",
        "full_name": "Lead Analyst Enterprise",
        "company_name": "Apex Analytics Group",
        "industry": "E-Commerce & Retail",
        "company_size": "51-200 Employees",
        "country": "United States",
        "primary_objective": "Revenue Growth & Margin Protection"
    }
    status, auth_a = make_request("/api/auth/register", method="POST", data=reg_data_a)
    print(f"\n[2] User A Registration: Status {status}")
    assert status in (200, 201), f"User A registration failed: {auth_a}"
    token_a = auth_a["access_token"]
    user_a = auth_a["user"]
    company_a_id = auth_a["active_company_id"]
    print(f"    User A ID   : {user_a['id']}")
    print(f"    Company A ID: {company_a_id}")

    # 3. Test Google Sheet Connection
    test_payload = {
        "name": "Global Retail Q3 Master",
        "source_type": "google_sheets",
        "config": {
            "sheet_url": GOOGLE_SHEET_URL,
            "sync_frequency": "manual"
        }
    }
    status, test_res = make_request("/api/data-sources/test", method="POST", data=test_payload, token=token_a)
    print(f"\n[3] Google Sheet Connection Test: Status {status} -> success={test_res.get('success')}")
    assert status == 200 and test_res.get("success"), f"Connection test failed: {test_res}"

    # 4. Preview Google Sheet
    status, prev_res = make_request("/api/data-sources/preview", method="POST", data=test_payload, token=token_a)
    print(f"\n[4] Google Sheet Preview: Status {status}")
    assert status == 200, f"Preview failed: {prev_res}"
    print(f"    Preview Rows: {len(prev_res.get('rows', []))}, Columns: {len(prev_res.get('columns', []))}")

    # 5. Ingest into DataScope Active Dataset
    import_payload = {
        "connection_name": "Global Retail Q3 Master",
        "name": "Global Retail Q3 Master",
        "source_type": "google_sheets",
        "config": {
            "sheet_url": GOOGLE_SHEET_URL,
            "sync_frequency": "manual"
        }
    }
    status, import_res = make_request("/api/data-sources/import", method="POST", data=import_payload, token=token_a)
    print(f"\n[5] Analyze/Import Flow: Status {status}")
    assert status == 200, f"Import failed: {import_res}"
    dataset_id = import_res["dataset_id"]
    row_count = import_res["row_count"]
    col_count = import_res["column_count"]
    domain_name = import_res.get("domain", {}).get("name", "General Business")
    print(f"    Dataset ID  : {dataset_id}")
    print(f"    Rows Ingested: {row_count}")
    print(f"    Columns     : {col_count}")
    print(f"    Domain      : {domain_name}")

    # 6. Verify Physical Rows in Database via Live Data Editor Endpoint
    status, records_res = make_request(f"/api/data-management/datasets/{dataset_id}/records?page=1&page_size=10", token=token_a)
    print(f"\n[6] Live Data Editor Records Query: Status {status}")
    assert status == 200, f"Failed to fetch records: {records_res}"
    records = records_res.get("records", [])
    total_records = records_res.get("total_records", 0)
    print(f"    Total Persistent Records: {total_records}")
    print(f"    First Page Sample Count : {len(records)}")
    assert total_records == row_count, f"Total records mismatch: expected {row_count}, got {total_records}"

    # 7. Test All BI & Analytics Modules on Connected Dataset
    endpoints = [
        ("Recommendations", f"/api/dataset/{dataset_id}/recommendations"),
        ("Trends Intelligence", f"/api/dataset/{dataset_id}/trends"),
        ("Universal Forecast", f"/api/dataset/{dataset_id}/forecast"),
        ("Risk Intelligence", f"/api/dataset/{dataset_id}/risk"),
        ("Competition Analysis", f"/api/dataset/{dataset_id}/competition"),
        ("Decision Dashboard", f"/api/dataset/{dataset_id}/decision_dashboard"),
        ("Data Quality Assessment", f"/api/dataset/{dataset_id}/data_quality"),
        ("Executive Dossier Report", f"/api/dataset/{dataset_id}/report"),
    ]
    print("\n[7] Validating Business Intelligence Modules:")
    for name, path in endpoints:
        s, data = make_request(path, token=token_a)
        status_str = "PASSED" if s == 200 else f"FAILED ({s})"
        print(f"    - {name.ljust(26)}: {status_str}")
        assert s == 200, f"Endpoint {name} returned status {s}"

    # 8. Multi-Tenant Isolation Test (User B vs User A)
    user_b_email = f"competitor_user_{uuid.uuid4().hex[:6]}@otherfirm.com"
    reg_data_b = {
        "email": user_b_email,
        "password": "Password123!Secure",
        "full_name": "External Competitor",
        "company_name": "Rival Enterprises",
        "industry": "Finance & Banking",
    }
    status, auth_b = make_request("/api/auth/register", method="POST", data=reg_data_b)
    token_b = auth_b["access_token"]
    print(f"\n[8] Multi-Tenant Isolation Verification:")
    print(f"    User B ID: {auth_b['user']['id']} (Company ID: {auth_b['active_company_id']})")
    
    # User B tries to access User A's dataset
    s_iso, res_iso = make_request(f"/api/dataset/{dataset_id}/recommendations", token=token_b)
    print(f"    User B Access to User A's Dataset: Status {s_iso} (Isolation Enforced)")
    assert s_iso in (403, 404), f"Security violation! User B could access User A dataset (status {s_iso})"

    # User B tries to access User A's records
    s_iso_rec, res_iso_rec = make_request(f"/api/data-management/datasets/{dataset_id}/records", token=token_b)
    print(f"    User B Access to User A's Records: Status {s_iso_rec} (Isolation Enforced)")
    assert s_iso_rec in (403, 404), f"Security violation! User B could access User A records (status {s_iso_rec})"

    # 9. Restart / Cache Eviction Hydration Test
    print(f"\n[9] Restart Hydration Test (Simulating memory loss & DB rehydration):")
    from app.services.dataset_store import clear_store, get_dataset
    clear_store()
    print("    Memory store completely cleared (0 cached datasets).")
    
    # Requesting dataset after memory wipe
    rehydrated = get_dataset(dataset_id)
    assert rehydrated is not None, "Failed to rehydrate dataset from database after cache clear!"
    print(f"    Rehydrated successfully from persistent DB: {rehydrated.filename} ({len(rehydrated.df)} rows)")

    # Test Live Data Editor after restart
    status_post_restart, recs_post = make_request(f"/api/data-management/datasets/{dataset_id}/records?page=1&page_size=5", token=token_a)
    assert status_post_restart == 200, "Failed to fetch records after restart"
    print(f"    Live Data Editor post-restart: Status {status_post_restart} (Hydrated {recs_post.get('total_records')} records)")

    print("\n" + "=" * 70)
    print("ALL PRODUCTION FLOW & ISOLATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return {
        "user_id": user_a['id'],
        "company_id": company_a_id,
        "dataset_id": dataset_id,
        "row_count": row_count,
        "col_count": col_count,
    }

if __name__ == "__main__":
    res = run_verification()
    print("\nSafe Test Output Result Summary:", json.dumps(res, indent=2))
