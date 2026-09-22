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
from app.services import dataset_service


class TestCompetitionIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_ecommerce_competition(self):
        """Verify product/category rankings, profit metric selection, and top vs bottom gaps."""
        df = pd.DataFrame({
            "product_name": ["MacBook Pro", "Dell XPS", "iPad Pro", "Galaxy Tab", "AirPods Max", "Sony WH1000"],
            "category": ["Laptops", "Laptops", "Tablets", "Tablets", "Audio", "Audio"],
            "sales": [45000.0, 32000.0, 18000.0, 12000.0, 8500.0, 6200.0],
            "profit": [9000.0, 4800.0, 3600.0, 1800.0, 2125.0, 1240.0],
            "units_sold": [30, 25, 20, 18, 17, 15],
            "order_date": pd.date_range("2024-01-01", periods=6, freq="ME"),
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="ecommerce", name="E-Commerce", description="")
        res = compute_competition_intelligence(df, "test_ecom", profiles, domain, dataset_currency="₹")

        self.assertTrue(res.is_available)
        self.assertEqual(res.overview.total_segments, 6)
        self.assertEqual(res.overview.top_segment_name, "MacBook Pro")
        self.assertEqual(res.overview.bottom_segment_name, "Sony WH1000")
        self.assertGreater(res.overview.performance_spread_ratio, 1.0)
        self.assertEqual(len(res.segments), 6)
        self.assertEqual(res.segments[0].rank, 1)
        self.assertEqual(res.segments[0].status, "top")
        self.assertEqual(res.segments[-1].status, "bottom")
        self.assertGreater(len(res.gaps), 0)

    def test_02_finance_asset_competition(self):
        """Verify financial entity comparison with operating cost and profit metrics."""
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
        self.assertEqual(res.overview.comparison_dimension, "company")
        self.assertEqual(res.overview.top_segment_name, "Apex Corp")
        self.assertEqual(res.overview.bottom_segment_name, "Delta Global")
        self.assertIn("$", res.overview.top_segment_formatted)

    def test_03_sports_cricket_team_comparison(self):
        """Verify sports team rankings by runs/points without inventing external positions."""
        df = pd.DataFrame({
            "team": ["India", "Australia", "England", "South Africa", "New Zealand"],
            "runs": [1850, 1620, 1490, 1380, 1250],
            "wickets": [45, 42, 38, 35, 30],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="sports_cricket", name="Cricket", description="")
        res = compute_competition_intelligence(df, "test_sports", profiles, domain)

        self.assertTrue(res.is_available)
        self.assertEqual(res.overview.comparison_dimension, "team")
        self.assertEqual(res.overview.top_segment_name, "India")
        self.assertEqual(res.overview.bottom_segment_name, "New Zealand")

    def test_04_hr_department_comparison(self):
        """Verify HR department comparison with average salary metric aggregation."""
        df = pd.DataFrame({
            "department": ["Engineering"] * 10 + ["Sales"] * 8 + ["HR"] * 5 + ["Support"] * 7,
            "salary": [120000] * 10 + [95000] * 8 + [75000] * 5 + [60000] * 7,
            "performance_score": [4.5] * 10 + [4.1] * 8 + [3.9] * 5 + [3.6] * 7,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="people_hr", name="Human Resources", description="")
        res = compute_competition_intelligence(df, "test_hr", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertEqual(res.overview.comparison_dimension, "department")
        self.assertEqual(res.overview.top_segment_name, "Engineering")
        self.assertEqual(res.overview.bottom_segment_name, "Support")

    def test_05_procurement_supplier_comparison(self):
        """Verify procurement supplier spend rankings."""
        df = pd.DataFrame({
            "supplier": ["Supplier Alpha", "Supplier Beta", "Supplier Gamma", "Supplier Delta"],
            "tender_value": [2500000.0, 1400000.0, 950000.0, 420000.0],
            "duration_in_days": [45, 30, 60, 20],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="procurement", name="Procurement", description="")
        res = compute_competition_intelligence(df, "test_proc", profiles, domain, dataset_currency="$")

        self.assertTrue(res.is_available)
        self.assertEqual(res.overview.comparison_dimension, "supplier")
        self.assertEqual(res.overview.top_segment_name, "Supplier Alpha")
        self.assertEqual(res.overview.bottom_segment_name, "Supplier Delta")

    def test_06_no_comparison_dimension_graceful_unavailable_state(self):
        """Verify dataset with purely uniform or continuous numeric values gracefully reports unavailable state."""
        df = pd.DataFrame({
            "temperature": [21.5, 22.0, 21.8, 23.1, 22.9, 21.4],
            "humidity": [55.0, 56.2, 54.8, 58.1, 57.0, 54.3],
            "pressure": [1013.2, 1012.8, 1014.0, 1013.5, 1012.9, 1013.1],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_competition_intelligence(df, "test_pure_num", profiles, domain)

        self.assertFalse(res.is_available)
        self.assertIn("cannot be reliably calculated", res.unavailable_reason)
        self.assertGreater(len(res.missing_requirements), 0)

    def test_07_no_date_column_cross_sectional_only(self):
        """Verify dataset without a date column disables longitudinal momentum while preserving cross-sectional ranking."""
        df = pd.DataFrame({
            "branch": ["North", "South", "East", "West"],
            "sales": [12000, 9500, 8400, 6200],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_competition_intelligence(df, "test_nodate", profiles, domain)

        self.assertTrue(res.is_available)
        self.assertFalse(res.time_comparison.is_available)
        self.assertIn("unavailable", res.time_comparison.summary.lower())

    def test_08_missing_and_nan_values_safety(self):
        """Verify nulls in categorical and numeric columns are handled gracefully without exceptions."""
        df = pd.DataFrame({
            "category": ["A", "B", None, "A", "C", "B", None],
            "sales": [100.0, np.nan, 50.0, 200.0, 150.0, np.nan, 30.0],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")
        res = compute_competition_intelligence(df, "test_nulls", profiles, domain)

        self.assertTrue(res.is_available)
        self.assertGreater(len(res.segments), 0)

    def test_09_api_route_integration(self):
        """Verify live HTTP API GET /api/dataset/{dataset_id}/competition integration."""
        csv_bytes = (
            "team,points,goals\n"
            "Arsenal,75,68\n"
            "Man City,73,71\n"
            "Liverpool,70,65\n"
            "Aston Villa,59,52\n"
            "Tottenham,53,49\n"
        ).encode("utf-8")

        upload_res = self.client.post(
            "/api/dataset/upload",
            files={"file": ("league_table.csv", io.BytesIO(csv_bytes), "text/csv")}
        )
        self.assertEqual(upload_res.status_code, 200)
        did = upload_res.json()["dataset_id"]

        comp_res = self.client.get(f"/api/dataset/{did}/competition")
        self.assertEqual(comp_res.status_code, 200)
        data = comp_res.json()

        self.assertEqual(data["dataset_id"], did)
        self.assertTrue(data["is_available"])
        self.assertIn("overview", data)
        self.assertEqual(data["overview"]["top_segment_name"], "Arsenal")
        self.assertEqual(data["overview"]["bottom_segment_name"], "Tottenham")

        # Invalid ID test
        bad_res = self.client.get("/api/dataset/fake_dataset_id_9999/competition")
        self.assertEqual(bad_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
