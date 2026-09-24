"""Integration & Unit Tests for Live Data Connectors, Password Reset & Onboarding."""
from __future__ import annotations

import unittest
import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.models.company import Company
from app.models.membership import CompanyMembership
from app.models.data_source import DataSource
from app.models.user import User


class TestLiveConnectorsAndAuthSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_forgot_password_and_reset_flow(self):
        """Test forgot password token generation and password reset verification."""
        # 1. Register a test user
        unique_email = f"reset_test_{uuid.uuid4().hex[:8]}@datascope.io"
        reg_resp = self.client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "initial_password_123",
                "full_name": "Reset Test User",
                "company_name": "Reset Test Corp",
            },
        )
        self.assertEqual(reg_resp.status_code, 201)

        # 2. Forgot password request
        forgot_resp = self.client.post("/api/auth/forgot-password", json={"email": unique_email})
        self.assertEqual(forgot_resp.status_code, 200)
        reset_token = forgot_resp.json().get("reset_token")
        self.assertIsNotNone(reset_token)

        # 3. Reset password with valid token
        reset_resp = self.client.post(
            "/api/auth/reset-password",
            json={"token": reset_token, "new_password": "new_secure_password_456"},
        )
        self.assertEqual(reset_resp.status_code, 200)
        self.assertIn("successfully updated", reset_resp.json()["message"])

        # 4. Login with new password
        login_resp = self.client.post(
            "/api/auth/login",
            json={"email": unique_email, "password": "new_secure_password_456"},
        )
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("access_token", login_resp.json())

    def test_02_company_onboarding_and_settings(self):
        """Test company onboarding update and settings endpoints."""
        unique_email = f"onboard_lead_{uuid.uuid4().hex[:8]}@company.com"
        # Register user and workspace
        reg_resp = self.client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "pass_onboard_123",
                "full_name": "Onboarding Lead",
                "company_name": "Tech Corp Growth",
            },
        )
        self.assertEqual(reg_resp.status_code, 201)
        token = reg_resp.json()["access_token"]
        company_id = reg_resp.json()["active_company_id"]

        headers = {"Authorization": f"Bearer {token}", "X-Company-Id": company_id}

        # Submit onboarding information
        onboard_resp = self.client.post(
            "/api/companies/onboarding",
            json={
                "industry": "E-Commerce & SaaS",
                "company_size": "50-200 Employees",
                "country": "United States",
                "primary_objective": "Revenue optimization & Margin protection",
            },
            headers=headers,
        )
        self.assertEqual(onboard_resp.status_code, 200)
        self.assertEqual(onboard_resp.json()["company"]["industry"], "E-Commerce & SaaS")

        # Verify company details reflect onboarding
        comp_resp = self.client.get(f"/api/companies/{company_id}", headers=headers)
        self.assertEqual(comp_resp.status_code, 200)
        comp_data = comp_resp.json()
        self.assertEqual(comp_data["industry"], "E-Commerce & SaaS")
        self.assertEqual(comp_data["primary_objective"], "Revenue optimization & Margin protection")

    def test_03_data_source_lifecycle_and_test_connection(self):
        """Test data source creation, connection testing, sync execution and job history."""
        unique_email = f"pipeline_analyst_{uuid.uuid4().hex[:8]}@datascope.io"
        # Register user
        reg_resp = self.client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "pipeline_pass_123",
                "full_name": "Pipeline Analyst",
                "company_name": "Pipeline Analytics Inc",
            },
        )
        self.assertEqual(reg_resp.status_code, 201)
        token = reg_resp.json()["access_token"]
        company_id = reg_resp.json()["active_company_id"]

        headers = {"Authorization": f"Bearer {token}", "X-Company-Id": company_id}

        # 1. Test connection endpoint (file_upload / manual_entry)
        test_resp = self.client.post(
            "/api/data-sources/test",
            json={"source_type": "manual_entry", "config": {}},
            headers=headers,
        )
        self.assertEqual(test_resp.status_code, 200)
        self.assertTrue(test_resp.json()["success"])

        # 2. Create a data source with sample mock records
        create_resp = self.client.post(
            "/api/data-sources",
            json={
                "name": "Live POS Feed",
                "source_type": "rest_api",
                "sync_frequency": "hourly",
                "config": {
                    "url": "https://httpbin.org/json",
                    "mock_data": [
                        {"Date": "2025-01-01", "Revenue": 10000, "Profit": 3000, "Category": "Hardware"},
                        {"Date": "2025-01-02", "Revenue": 15000, "Profit": 4500, "Category": "Software"},
                        {"Date": "2025-01-03", "Revenue": 12000, "Profit": 3200, "Category": "Hardware"},
                    ]
                }
            },
            headers=headers,
        )
        self.assertEqual(create_resp.status_code, 201)
        source_id = create_resp.json()["id"]

        # 3. List data sources
        list_resp = self.client.get("/api/data-sources", headers=headers)
        self.assertEqual(list_resp.status_code, 200)
        self.assertTrue(len(list_resp.json()) >= 1)

        # 4. Trigger manual synchronization
        sync_resp = self.client.post(f"/api/data-sources/{source_id}/sync", headers=headers)
        self.assertEqual(sync_resp.status_code, 200)
        self.assertEqual(sync_resp.json()["status"], "success")
        self.assertEqual(sync_resp.json()["records_synced"], 3)
        dataset_id = sync_resp.json()["dataset_id"]

        # 5. Check sync job history
        jobs_resp = self.client.get(f"/api/data-sources/{source_id}/jobs", headers=headers)
        self.assertEqual(jobs_resp.status_code, 200)
        self.assertTrue(len(jobs_resp.json()) >= 1)
        self.assertEqual(jobs_resp.json()[0]["status"], "success")

        # 6. Pause and resume data source
        pause_resp = self.client.post(f"/api/data-sources/{source_id}/pause", headers=headers)
        self.assertEqual(pause_resp.status_code, 200)
        self.assertTrue(pause_resp.json()["is_paused"])

        resume_resp = self.client.post(f"/api/data-sources/{source_id}/resume", headers=headers)
        self.assertEqual(resume_resp.status_code, 200)
        self.assertFalse(resume_resp.json()["is_paused"])


if __name__ == "__main__":
    unittest.main()
