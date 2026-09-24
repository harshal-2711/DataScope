"""Complete Connected Data (Google Sheets -> Active Dataset -> All Modules) End-to-End Test."""
import unittest
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.services import dataset_store

class TestConnectedDataFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        
        # 1. Register test user
        cls.email = f"tester_{uuid.uuid4().hex[:8]}@datascope.io"
        reg = cls.client.post("/api/auth/register", json={
            "email": cls.email,
            "password": "Password123!",
            "full_name": "Connected Tester",
            "company_name": "Connected Corp"
        })
        assert reg.status_code == 201, f"Registration failed: {reg.text}"
        cls.token = reg.json()["access_token"]
        cls.company_id = reg.json()["active_company_id"]
        cls.headers = {"Authorization": f"Bearer {cls.token}", "X-Company-Id": cls.company_id}

    def test_01_google_sheets_import_to_active_dataset(self):
        """Test importing Google Sheet and verifying all downstream analytics and data-management modules."""
        # 1. Import Google Sheet
        sheet_url = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
        import_resp = self.client.post("/api/data-sources/import", json={
            "source_type": "google_sheets",
            "config": {"sheet_url": sheet_url},
            "connection_name": "Class Roster"
        }, headers=self.headers)
        
        self.assertEqual(import_resp.status_code, 200, f"Import failed: {import_resp.text}")
        data = import_resp.json()
        dataset_id = data.get("dataset_id")
        self.assertIsNotNone(dataset_id)
        self.assertGreater(data.get("row_count", 0), 0)
        self.assertGreater(data.get("column_count", 0), 0)
        print(f"Successfully imported dataset_id={dataset_id}, rows={data['row_count']}, cols={data['column_count']}")

        # 2. Test Live Data Editor Records endpoint
        rec_resp = self.client.get(f"/api/data-management/datasets/{dataset_id}/records?page=1&page_size=25", headers=self.headers)
        self.assertEqual(rec_resp.status_code, 200, f"Records endpoint failed: {rec_resp.text}")
        rec_data = rec_resp.json()
        self.assertGreater(rec_data["total_records"], 0)
        self.assertGreater(len(rec_data["columns"]), 0)
        self.assertGreater(len(rec_data["records"]), 0)
        print(f"Live Data Editor returned {rec_data['total_records']} records, {len(rec_data['columns'])} columns.")

        # 3. Test Recommendations / Explore
        rec_resp = self.client.get(f"/api/dataset/{dataset_id}/recommendations")
        self.assertEqual(rec_resp.status_code, 200, f"Recommendations failed: {rec_resp.text}")
        rec_body = rec_resp.json()
        self.assertIn("charts", rec_body)
        print(f"Recommendations returned {len(rec_body.get('charts', []))} charts.")

        # 4. Test Intelligence
        intel_resp = self.client.get(f"/api/dataset/{dataset_id}/intelligence")
        self.assertEqual(intel_resp.status_code, 200, f"Intelligence failed: {intel_resp.text}")
        
        # 5. Test Statistics
        stats_resp = self.client.get(f"/api/dataset/{dataset_id}/statistics")
        self.assertEqual(stats_resp.status_code, 200, f"Statistics failed: {stats_resp.text}")

        # 6. Test Trends
        trends_resp = self.client.get(f"/api/dataset/{dataset_id}/trends")
        self.assertEqual(trends_resp.status_code, 200, f"Trends failed: {trends_resp.text}")

        # 7. Test Forecast
        fc_resp = self.client.get(f"/api/dataset/{dataset_id}/forecast")
        self.assertEqual(fc_resp.status_code, 200, f"Forecast failed: {fc_resp.text}")

        # 8. Test Risks
        risk_resp = self.client.get(f"/api/dataset/{dataset_id}/risk")
        self.assertEqual(risk_resp.status_code, 200, f"Risks failed: {risk_resp.text}")

        # 9. Test Competition
        comp_resp = self.client.get(f"/api/dataset/{dataset_id}/competition")
        self.assertEqual(comp_resp.status_code, 200, f"Competition failed: {comp_resp.text}")

        # 10. Test Recommendations Intelligence
        rec_intel_resp = self.client.get(f"/api/dataset/{dataset_id}/recommendations_intelligence")
        self.assertEqual(rec_intel_resp.status_code, 200, f"Recommendations Intel failed: {rec_intel_resp.text}")

        # 11. Test Decision Dashboard
        dec_resp = self.client.get(f"/api/dataset/{dataset_id}/decision_dashboard")
        self.assertEqual(dec_resp.status_code, 200, f"Decisions failed: {dec_resp.text}")

        # 12. Test Data Quality
        dq_resp = self.client.get(f"/api/dataset/{dataset_id}/data_quality")
        self.assertEqual(dq_resp.status_code, 200, f"Data Quality failed: {dq_resp.text}")

        # 13. Test Comprehensive Report JSON
        rep_resp = self.client.get(f"/api/dataset/{dataset_id}/report")
        self.assertEqual(rep_resp.status_code, 200, f"Report JSON failed: {rep_resp.text}")

        # 14. Test Reports Export (PDF and DOCX)
        pdf_resp = self.client.get(f"/api/dataset/{dataset_id}/report/pdf")
        self.assertEqual(pdf_resp.status_code, 200, f"PDF Export failed: {pdf_resp.text}")

        docx_resp = self.client.get(f"/api/dataset/{dataset_id}/report/docx")
        self.assertEqual(docx_resp.status_code, 200, f"DOCX Export failed: {docx_resp.text}")

        print("ALL 14 backend endpoints successfully verified with Google Sheet dataset!")

    def test_02_csv_upload_regression_flow(self):
        """Test standard CSV file upload to ensure backward compatibility and no regression."""
        import io
        csv_content = b"Date,Product,Category,Revenue,Units_Sold\n2025-01-01,Widget A,Hardware,1500,30\n2025-01-02,Widget B,Hardware,2200,45\n2025-01-03,Service C,Software,4500,10\n2025-01-04,Widget A,Hardware,1800,35\n2025-01-05,Service C,Software,5000,12\n"
        
        files = {"file": ("sales_sample.csv", io.BytesIO(csv_content), "text/csv")}
        upload_resp = self.client.post("/api/dataset/upload", files=files)
        self.assertEqual(upload_resp.status_code, 200, f"CSV Upload failed: {upload_resp.text}")
        
        data = upload_resp.json()
        csv_dataset_id = data["dataset_id"]
        self.assertEqual(data["row_count"], 5)
        self.assertEqual(data["column_count"], 5)

        # Explore / Recommendations
        rec_resp = self.client.get(f"/api/dataset/{csv_dataset_id}/recommendations")
        self.assertEqual(rec_resp.status_code, 200)

        # Trends
        trends_resp = self.client.get(f"/api/dataset/{csv_dataset_id}/trends")
        self.assertEqual(trends_resp.status_code, 200)

        # Reports
        rep_resp = self.client.get(f"/api/dataset/{csv_dataset_id}/report")
        self.assertEqual(rep_resp.status_code, 200)
        print("CSV upload regression test passed successfully!")

if __name__ == "__main__":
    unittest.main()
