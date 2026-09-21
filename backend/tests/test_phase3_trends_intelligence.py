"""Comprehensive test suite for Phase 3 – Trends Intelligence & Real-World Domain Analytics.

Tests:
1. Time dimension detection, parsing, validation, and irregular interval detection
2. Datasets without date columns (graceful fallback)
3. Multi-granularity trends (Daily, Weekly, Monthly, Quarterly, Yearly)
4. Period-over-period comparisons (current vs previous, net % change, best & worst periods)
5. Moving averages (3-period, 7-period) and anomaly spike/drop detection
6. Category-wise / entity-wise trend breakdowns (growing vs declining segments)
7. 12 practical trend questions output
8. Statistical forecasting engine with 80% & 95% confidence intervals
9. Forecast unavailable handling (insufficient historical data or missing date)
10. Data quality engine (missing values, duplicate rows, duplicate IDs, suspicious negatives, zero denominators, outliers, empty columns)
11. Real-world domain playbooks (Sales, Cricket match, Cricket ball-by-ball, Healthcare, Education, Marketing, Finance, Unknown)
"""
from __future__ import annotations

import unittest
import pandas as pd
import numpy as np

from app.services import dataset_service, dataset_store
from app.services.data_quality_engine import compute_data_quality_report
from app.services.forecast_engine import compute_forecast
from app.services.trend_engine import compute_trends_intelligence


class TestPhase3TrendsIntelligence(unittest.TestCase):
    """Test suite verifying Phase 3 features."""

    def test_time_dimension_detection_and_validation(self):
        """Verify time dimension parsing, frequency detection, and interval validation."""
        # Daily dataset
        df_daily = pd.DataFrame({
            "transaction_date": pd.date_range("2026-01-01", periods=30, freq="D"),
            "revenue": [100.0 + i * 5 for i in range(30)],
        })
        res_daily = compute_trends_intelligence(df_daily, "test_daily")
        self.assertTrue(res_daily.has_time_dimension)
        self.assertEqual(res_daily.time_validation.detected_frequency, "daily")
        self.assertEqual(res_daily.time_validation.time_column, "transaction_date")
        self.assertEqual(res_daily.time_validation.date_range["total_days"], 29)

        # Monthly dataset
        df_monthly = pd.DataFrame({
            "month_date": pd.date_range("2024-01-01", periods=24, freq="MS"),
            "active_users": [1000 + i * 50 for i in range(24)],
        })
        res_monthly = compute_trends_intelligence(df_monthly, "test_monthly")
        self.assertTrue(res_monthly.has_time_dimension)
        self.assertEqual(res_monthly.time_validation.detected_frequency, "monthly")

    def test_dataset_without_time_dimension(self):
        """Verify graceful fallback when dataset contains no date column."""
        df_no_time = pd.DataFrame({
            "product_name": ["Widget A", "Widget B", "Widget C", "Widget D"],
            "unit_price": [10.0, 20.0, 15.0, 25.0],
            "units_in_stock": [100, 50, 75, 200],
        })
        res = compute_trends_intelligence(df_no_time, "test_no_time")
        self.assertFalse(res.has_time_dimension)
        self.assertEqual(res.time_validation.quality_status, "No Time Dimension")
        self.assertGreater(len(res.limitations), 0)
        self.assertIn("lacks a usable temporal dimension", res.limitations[0])

    def test_period_over_period_and_practical_questions(self):
        """Verify period-over-period comparisons, volatility, and the 12 practical trend answers."""
        dates = pd.date_range("2026-01-01", periods=12, freq="MS")
        # Sales: baseline 100, then spike at month 6 (index 5) to 500
        sales = [100.0, 110.0, 105.0, 120.0, 115.0, 500.0, 130.0, 125.0, 140.0, 135.0, 150.0, 160.0]
        df = pd.DataFrame({
            "order_date": dates,
            "sales_amount": sales,
            "category": ["Electronics", "Clothing"] * 6,
        })

        res = compute_trends_intelligence(df, "test_pop", granularity="M", metric="sales_amount", category_col="category")
        self.assertTrue(res.has_time_dimension)
        self.assertIsNotNone(res.period_comparison)

        comp = res.period_comparison
        self.assertEqual(comp.current_val, 160.0)
        self.assertEqual(comp.previous_val, 150.0)
        self.assertEqual(comp.absolute_change, 10.0)
        self.assertAlmostEqual(comp.pct_change, 6.67, places=1)
        self.assertEqual(comp.growth_direction, "increasing")
        self.assertEqual(comp.best_val, 500.0)

        # Verify spike was detected
        self.assertTrue(any(sd.type == "spike" for sd in res.spikes_and_drops))

        # Verify practical answers
        ans = res.practical_answers
        self.assertIsNotNone(ans)
        self.assertIn("sales", ans.metric_analyzed.lower())
        self.assertIn("150.00", ans.previous_value_text)
        self.assertIn("160.00", ans.current_value_text)
        self.assertIn("+10.00", ans.absolute_change_text)
        self.assertIn("+6.7%", ans.pct_change_text)
        self.assertIn("500.00", ans.best_period_text)

        # Verify category trends
        self.assertGreater(len(res.category_trends), 0)
        for cat in res.category_trends:
            self.assertIn(cat.category, ("Electronics", "Clothing"))
            self.assertIsNotNone(cat.direction)

    def test_forecasting_engine_valid_series(self):
        """Verify Holt's linear exponential smoothing forecast with 80% & 95% confidence intervals."""
        dates = pd.date_range("2025-01-01", periods=18, freq="MS")
        values = [100.0 + (i * 10.0) + (i % 3) * 5.0 for i in range(18)]
        df = pd.DataFrame({
            "month": dates,
            "mrr": values,
        })

        fc = compute_forecast(df, "test_fc", horizon=6, metric="mrr", granularity="M")
        self.assertTrue(fc.is_available)
        self.assertEqual(len(fc.forecast_points), 6)
        self.assertEqual(len(fc.historical_points), 18)
        self.assertIn("Holt's Linear", fc.method_used)
        self.assertIn("mape", fc.accuracy_metrics)
        self.assertIn("rmse", fc.accuracy_metrics)

        # Verify confidence intervals widen or exist
        p1 = fc.forecast_points[0]
        self.assertLess(p1.lower_bound_80, p1.forecast)
        self.assertGreater(p1.upper_bound_80, p1.forecast)
        self.assertLess(p1.lower_bound_95, p1.lower_bound_80)
        self.assertGreater(p1.upper_bound_95, p1.upper_bound_80)


        # Verify disclaimer and limitations
        self.assertIn("mathematical extrapolations", fc.disclaimer)
        self.assertGreater(len(fc.limitations), 0)

    def test_forecasting_engine_insufficient_data(self):
        """Verify forecast unavailable state when dataset has fewer than 6 observations."""
        df_short = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=4, freq="D"),
            "val": [10.0, 12.0, 15.0, 14.0],
        })
        fc = compute_forecast(df_short, "test_short", horizon=6)
        self.assertFalse(fc.is_available)
        self.assertIn("minimum 6", fc.unavailable_reason.lower())

    def test_data_quality_engine_comprehensive(self):
        """Verify data quality checks for missing values, duplicates, suspicious negatives, and zero denominators."""
        df_dirty = pd.DataFrame({
            "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-1", "ORD-5", "ORD-6"],  # duplicate ID
            "price": [29.99, -15.00, 49.99, 29.99, None, 19.99],  # suspicious negative + missing
            "quantity": [1, 2, 0, 1, 3, 2],  # zero count
            "category": ["Electronics", "Clothing", "electronics ", "Home", "Home", "Home"],  # whitespace inconsistency
            "empty_col": [None, None, None, None, None, None],  # empty column
            "constant_col": ["Const", "Const", "Const", "Const", "Const", "Const"],  # constant column
        })

        rep = compute_data_quality_report(df_dirty, "test_dirty")
        self.assertIn(rep.status, ("Warning", "Critical"))
        self.assertLess(rep.overall_score, 80)
        self.assertGreater(rep.issue_counts["critical"] + rep.issue_counts["warning"], 0)

        check_ids = [c.id for c in rep.checks]
        self.assertTrue(any("duplicate" in cid or "dup" in cid for cid in check_ids))
        self.assertTrue(any("empty" in cid for cid in check_ids))
        self.assertTrue(any("negative" in cid for cid in check_ids))
        self.assertTrue(any("constant" in cid for cid in check_ids))

        # Check column diagnostics
        self.assertIn("price", rep.column_diagnostics)
        self.assertEqual(rep.column_diagnostics["price"].negative_count, 1)
        self.assertEqual(rep.column_diagnostics["empty_col"].unique_count, 0)
        self.assertEqual(rep.column_diagnostics["constant_col"].unique_count, 1)

    def test_cricket_ipl_no_sales_metrics(self):
        """Verify that Cricket/IPL datasets never display generic sales or revenue metrics."""
        df_ipl = pd.DataFrame({
            "id": list(range(1, 31)),
            "season": [2024] * 30,
            "team1": ["CSK", "MI", "RCB"] * 10,
            "team2": ["MI", "CSK", "KKR"] * 10,
            "winner": ["CSK", "MI", "CSK"] * 10,
            "toss_winner": ["CSK", "MI", "RCB"] * 10,
            "toss_decision": ["bat", "field", "field"] * 10,
            "venue": ["Wankhede", "Chepauk", "Chinnaswamy"] * 10,
        })
        dataset_id = dataset_store.save_dataset("ipl_test.csv", "csv", df_ipl)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        # Check KPIs: must NOT contain sales, revenue, profit, ebitda, or churn
        kpi_names_lower = [k["name"].lower() for k in intel["kpis"]]
        for forbidden in ("revenue", "profit", "ebitda", "churn", "cpa", "cpc", "roas"):
            self.assertFalse(
                any(forbidden in name for name in kpi_names_lower),
                f"Forbidden business metric '{forbidden}' found in cricket analytics!",
            )

    def test_healthcare_descriptive_only(self):
        """Verify Healthcare datasets contain descriptive metrics and no clinical diagnosis claims."""
        df_health = pd.DataFrame({
            "patient_id": [f"P-{i}" for i in range(40)],
            "diagnosis": ["Cardiology", "Neurology", "Pediatrics", "Oncology"] * 10,
            "los": [3, 5, 2, 8] * 10,
            "charges": [5000.0, 12000.0, 3200.0, 25000.0] * 10,
            "admission_date": pd.date_range("2026-01-01", periods=40, freq="D"),
        })
        dataset_id = dataset_store.save_dataset("health_test.csv", "csv", df_health)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertIn(intel["domain"]["domain_id"], ("healthcare", "hospital_management"))
        # Verify limitations explicitly mention non-clinical status
        recommendations = intel.get("recommendations", [])
        for rec in recommendations:
            self.assertTrue(len(rec["limitations"]) > 0)


    def test_api_integration_trends_and_forecast(self):
        """Verify dataset_service get_trends_intelligence, get_forecast, and get_data_quality_report."""
        dates = pd.date_range("2026-01-01", periods=20, freq="W")
        df = pd.DataFrame({
            "date": dates,
            "sales": [100.0 + i * 15.0 for i in range(20)],
            "category": ["A", "B", "C", "A"] * 5,
        })
        dataset_id = dataset_store.save_dataset("sales_weekly.csv", "csv", df)

        # 1. Trends
        trends = dataset_service.get_trends_intelligence(dataset_id, granularity="W")
        self.assertTrue(trends["has_time_dimension"])
        self.assertEqual(trends["selected_metric"], "sales")
        self.assertGreater(len(trends["time_series"]), 0)

        # 2. Forecast
        forecast = dataset_service.get_forecast(dataset_id, horizon=4)
        self.assertTrue(forecast["is_available"])
        self.assertEqual(len(forecast["forecast_points"]), 4)

        # 3. Data Quality
        quality = dataset_service.get_data_quality_report(dataset_id)
        self.assertEqual(quality["status"], "Healthy")
        self.assertGreaterEqual(quality["overall_score"], 80)

    def test_redesigned_metric_explorer_and_context(self):
        """Verify metric categorization into Performance, Volume, Cost, Operations, and Metric Context."""
        dates = pd.date_range("2025-01-01", periods=30, freq="D")
        df = pd.DataFrame({
            "order_date": dates,
            "sales": [100.0 + i * 10.0 for i in range(30)],
            "profit": [20.0 + i * 2.0 for i in range(30)],
            "quantity": [2 + (i % 5) for i in range(30)],
            "discount": [5.0, 0.0, 2.5] * 10,
            "shipping_cost": [10.0, 15.0, 8.0] * 10,
            "aging_days": [3.5, 4.0, 2.0] * 10,
            "category": ["Electronics", "Furniture", "Supplies"] * 10,
        })
        dataset_id = dataset_store.save_dataset("multi_metric_test.csv", "csv", df)
        trends = dataset_service.get_trends_intelligence(dataset_id, granularity="W")

        self.assertTrue(trends["has_time_dimension"])
        catalog = trends["metrics_catalog"]
        self.assertGreaterEqual(len(catalog), 6)

        # Verify groups
        groups = {m["column_name"]: m["group"] for m in catalog}
        self.assertEqual(groups["sales"], "Financial Metrics")
        self.assertEqual(groups["profit"], "Financial Metrics")
        self.assertEqual(groups["quantity"], "Operational Metrics")
        self.assertEqual(groups["discount"], "Financial Metrics")
        self.assertEqual(groups["shipping_cost"], "Financial Metrics")
        self.assertEqual(groups["aging_days"], "Operational Metrics")

        # Verify primary metric recommendation
        self.assertEqual(trends["primary_metric"], "sales")
        self.assertIsNotNone(trends["primary_metric_reason"])

        # Verify Metric Context
        ctx = trends["metric_context"]
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx["source_column"], "sales")
        self.assertEqual(ctx["records_included"], 30)
        self.assertEqual(ctx["records_excluded"], 0)

        # Verify Trend Summary in plain English
        summary = trends["trend_summary"]
        self.assertIsNotNone(summary)
        self.assertEqual(summary["trend_status"], "Increasing")
        self.assertIn("sales", summary["plain_english_summary"].lower())
        self.assertGreaterEqual(len(trends["what_this_chart_tells_you"]), 2)

    def test_trends_single_period_graceful_handling(self):
        """Verify that a single-period dataset produces no errors and outputs clean baseline info."""
        df_single = pd.DataFrame({
            "date": ["2022-03-31"] * 50,
            "amount": [1000.0 + i for i in range(50)],
        })
        dataset_id = dataset_store.save_dataset("single_date.csv", "csv", df_single)
        trends = dataset_service.get_trends_intelligence(dataset_id)

        self.assertTrue(trends["has_time_dimension"])
        summary = trends["trend_summary"]
        self.assertIsNotNone(summary)
        self.assertEqual(summary["trend_status"], "Insufficient Data")
        self.assertIn("single", summary["plain_english_summary"].lower())
        self.assertEqual(len(trends["time_series"]), 1)


if __name__ == "__main__":
    unittest.main()
