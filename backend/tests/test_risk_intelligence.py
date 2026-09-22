"""Comprehensive unit tests for universal domain-aware Risk Intelligence engine."""
import unittest
import numpy as np
import pandas as pd

from app.schemas.domain_blueprint import DomainIdentitySchema
from app.services.column_profiler import profile_dataset
from app.services.risk_engine import compute_full_risk_intelligence
from app.services import dataset_service, dataset_store


class TestRiskIntelligenceEngine(unittest.TestCase):

    def test_ecommerce_risk_detection(self):
        """Verify performance decline, negative profit, and customer concentration in ecommerce data."""
        dates = pd.date_range(start="2024-01-01", periods=10, freq="ME")
        sales = [1000.0, 950.0, 900.0, 850.0, 800.0, 750.0, 700.0, 650.0, 500.0, 350.0]
        profit = [200.0, 180.0, 150.0, 120.0, 100.0, 80.0, 50.0, 20.0, -80.0, -150.0]
        customers = ["Customer_A"] * 7 + ["Customer_B", "Customer_C", "Customer_D"]

        df = pd.DataFrame({
            "order_date": dates,
            "sales": sales,
            "profit": profit,
            "customer_name": customers,
        })

        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(
            domain_id="ecommerce",
            name="E-Commerce & Retail",
            description="Online store sales and fulfillment.",
        )

        res = compute_full_risk_intelligence(df, "test_ecom", profiles, domain, dataset_currency="₹")

        self.assertGreater(res.overview.total_risks, 0)
        self.assertIn(res.overview.health_status, ("Critical Risks Identified", "Attention Required"))

        # Both sales and profit show performance decline
        decline_risks = [r for r in res.risks if r.risk_type == "performance_decline"]
        self.assertTrue(len(decline_risks) > 0)
        decline_metrics = [r.affected_metric for r in decline_risks]
        self.assertIn("sales", decline_metrics)

        sales_risk = next(r for r in decline_risks if r.affected_metric == "sales")
        self.assertLess(sales_risk.pct_change, 0)
        self.assertIn("₹", str(sales_risk.current_value_formatted))

        # Verify profit loss risk
        profit_risks = [r for r in res.risks if r.risk_type == "financial_loss"]
        self.assertTrue(len(profit_risks) > 0)

    def test_finance_cost_escalation_and_volatility(self):
        """Verify cost surge and volatility detection in financial time series."""
        dates = pd.date_range(start="2024-01-01", periods=10, freq="D")
        expenses = [100.0, 800.0, 150.0, 950.0, 120.0, 1100.0, 200.0, 1300.0, 1500.0, 2200.0]

        df = pd.DataFrame({
            "report_date": dates,
            "operating_expense": expenses,
            "cost_center": ["Engineering"] * 5 + ["Marketing"] * 5,
        })

        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(
            domain_id="finance",
            name="Finance & Accounting",
            description="Financial statement analysis.",
        )

        res = compute_full_risk_intelligence(df, "test_fin", profiles, domain, dataset_currency="$")

        escalation_risks = [r for r in res.risks if r.risk_type in ("cost_escalation", "volatility", "performance_decline")]
        self.assertTrue(len(escalation_risks) > 0)
        self.assertTrue(any(r.severity in ("high", "medium") for r in res.risks))

    def test_hr_workforce_attrition(self):
        """Verify employee attrition rate detection."""
        records = 50
        status = ["Left"] * 15 + ["Active"] * 35

        df = pd.DataFrame({
            "employee_id": [f"EMP_{i:03d}" for i in range(records)],
            "attrition": status,
            "salary": [60000 + (i * 500) for i in range(records)],
        })

        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(
            domain_id="people_hr",
            name="Human Resources",
            description="Workforce and personnel analytics.",
        )

        res = compute_full_risk_intelligence(df, "test_hr", profiles, domain)
        attrition_risks = [r for r in res.risks if r.risk_type == "workforce_attrition"]
        self.assertTrue(len(attrition_risks) > 0)
        self.assertEqual(attrition_risks[0].severity, "high")
        self.assertAlmostEqual(attrition_risks[0].current_value, 30.0, places=1)

    def test_data_quality_duplicate_and_missing(self):
        """Verify duplicate rows and high null percentages trigger data quality risks."""
        data = {
            "col_a": [10, 20, 30, 10, 10, 10, 10, 10, 10, 10],
            "col_b": ["x", "y", "z", "x", "x", "x", "x", "x", "x", "x"],
            "incomplete_col": [1.0, 2.0, None, None, None, None, None, None, None, None],
        }
        df = pd.DataFrame(data)

        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(
            domain_id="general",
            name="General Dataset",
            description="Generic tabular records.",
        )

        res = compute_full_risk_intelligence(df, "test_dq", profiles, domain)

        dq_risks = [r for r in res.risks if r.risk_type == "data_quality"]
        self.assertTrue(len(dq_risks) >= 1)
        self.assertGreater(res.overview.data_quality_warnings_count, 0)

    def test_clean_dataset_no_risk_state(self):
        """Verify stable dataset produces clean healthy status without false alarms."""
        df = pd.DataFrame({
            "metric_a": [100.0, 101.0, 100.5, 99.8, 100.2, 100.0, 100.4, 99.9, 100.1, 100.0],
            "category": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
        })

        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(
            domain_id="general",
            name="General Dataset",
            description="",
        )

        res = compute_full_risk_intelligence(df, "test_clean", profiles, domain)
        self.assertEqual(res.overview.high_count, 0)
        self.assertEqual(res.overview.health_status, "Healthy")
        self.assertIn("No significant risks detected in the available data.", res.overview.summary_statement)

    def test_non_summable_metric_rejected_from_concentration(self):
        """Verify non-summable metrics like Aging days are NOT summed for concentration risks,
        and categorical distributions like Login Type or Device Type are placed in distribution_insights."""
        # 100 records with Aging days, Customer_Login_type, and Device_Type
        df = pd.DataFrame({
            "Customer_Login_type": ["Member"] * 95 + ["Guest"] * 5,
            "Device_Type": ["Web"] * 93 + ["Mobile"] * 7,
            "Aging": [30.0] * 95 + [10.0] * 5,
            "Rating": [4.8] * 95 + [3.2] * 5,
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="general", name="General", description="")

        res = compute_full_risk_intelligence(df, "test_aging", profiles, domain)
        # Verify NO risk sums 'Aging' or 'Rating' as concentration risk
        aging_risks = [r for r in res.risks if "aging" in (r.affected_metric or "").lower() and r.category != "Data Quality Issue"]
        self.assertEqual(len(aging_risks), 0)

        # Login type and Device Type MUST NOT appear in primary risks list
        login_risks = [r for r in res.risks if "login" in (r.affected_column or "").lower()]
        device_risks = [r for r in res.risks if "device" in (r.affected_column or "").lower()]
        self.assertEqual(len(login_risks), 0)
        self.assertEqual(len(device_risks), 0)

        # But should be captured cleanly in distribution_insights
        login_dist = [d for d in res.distribution_insights if "login" in d.dimension.lower()]
        device_dist = [d for d in res.distribution_insights if "device" in d.dimension.lower()]
        self.assertEqual(len(login_dist), 1)
        self.assertEqual(login_dist[0].dominant_category, "Member")
        self.assertEqual(len(device_dist), 1)
        self.assertEqual(device_dist[0].dominant_category, "Web")

    def test_all_risks_have_why_it_matters_and_human_readable_fields(self):
        """Verify every detected risk item includes why_it_matters and clean titles."""
        df = pd.DataFrame({
            "order_date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "revenue": [1000.0, 950.0, 900.0, 850.0, 800.0, 750.0, 700.0, 600.0, 500.0, 400.0],
            "customer_name": ["Acme Corp"] * 9 + ["Other"] * 1,
            "cost": [100.0, 150.0, 200.0, 250.0, 300.0, 400.0, 500.0, 600.0, 800.0, 1200.0],
        })
        profiles = profile_dataset(df)
        domain = DomainIdentitySchema(domain_id="ecommerce", name="E-Commerce", description="")
        res = compute_full_risk_intelligence(df, "test_full_fields", profiles, domain)

        self.assertGreater(len(res.risks), 0)
        for r in res.risks:
            self.assertIsNotNone(r.why_it_matters)
            self.assertGreater(len(r.why_it_matters), 10)
            self.assertIsNotNone(r.recommended_action)
            self.assertGreater(len(r.recommended_action), 10)
            self.assertIn(r.category, [
                "Performance Decline", "Revenue/Profit Risk", "Cost Increase",
                "Data Quality Issue", "Unusual Outlier", "High Volatility",
                "Operational Risk", "Distribution Observation",
            ])

    def test_risk_service_integration(self):
        """Test dataset_service.get_risk_intelligence integration."""
        csv_bytes = (
            "order_date,sales,cost,region\n"
            "2024-01-01,1000,500,North\n"
            "2024-02-01,900,550,North\n"
            "2024-03-01,800,600,North\n"
            "2024-04-01,700,700,North\n"
            "2024-05-01,500,850,North\n"
            "2024-06-01,350,1100,North\n"
        ).encode("utf-8")

        summary = dataset_service.process_upload("test_sales.csv", csv_bytes, "text/csv")
        dataset_id = summary["dataset_id"]

        risk_data = dataset_service.get_risk_intelligence(dataset_id)
        self.assertEqual(risk_data["dataset_id"], dataset_id)
        self.assertIn("overview", risk_data)
        self.assertIn("risks", risk_data)
        self.assertIsInstance(risk_data["risks"], list)
        self.assertGreater(len(risk_data["risks"]), 0)


if __name__ == "__main__":
    unittest.main()

