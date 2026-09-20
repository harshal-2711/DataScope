"""Comprehensive multi-domain regression test suite for DataScope Universal Platform.

Tests:
1. IPL match-level dataset
2. IPL ball-by-ball dataset
3. Sales & Retail dataset
4. Finance & Banking dataset
5. Healthcare & Hospital dataset
6. Education & Academic dataset
7. Movies & Entertainment dataset
8. Music & Streaming dataset
9. Unknown / Arbitrary tabular dataset
10. Universal statistics calculations (mean, median, mode, percentiles, correlation)
11. Analysis Validation & Quality Checker (Valid, Needs Review, Unsupported)
"""
from __future__ import annotations

import unittest
import pandas as pd

from app.services import dataset_service, dataset_store
from app.services.analysis_validator import run_analysis_quality_check, validate_kpi
from app.services.column_profiler import profile_dataset
from app.services.domain_detector import detect_domain
from app.services.sports_cricket_service import (
    compute_cricket_ball_analytics,
    compute_cricket_match_analytics,
    detect_cricket_dataset_type,
)
from app.services.universal_stats import compute_universal_statistics


class TestUniversalPlatform(unittest.TestCase):
    """Test suite verifying multi-domain intelligence, universal statistics, and validation."""

    def test_ipl_match_level_dataset(self):
        """Verify specialized IPL match-level analytics and validation."""
        df = pd.DataFrame({
            "id": list(range(1, 61)),
            "season": [2024] * 60,
            "city": ["Mumbai", "Chennai", "Bengaluru", "Kolkata", "Delhi"] * 12,
            "team1": ["Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bengaluru", "Kolkata Knight Riders"] * 15,
            "team2": ["Mumbai Indians", "Kolkata Knight Riders", "Chennai Super Kings", "Delhi Capitals"] * 15,
            "toss_winner": ["Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bengaluru", "Kolkata Knight Riders"] * 15,
            "toss_decision": ["bat", "field", "field", "bat"] * 15,
            "winner": ["Chennai Super Kings", "Mumbai Indians", "Chennai Super Kings", "Kolkata Knight Riders"] * 15,
            "result_margin": [20, 5, 8, 14] * 15,
            "player_of_match": ["MS Dhoni", "Rohit Sharma", "Virat Kohli", "Andre Russell"] * 15,
            "venue": ["Wankhede Stadium", "MA Chidambaram Stadium", "M Chinnaswamy Stadium", "Eden Gardens"] * 15,
        })
        dataset_id = dataset_store.save_dataset("ipl_matches_2024.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertEqual(intel["domain"]["domain_id"], "sports")
        self.assertIn("Cricket", intel["domain"]["name"])

        # Check cricket-specific KPIs
        kpi_names = [k["name"] for k in intel["kpis"]]
        self.assertTrue(any("Matches Played" in name for name in kpi_names))
        self.assertTrue(any("Toss Advantage" in name for name in kpi_names))

        # Check cricket-specific charts
        chart_titles = [c["title"] for c in intel["charts"]]
        self.assertTrue(any("Wins by Team" in title for title in chart_titles))
        self.assertTrue(any("Toss Decision" in title for title in chart_titles))

        # Verify validation report status
        val = intel["validation_report"]
        self.assertIn(val["overall_status"], ("Valid", "Needs Review"))

    def test_ipl_ball_by_ball_dataset(self):
        """Verify specialized IPL ball-by-ball analytics and over-wise trends."""
        df = pd.DataFrame({
            "match_id": [1] * 120,
            "inning": [1] * 120,
            "batting_team": ["Chennai Super Kings"] * 120,
            "bowling_team": ["Mumbai Indians"] * 120,
            "over": [i // 6 + 1 for i in range(120)],
            "ball": [i % 6 + 1 for i in range(120)],
            "batsman": ["Ruturaj Gaikwad", "Devon Conway"] * 60,
            "bowler": ["Jasprit Bumrah", "Trent Boult"] * 60,
            "batsman_runs": [1, 4, 0, 6, 2, 0] * 20,
            "extra_runs": [0] * 120,
            "total_runs": [1, 4, 0, 6, 2, 0] * 20,
            "is_wicket": [0, 0, 0, 0, 0, 1] * 20,
            "dismissal_kind": [None, None, None, None, None, "caught"] * 20,
        })
        cricket_type = detect_cricket_dataset_type(df)
        self.assertEqual(cricket_type, "ball_by_ball")

        dataset_id = dataset_store.save_dataset("ipl_deliveries.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertEqual(intel["domain"]["domain_id"], "sports_performance")
        self.assertIn("Ball-by-Ball", intel["domain"]["name"])

        # Check top batsmen & bowler charts
        chart_titles = [c["title"] for c in intel["charts"]]
        self.assertTrue(any("Run Scorers" in title for title in chart_titles))
        self.assertTrue(any("Wicket Takers" in title for title in chart_titles))
        self.assertTrue(any("Run Rate" in title for title in chart_titles))

    def test_retail_sales_dataset(self):
        """Verify Sales and Retail dataset analytics."""
        df = pd.DataFrame({
            "order_id": [f"ORD-{i}" for i in range(100)],
            "customer_id": [f"CUST-{i%20}" for i in range(100)],
            "category": ["Electronics", "Clothing", "Furniture", "Books"] * 25,
            "sales": [120.50, 45.00, 310.00, 15.99] * 25,
            "quantity": [1, 2, 1, 3] * 25,
            "discount": [10.0, 0.0, 25.0, 0.0] * 25,
            "order_date": [f"2026-02-{i%28+1:02d}" for i in range(100)],
        })
        dataset_id = dataset_store.save_dataset("retail_sales.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertIn(intel["domain"]["domain_id"], ("ecommerce", "retail", "general_business"))
        self.assertGreater(len(intel["kpis"]), 0)
        self.assertGreater(len(intel["charts"]), 0)

    def test_finance_banking_dataset(self):
        """Verify Finance and Banking dataset analytics."""
        df = pd.DataFrame({
            "account_number": [f"ACC-{i%10}" for i in range(100)],
            "debit_amount": [50.0, 0.0, 200.0, 0.0] * 25,
            "credit_amount": [0.0, 1500.0, 0.0, 450.0] * 25,
            "balance": [5000.0, 6500.0, 6300.0, 6750.0] * 25,
            "branch": ["North", "South", "East", "West"] * 25,
            "transaction_date": [f"2026-03-{i%28+1:02d}" for i in range(100)],
        })
        dataset_id = dataset_store.save_dataset("bank_ledger.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertIn(intel["domain"]["domain_id"], ("finance", "banking", "general_business"))
        self.assertGreater(len(intel["kpis"]), 0)

    def test_healthcare_dataset(self):
        """Verify Healthcare and Hospital dataset analytics."""
        df = pd.DataFrame({
            "patient_id": [f"PAT-{i}" for i in range(50)],
            "diagnosis": ["Cardiac", "Neurology", "Orthopedic", "Pediatric"] * 12 + ["Cardiac", "Neurology"],
            "los": [3, 5, 2, 1] * 12 + [4, 6],
            "charges": [4500.0, 8900.0, 3200.0, 1500.0] * 12 + [5000.0, 9200.0],
            "admission_date": [f"2026-01-{i%28+1:02d}" for i in range(50)],
        })
        dataset_id = dataset_store.save_dataset("hospital_admissions.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertIn(intel["domain"]["domain_id"], ("healthcare", "hospital_management"))
        self.assertGreater(len(intel["kpis"]), 0)

    def test_education_academic_dataset(self):
        """Verify Education and Student Performance analytics."""
        df = pd.DataFrame({
            "student_id": [f"STU-{i}" for i in range(60)],
            "gpa": [3.5, 3.8, 2.9, 3.2, 4.0, 2.5] * 10,
            "exam_score": [85, 92, 68, 79, 98, 55] * 10,
            "attendance": [95.0, 98.0, 82.0, 88.0, 99.0, 72.0] * 10,
            "department": ["Computer Science", "Physics", "Mathematics"] * 20,
        })
        dataset_id = dataset_store.save_dataset("students.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertIn(intel["domain"]["domain_id"], ("academic_performance", "education", "edtech"))
        self.assertGreater(len(intel["kpis"]), 0)

    def test_movies_entertainment_dataset(self):
        """Verify Movies and Entertainment box office analytics."""
        df = pd.DataFrame({
            "movie_id": [f"MOV-{i}" for i in range(40)],
            "title": [f"Movie Title {i}" for i in range(40)],
            "genre": ["Action", "Comedy", "Drama", "Sci-Fi"] * 10,
            "box_office": [150000000, 45000000, 80000000, 220000000] * 10,
            "budget": [80000000, 20000000, 30000000, 120000000] * 10,
            "rating": [7.8, 6.5, 8.2, 7.9] * 10,
        })
        dataset_id = dataset_store.save_dataset("box_office.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertEqual(intel["domain"]["domain_id"], "movies_entertainment")
        self.assertGreater(len(intel["kpis"]), 0)

    def test_music_streaming_dataset(self):
        """Verify Music and Streaming catalog analytics."""
        df = pd.DataFrame({
            "track_id": [f"TRK-{i}" for i in range(50)],
            "song_title": [f"Song {i}" for i in range(50)],
            "artist_name": ["Artist Alpha", "Artist Beta", "Artist Gamma"] * 16 + ["Artist Alpha", "Artist Beta"],
            "genre": ["Pop", "Rock", "Hip-Hop", "Jazz"] * 12 + ["Pop", "Rock"],
            "streams": [500000, 1200000, 340000, 80000] * 12 + [600000, 1400000],
        })
        dataset_id = dataset_store.save_dataset("music_catalog.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertEqual(intel["domain"]["domain_id"], "music")
        self.assertGreater(len(intel["kpis"]), 0)

    def test_unknown_dataset_universal_stats(self):
        """Verify that arbitrary/unknown datasets receive complete universal statistics."""
        df = pd.DataFrame({
            "param_alpha": [10.5, 12.3, 14.1, 11.2, 13.8, 100.0],  # has outlier 100
            "param_beta": [100.0, 105.0, 98.0, 102.0, 101.0, 99.0],
            "group_label": ["A", "B", "A", "B", "A", "C"],
        })
        stats = compute_universal_statistics(df)

        self.assertEqual(stats["dataset_summary"]["row_count"], 6)
        self.assertEqual(stats["dataset_summary"]["column_count"], 3)
        self.assertIn("param_alpha", stats["numeric_statistics"])
        self.assertIn("group_label", stats["categorical_statistics"])

        alpha_stats = stats["numeric_statistics"]["param_alpha"]
        self.assertIsNotNone(alpha_stats["mean"])
        self.assertIsNotNone(alpha_stats["median"])
        self.assertIsNotNone(alpha_stats["p25"])
        self.assertIsNotNone(alpha_stats["p75"])
        self.assertIsNotNone(alpha_stats["p90"])
        self.assertIsNotNone(alpha_stats["iqr"])
        self.assertIn("correlation_matrix", stats)

    def test_analysis_validator_flags_invalid_math(self):
        """Verify that analysis validator flags invalid percentages or mathematical states."""
        from app.schemas.domain_blueprint import DomainKpiSchema

        df = pd.DataFrame({"metric": [1, 2, 3]})
        # Invalid percentage > 100%
        kpi_bad = DomainKpiSchema(
            id="bad_pct",
            name="Bad Percentage",
            description="Invalid percentage",
            value=150.0,
            format="percentage",
            aggregation="mean",
            matched_columns=["metric"],
        )
        res = validate_kpi(kpi_bad, df)
        self.assertEqual(res.status, "Needs Review")
        self.assertIn("outside the expected 0-100%", res.reason)


if __name__ == "__main__":
    unittest.main()
