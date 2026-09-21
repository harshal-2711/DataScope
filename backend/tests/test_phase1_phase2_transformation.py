"""Tests for Phase 1 & Phase 2 transformation:
- Robust file parsing (encodings, delimiters, duplicate headers, malformed rows)
- Universal 12-type semantic inference (preventing phone/zip misclassification, currency, duration, dates)
- Dataset grain detection (row count vs entity count, guardrails)
- Government Procurement domain blueprint & decision dashboard
- Chart engine strict hierarchy (no pie charts for duration or averages, rich analytical metadata)
"""
from __future__ import annotations

import unittest
import pandas as pd
import numpy as np

from app.domains.registry import get_blueprint_by_id
from app.domains.base import ChartRule
from app.services.file_parser import parse_tabular_file
from app.services.type_inference import infer_column_type, infer_dataset_types
from app.services.grain_engine import detect_dataset_grain
from app.services.chart_engine import generate_domain_charts
from app.services.business_analytics_engine import generate_decision_dashboard
from app.services.domain_detector import detect_domain
from app.services.column_profiler import profile_dataset


class TestPhase1Phase2Transformation(unittest.TestCase):

    def test_file_parser_delimiters_and_duplicates(self):
        # Semicolon separated, duplicate column 'Amount'
        csv_data = "Tender_ID;Buyer;Amount;Amount\nT-101;Ministry of Health;50000;50000\nT-102;Ministry of Transport;120000;120000\n".encode("utf-8")
        df, diag = parse_tabular_file(csv_data, "tenders.csv", "csv")
        self.assertEqual(len(df), 2)
        self.assertEqual(diag.delimiter_used, ";")
        self.assertEqual(len(diag.duplicate_columns_renamed), 1)
        self.assertIn("Amount_1", df.columns)

    def test_file_parser_latin1_encoding(self):
        csv_data = "City,Description\nMünchen,Bavaria\nZürich,Switzerland\n".encode("latin1")
        df, diag = parse_tabular_file(csv_data, "cities.csv", "csv")
        self.assertEqual(len(df), 2)
        self.assertIn(diag.encoding_used, ("utf-8", "latin1", "cp1252"))

    def test_type_inference_all_12_types(self):
        data = {
            "int_col": [1, 2, 3, 4, 5],
            "float_col": [1.25, 2.5, 3.75, 4.1, 5.9],
            "bool_col": ["True", "False", "True", "False", "True"],
            "text_col": ["Notes about tender A", "Notes about tender B", "Details on item C", "Review on D", "Final notes E"],
            "cat_col": ["High", "Medium", "Low", "Medium", "High"],
            "id_col": ["TND-001", "TND-002", "TND-003", "TND-004", "TND-005"],
            "date_col": ["2024-01-15", "2024-02-20", "2024-03-25", "2024-04-10", "2024-05-01"],
            "datetime_col": ["2024-01-15 14:30:00", "2024-02-20 09:15:00", "2024-03-25 18:45:00", "2024-04-10 11:00:00", "2024-05-01 16:20:00"],
            "duration_col": ["15 days", "30 days", "45 days", "60 days", "90 days"],
            "percentage_col": ["12.5%", "25.0%", "50.0%", "75.0%", "95.0%"],
            "currency_col": ["$1,200", "$3,500", "$10,000", "$25,000", "$50,000"],
            "timestamp_col": [1704067200, 1704153600, 1704240000, 1704326400, 1704412800],
        }
        df = pd.DataFrame(data)
        inferences = {inf.name: inf for inf in infer_dataset_types(df)}

        self.assertEqual(inferences["int_col"].inferred_type, "Integer")
        self.assertEqual(inferences["float_col"].inferred_type, "Float")
        self.assertEqual(inferences["bool_col"].inferred_type, "Boolean")
        self.assertEqual(inferences["text_col"].inferred_type, "Text")
        self.assertEqual(inferences["cat_col"].inferred_type, "Category")
        self.assertEqual(inferences["id_col"].inferred_type, "Identifier")
        self.assertEqual(inferences["date_col"].inferred_type, "Date")
        self.assertEqual(inferences["datetime_col"].inferred_type, "Datetime")
        self.assertEqual(inferences["duration_col"].inferred_type, "Duration")
        self.assertEqual(inferences["percentage_col"].inferred_type, "Percentage")
        self.assertEqual(inferences["currency_col"].inferred_type, "Currency")
        self.assertEqual(inferences["timestamp_col"].inferred_type, "Timestamp")

    def test_type_inference_phone_and_zip_not_date(self):
        phones = pd.Series(["555-123-4567", "555-987-6543", "555-456-7890", "555-234-5678", "555-876-5432"], name="phone_number")
        inf_phone = infer_column_type(phones, len(phones))
        self.assertNotEqual(inf_phone.inferred_type, "Date")
        self.assertNotEqual(inf_phone.inferred_type, "Datetime")

        zips = pd.Series(["90210", "10001", "94105", "60601", "30301"], name="postal_code")
        inf_zip = infer_column_type(zips, len(zips))
        self.assertNotEqual(inf_zip.inferred_type, "Date")

    def test_grain_detection_tender_and_repeated_entities(self):
        data = {
            "tender_id": ["T-1", "T-1", "T-2", "T-3", "T-3"],  # Repeated lines per tender
            "buyer": ["Agency A", "Agency A", "Agency B", "Agency C", "Agency C"],
            "tender_value": [10000, 15000, 50000, 30000, 20000],
            "tender_duration": [30, 30, 60, 45, 45],
            "procurement_method": ["Open", "Open", "Direct", "Open", "Open"],
            "bids_received": [3, 3, 1, 4, 4],
        }
        df = pd.DataFrame(data)
        grain = detect_dataset_grain(df)

        self.assertEqual(grain.grain_type, "one_row_per_tender")
        self.assertEqual(grain.row_count, 5)
        self.assertEqual(grain.unique_entity_count, 3)
        self.assertFalse(grain.is_one_to_one)
        self.assertGreater(grain.repetition_ratio, 0.0)
        self.assertTrue(any("double-counting" in g for g in grain.aggregation_guardrails))

    def test_government_procurement_blueprint_and_dashboard(self):
        bp = get_blueprint_by_id("government_procurement")
        self.assertIsNotNone(bp)
        self.assertEqual(bp.name, "Government Procurement")

        data = {
            "tender_id": [f"T-{i}" for i in range(1, 21)],
            "buyer": ["Health Dept", "Transport Agency", "Education Board", "Defense Org"] * 5,
            "tender_value": [10000 * i for i in range(1, 21)],
            "tender_duration": [15 + (i * 5) for i in range(1, 21)],
            "procurement_method": ["Open Tender", "Restricted Tender", "Direct Award", "Open Tender"] * 5,
            "bids_received": [1, 2, 3, 4] * 5,
            "category": ["IT Equipment", "Medical Supplies", "Construction", "Consulting"] * 5,
        }
        df = pd.DataFrame(data)
        profiles = profile_dataset(df)
        domain = detect_domain(df, profiles)

        self.assertEqual(domain.domain_id, "government_procurement")
        dashboard = generate_decision_dashboard(df, domain, profiles)
        self.assertEqual(dashboard.domain_name, "Government Procurement")
        self.assertTrue(dashboard.executive_summary.is_available)
        self.assertGreater(len(dashboard.executive_summary.metrics), 3)

    def test_chart_engine_strictly_forbids_pie_charts_on_duration_and_averages(self):
        data = {
            "category": ["IT", "Medical", "Construction", "Consulting", "Transport", "Security"],
            "avg_duration": [45.2, 80.5, 120.0, 30.1, 65.4, 90.0],
        }
        df = pd.DataFrame(data)

        # Rule requests pie chart for duration average
        rule = ChartRule(
            id="test_pie_duration",
            title="Share of Average Tender Duration by Category",
            chart_type="pie",  # Specifically requesting pie!
            dimension_patterns=("category",),
            metric_patterns=("avg_duration",),
            aggregation="mean",
            business_question="What is the average duration across categories?",
        )

        charts = generate_domain_charts(df, [(rule, "category", "avg_duration")])
        self.assertEqual(len(charts), 1)
        # Chart engine MUST convert pie to bar because it's a duration/average!
        self.assertEqual(charts[0].chart_type, "bar")
        self.assertIsNotNone(charts[0].analytical_question)
        self.assertIsNotNone(charts[0].unit)
        self.assertIsNotNone(charts[0].dataset_grain)
        self.assertIsNotNone(charts[0].explanation)
        self.assertIsNotNone(charts[0].limitations)


if __name__ == "__main__":
    unittest.main()
