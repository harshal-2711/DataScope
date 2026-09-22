"""Comprehensive unit and integration tests for Market-Based Competition Intelligence."""
import io
import unittest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.domain_blueprint import DomainIdentitySchema
from app.services.column_profiler import profile_dataset
from app.services.competition_engine import compute_competition_intelligence


class TestMarketCompetitionIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_customer_login_and_device_types_never_market_competitors(self):
        """Verify internal transaction columns (Customer Login Type, Device Type)
        are strictly rejected and return the clear market-data-unavailable state."""
        df = pd.DataFrame({
            "Customer_Login_type": ["Member"] * 95 + ["Guest"] * 5,
            "Device_Type": ["Web"] * 90 + ["Mobile"] * 10,
            "Sales": [150.0] * 100,
            "Profit": [25.0] * 100,
            "Aging": [12] * 100,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="ecommerce", name="E-Commerce", description="")
        res = compute_competition_intelligence(df, "test_ecom_internal", profiles, domain, dataset_currency="$")

        self.assertFalse(res.is_available)
        self.assertEqual(res.market_data_status, "market_data_absent")
        self.assertEqual(res.status_title, "Market competition analysis is not available yet.")
        self.assertIn("internal transaction data", res.unavailable_reason.lower())
        self.assertGreater(len(res.required_market_fields), 0)
        self.assertGreater(len(res.missing_requirements), 0)
        self.assertGreater(len(res.market_limitations), 0)

    def test_02_market_dataset_with_competitors_detected(self):
        """Verify dataset containing competitor entities is detected and processed."""
        df = pd.DataFrame({
            "competitor_name": ["Apex Market Leader", "Beta Solutions", "Gamma Enterprises", "Delta Corp"],
            "revenue": [5000000.0, 3200000.0, 2100000.0, 1200000.0],
            "profit": [950000.0, 480000.0, 210000.0, 96000.0],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="ecommerce", name="E-Commerce Market", description="")
        res = compute_competition_intelligence(df, "test_competitor_data", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertEqual(res.market_data_status, "market_data_detected")
        self.assertIsNotNone(res.overview)
        self.assertEqual(res.overview.total_competitors_tracked, 4)
        self.assertEqual(res.overview.top_competitor_name, "Apex Market Leader")
        
        # Competitor list checks
        self.assertEqual(len(res.competitors), 4)
        self.assertEqual(res.competitors[0].name, "Apex Market Leader")
        self.assertEqual(res.competitors[0].rank, 1)
        self.assertIsNotNone(res.competitors[0].market_share_pct)
        self.assertIsNotNone(res.competitors[0].profit_margin_pct)
        
        # Gaps & Recommendations
        self.assertGreater(len(res.market_gaps), 0)
        self.assertGreater(len(res.strategic_recommendations), 0)
        
        # Check evidence and limitations on recommendations
        rec = res.strategic_recommendations[0]
        self.assertTrue(bool(rec.evidence))
        self.assertTrue(bool(rec.metric))
        self.assertTrue(bool(rec.comparison))
        self.assertTrue(bool(rec.limitation))
        self.assertTrue(bool(rec.suggested_investigation))

    def test_03_dataset_with_explicit_market_share(self):
        """Verify explicit market share column is preserved accurately."""
        df = pd.DataFrame({
            "company": ["Alpha Inc", "Beta LLC", "Gamma Co"],
            "revenue": [1000000.0, 600000.0, 400000.0],
            "market_share_pct": [50.0, 30.0, 20.0],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="finance", name="Finance Market", description="")
        res = compute_competition_intelligence(df, "test_share", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertEqual(res.competitors[0].market_share_pct, 50.0)
        self.assertEqual(res.competitors[1].market_share_pct, 30.0)
        self.assertEqual(res.competitors[2].market_share_pct, 20.0)

    def test_04_empty_dataset_returns_insufficient_data(self):
        """Verify empty dataframe returns structured insufficient data status."""
        df = pd.DataFrame()
        profiles = []
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_competition_intelligence(df, "test_empty", profiles, domain)

        self.assertFalse(res.is_available)
        self.assertEqual(res.market_data_status, "insufficient_data")
        self.assertEqual(res.status_title, "Market competition analysis is not available yet.")

    def test_05_single_competitor_returns_insufficient_data(self):
        """Verify dataset with only 1 competitor entity cannot perform comparison."""
        df = pd.DataFrame({
            "competitor_name": ["Monopoly Corp", "Monopoly Corp"],
            "revenue": [1000.0, 2000.0],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_competition_intelligence(df, "test_single", profiles, domain)

        self.assertFalse(res.is_available)
        self.assertEqual(res.market_data_status, "insufficient_data")

    def test_06_live_http_api_competition_endpoint(self):
        """Verify live API upload and competition endpoint."""
        # 1. Upload market dataset
        csv_bytes = (
            "competitor,revenue,profit\n"
            "Competitor A,50000,10000\n"
            "Competitor B,35000,7000\n"
            "Competitor C,20000,3000\n"
        ).encode("utf-8")

        upload_res = self.client.post(
            "/api/dataset/upload",
            files={"file": ("market_benchmarks.csv", io.BytesIO(csv_bytes), "text/csv")}
        )
        self.assertEqual(upload_res.status_code, 200)
        did = upload_res.json()["dataset_id"]

        comp_res = self.client.get(f"/api/dataset/{did}/competition")
        self.assertEqual(comp_res.status_code, 200)
        data = comp_res.json()

        self.assertEqual(data["dataset_id"], did)
        self.assertTrue(data["is_available"])
        self.assertEqual(data["market_data_status"], "market_data_detected")
        self.assertEqual(data["overview"]["top_competitor_name"], "Competitor A")
        self.assertEqual(len(data["competitors"]), 3)

        # 2. Upload internal transactional data (e.g. login & device)
        ecom_csv_bytes = (
            "Customer_Login_type,Device_Type,Sales,Profit\n"
            "Member,Web,100,20\n"
            "Member,Web,150,30\n"
            "Guest,Mobile,80,10\n"
        ).encode("utf-8")

        ecom_upload = self.client.post(
            "/api/dataset/upload",
            files={"file": ("internal_sales.csv", io.BytesIO(ecom_csv_bytes), "text/csv")}
        )
        self.assertEqual(ecom_upload.status_code, 200)
        ecom_did = ecom_upload.json()["dataset_id"]

        ecom_comp = self.client.get(f"/api/dataset/{ecom_did}/competition")
        # 3. Test Market Benchmark Workflow on internal sales dataset
        # 3a. Benchmark Preview with JSON format
        benchmark_json = (
            '[\n'
            '  {"company": "Market Leader Alpha", "revenue": 12000000, "profit": 3100000, "market_share_pct": 42.5},\n'
            '  {"company": "Competitor Beta", "revenue": 8500000, "profit": 1900000, "market_share_pct": 30.1},\n'
            '  {"company": "Competitor Gamma", "revenue": 4800000, "profit": 750000, "market_share_pct": 17.0}\n'
            ']'
        ).encode("utf-8")

        prev_res = self.client.post(
            f"/api/dataset/{ecom_did}/benchmark/preview",
            files={"file": ("market_peers.json", io.BytesIO(benchmark_json), "application/json")}
        )
        self.assertEqual(prev_res.status_code, 200)
        prev_data = prev_res.json()
        self.assertTrue(prev_data["is_valid"])
        self.assertEqual(prev_data["company_count"], 3)
        self.assertIn("Market Leader Alpha", prev_data["companies_sample"])
        self.assertEqual(len(prev_data["missing_required_fields"]), 0)

        # 3b. Benchmark Preview with invalid/missing columns
        bad_csv = "product_name,category,rating\nItem 1,Tech,4.5\nItem 2,Home,3.8\n".encode("utf-8")
        bad_prev = self.client.post(
            f"/api/dataset/{ecom_did}/benchmark/preview",
            files={"file": ("invalid_benchmark.csv", io.BytesIO(bad_csv), "text/csv")}
        )
        self.assertEqual(bad_prev.status_code, 200)
        self.assertFalse(bad_prev.json()["is_valid"])
        self.assertGreater(len(bad_prev.json()["missing_required_fields"]), 0)

        # 3c. Benchmark Apply
        apply_res = self.client.post(
            f"/api/dataset/{ecom_did}/benchmark/apply",
            files={"file": ("market_peers.json", io.BytesIO(benchmark_json), "application/json")}
        )
        self.assertEqual(apply_res.status_code, 200)
        apply_data = apply_res.json()
        self.assertTrue(apply_data["is_available"])
        self.assertEqual(apply_data["market_data_status"], "market_data_detected")
        self.assertTrue(apply_data["has_external_benchmark"])
        self.assertEqual(apply_data["benchmark_filename"], "market_peers.json")
        self.assertEqual(apply_data["overview"]["top_competitor_name"], "Market Leader Alpha")

        # 3d. Delete Benchmark restores internal state
        del_res = self.client.delete(f"/api/dataset/{ecom_did}/benchmark")
        self.assertEqual(del_res.status_code, 200)
        del_data = del_res.json()
        self.assertFalse(del_data["is_available"])
        self.assertEqual(del_data["market_data_status"], "market_data_absent")
        self.assertFalse(del_data["has_external_benchmark"])


if __name__ == "__main__":
    unittest.main()


