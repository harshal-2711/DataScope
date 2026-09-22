"""Comprehensive unit and integration tests for universal domain-aware Competition Intelligence."""
import io
import unittest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.domain_blueprint import DomainIdentitySchema
from app.services.column_profiler import profile_dataset
from app.services.competition_engine import compute_competition_intelligence


class TestCompetitionIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_customer_login_type_and_device_type_strictly_rejected(self):
        """Verify Customer Login Type and Device Type are NEVER used as competitive entities,
        triggering the clear competition unavailable state."""
        df = pd.DataFrame({
            "Customer_Login_type": ["Member"] * 95 + ["Guest"] * 5,
            "Device_Type": ["Web"] * 90 + ["Mobile"] * 10,
            "Sales": [100.0] * 100,
            "Profit": [20.0] * 100,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="ecommerce", name="E-Commerce", description="")
        res = compute_competition_intelligence(df, "test_ecom_login", profiles, domain)

        self.assertFalse(res.is_available)
        self.assertEqual(res.competition_mode, "unavailable")
        self.assertIn("unavailable", res.unavailable_reason.lower())
        self.assertIn("verified company, brand or competitor", res.summary_statement.lower())
        self.assertGreater(len(res.missing_requirements), 0)
        self.assertGreater(len(res.required_data_guide), 0)

    def test_02_brand_column_accepted_for_benchmarking(self):
        """Verify dataset with a valid Brand column triggers Dataset-Based Benchmarking."""
        df = pd.DataFrame({
            "brand_name": ["Apple", "Samsung", "Sony", "Dell", "Lenovo"],
            "category": ["Electronics"] * 5,
            "revenue": [50000.0, 42000.0, 28000.0, 22000.0, 18000.0],
            "profit": [12000.0, 8500.0, 4200.0, 3100.0, 2400.0],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="ecommerce", name="E-Commerce", description="")
        res = compute_competition_intelligence(df, "test_brands", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertEqual(res.competition_mode, "internal_benchmarking")
        self.assertEqual(res.entity_type, "Brand")
        self.assertEqual(res.overview.comparison_dimension, "brand_name")
        self.assertEqual(res.overview.top_segment_name, "Apple")
        self.assertEqual(res.overview.bottom_segment_name, "Lenovo")
        self.assertIn("$", res.overview.top_segment_formatted)
        self.assertGreater(len(res.areas_of_strength), 0)
        self.assertGreater(len(res.areas_for_improvement), 0)

    def test_03_company_column_accepted_for_benchmarking(self):
        """Verify dataset with a valid Company column triggers company-level benchmarking."""
        df = pd.DataFrame({
            "company": ["Apex Corp", "Beta LLC", "Gamma Inc", "Delta Global"],
            "revenue": [500000.0, 320000.0, 210000.0, 150000.0],
            "net_profit": [120000.0, 80000.0, 35000.0, 15000.0],
            "operating_expense": [380000.0, 240000.0, 175000.0, 135000.0],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="finance", name="Finance", description="")
        res = compute_competition_intelligence(df, "test_fin", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertEqual(res.competition_mode, "internal_benchmarking")
        self.assertEqual(res.entity_type, "Company")
        self.assertEqual(res.overview.comparison_dimension, "company")
        self.assertEqual(res.overview.top_segment_name, "Apex Corp")
        self.assertEqual(res.overview.bottom_segment_name, "Delta Global")

    def test_04_device_type_only_dataset_rejected(self):
        """Verify dataset with only Device Type and metrics is rejected from competition."""
        df = pd.DataFrame({
            "device_type": ["Mobile", "Desktop", "Tablet"],
            "views": [50000, 35000, 15000],
            "clicks": [2500, 1800, 600],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_competition_intelligence(df, "test_device_only", profiles, domain)

        self.assertFalse(res.is_available)
        self.assertEqual(res.competition_mode, "unavailable")

    def test_05_sports_team_benchmarking(self):
        """Verify sports team rankings by points/runs."""
        df = pd.DataFrame({
            "team": ["Arsenal", "Man City", "Liverpool", "Aston Villa", "Tottenham"],
            "points": [75, 73, 70, 59, 53],
            "goals": [68, 71, 65, 52, 49],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="sports", name="Sports", description="")
        res = compute_competition_intelligence(df, "test_sports", profiles, domain)

        self.assertTrue(res.is_available)
        self.assertEqual(res.competition_mode, "internal_benchmarking")
        self.assertEqual(res.entity_type, "Team")
        self.assertEqual(res.overview.top_segment_name, "Arsenal")
        self.assertEqual(res.overview.bottom_segment_name, "Tottenham")

    def test_06_procurement_supplier_benchmarking(self):
        """Verify procurement supplier spend benchmarking."""
        df = pd.DataFrame({
            "supplier": ["Supplier Alpha", "Supplier Beta", "Supplier Gamma", "Supplier Delta"],
            "tender_value": [2500000.0, 1400000.0, 950000.0, 420000.0],
            "duration_in_days": [45, 30, 60, 20],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="procurement", name="Procurement", description="")
        res = compute_competition_intelligence(df, "test_proc", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertEqual(res.competition_mode, "internal_benchmarking")
        self.assertEqual(res.entity_type, "Supplier")
        self.assertEqual(res.overview.top_segment_name, "Supplier Alpha")

    def test_07_api_route_integration(self):
        """Verify live HTTP API GET /api/dataset/{dataset_id}/competition integration."""
        csv_bytes = (
            "brand_name,sales,profit\n"
            "Brand A,10000,2500\n"
            "Brand B,8000,1800\n"
            "Brand C,5000,900\n"
        ).encode("utf-8")

        upload_res = self.client.post(
            "/api/dataset/upload",
            files={"file": ("brands_table.csv", io.BytesIO(csv_bytes), "text/csv")}
        )
        self.assertEqual(upload_res.status_code, 200)
        did = upload_res.json()["dataset_id"]

        comp_res = self.client.get(f"/api/dataset/{did}/competition")
        self.assertEqual(comp_res.status_code, 200)
        data = comp_res.json()

        self.assertEqual(data["dataset_id"], did)
        self.assertTrue(data["is_available"])
        self.assertEqual(data["competition_mode"], "internal_benchmarking")
        self.assertEqual(data["entity_type"], "Brand")
        self.assertEqual(data["overview"]["top_segment_name"], "Brand A")

        # Invalid ID returns application 404
        bad_res = self.client.get("/api/dataset/fake_dataset_id_9999/competition")
        self.assertEqual(bad_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
