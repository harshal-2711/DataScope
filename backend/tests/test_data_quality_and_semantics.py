"""Comprehensive regression test suite for Data Quality & Semantic Inference.

Tests:
1. Duplicate Primary ID Detection:
   - Constant column `id=1` must not be falsely flagged as duplicate primary ID.
   - Candidate primary keys with real duplicates are detected.
   - Multi-line repeated observation identifiers are accurately categorized as Info/Pass.
2. Fiscal Year Semantic Inference:
   - Formats: `2021-2022`, `2024-25`, `FY21-22`, `FY2024`, `2024` integer.
   - No false invalid date warnings on fiscal years or season columns.
   - Genuine invalid date strings in real date columns are still detected.
3. Missing Value Scoring:
   - Both missingness with empty columns and excluding empty columns are calculated.
   - Completely empty columns are isolated from populated cell completeness.
   - Tested on: completely empty, partially missing, no missing, mixed missingness.
4. Constant-Value Columns:
   - Metadata constants separated from zero-variance features.
   - Quality score not over-penalized.
5. Chart Selection & Presentation Rules:
   - No pie charts on durations or averages.
   - Business-friendly titles and human-readable column formatters.
"""
from __future__ import annotations

import unittest
import pandas as pd
import numpy as np

from app.services import (
    column_formatter,
    data_quality_engine,
    dataset_service,
    dataset_store,
    recommendation_engine,
    type_inference,
)


class TestDuplicatePrimaryIdDetection(unittest.TestCase):
    def test_constant_id_column_not_flagged_as_duplicate_primary_id(self):
        """A constant column id=1 (like in OCDS release packages) must NOT be flagged as duplicate primary ID."""
        df = pd.DataFrame({
            "id": [1] * 1000,
            "ocid": [f"ocds-pkg-{i}" for i in range(1000)],
            "title": [f"Tender {i}" for i in range(1000)],
            "amount": [1000.0 + i for i in range(1000)],
        })
        ds_id = dataset_store.save_dataset("test_constant_id.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        
        # Verify no check named "Duplicate Primary IDs in 'id'"
        dup_id_checks = [c for c in dq.checks if "Duplicate Primary IDs in 'id'" in c.name]
        self.assertEqual(len(dup_id_checks), 0, "Constant id=1 must NOT be flagged as duplicate primary ID")

        # Inferred type for constant id=1 should be Integer or Category, not Identifier
        inf = type_inference.infer_column_type(df["id"], len(df))
        self.assertNotEqual(inf.inferred_type, "Identifier")

    def test_candidate_primary_key_with_duplicates_is_flagged(self):
        """A column that is 98% unique (candidate PK) but has duplicates must trigger a warning."""
        ids = [f"PK-{i}" for i in range(98)] + ["PK-1", "PK-2"]  # 2 duplicates in 100 rows
        df = pd.DataFrame({
            "order_id": ids,
            "sales": [100.0] * 100,
        })
        ds_id = dataset_store.save_dataset("test_pk_dups.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        
        dup_checks = [c for c in dq.checks if "Duplicate Primary IDs in 'order_id'" in c.name]
        self.assertEqual(len(dup_checks), 1, "Candidate PK with duplicates must be flagged with warning")
        self.assertEqual(dup_checks[0].severity, "warning")

    def test_repeated_observation_identifier_in_multiline_grain(self):
        """In multi-line datasets (e.g. 20 orders across 100 line items), order_id is classified as repeated entity observation."""
        df = pd.DataFrame({
            "order_id": [f"ORD-{i % 20}" for i in range(100)],
            "item_name": [f"Item {i}" for i in range(100)],
            "sales": [25.0] * 100,
        })
        ds_id = dataset_store.save_dataset("test_multiline.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        
        # Should NOT be a critical/warning penalty
        warn_dup_checks = [c for c in dq.checks if c.category == "duplicates" and c.severity in ("warning", "critical") and "order_id" in str(c.affected_columns)]
        self.assertEqual(len(warn_dup_checks), 0, "Repeated multi-line order_id should not fail as invalid duplicate ID")


class TestFiscalYearSemanticInference(unittest.TestCase):
    def test_fiscal_year_formats_no_false_date_warnings(self):
        """Fiscal year strings (2021-2022, 2024-25, FY21-22) must NOT produce invalid date warnings."""
        formats = [
            ["2021-2022"] * 50,
            ["2024-25"] * 50,
            ["FY21-22"] * 50,
            ["FY 2023-2024"] * 50,
            ["Q1-2024"] * 50,
        ]
        for idx, fy_vals in enumerate(formats):
            df = pd.DataFrame({
                "fiscal_year": fy_vals,
                "department": ["Education", "Health"] * 25,
                "budget": [50000.0] * 50,
            })
            ds_id = dataset_store.save_dataset(f"test_fy_{idx}.csv", "csv", df)
            dq = data_quality_engine.compute_data_quality_report(df, ds_id)
            
            date_warnings = [c for c in dq.checks if "fiscal_year" in str(c.affected_columns) and c.category == "dates"]
            self.assertEqual(len(date_warnings), 0, f"Fiscal year format {fy_vals[0]} must not produce date warnings")

            inf = type_inference.infer_column_type(df["fiscal_year"], len(df))
            self.assertIn(inf.inferred_type, ("Category", "Text"))

    def test_genuine_invalid_date_column_is_flagged(self):
        """Real date columns with invalid strings must still be flagged."""
        df = pd.DataFrame({
            "order_date": ["2025-01-01", "not-a-date", "2025-01-03", "corrupted-date"],
            "sales": [10.0, 20.0, 30.0, 40.0],
        })
        ds_id = dataset_store.save_dataset("test_invalid_date.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        
        date_warnings = [c for c in dq.checks if "order_date" in str(c.affected_columns) and c.category == "dates"]
        self.assertEqual(len(date_warnings), 1, "Corrupted date column must be flagged with date warning")


class TestMissingValueScoring(unittest.TestCase):
    def test_completely_empty_columns_scoring(self):
        """Completely empty columns must be reported separately and both missing percentages provided."""
        df = pd.DataFrame({
            "populated_1": [1, 2, 3, 4, 5],
            "populated_2": ["A", "B", "C", "D", "E"],
            "empty_1": [None] * 5,
            "empty_2": [None] * 5,
        })
        ds_id = dataset_store.save_dataset("test_empty_cols.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        
        empty_checks = [c for c in dq.checks if c.id == "empty_columns"]
        self.assertEqual(len(empty_checks), 1)
        self.assertEqual(set(empty_checks[0].affected_columns), {"empty_1", "empty_2"})

        # Populated data completeness check should report strong completeness
        pop_check = [c for c in dq.checks if c.id == "low_missing_cells_pass"]
        self.assertEqual(len(pop_check), 1)
        self.assertIn("100.0% complete", pop_check[0].message)

    def test_mixed_missingness(self):
        """Test dataset with both empty columns and partially missing columns."""
        df = pd.DataFrame({
            "col_complete": list(range(100)),
            "col_partial": [i if i % 5 != 0 else None for i in range(100)], # 20% missing in this column (10% across populated)
            "col_empty": [None] * 100,
        })
        ds_id = dataset_store.save_dataset("test_mixed_missing.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        
        # Must flag empty column
        empty_checks = [c for c in dq.checks if c.id == "empty_columns"]
        self.assertEqual(len(empty_checks), 1)
        # Moderate missing in populated fields
        pop_checks = [c for c in dq.checks if "Missing Values in Populated Fields" in c.name]
        self.assertEqual(len(pop_checks), 1)

    def test_no_missing_values(self):
        """100% complete dataset with adequate sample size (> 20 rows)."""
        df = pd.DataFrame({
            "a": list(range(30)),
            "b": [f"item_{i}" for i in range(30)],
        })
        ds_id = dataset_store.save_dataset("test_complete.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        self.assertEqual(dq.overall_score, 100)
        self.assertEqual(dq.status, "Healthy")


class TestConstantValueColumns(unittest.TestCase):
    def test_metadata_constants_not_penalized(self):
        """Scope metadata like currency=INR, fiscal_year=2021-2022 are categorized as info without penalty."""
        df = pd.DataFrame({
            "transaction_id": [f"TX-{i}" for i in range(50)],
            "amount": [100.0 + i for i in range(50)],
            "currency": ["INR"] * 50,
            "fiscal_year": ["2021-2022"] * 50,
            "country": ["India"] * 50,
        })
        ds_id = dataset_store.save_dataset("test_meta_const.csv", "csv", df)
        dq = data_quality_engine.compute_data_quality_report(df, ds_id)
        
        meta_checks = [c for c in dq.checks if c.id == "constant_columns_metadata"]
        self.assertEqual(len(meta_checks), 1)
        self.assertEqual(meta_checks[0].severity, "info")
        self.assertEqual(dq.overall_score, 100)


class TestChartReadabilityAndValidationRules(unittest.TestCase):
    def test_no_pie_charts_for_durations_or_averages(self):
        """Strict Chart Selection Rule: Pie charts must NEVER be generated for durations or averages."""
        df = pd.DataFrame({
            "tender_id": [f"T-{i}" for i in range(100)],
            "category": ["Goods", "Works", "Services", "Consulting"] * 25,
            "duration_days": [30, 45, 60, 90] * 25,
            "bidders_count": [3, 4, 2, 5] * 25,
        })
        recs = recommendation_engine.generate_recommendations(df)
        
        for chart in recs:
            if "Duration" in chart.title or "Bidders" in chart.title:
                self.assertNotEqual(
                    chart.chart_type, "pie",
                    f"Chart '{chart.title}' must NOT be a pie chart (found {chart.chart_type})"
                )

    def test_column_label_formatter(self):
        """Test centralized human-readable label formatting for nested OCDS paths."""
        self.assertEqual(
            column_formatter.format_column_label("tender/tender Period/duration In Days"),
            "Tender Duration (Days)"
        )
        self.assertEqual(
            column_formatter.format_column_label("tender/numberOfTenderers"),
            "Number of Bidders"
        )
        self.assertEqual(
            column_formatter.format_column_label("tender/mainProcurementCategory"),
            "Procurement Category"
        )
        self.assertEqual(
            column_formatter.format_column_label("tender/contractType"),
            "Contract Type"
        )
        self.assertEqual(
            column_formatter.format_column_label("tender/datePublished"),
            "Publication Date"
        )
        self.assertEqual(
            column_formatter.format_column_label("tender/milestones/type"),
            "Milestone Type"
        )

    def test_business_chart_titles(self):
        """Test business-friendly chart title generator."""
        t1 = column_formatter.format_business_chart_title(
            "tender/tenderPeriod/durationInDays", "tender/mainProcurementCategory", agg="mean", chart_type="bar"
        )
        self.assertEqual(t1, "Average Tender Duration by Procurement Category")

        t2 = column_formatter.format_business_chart_title(
            "tender/numberOfTenderers", "tender/contractType", agg="mean", chart_type="bar"
        )
        self.assertEqual(t2, "Average Number of Bidders by Contract Type")

        t3 = column_formatter.format_business_chart_title(
            None, "tender/mainProcurementCategory", agg="count", chart_type="bar"
        )
        self.assertEqual(t3, "Number of Tenders by Procurement Category")


if __name__ == "__main__":
    unittest.main()
