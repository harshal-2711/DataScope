"""Comprehensive unit and integration tests for Evidence-Based Recommendations Intelligence."""
import io
import unittest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.domain_blueprint import DomainIdentitySchema
from app.services.column_profiler import profile_dataset
from app.services.recommendations_intelligence_engine import compute_recommendations_intelligence


class TestRecommendationsIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_ecommerce_recommendations(self):
        """Test E-Commerce dataset generating low margin, high discount, and category findings."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        df = pd.DataFrame({
            "order_date": dates,
            "product_name": ["Product A"] * 30 + ["Product B"] * 30 + ["Product C"] * 40,
            "category": ["Electronics"] * 50 + ["Clothing"] * 50,
            "sales": [100.0] * 30 + [500.0] * 30 + [200.0] * 40,
            "profit": [-10.0] * 30 + [150.0] * 30 + [40.0] * 40,
            "discount": [0.35] * 30 + [0.05] * 30 + [0.10] * 40,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="ecommerce", name="E-Commerce", description="")
        res = compute_recommendations_intelligence(df, "ecom_test", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertGreater(res.overview.total_recommendations, 0)
        self.assertGreater(res.overview.evidence_backed_count, 0)

        # Verify structured attributes on all recommendations
        for rec in res.recommendations:
            self.assertTrue(rec.business_problem)
            self.assertTrue(rec.why_it_matters)
            self.assertTrue(rec.evidence)
            self.assertTrue(rec.root_cause_signal)
            self.assertTrue(rec.recommended_action)
            self.assertTrue(rec.expected_objective)
            self.assertTrue(rec.limitations)
            self.assertIn(rec.priority, ["high", "medium", "low"])
            self.assertTrue(rec.priority_reason)

    def test_02_finance_recommendations(self):
        """Test Finance dataset with declining revenue trend and high cost concentration."""
        dates = pd.date_range("2024-01-01", periods=60, freq="D")
        revenue = [1000.0 - i * 8.0 for i in range(60)]
        costs = [500.0 + i * 4.0 for i in range(60)]
        df = pd.DataFrame({
            "date": dates,
            "revenue": revenue,
            "operational_cost": costs,
            "net_income": [r - c for r, c in zip(revenue, costs)],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="finance", name="Finance & Banking", description="")
        res = compute_recommendations_intelligence(df, "fin_test", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertGreater(res.overview.total_recommendations, 0)
        # Should detect margin/cost or trend issues
        rec_titles = [r.title.lower() for r in res.recommendations]
        self.assertTrue(any("margin" in t or "revenue" in t or "cost" in t or "trend" in t for t in rec_titles))

    def test_03_procurement_recommendations(self):
        """Test Procurement dataset with supplier pricing/delay variance."""
        df = pd.DataFrame({
            "supplier": ["Supplier Alpha"] * 40 + ["Supplier Beta"] * 40 + ["Supplier Gamma"] * 20,
            "item_name": ["Widget X"] * 50 + ["Widget Y"] * 50,
            "unit_price": [120.0] * 40 + [85.0] * 40 + [90.0] * 20,
            "delivery_delay_days": [14] * 40 + [2] * 40 + [3] * 20,
            "defect_count": [10] * 40 + [1] * 40 + [2] * 20,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="procurement", name="Procurement & Operations", description="")
        res = compute_recommendations_intelligence(df, "proc_test", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertGreater(res.overview.total_recommendations, 0)
        # Must detect supplier cost difference or delivery delay
        rec_problems = [r.problem_detected.lower() for r in res.recommendations]
        self.assertTrue(any("supplier" in p or "delay" in p or "defect" in p or "price" in p for p in rec_problems))

    def test_04_hr_workforce_recommendations(self):
        """Test HR dataset with department attrition disparities."""
        df = pd.DataFrame({
            "department": ["Sales"] * 50 + ["Engineering"] * 50 + ["Marketing"] * 20,
            "attrition": [1] * 25 + [0] * 25 + [1] * 5 + [0] * 45 + [1] * 2 + [0] * 18,
            "tenure_months": [12] * 50 + [36] * 50 + [24] * 20,
            "monthly_salary": [5000] * 50 + [8000] * 50 + [6000] * 20,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="hr", name="Human Resources", description="")
        res = compute_recommendations_intelligence(df, "hr_test", profiles, domain)

        self.assertTrue(res.is_available)
        self.assertGreater(res.overview.total_recommendations, 0)
        rec_texts = [((r.business_problem or "") + " " + (r.observation or "") + " " + (r.title or "")).lower() for r in res.recommendations]
        self.assertTrue(any("attrition" in t or "sales" in t or "turnover" in t for t in rec_texts))

    def test_05_sports_recommendations(self):
        """Test Sports dataset evaluating consistency and performance gaps."""
        df = pd.DataFrame({
            "player": ["Player 1"] * 20 + ["Player 2"] * 20 + ["Player 3"] * 20,
            "match_date": pd.date_range("2024-01-01", periods=60, freq="W"),
            "runs": [85, 12, 0, 95, 4, 102, 8, 70, 0, 15] * 2 + [45, 52, 48, 50, 47, 55, 49, 51, 53, 46] * 2 + [10, 15, 8, 12, 14, 9, 11, 13, 10, 12] * 2,
            "strike_rate": [140.0] * 20 + [125.0] * 20 + [80.0] * 20,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="sports", name="Sports Analytics", description="")
        res = compute_recommendations_intelligence(df, "sports_test", profiles, domain)

        self.assertTrue(res.is_available)
        self.assertGreater(res.overview.total_recommendations, 0)

    def test_06_data_quality_driven_recommendation(self):
        """Test dataset with severe missing values producing data quality recommendation."""
        df = pd.DataFrame({
            "col_a": [1.0, np.nan, np.nan, np.nan, np.nan, 2.0, np.nan, np.nan, np.nan, 3.0],
            "col_b": ["x"] * 10,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_recommendations_intelligence(df, "dq_test", profiles, domain)

        self.assertTrue(res.is_available)
        categories = [r.category for r in res.recommendations]
        self.assertIn("data_quality", categories)

    def test_07_insufficient_records_returns_clean_response(self):
        """Test dataset with only 2 rows returns graceful overview and explicit limitations."""
        df = pd.DataFrame({
            "a": [1, 2],
            "b": [10, 20],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_recommendations_intelligence(df, "tiny_test", profiles, domain)

        self.assertFalse(res.is_available)
        self.assertGreater(len(res.overview.data_limitations_summary), 0)

    def test_08_http_api_route_upload_and_get_recommendations(self):
        """Test end-to-end HTTP API upload and GET /api/dataset/{id}/recommendations_intelligence."""
        csv_data = (
            "order_date,product,category,revenue,profit,discount\n"
            "2024-01-01,Alpha,Tech,1000,-50,0.30\n"
            "2024-01-02,Alpha,Tech,1200,-80,0.35\n"
            "2024-01-03,Beta,Furniture,3000,600,0.05\n"
            "2024-01-04,Beta,Furniture,3200,650,0.05\n"
            "2024-01-05,Gamma,Tech,800,200,0.10\n"
            "2024-01-06,Gamma,Tech,850,210,0.10\n"
        )
        file_obj = io.BytesIO(csv_data.encode("utf-8"))
        upload_res = self.client.post(
            "/api/dataset/upload",
            files={"file": ("ecom_sample.csv", file_obj, "text/csv")},
        )
        self.assertEqual(upload_res.status_code, 200)
        dataset_id = upload_res.json()["dataset_id"]

        # Call GET /api/dataset/{dataset_id}/recommendations_intelligence
        rec_res = self.client.get(f"/api/dataset/{dataset_id}/recommendations_intelligence")
        self.assertEqual(rec_res.status_code, 200)
        data = rec_res.json()

        self.assertEqual(data["dataset_id"], dataset_id)
        self.assertTrue(data["is_available"])
        self.assertIn("overview", data)
        self.assertIn("recommendations", data)
        self.assertGreater(data["overview"]["total_recommendations"], 0)

        # Call the hyphenated alias as well
        rec_res_alias = self.client.get(f"/api/dataset/{dataset_id}/recommendations-intelligence")
        self.assertEqual(rec_res_alias.status_code, 200)


if __name__ == "__main__":
    unittest.main()
