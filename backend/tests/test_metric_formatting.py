"""Unit tests for metric value units and domain-aware formatting across DataScope."""
import unittest
import pandas as pd
import numpy as np

from app.services.column_formatter import (
    detect_column_unit,
    format_metric_display,
    build_metric_tooltip_details,
)
from app.services.type_inference import detect_dataset_currency
from app.services.recommendation_engine import compute_kpis
from app.services.universal_stats import compute_universal_statistics


class TestMetricFormattingAndUnits(unittest.TestCase):
    """Verify semantic unit detection, formatting rules, percentage preservation, and tooltips."""

    def test_currency_detection_and_formatting(self):
        """Test currency detection for INR, USD, EUR, GBP, and formatting."""
        # INR / Indian Rupee
        unit, sem, curr = detect_column_unit("profit", None, dataset_currency="₹")
        self.assertEqual(unit, "₹")
        self.assertEqual(sem, "currency")
        self.assertEqual(curr, "₹")

        unit, sem, curr = detect_column_unit("revenue_inr", None)
        self.assertEqual(unit, "₹")
        self.assertEqual(sem, "currency")
        self.assertEqual(curr, "₹")
        
        # USD
        unit, sem, curr = detect_column_unit("revenue_usd", None)
        self.assertEqual(unit, "$")
        self.assertEqual(curr, "$")

        # EUR & GBP
        unit_eur, _, curr_eur = detect_column_unit("cost_eur", None)
        self.assertEqual(unit_eur, "€")
        unit_gbp, _, curr_gbp = detect_column_unit("price_gbp", None)
        self.assertEqual(unit_gbp, "£")

        # Formatting values
        self.assertEqual(format_metric_display(70.41, unit="₹", currency_symbol="₹"), "₹70.41")
        self.assertEqual(format_metric_display(767147, unit="₹", currency_symbol="₹"), "₹767,147")
        self.assertEqual(format_metric_display(1250000.5, unit="$", currency_symbol="$"), "$1,250,000.50")

    def test_percentage_preservation_and_formatting(self):
        """Test percentage detection and ensure raw values (0.3 vs 30) are not blindly multiplied/divided."""
        # 0.3 stored as percentage fraction
        unit_disc, sem_disc, _ = detect_column_unit("discount_rate")
        self.assertEqual(unit_disc, "%")
        self.assertEqual(sem_disc, "percentage")

        unit_pct, sem_pct, _ = detect_column_unit("growth_pct")
        self.assertEqual(unit_pct, "%")

        unit_margin, _, _ = detect_column_unit("margin_percentage")
        self.assertEqual(unit_margin, "%")

        # Value 0.3 should format as 0.3% (or 0.30% with precision=2)
        formatted_03 = format_metric_display(0.3, unit="%", semantic_type="percentage", precision=2)
        self.assertEqual(formatted_03, "0.30%")

        # Value 30 should format as 30%
        formatted_30 = format_metric_display(30.0, unit="%", semantic_type="percentage")
        self.assertEqual(formatted_30, "30%")

        # Value 85.5 should format as 85.50%
        formatted_855 = format_metric_display(85.5, unit="%", semantic_type="percentage", precision=2)
        self.assertEqual(formatted_855, "85.50%")

    def test_quantity_and_count_metrics(self):
        """Test counts and quantities across sports, healthcare, HR, and sales."""
        # Quantities
        u, sem, _ = detect_column_unit("units_sold")
        self.assertEqual(u, "units")
        self.assertEqual(sem, "quantity")

        self.assertEqual(format_metric_display(2.5, unit="units", semantic_type="quantity"), "2.50 units")

        # Domain counts
        self.assertEqual(detect_column_unit("runs_scored")[0], "runs")
        self.assertEqual(detect_column_unit("wickets")[0], "wickets")
        self.assertEqual(detect_column_unit("view_count")[0], "views")
        self.assertEqual(detect_column_unit("order_id")[0], "records")

        self.assertEqual(format_metric_display(150, unit="records", semantic_type="count"), "150 records")
        self.assertEqual(format_metric_display(4500, unit="orders", semantic_type="count"), "4,500 orders")

    def test_duration_and_rating_metrics(self):
        """Test duration, time, and score metric units."""
        self.assertEqual(detect_column_unit("delivery_days")[0], "days")
        self.assertEqual(detect_column_unit("tenure_months")[0], "yrs")
        self.assertEqual(detect_column_unit("duration_seconds")[0], "s")
        self.assertEqual(detect_column_unit("response_time_ms")[0], "ms")
        self.assertEqual(detect_column_unit("satisfaction_rating")[0], "/ 10")
        self.assertEqual(detect_column_unit("score")[0], "pts")

        self.assertEqual(format_metric_display(15, unit="days", semantic_type="duration"), "15 days")
        self.assertEqual(format_metric_display(8.5, unit="/ 10", semantic_type="score"), "8.50 / 10")

    def test_unknown_and_neutral_metrics(self):
        """Unknown numeric columns must use neutral formatting without fake units."""
        u, sem, _ = detect_column_unit("custom_alpha_factor")
        self.assertEqual(u, "units")
        self.assertEqual(sem, "number")
        self.assertEqual(format_metric_display(12345.67, unit="units", semantic_type="number"), "12,345.67")

    def test_tooltip_details_builder(self):
        """Test tooltip/details section builder with aggregation, source column, and rule."""
        tooltip = build_metric_tooltip_details(
            metric_name="Average Profit",
            value=70.41,
            unit="₹",
            aggregation="mean",
            source_column="profit",
            semantic_type="currency",
        )
        self.assertEqual(tooltip["metric_name"], "Average Profit")
        self.assertEqual(tooltip["value"], 70.41)
        self.assertEqual(tooltip["formatted_value"], "₹70.41")
        self.assertEqual(tooltip["unit"], "₹")
        self.assertEqual(tooltip["aggregation_method"], "MEAN")
        self.assertEqual(tooltip["source_column"], "profit")
        self.assertIn("Currency", tooltip["formatting_rule"])

    def test_dataset_currency_detection(self):
        """Test dataset-level currency detection from Indian context, columns, and symbols."""
        # Indian dataset with GST and INR
        df_india = pd.DataFrame({
            "order_id": [1, 2, 3],
            "gst_amount": [180.0, 360.0, 90.0],
            "total_inr": [1000.0, 2000.0, 500.0],
        })
        self.assertEqual(detect_dataset_currency(df_india), "₹")

        # US dataset with USD column
        df_us = pd.DataFrame({
            "product_id": [101, 102],
            "revenue_usd": [5000.0, 7500.0],
        })
        self.assertEqual(detect_dataset_currency(df_us), "$")

        # Dataset with raw currency symbol in strings
        df_symbol = pd.DataFrame({
            "price": ["€100.00", "€250.00", "€80.00"],
            "qty": [1, 2, 3],
        })
        self.assertEqual(detect_dataset_currency(df_symbol), "€")

    def test_compute_kpis_with_units(self):
        """Test KPI computation returns populated units, formatted values, and formatting rules."""
        df = pd.DataFrame({
            "profit": [50.0, 70.0, 91.23],
            "units_sold": [2, 3, 2.5],
            "discount_rate": [0.1, 0.2, 0.3],
            "category": ["A", "B", "A"],
        })
        kpis = compute_kpis(df)
        self.assertGreater(len(kpis), 0)

        # Check that KPIs have unit and formatted_value
        profit_kpi = next((k for k in kpis if "profit" in k["label"].lower()), None)
        self.assertIsNotNone(profit_kpi)
        self.assertEqual(profit_kpi["unit"], "₹")
        self.assertTrue(profit_kpi["formatted_value"].startswith("₹"))

        units_kpi = next((k for k in kpis if "units" in k["label"].lower() or "sold" in k["label"].lower()), None)
        if units_kpi:
            self.assertEqual(units_kpi["unit"], "units")
            self.assertTrue("units" in units_kpi["formatted_value"])

    def test_universal_stats_with_units(self):
        """Test universal descriptive statistics include unit and currency symbol."""
        df = pd.DataFrame({
            "revenue": [1000.0, 2000.0, 3000.0, 4000.0],
            "churn_pct": [2.5, 3.1, 1.8, 4.0],
        })
        stats = compute_universal_statistics(df)
        self.assertIn("revenue", stats["numeric_statistics"])
        self.assertIn("churn_pct", stats["numeric_statistics"])

        self.assertEqual(stats["numeric_statistics"]["revenue"]["unit"], "₹")
        self.assertEqual(stats["numeric_statistics"]["revenue"]["currency_symbol"], "₹")
        self.assertEqual(stats["numeric_statistics"]["churn_pct"]["unit"], "%")


if __name__ == "__main__":
    unittest.main()
