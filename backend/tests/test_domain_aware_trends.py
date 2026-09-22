"""Comprehensive Unit Tests for Domain-Aware Trends Intelligence.

Verifies:
1. Finance / Sales / E-Commerce:
   - Revenue decline is NOT called profit loss (Top-line sales vs net profit).
   - Profit increase/decrease correctly interpreted.
   - Expense/cost increase is potential concern, decrease is cost reduction.
   - Loss increase is loss worsening, decrease is loss reduction.
2. Sports:
   - Wins increase = improved performance.
   - Losses increase = performance concern.
   - Points/runs = scoring improvement.
3. Healthcare:
   - Patient count = patient volume trend.
   - Recovery rate increase = improved recovery rate.
   - Readmissions increase = potential concern.
   - Clinical safety: no medical diagnosis claims.
4. HR / Employee Analytics:
   - Headcount = workforce growth/decline.
   - Attrition increase = higher attrition / retention concern.
   - Salary = compensation increase.
   - Attendance decrease = attendance decline.
5. Education:
   - Student scores = academic performance improvement/decline.
   - Failure rate increase = potential academic concern.
6. Operations / Procurement:
   - Delivery time increase = slower delivery / turnaround delay.
   - Defect rate increase = quality concern.
   - Procurement cost increase = cost increase.
   - Order volume = volume growth.
7. General / Unknown Domains:
   - Neutral language: "The selected metric increased/decreased by X%".
   - No unsupported positive/negative assumptions.
"""
from __future__ import annotations

import unittest
import pandas as pd
import numpy as np

from app.services.trend_engine import compute_trends_intelligence
from app.services.trend_domain_interpreter import (
    classify_metric_semantic_role,
    interpret_domain_trend,
)
from app.schemas.domain_blueprint import DomainIdentitySchema


class TestDomainAwareTrends(unittest.TestCase):
    """Test suite for domain-aware trend interpretations."""

    # =========================================================================
    # 1. FINANCE / SALES / E-COMMERCE TESTS
    # =========================================================================
    def test_finance_revenue_decline_not_profit_loss(self):
        """Verify revenue decrease is interpreted as top-line sales decline and NEVER as profit loss."""
        dates = pd.date_range("2024-01-01", periods=10, freq="W")
        # Declining revenue from 5000 down to 1000
        df = pd.DataFrame({
            "order_date": dates,
            "revenue": [5000.0 - i * 400 for i in range(10)],
            "units_sold": [100 - i * 8 for i in range(10)],
        })
        res = compute_trends_intelligence(df, "test_rev_decline", metric="revenue")
        self.assertTrue(res.has_time_dimension)
        interp = res.domain_interpretation
        self.assertIsNotNone(interp)
        self.assertEqual(interp.direction, "decreasing")
        self.assertIn("Revenue", interp.metric_role)
        
        # Verify revenue decrease is NOT called profit loss
        summary_text = res.trend_summary.plain_english_summary.lower()
        context_text = interp.contextual_interpretation.lower()
        self.assertIn("revenue", context_text)
        self.assertNotIn("profit loss", context_text)
        self.assertNotIn("net loss", context_text)
        self.assertIn("top-line", context_text + " " + interp.qualification.lower() + " " + (interp.distinction_note or "").lower())
        self.assertEqual(interp.business_sentiment, "warning")

    def test_finance_revenue_growth_and_profit_distinction(self):
        """Verify Revenue increase is growth and Profit increase is profit improvement."""
        dates = pd.date_range("2024-01-01", periods=8, freq="MS")
        df = pd.DataFrame({
            "transaction_date": dates,
            "sales_amount": [1000.0 + i * 200 for i in range(8)],
            "net_profit": [200.0 + i * 50 for i in range(8)],
            "operating_expense": [800.0 + i * 150 for i in range(8)],
        })
        # Test Sales Revenue
        res_sales = compute_trends_intelligence(df, "test_sales", metric="sales_amount")
        self.assertEqual(res_sales.domain_interpretation.direction, "increasing")
        self.assertEqual(res_sales.domain_interpretation.business_sentiment, "positive")
        self.assertIn("Sales Growth", res_sales.domain_interpretation.contextual_interpretation)
        self.assertIn("Revenue", res_sales.domain_interpretation.metric_role)

        # Test Profit
        res_profit = compute_trends_intelligence(df, "test_profit", metric="net_profit")
        self.assertEqual(res_profit.domain_interpretation.direction, "increasing")
        self.assertEqual(res_profit.domain_interpretation.business_sentiment, "improvement")
        self.assertIn("Profit Improvement", res_profit.domain_interpretation.contextual_interpretation)
        self.assertIn("Profit", res_profit.domain_interpretation.metric_role)

    def test_finance_cost_and_loss_polarity(self):
        """Verify Expense increase is concern and Loss decrease is loss reduction."""
        dates = pd.date_range("2024-01-01", periods=6, freq="MS")
        df_cost_up = pd.DataFrame({
            "month_date": dates,
            "shipping_cost": [100.0 + i * 50 for i in range(6)],
        })
        res_cost = compute_trends_intelligence(df_cost_up, "test_cost", metric="shipping_cost")
        self.assertEqual(res_cost.domain_interpretation.direction, "increasing")
        self.assertEqual(res_cost.domain_interpretation.business_sentiment, "concern")
        self.assertIn("Cost Increase", res_cost.domain_interpretation.contextual_interpretation)

        df_loss_down = pd.DataFrame({
            "month_date": dates,
            "net_loss": [500.0 - i * 80 for i in range(6)],
        })
        res_loss = compute_trends_intelligence(df_loss_down, "test_loss", metric="net_loss")
        self.assertEqual(res_loss.domain_interpretation.direction, "decreasing")
        self.assertEqual(res_loss.domain_interpretation.business_sentiment, "improvement")
        self.assertIn("Loss Reduction", res_loss.domain_interpretation.contextual_interpretation)

    # =========================================================================
    # 2. SPORTS DOMAIN TESTS
    # =========================================================================
    def test_sports_wins_and_losses_interpretation(self):
        """Verify sports wins increase = improved performance and losses increase = performance concern."""
        domain_sports = DomainIdentitySchema(
            domain_id="sports_cricket",
            name="Cricket Analytics",
            description="Cricket match analytics",
            confidence=0.95,
        )
        dates = pd.date_range("2024-01-01", periods=10, freq="W")
        # Wins increasing
        df_wins = pd.DataFrame({
            "match_date": dates,
            "matches_won": [1, 2, 2, 3, 4, 4, 5, 6, 7, 8],
            "runs_scored": [120, 140, 150, 165, 180, 190, 200, 210, 220, 240],
        })
        res_wins = compute_trends_intelligence(df_wins, "test_sports_wins", metric="matches_won", domain=domain_sports)
        self.assertEqual(res_wins.domain_interpretation.business_sentiment, "improvement")
        self.assertIn("Improved Performance", res_wins.domain_interpretation.contextual_interpretation)

        # Runs scored increasing
        res_runs = compute_trends_intelligence(df_wins, "test_sports_runs", metric="runs_scored", domain=domain_sports)
        self.assertEqual(res_runs.domain_interpretation.business_sentiment, "improvement")
        self.assertIn("Scoring Improvement", res_runs.domain_interpretation.contextual_interpretation)

        # Defeats increasing
        df_losses = pd.DataFrame({
            "match_date": dates,
            "match_losses": [0, 1, 1, 2, 2, 3, 4, 5, 6, 7],
        })
        res_losses = compute_trends_intelligence(df_losses, "test_sports_losses", metric="match_losses", domain=domain_sports)
        self.assertEqual(res_losses.domain_interpretation.business_sentiment, "concern")
        self.assertIn("Performance Concern", res_losses.domain_interpretation.contextual_interpretation)

    # =========================================================================
    # 3. HEALTHCARE DOMAIN TESTS (Strict Clinical Safety)
    # =========================================================================
    def test_healthcare_patient_volume_recovery_readmission(self):
        """Verify healthcare interpretations and absence of clinical diagnosis claims."""
        domain_health = DomainIdentitySchema(
            domain_id="healthcare",
            name="Healthcare Clinical Operations",
            description="Hospital patient operations",
            confidence=0.90,
        )
        dates = pd.date_range("2024-01-01", periods=6, freq="MS")
        df_health = pd.DataFrame({
            "admission_date": dates,
            "patient_count": [120, 140, 160, 180, 200, 220],
            "recovery_rate": [75.0, 78.0, 80.0, 82.0, 85.0, 88.0],
            "readmission_rate": [12.0, 14.0, 15.0, 16.0, 18.0, 20.0],
        })

        # Patient Volume
        res_vol = compute_trends_intelligence(df_health, "test_h_vol", metric="patient_count", domain=domain_health)
        self.assertIn("Patient Volume", res_vol.domain_interpretation.metric_role)
        self.assertIn("Patient Volume Expansion", res_vol.domain_interpretation.contextual_interpretation)
        # Check clinical safety guardrail
        self.assertIn("Guardrail", res_vol.domain_interpretation.qualification)
        self.assertNotIn("diagnos", res_vol.domain_interpretation.contextual_interpretation.lower())

        # Recovery Rate
        res_rec = compute_trends_intelligence(df_health, "test_h_rec", metric="recovery_rate", domain=domain_health)
        self.assertIn("Improved Recovery Rate", res_rec.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_rec.domain_interpretation.business_sentiment, "improvement")

        # Readmission Rate (increasing is a concern)
        res_readm = compute_trends_intelligence(df_health, "test_h_readm", metric="readmission_rate", domain=domain_health)
        self.assertIn("Readmission Escalation", res_readm.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_readm.domain_interpretation.business_sentiment, "concern")

    # =========================================================================
    # 4. HR / EMPLOYEE ANALYTICS TESTS
    # =========================================================================
    def test_hr_headcount_attrition_salary_attendance(self):
        """Verify HR metrics: headcount growth, attrition concern, salary expansion, attendance decline."""
        domain_hr = DomainIdentitySchema(
            domain_id="people_hr",
            name="Human Resources & People Analytics",
            description="Workforce operations",
            confidence=0.92,
        )
        dates = pd.date_range("2024-01-01", periods=6, freq="MS")
        df_hr = pd.DataFrame({
            "event_date": dates,
            "headcount": [100, 110, 120, 135, 150, 165],
            "attrition_rate": [2.1, 2.5, 3.0, 3.8, 4.5, 5.2],
            "salary": [60000, 62000, 64000, 65000, 68000, 70000],
            "attendance_rate": [98.0, 96.5, 95.0, 93.0, 91.0, 89.0],
        })

        # Headcount growth
        res_hc = compute_trends_intelligence(df_hr, "test_hc", metric="headcount", domain=domain_hr)
        self.assertIn("Workforce Growth", res_hc.domain_interpretation.contextual_interpretation)

        # Attrition increase (concern)
        res_att = compute_trends_intelligence(df_hr, "test_att", metric="attrition_rate", domain=domain_hr)
        self.assertIn("Higher Attrition", res_att.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_att.domain_interpretation.business_sentiment, "concern")

        # Salary increase
        res_sal = compute_trends_intelligence(df_hr, "test_sal", metric="salary", domain=domain_hr)
        self.assertIn("Compensation Increase", res_sal.domain_interpretation.contextual_interpretation)

        # Attendance decrease (concern)
        res_attend = compute_trends_intelligence(df_hr, "test_attend", metric="attendance_rate", domain=domain_hr)
        self.assertIn("Attendance Decline", res_attend.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_attend.domain_interpretation.business_sentiment, "concern")

    # =========================================================================
    # 5. EDUCATION DOMAIN TESTS
    # =========================================================================
    def test_education_student_performance_and_failure_rate(self):
        """Verify Education metrics: student performance improvement and failure rate escalation."""
        domain_edu = DomainIdentitySchema(
            domain_id="education",
            name="Academic Education",
            description="Student learning analytics",
            confidence=0.92,
        )
        dates = pd.date_range("2024-01-01", periods=6, freq="MS")
        df_edu = pd.DataFrame({
            "semester_date": dates,
            "gpa": [2.8, 3.0, 3.2, 3.3, 3.5, 3.7],
            "failure_rate": [15.0, 18.0, 20.0, 22.0, 25.0, 28.0],
        })

        # GPA performance improvement
        res_gpa = compute_trends_intelligence(df_edu, "test_gpa", metric="gpa", domain=domain_edu)
        self.assertIn("Academic Performance Improvement", res_gpa.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_gpa.domain_interpretation.business_sentiment, "improvement")

        # Failure rate increase (concern)
        res_fail = compute_trends_intelligence(df_edu, "test_fail", metric="failure_rate", domain=domain_edu)
        self.assertIn("Potential Academic Concern", res_fail.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_fail.domain_interpretation.business_sentiment, "concern")

    # =========================================================================
    # 6. OPERATIONS / PROCUREMENT DOMAIN TESTS
    # =========================================================================
    def test_operations_procurement_metrics(self):
        """Verify Operations: delivery time, defect rate, procurement cost, and order volume."""
        domain_ops = DomainIdentitySchema(
            domain_id="procurement",
            name="Operations & Procurement",
            description="Supply chain and purchasing",
            confidence=0.94,
        )
        dates = pd.date_range("2024-01-01", periods=6, freq="MS")
        df_ops = pd.DataFrame({
            "order_date": dates,
            "delivery_time": [2.0, 2.5, 3.2, 4.0, 5.1, 6.0],  # Slower delivery
            "defect_rate": [1.0, 1.2, 1.5, 2.0, 2.8, 3.5],    # Higher defect rate
            "procurement_cost": [10000, 12000, 15000, 18000, 20000, 25000],
            "order_volume": [500, 600, 750, 900, 1100, 1300],
        })

        # Slower delivery (concern)
        res_deliv = compute_trends_intelligence(df_ops, "test_deliv", metric="delivery_time", domain=domain_ops)
        self.assertIn("Slower Delivery", res_deliv.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_deliv.domain_interpretation.business_sentiment, "concern")

        # Defect rate increase (quality concern)
        res_defect = compute_trends_intelligence(df_ops, "test_defect", metric="defect_rate", domain=domain_ops)
        self.assertIn("Quality Concern", res_defect.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_defect.domain_interpretation.business_sentiment, "concern")

        # Procurement cost increase (concern)
        res_proc = compute_trends_intelligence(df_ops, "test_proc", metric="procurement_cost", domain=domain_ops)
        self.assertIn("Procurement Cost Increase", res_proc.domain_interpretation.contextual_interpretation)

        # Order volume increase (volume growth)
        res_ord = compute_trends_intelligence(df_ops, "test_ord", metric="order_volume", domain=domain_ops)
        self.assertIn("Volume Growth", res_ord.domain_interpretation.contextual_interpretation)
        self.assertEqual(res_ord.domain_interpretation.business_sentiment, "improvement")

    # =========================================================================
    # 7. GENERAL / UNKNOWN DOMAIN TESTS (Strict Neutral Wording)
    # =========================================================================
    def test_general_unknown_domain_neutral_phrasing(self):
        """Verify general/unknown datasets use strictly neutral phrasing without positive/negative bias."""
        domain_unknown = DomainIdentitySchema(
            domain_id="general_unknown",
            name="General / Unknown",
            description="Unidentified domain",
            confidence=0.20,
        )
        dates = pd.date_range("2024-01-01", periods=6, freq="MS")
        df_unk = pd.DataFrame({
            "timestamp": dates,
            "sensor_alpha": [10.5, 14.2, 18.0, 22.1, 26.5, 30.0],
        })
        res = compute_trends_intelligence(df_unk, "test_unk", metric="sensor_alpha", domain=domain_unknown)
        interp = res.domain_interpretation
        self.assertIsNotNone(interp)
        self.assertEqual(interp.business_sentiment, "neutral")
        self.assertEqual(interp.confidence_level, "Neutral / Unassumed")
        
        # Verify neutral language format: "The selected metric ... increased by X%"
        self.assertIn("The selected metric (Sensor Alpha) increased by", interp.contextual_interpretation)
        self.assertIn("Neutral Interpretation", interp.qualification)
        # Verify no assumed positive or negative words in unknown context
        self.assertNotIn("growth concern", interp.contextual_interpretation.lower())
        self.assertNotIn("profit", interp.contextual_interpretation.lower())
        self.assertNotIn("warning", interp.contextual_interpretation.lower())


if __name__ == "__main__":
    unittest.main()
