"""Comprehensive Unit Test Suite for Phase 5 — Universal Forecasting Engine."""
import unittest
import pandas as pd
import numpy as np

from app.services.forecast_engine import (
    compute_forecast,
    _fit_naive,
    _fit_moving_average,
    _fit_holt_linear,
    _fit_linear_trend,
    _generate_domain_interpretation,
)


class TestUniversalForecastingEngine(unittest.TestCase):
    """Verify time-series detection, algorithms, holdout validation, domain narratives, and multi-domain datasets."""

    def test_naive_baseline_model(self):
        """Test Naive baseline projection."""
        series = np.array([10.0, 12.0, 15.0, 14.0, 18.0, 20.0])
        fitted, forecast, metrics, desc = _fit_naive(series, horizon=4)
        
        self.assertEqual(len(forecast), 4)
        self.assertTrue(np.all(forecast == 20.0))
        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("Naive", desc)

    def test_moving_average_model(self):
        """Test Moving average model."""
        series = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        fitted, forecast, metrics, desc = _fit_moving_average(series, horizon=3, window=3)
        
        self.assertEqual(len(forecast), 3)
        # Expected average of last 3 values (40, 50, 60) is 50.0
        self.assertAlmostEqual(forecast[0], 50.0, places=1)
        self.assertIn("Moving Average", desc)

    def test_linear_trend_model(self):
        """Test Ordinary Least Squares Linear Trend extrapolation."""
        series = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        fitted, forecast, metrics, desc = _fit_linear_trend(series, horizon=3)
        
        self.assertEqual(len(forecast), 3)
        # Sequence continues: 70.0, 80.0, 90.0
        self.assertAlmostEqual(forecast[0], 70.0, places=1)
        self.assertAlmostEqual(forecast[1], 80.0, places=1)
        self.assertAlmostEqual(forecast[2], 90.0, places=1)
        self.assertAlmostEqual(metrics["mae"], 0.0, places=1)

    def test_holt_linear_exponential_smoothing(self):
        """Test Holt's linear exponential smoothing model."""
        series = np.array([100.0, 110.0, 122.0, 135.0, 148.0, 162.0, 178.0])
        fitted, forecast, metrics, desc = _fit_holt_linear(series, horizon=3)
        
        self.assertEqual(len(forecast), 3)
        self.assertGreater(forecast[0], series[-1])  # Upward trend continued
        self.assertIn("Holt's", desc)

    def test_daily_and_weekly_frequency_detection(self):
        """Test daily and weekly series frequency inference."""
        # Daily series
        dates_d = pd.date_range("2024-01-01", periods=15, freq="D")
        df_daily = pd.DataFrame({
            "record_date": dates_d,
            "revenue": [1000.0 + i * 50 for i in range(15)],
        })
        res_d = compute_forecast(df_daily, "test_daily", horizon=7)
        self.assertTrue(res_d.is_available)
        self.assertEqual(res_d.frequency, "D")
        self.assertEqual(res_d.frequency_label, "Daily")
        self.assertEqual(len(res_d.forecast_points), 7)

        # Weekly series
        dates_w = pd.date_range("2023-01-01", periods=20, freq="W")
        df_weekly = pd.DataFrame({
            "week_start": dates_w,
            "orders": [200 + (i % 5) * 10 for i in range(20)],
        })
        res_w = compute_forecast(df_weekly, "test_weekly", horizon=4)
        self.assertTrue(res_w.is_available)
        self.assertEqual(res_w.frequency, "W")
        self.assertEqual(res_w.frequency_label, "Weekly")

    def test_monthly_and_yearly_frequency_detection(self):
        """Test monthly and yearly series frequency inference."""
        dates_m = pd.date_range("2022-01-01", periods=24, freq="MS")
        df_monthly = pd.DataFrame({
            "month_date": dates_m,
            "sales_amount": [50000.0 + i * 2000 for i in range(24)],
        })
        res_m = compute_forecast(df_monthly, "test_monthly", horizon=6)
        self.assertTrue(res_m.is_available)
        self.assertEqual(res_m.frequency, "M")
        self.assertEqual(res_m.frequency_label, "Monthly")

    def test_unsorted_and_duplicate_dates_handling(self):
        """Test that unsorted dates and duplicate timestamp rows are grouped and sorted properly."""
        dates = ["2024-03-01", "2024-01-01", "2024-01-01", "2024-02-01", "2024-04-01", "2024-05-01", "2024-06-01", "2024-07-01"]
        df_unsorted = pd.DataFrame({
            "timestamp": dates,
            "amount": [300.0, 100.0, 50.0, 200.0, 400.0, 500.0, 600.0, 700.0],
        })
        res = compute_forecast(df_unsorted, "test_unsorted", horizon=3)
        self.assertTrue(res.is_available)
        self.assertGreaterEqual(len(res.historical_points), 6)
        # Jan 1st duplicate should be summed: 100 + 50 = 150
        first_hist = res.historical_points[0]
        self.assertEqual(first_hist.actual, 150.0)

    def test_holdout_validation_scoring(self):
        """Test holdout validation for series with N >= 10."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        df = pd.DataFrame({
            "date": dates,
            "views": [1000 + i * 30 + (i % 3) * 10 for i in range(20)],
        })
        res = compute_forecast(df, "test_holdout", horizon=7, method="auto")
        self.assertTrue(res.is_available)
        self.assertTrue(res.validation_summary["has_holdout"])
        self.assertGreater(res.validation_summary["holdout_periods"], 0)
        self.assertGreater(len(res.method_comparison), 0)
        
        # Verify selected model is flagged
        selected_models = [m for m in res.method_comparison if m["is_selected"]]
        self.assertEqual(len(selected_models), 1)

    def test_constant_and_zero_valued_metrics(self):
        """Test zero-inflation and constant metric series without errors or divide-by-zero crashes."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        # Constant series
        df_const = pd.DataFrame({"date": dates, "score": [10.0] * 10})
        res_const = compute_forecast(df_const, "test_const", horizon=5)
        self.assertTrue(res_const.is_available)
        self.assertEqual(res_const.accuracy_metrics["mae"], 0.0)

        # Zero-valued series
        df_zero = pd.DataFrame({"date": dates, "defect_rate": [0.0] * 10})
        res_zero = compute_forecast(df_zero, "test_zero", horizon=5)
        self.assertTrue(res_zero.is_available)
        self.assertEqual(res_zero.accuracy_metrics["mape"], 0.0)

    def test_negative_series_and_bounds(self):
        """Test series with negative numbers (e.g. net profit or temperature)."""
        dates = pd.date_range("2024-01-01", periods=12, freq="M")
        df_neg = pd.DataFrame({
            "date": dates,
            "net_profit": [-100.0, -50.0, 0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0],
        })
        res_neg = compute_forecast(df_neg, "test_neg", horizon=4)
        self.assertTrue(res_neg.is_available)
        self.assertGreater(res_neg.forecast_points[-1].forecast, 450.0)

    def test_insufficient_observations_graceful_response(self):
        """Test that datasets with < 6 observations return clear reasons instead of crash."""
        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        df_short = pd.DataFrame({"date": dates, "revenue": [100, 200, 300, 400]})
        res = compute_forecast(df_short, "test_short", horizon=5)
        self.assertFalse(res.is_available)
        self.assertIn("minimum 6 required", res.unavailable_reason)

    def test_no_date_column_graceful_response(self):
        """Test dataset without date column returns clear explanation."""
        df_no_date = pd.DataFrame({
            "category": ["A", "B", "C", "D", "E", "F", "G"],
            "value": [10, 20, 30, 40, 50, 60, 70],
        })
        res = compute_forecast(df_no_date, "test_no_date", horizon=5)
        self.assertFalse(res.is_available)
        self.assertIn("date", res.unavailable_reason.lower())

    def test_domain_aware_interpretations(self):
        """Test domain narrative generator for Revenue, Profit, Expenses, Quantity, Rates, and Neutral."""
        interp_rev = _generate_domain_interpretation(
            metric_name="total_revenue",
            semantic_type="currency",
            unit="₹",
            latest_val=100000.0,
            final_val=125000.0,
            growth_pct=25.0,
            horizon=6,
            freq_label="Monthly",
            method_name="Holt's Linear Exponential Smoothing",
        )
        self.assertIn("revenue", interp_rev.lower())
        self.assertIn("25.0%", interp_rev)
        self.assertIn("not guarantee", interp_rev.lower())

        interp_prof = _generate_domain_interpretation(
            metric_name="net_profit",
            semantic_type="currency",
            unit="$",
            latest_val=5000.0,
            final_val=4000.0,
            growth_pct=-20.0,
            horizon=4,
            freq_label="Quarterly",
            method_name="Linear Trend",
        )
        self.assertIn("profit", interp_prof.lower())
        self.assertIn("-20.0%", interp_prof)

        interp_rate = _generate_domain_interpretation(
            metric_name="churn_rate",
            semantic_type="percentage",
            unit="%",
            latest_val=5.5,
            final_val=4.2,
            growth_pct=-23.6,
            horizon=3,
            freq_label="Monthly",
            method_name="Moving Average",
        )
        self.assertIn("rate", interp_rate.lower())

    def test_excessive_horizon_warning(self):
        """Test that horizon exceeding historical observations generates a clear warning."""
        dates = pd.date_range("2024-01-01", periods=8, freq="D")
        df = pd.DataFrame({"date": dates, "sales": [100 + i * 10 for i in range(8)]})
        res = compute_forecast(df, "test_excessive", horizon=30)
        self.assertTrue(res.is_available)
        self.assertIsNotNone(res.horizon_warning)
        self.assertIn("exceeds historical data length", res.horizon_warning)

    def test_multi_domain_support(self):
        """Test forecasting engine across Healthcare, Sports, HR, and Procurement datasets."""
        # Healthcare: Daily patient admissions
        dates_h = pd.date_range("2024-01-01", periods=30, freq="D")
        df_health = pd.DataFrame({
            "admit_date": dates_h,
            "patient_count": [45 + (i % 7) * 3 for i in range(30)],
        })
        res_h = compute_forecast(df_health, "health_ds", horizon=14)
        self.assertTrue(res_h.is_available)
        self.assertEqual(res_h.unit, "patients")

        # Sports: IPL runs per match over time
        dates_s = pd.date_range("2024-03-01", periods=25, freq="D")
        df_sports = pd.DataFrame({
            "match_date": dates_s,
            "runs_scored": [160 + (i % 6) * 12 for i in range(25)],
        })
        res_s = compute_forecast(df_sports, "sports_ds", horizon=7)
        self.assertTrue(res_s.is_available)
        self.assertEqual(res_s.unit, "runs")

        # Procurement: Monthly tender values in INR
        dates_p = pd.date_range("2023-01-01", periods=18, freq="MS")
        df_proc = pd.DataFrame({
            "tender_publication_date": dates_p,
            "tender_value_inr": [5000000.0 + i * 250000.0 for i in range(18)],
        })
        res_p = compute_forecast(df_proc, "proc_ds", horizon=6)
        self.assertTrue(res_p.is_available)
        self.assertEqual(res_p.unit, "₹")


if __name__ == "__main__":
    unittest.main()
