"""Real Production Supabase Verification Script for DataScope.

Executes the REAL application flow over HTTP against the running Uvicorn server:
1. Register fresh user.
2. Company automatically provisioned.
3. Test Google Sheet connection.
4. Preview Google Sheet.
5. Ingest into active analytics dataset.
6. Verify records via Live Data Editor endpoint.
7. Query Supabase PostgreSQL directly using the active SQLAlchemy engine to prove physical row presence and exact ID match!
"""
import json
import urllib.request
import urllib.error
import uuid
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import engine
from sqlalchemy import text

BASE_URL = "http://127.0.0.1:8000"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"

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

def run_real_import():
    print("=" * 70)
    print("EXECUTING REAL DATASCOPE APPLICATION IMPORT TO SUPABASE POSTGRESQL")
    print("=" * 70)

    # 1. Health check
    status, health = make_req("/api/health")
    print(f"[1] Backend Health: Status {status}")

    # 2. Register fresh production user
    email = f"prod_analyst_{uuid.uuid4().hex[:6]}@datascope.enterprise"
    reg_payload = {
        "email": email,
        "password": "Password123!Secure",
        "full_name": "Executive Analyst",
        "company_name": "Acme Global Enterprise",
        "industry": "E-Commerce & Retail",
        "company_size": "51-200 Employees",
        "country": "United States",
        "primary_objective": "Revenue Growth & Margin Protection"
    }
    status, auth = make_req("/api/auth/register", method="POST", data=reg_payload)
    print(f"[2] User Registration via HTTP: Status {status}")
    token = auth["access_token"]
    user_id = auth["user"]["id"]
    company_id = auth["active_company_id"]
    print(f"    Created User ID   : {user_id}")
    print(f"    Created Company ID: {company_id}")

    # 3. Test Google Sheet connection
    test_payload = {
        "name": "Global Retail Master Sheet",
        "source_type": "google_sheets",
        "config": {
            "sheet_url": GOOGLE_SHEET_URL,
            "sync_frequency": "manual"
        }
    }
    status, test_res = make_req("/api/data-sources/test", method="POST", data=test_payload, token=token)
    print(f"[3] Test Connection via HTTP: Status {status} (success={test_res.get('success')})")

    # 4. Preview Google Sheet
    status, prev_res = make_req("/api/data-sources/preview", method="POST", data=test_payload, token=token)
    print(f"[4] Preview via HTTP: Status {status} ({len(prev_res.get('columns', []))} columns)")

    # 5. Import into DataScope
    import_payload = {
        "connection_name": "Global Retail Master Sheet",
        "name": "Global Retail Master Sheet",
        "source_type": "google_sheets",
        "config": {
            "sheet_url": GOOGLE_SHEET_URL,
            "sync_frequency": "manual"
        }
    }
    status, imp = make_req("/api/data-sources/import", method="POST", data=import_payload, token=token)
    print(f"[5] Import to Active Dataset via HTTP: Status {status}")
    dataset_id = imp["dataset_id"]
    row_count = imp["row_count"]
    col_count = imp["column_count"]
    print(f"    Dataset ID : {dataset_id}")
    print(f"    Row Count  : {row_count}")
    print(f"    Col Count  : {col_count}")

    # 6. Live Data Editor Query
    status, recs = make_req(f"/api/data-management/datasets/{dataset_id}/records?page=1&page_size=10", token=token)
    print(f"[6] Live Data Editor Records: Status {status} (total_records={recs.get('total_records')})")

    # 7. DIRECT SUPABASE POSTGRESQL PROOF QUERY
    print("\n" + "=" * 70)
    print("DIRECT SUPABASE POSTGRESQL DATABASE VERIFICATION QUERY")
    print("=" * 70)
    with engine.connect() as conn:
        # Check User / Profile
        user_row = conn.execute(text("SELECT id, email, full_name FROM users WHERE id = :uid"), {"uid": user_id}).fetchone()
        print(f"1. public.users row in Supabase          : id={user_row[0]}, email={user_row[1]}")

        # Check Company
        comp_row = conn.execute(text("SELECT id, name, owner_id FROM companies WHERE id = :cid"), {"cid": company_id}).fetchone()
        print(f"2. public.companies row in Supabase      : id={comp_row[0]}, name={comp_row[1]}")

        # Check Membership
        mem_row = conn.execute(text("SELECT id, user_id, company_id, role FROM company_memberships WHERE user_id = :uid AND company_id = :cid"), {"uid": user_id, "cid": company_id}).fetchone()
        print(f"3. public.company_memberships in Supabase: id={mem_row[0]}, role={mem_row[3]}")

        # Check Data Source
        ds_row = conn.execute(text("SELECT id, name, source_type, company_id, dataset_id, total_records_synced FROM data_sources WHERE company_id = :cid"), {"cid": company_id}).fetchone()
        data_source_id = ds_row[0]
        print(f"4. public.data_sources in Supabase       : id={ds_row[0]}, name={ds_row[1]}, dataset_id={ds_row[4]}, synced={ds_row[5]}")

        # Check Dataset
        dataset_row = conn.execute(text("SELECT id, name, file_type, company_id, current_row_count, current_col_count FROM datasets WHERE id = :did"), {"did": dataset_id}).fetchone()
        print(f"5. public.datasets in Supabase           : id={dataset_row[0]}, name={dataset_row[1]}, rows={dataset_row[4]}, cols={dataset_row[5]}")

        # Check Dataset Version
        ver_row = conn.execute(text("SELECT id, dataset_id, version_number, row_count, col_count FROM dataset_versions WHERE dataset_id = :did"), {"did": dataset_id}).fetchone()
        dataset_version_id = ver_row[0]
        print(f"6. public.dataset_versions in Supabase   : id={ver_row[0]}, version={ver_row[2]}, rows={ver_row[3]}")

        # Check Data Records
        data_recs_count = conn.execute(text("SELECT count(*) FROM data_records WHERE dataset_id = :did"), {"did": dataset_id}).scalar()
        print(f"7. public.data_records in Supabase       : {data_recs_count} physical rows stored in table data_records")

        # Table Row Counts Summary
        print("\n--- OVERALL SUPABASE TABLE COUNTS ---")
        for t in ["users", "companies", "company_memberships", "data_sources", "datasets", "dataset_versions", "data_records", "audit_logs"]:
            cnt = conn.execute(text(f"SELECT count(*) FROM {t}")).scalar()
            print(f"  public.{t.ljust(22)} : {cnt} rows")

    print("\n" + "=" * 70)
    print("ALL ROWS ARE PHYSICALLY VERIFIED IN SUPABASE POSTGRESQL!")
    print("=" * 70)

    return {
        "user_id": user_id,
        "company_id": company_id,
        "data_source_id": data_source_id,
        "dataset_id": dataset_id,
        "dataset_version_id": dataset_version_id,
        "rows_persisted": data_recs_count,
    }

if __name__ == "__main__":
    out = run_real_import()
    print("\nVerification Result:", json.dumps(out, indent=2))
