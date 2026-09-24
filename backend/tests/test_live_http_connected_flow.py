"""Live HTTP socket test for running servers (127.0.0.1:8000)."""
import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_live_test():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Health check
        health = client.get("/api/health")
        print(f"[1] Health Check: {health.status_code}")
        assert health.status_code == 200

        # 2. Register new company & user
        unique_id = uuid.uuid4().hex[:8]
        reg_resp = client.post("/api/auth/register", json={
            "email": f"live_tester_{unique_id}@datascope.io",
            "password": "Password123!",
            "full_name": "Live Connected Tester",
            "company_name": f"Live Corp {unique_id}"
        })
        print(f"[2] Register: {reg_resp.status_code}")
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        company_id = reg_resp.json()["active_company_id"]
        headers = {"Authorization": f"Bearer {token}", "X-Company-Id": company_id}

        # 3. Test Connection with Google Sheets
        sheet_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
        test_conn_resp = client.post("/api/data-sources/test", json={
            "source_type": "google_sheets",
            "config": {"sheet_url": sheet_url}
        }, headers=headers)
        print(f"[3] Test Connection: {test_conn_resp.status_code}, success={test_conn_resp.json().get('success')}")
        assert test_conn_resp.status_code == 200
        assert test_conn_resp.json()["success"] is True

        # 4. Preview Data
        preview_resp = client.post("/api/data-sources/preview", json={
            "source_type": "google_sheets",
            "config": {"sheet_url": sheet_url},
            "limit": 10
        }, headers=headers)
        print(f"[4] Preview Data: {preview_resp.status_code}, sample_rows={preview_resp.json().get('row_count_sample')}")
        assert preview_resp.status_code == 200
        assert preview_resp.json()["success"] is True
        assert len(preview_resp.json()["preview"]) > 0

        # 5. Import to Dataset (Analyze in DataScope)
        import_resp = client.post("/api/data-sources/import", json={
            "source_type": "google_sheets",
            "config": {"sheet_url": sheet_url},
            "connection_name": "Live Student Records"
        }, headers=headers)
        print(f"[5] Import to Dataset: {import_resp.status_code}")
        assert import_resp.status_code == 200
        import_data = import_resp.json()
        dataset_id = import_data["dataset_id"]
        print(f"    Dataset ID: {dataset_id}")
        print(f"    Row Count: {import_data['row_count']}, Column Count: {import_data['column_count']}")
        print(f"    Columns: {import_data['columns']}")

        # 6. Live Data Editor records
        records_resp = client.get(f"/api/data-management/datasets/{dataset_id}/records?page=1&page_size=25", headers=headers)
        print(f"[6] Live Data Editor Records: {records_resp.status_code}, total={records_resp.json().get('total_records')}")
        assert records_resp.status_code == 200
        assert records_resp.json()["total_records"] > 0
        assert len(records_resp.json()["records"]) > 0

        # 7. Explore & Recommendations
        rec_resp = client.get(f"/api/dataset/{dataset_id}/recommendations", headers=headers)
        print(f"[7] Recommendations: {rec_resp.status_code}, charts={len(rec_resp.json().get('charts', []))}")
        assert rec_resp.status_code == 200
        assert len(rec_resp.json()["charts"]) > 0

        # 8. Trends Intelligence
        trends_resp = client.get(f"/api/dataset/{dataset_id}/trends", headers=headers)
        print(f"[8] Trends: {trends_resp.status_code}")
        assert trends_resp.status_code == 200

        # 9. Forecast Intelligence
        fc_resp = client.get(f"/api/dataset/{dataset_id}/forecast", headers=headers)
        print(f"[9] Forecast: {fc_resp.status_code}")
        assert fc_resp.status_code == 200

        # 10. Risk Intelligence
        risk_resp = client.get(f"/api/dataset/{dataset_id}/risk", headers=headers)
        print(f"[10] Risks: {risk_resp.status_code}")
        assert risk_resp.status_code == 200

        # 11. Competition Intelligence
        comp_resp = client.get(f"/api/dataset/{dataset_id}/competition", headers=headers)
        print(f"[11] Competition: {comp_resp.status_code}")
        assert comp_resp.status_code == 200

        # 12. Recommendations Intelligence
        rec_intel_resp = client.get(f"/api/dataset/{dataset_id}/recommendations_intelligence", headers=headers)
        print(f"[12] Recommendations Intelligence: {rec_intel_resp.status_code}")
        assert rec_intel_resp.status_code == 200

        # 13. Decision Dashboard
        dec_resp = client.get(f"/api/dataset/{dataset_id}/decision_dashboard", headers=headers)
        print(f"[13] Decision Dashboard: {dec_resp.status_code}")
        assert dec_resp.status_code == 200

        # 14. Data Quality
        dq_resp = client.get(f"/api/dataset/{dataset_id}/data_quality", headers=headers)
        print(f"[14] Data Quality: {dq_resp.status_code}")
        assert dq_resp.status_code == 200

        # 15. Reports (JSON, PDF, DOCX)
        rep_resp = client.get(f"/api/dataset/{dataset_id}/report", headers=headers)
        print(f"[15a] Report JSON: {rep_resp.status_code}")
        assert rep_resp.status_code == 200

        pdf_resp = client.get(f"/api/dataset/{dataset_id}/report/pdf", headers=headers)
        print(f"[15b] PDF Export: {pdf_resp.status_code}, content_length={len(pdf_resp.content)}")
        assert pdf_resp.status_code == 200
        assert len(pdf_resp.content) > 0

        docx_resp = client.get(f"/api/dataset/{dataset_id}/report/docx", headers=headers)
        print(f"[15c] DOCX Export: {docx_resp.status_code}, content_length={len(docx_resp.content)}")
        assert docx_resp.status_code == 200
        assert len(docx_resp.content) > 0

        print("\n=======================================================")
        print("ALL 15 LIVE HTTP SOCKET ENDPOINTS VERIFIED SUCCESSFULLY!")
        print("=======================================================")

if __name__ == "__main__":
    run_live_test()
