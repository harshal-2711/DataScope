import os
import sys
from pathlib import Path

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import uuid
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.models.company import Company
from app.models.membership import CompanyMembership
from app.models.data_source import DataSource
from app.models.dataset import Dataset
from app.models.data_record import DataRecord
from app.services import dataset_store

client = TestClient(app)


def setup_test_user_and_company(email_prefix: str, company_name: str):
    """Create an isolated test user and tenant company in the DB and return credentials."""
    db = SessionLocal()
    try:
        user_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())
        email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@datascope-test.io"

        user = User(
            id=user_id,
            email=email,
            full_name=f"Test User {email_prefix.upper()}",
            is_active=True,
            is_verified=True,
        )
        db.add(user)

        company = Company(
            id=company_id,
            name=company_name,
            slug=f"co-{uuid.uuid4().hex[:8]}",
            owner_id=user_id,
            domain_type="E-Commerce & Retail",
        )
        db.add(company)

        membership = CompanyMembership(
            id=str(uuid.uuid4()),
            company_id=company_id,
            user_id=user_id,
            role="owner",
            status="active",
        )
        db.add(membership)
        db.commit()

        token = create_access_token(data={"sub": user_id, "email": email, "company_id": company_id})
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Company-Id": company_id,
        }
        return {
            "user_id": user_id,
            "company_id": company_id,
            "email": email,
            "token": token,
            "headers": headers,
        }
    finally:
        db.close()


def test_multi_user_tenant_isolation_and_persistence():
    """Verify that User A and User B data are strictly isolated and persisted to DB."""
    # 1. Setup User A (Company Alpha) and User B (Company Beta)
    user_a = setup_test_user_and_company("user_a", "Company Alpha Workspace")
    user_b = setup_test_user_and_company("user_b", "Company Beta Workspace")

    print(f"User A: {user_a['email']} (Company: {user_a['company_id']})")
    print(f"User B: {user_b['email']} (Company: {user_b['company_id']})")

    # 2. User A imports Google Sheets dataset
    sheet_data = [
        {"Product": "Alpha Widget", "Category": "Hardware", "Revenue": 5000, "Date": "2026-01-01"},
        {"Product": "Alpha Gadget", "Category": "Electronics", "Revenue": 8500, "Date": "2026-01-02"},
        {"Product": "Alpha Pro", "Category": "Hardware", "Revenue": 12000, "Date": "2026-01-03"},
    ]
    import_payload_a = {
        "connection_name": "Alpha Q1 Performance Sheet",
        "source_type": "google_sheets",
        "config": {
            "sheet_url": "https://docs.google.com/spreadsheets/d/1_ALPHA_TEST_SHEET_KEY/edit",
            "sheet_name": "Sheet1",
            "records": sheet_data,
        },
    }

    res_a = client.post("/api/data-sources/import", json=import_payload_a, headers=user_a["headers"])
    assert res_a.status_code == 200, f"User A import failed: {res_a.text}"
    data_a = res_a.json()
    dataset_a_id = data_a["dataset_id"]
    print(f"User A successfully imported Dataset A: {dataset_a_id}")

    # 3. User B imports CSV dataset
    csv_data = [
        {"Service": "Beta Consulting", "Department": "Advisory", "Billed": 20000, "Month": "2026-02"},
        {"Service": "Beta Audit", "Department": "Compliance", "Billed": 15000, "Month": "2026-02"},
    ]
    import_payload_b = {
        "connection_name": "Beta Services Billing",
        "source_type": "csv",
        "config": {
            "filename": "beta_billing.csv",
            "records": csv_data,
        },
    }

    res_b = client.post("/api/data-sources/import", json=import_payload_b, headers=user_b["headers"])
    assert res_b.status_code == 200, f"User B import failed: {res_b.text}"
    data_b = res_b.json()
    dataset_b_id = data_b["dataset_id"]
    print(f"User B successfully imported Dataset B: {dataset_b_id}")

    # 4. Verify Database Persistence (Supabase / SQLAlchemy DB Models)
    db = SessionLocal()
    try:
        # Check Dataset A in DB
        db_ds_a = db.query(Dataset).filter(Dataset.id == dataset_a_id).first()
        assert db_ds_a is not None, "Dataset A record missing from database"
        assert db_ds_a.company_id == user_a["company_id"], "Dataset A company_id mismatch"

        # Check DataSource A in DB
        db_source_a = db.query(DataSource).filter(DataSource.dataset_id == dataset_a_id).first()
        assert db_source_a is not None, "DataSource A record missing from database"
        assert db_source_a.company_id == user_a["company_id"]
        assert db_source_a.source_type == "google_sheets"
        source_a_id = db_source_a.id

        # Check DataRecord A rows in DB
        records_a = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_a_id).all()
        assert len(records_a) == 3, f"Expected 3 records in DB for Dataset A, got {len(records_a)}"

        # Check Dataset B in DB
        db_ds_b = db.query(Dataset).filter(Dataset.id == dataset_b_id).first()
        assert db_ds_b is not None, "Dataset B record missing from database"
        assert db_ds_b.company_id == user_b["company_id"], "Dataset B company_id mismatch"

        # Check DataSource B in DB
        db_source_b = db.query(DataSource).filter(DataSource.dataset_id == dataset_b_id).first()
        assert db_source_b is not None, "DataSource B record missing from database"
        assert db_source_b.company_id == user_b["company_id"]
        source_b_id = db_source_b.id

        # Check DataRecord B rows in DB
        records_b = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_b_id).all()
        assert len(records_b) == 2, f"Expected 2 records in DB for Dataset B, got {len(records_b)}"

        print("[PASS] Confirmed physical database records for both tenants (DataSources, Datasets, DataRecords).")
    finally:
        db.close()

    # 5. Verify User A cannot see or access User B's datasets or data sources
    # List datasets for User A
    res_list_a = client.get("/api/data-management/datasets", headers=user_a["headers"])
    assert res_list_a.status_code == 200
    dataset_ids_a = [d["id"] for d in res_list_a.json()]
    assert dataset_a_id in dataset_ids_a, "Dataset A should be in User A's dataset list"
    assert dataset_b_id not in dataset_ids_a, "SECURITY VIOLATION: Dataset B visible in User A's dataset list"

    # List sources for User A
    res_sources_a = client.get("/api/data-sources", headers=user_a["headers"])
    assert res_sources_a.status_code == 200
    source_ids_a = [s["id"] for s in res_sources_a.json()]
    assert source_a_id in source_ids_a, "Source A should be in User A's source list"
    assert source_b_id not in source_ids_a, "SECURITY VIOLATION: Source B visible in User A's source list"

    # List datasets for User B
    res_list_b = client.get("/api/data-management/datasets", headers=user_b["headers"])
    assert res_list_b.status_code == 200
    dataset_ids_b = [d["id"] for d in res_list_b.json()]
    assert dataset_b_id in dataset_ids_b, "Dataset B should be in User B's dataset list"
    assert dataset_a_id not in dataset_ids_b, "SECURITY VIOLATION: Dataset A visible in User B's dataset list"

    # 6. ID Tampering Protection: User A directly requests Dataset B's ID
    res_tamper_records = client.get(f"/api/data-management/datasets/{dataset_b_id}/records", headers=user_a["headers"])
    assert res_tamper_records.status_code in (403, 404), f"Expected 404/403 for tampered records request, got {res_tamper_records.status_code}"

    res_tamper_recs = client.get(f"/api/dataset/{dataset_b_id}/recommendations", headers=user_a["headers"])
    assert res_tamper_recs.status_code in (403, 404), f"Expected 404/403 for tampered recommendations request, got {res_tamper_recs.status_code}"

    res_tamper_risk = client.get(f"/api/dataset/{dataset_b_id}/risk", headers=user_a["headers"])
    assert res_tamper_risk.status_code in (403, 404), f"Expected 404/403 for tampered risk request, got {res_tamper_risk.status_code}"

    print("[PASS] Confirmed cross-tenant isolation and ID tampering protection.")

    # 7. Backend Restart Simulation Test
    # Clear in-memory dataset cache completely
    dataset_store.clear_store()
    assert len(dataset_store._store) == 0, "In-memory dataset cache not cleared"
    print("In-memory store cleared (backend restart simulated).")

    # User A requests active dataset
    res_active = client.get("/api/data-management/active-dataset", headers=user_a["headers"])
    assert res_active.status_code == 200
    active_data = res_active.json()
    assert active_data["active"] is True
    assert active_data["dataset"]["id"] == dataset_a_id

    # User A requests Live Data Editor records after restart
    res_records_after = client.get(f"/api/data-management/datasets/{dataset_a_id}/records", headers=user_a["headers"])
    assert res_records_after.status_code == 200
    records_body = res_records_after.json()
    assert records_body["total_records"] == 3
    assert len(records_body["records"]) == 3
    assert records_body["records"][0]["data"]["Product"] == "Alpha Widget"

    # User A requests all analytics modules after restart
    endpoints_to_test = [
        f"/api/dataset/{dataset_a_id}/recommendations",
        f"/api/dataset/{dataset_a_id}/intelligence",
        f"/api/dataset/{dataset_a_id}/decision_dashboard",
        f"/api/dataset/{dataset_a_id}/trends",
        f"/api/dataset/{dataset_a_id}/forecast",
        f"/api/dataset/{dataset_a_id}/data_quality",
        f"/api/dataset/{dataset_a_id}/risk",
        f"/api/dataset/{dataset_a_id}/competition",
        f"/api/dataset/{dataset_a_id}/report",
    ]
    for endpoint in endpoints_to_test:
        res_module = client.get(endpoint, headers=user_a["headers"])
        assert res_module.status_code == 200, f"Failed module after restart on {endpoint}: {res_module.text}"

    print("[PASS] Confirmed 100% data hydration across all analytics modules after complete backend restart.")


if __name__ == "__main__":
    test_multi_user_tenant_isolation_and_persistence()
    print("ALL TESTS PASSED SUCCESSFULLY!")
