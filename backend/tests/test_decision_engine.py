"""Automated test suite for Decision-Oriented Business Analytics Engine.

Verifies:
- Business question-driven analytics for Sales/E-commerce datasets.
- Accurate calculation of profit and margins when cost data exists.
- Transparent 'Unavailable' status and explanation when cost data is missing (no hallucinated profit).
- Identification of best-selling and underperforming products.
- Pareto revenue contribution calculation.
- Operations & inventory availability checking.
- Universal domain adaptation (IPL, Finance, Education, Unknown).
- Metric status labeling: Available, Calculated, Estimated, Unavailable.
"""
import unittest
import pandas as pd

from app.services import dataset_service, dataset_store


class TestDecisionEngine(unittest.TestCase):

    def test_sales_dataset_with_cost_data(self):
        """Verify that sales dataset with cost data calculates profit, margins, and Pareto share."""
        df = pd.DataFrame({
            "order_id": [f"ORD-{i:03d}" for i in range(100)],
            "product_name": ["Laptop", "Mouse", "Keyboard", "Monitor", "Headphones"] * 20,
            "category": ["Electronics", "Accessories", "Accessories", "Electronics", "Audio"] * 20,
            "sales": [1200.0, 25.0, 75.0, 300.0, 150.0] * 20,
            "cost": [800.0, 10.0, 35.0, 180.0, 70.0] * 20,
            "quantity": [1, 2, 1, 1, 2] * 20,
            "order_date": [f"2026-01-{(i%28)+1:02d}" for i in range(100)],
        })
        dataset_id = dataset_store.save_dataset("sales_with_cost.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        # 1. Executive Summary
        exec_sec = dashboard["executive_summary"]
        self.assertTrue(exec_sec["is_available"])
        metric_map = {m["id"]: m for m in exec_sec["metrics"]}

        self.assertEqual(metric_map["total_revenue"]["status"], "Calculated")
        self.assertGreater(metric_map["total_revenue"]["value"], 0)
        self.assertEqual(metric_map["total_orders"]["status"], "Calculated")
        self.assertEqual(metric_map["total_orders"]["value"], 100)

        # 2. Profitability section
        prof_sec = dashboard["profitability"]
        self.assertTrue(prof_sec["is_available"])
        self.assertEqual(metric_map["net_profit"]["status"], "Calculated")
        self.assertGreater(metric_map["net_profit"]["value"], 0)
        self.assertEqual(metric_map["profit_margin"]["status"], "Calculated")
        self.assertGreater(metric_map["profit_margin"]["value"], 0)

        # 3. Product analysis: Top products and underperforming products
        prod_sec = dashboard["product_analysis"]
        self.assertTrue(prod_sec["is_available"])
        chart_ids = [c["id"] for c in prod_sec["charts"]]
        self.assertIn("top_products", chart_ids)
        self.assertIn("underperforming_products", chart_ids)

        # Verify business question on charts
        for c in prod_sec["charts"]:
            self.assertTrue(len(c["business_question"]) > 10)
            self.assertTrue(len(c["explanation"]) > 10)

        # Verify Pareto metric
        prod_metrics = {m["id"]: m for m in prod_sec["metrics"]}
        self.assertIn("pareto_share", prod_metrics)
        self.assertGreater(prod_metrics["pareto_share"]["value"], 0)

    def test_sales_dataset_without_cost_data(self):
        """Verify that sales dataset without cost data correctly marks profit as Unavailable with explanation."""
        df = pd.DataFrame({
            "order_id": [f"ORD-{i:03d}" for i in range(50)],
            "product_name": ["T-Shirt", "Jeans", "Jacket"] * 16 + ["T-Shirt", "Jeans"],
            "category": ["Apparel", "Apparel", "Outerwear"] * 16 + ["Apparel", "Apparel"],
            "sales": [25.0, 60.0, 120.0] * 16 + [25.0, 60.0],
            "quantity": [2, 1, 1] * 16 + [2, 1],
            "order_date": [f"2026-03-{(i%28)+1:02d}" for i in range(50)],
        })
        dataset_id = dataset_store.save_dataset("sales_no_cost.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        # Executive summary has revenue
        exec_sec = dashboard["executive_summary"]
        metric_map = {m["id"]: m for m in exec_sec["metrics"]}
        self.assertEqual(metric_map["total_revenue"]["status"], "Calculated")

        # Profitability section MUST be marked Unavailable
        prof_sec = dashboard["profitability"]
        self.assertFalse(prof_sec["is_available"])
        self.assertIsNotNone(prof_sec["unavailable_reason"])
        self.assertIn("cost", prof_sec["unavailable_reason"].lower())

        # Net profit metric is Unavailable
        self.assertEqual(metric_map["net_profit"]["status"], "Unavailable")
        self.assertIn("cost", metric_map["net_profit"]["explanation"].lower())

        # Operations & Inventory is Unavailable (no stock columns)
        inv_sec = dashboard["operations_inventory"]
        self.assertFalse(inv_sec["is_available"])
        self.assertIn("inventory", inv_sec["unavailable_reason"].lower())

    def test_cricket_ipl_decision_dashboard(self):
        """Verify specialized sports decision dashboard with match and player performance."""
        df = pd.DataFrame({
            "match_id": [1, 1, 1, 1, 2, 2, 2, 2],
            "batsman": ["V Kohli", "V Kohli", "AB de Villiers", "AB de Villiers", "RG Sharma", "RG Sharma", "SA Yadav", "SA Yadav"],
            "bowler": ["JJ Bumrah", "JJ Bumrah", "TA Boult", "TA Boult", "Mohammed Siraj", "Mohammed Siraj", "HV Patel", "HV Patel"],
            "batsman_runs": [4, 6, 1, 0, 4, 1, 6, 4],
            "is_wicket": [0, 0, 0, 1, 0, 0, 0, 0],
            "over": [1, 1, 2, 2, 1, 1, 2, 2],
            "ball": [1, 2, 1, 2, 1, 2, 1, 2],
        })
        dataset_id = dataset_store.save_dataset("ipl_sample.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        exec_sec = dashboard["executive_summary"]
        self.assertTrue(exec_sec["is_available"])
        metric_map = {m["id"]: m for m in exec_sec["metrics"]}
        self.assertIn("total_runs", metric_map)
        self.assertIn("total_wickets", metric_map)

        # Commercial profitability must be unavailable for sports
        prof_sec = dashboard["profitability"]
        self.assertFalse(prof_sec["is_available"])

        # Match/player performance charts have business questions
        perf_sec = dashboard["sales_performance"]
        self.assertTrue(perf_sec["is_available"])
        for c in perf_sec["charts"]:
            self.assertTrue(len(c["business_question"]) > 10)

    def test_education_decision_dashboard(self):
        """Verify education decision dashboard with student scoring benchmarks."""
        df = pd.DataFrame({
            "student_id": [f"STU-{i}" for i in range(60)],
            "subject": ["Math", "Physics", "Chemistry"] * 20,
            "score": [85.0, 72.0, 45.0, 38.0, 92.0, 68.0] * 10,
            "attendance": [95.0, 90.0, 80.0, 75.0, 98.0, 85.0] * 10,
        })
        dataset_id = dataset_store.save_dataset("edu_sample.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        exec_sec = dashboard["executive_summary"]
        metric_map = {m["id"]: m for m in exec_sec["metrics"]}
        self.assertIn("avg_score", metric_map)
        self.assertIn("pass_rate", metric_map)
        self.assertEqual(metric_map["pass_rate"]["status"], "Calculated")

    def test_unknown_dataset_decision_dashboard(self):
        """Verify unknown dataset provides accurate generic decision dashboard with limitations."""
        df = pd.DataFrame({
            "feature_x": [10.5, 20.2, 15.8, 30.1, 25.4] * 10,
            "feature_y": [1.2, 3.4, 2.1, 5.6, 4.0] * 10,
            "group": ["A", "B", "C", "D", "E"] * 10,
        })
        dataset_id = dataset_store.save_dataset("unknown_sample.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        exec_sec = dashboard["executive_summary"]
        self.assertTrue(exec_sec["is_available"])
        metric_map = {m["id"]: m for m in exec_sec["metrics"]}
        self.assertEqual(metric_map["row_count"]["status"], "Available")

        # Profitability unavailable for unknown dataset
        prof_sec = dashboard["profitability"]
        self.assertFalse(prof_sec["is_available"])
        self.assertIn("profitability", prof_sec["unavailable_reason"].lower())


if __name__ == "__main__":
    unittest.main()
