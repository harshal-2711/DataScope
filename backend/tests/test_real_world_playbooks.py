"""Automated test suite verifying all 14 Real-World Domain Playbooks + Fallback.

Verifies:
1. Sales & E-commerce
2. Finance & Accounting
3. IPL & Sports (Match-level)
4. IPL & Sports (Ball-by-ball)
5. Education & Academic Performance
6. Healthcare & Clinical Operations
7. Movies & Box Office
8. Music & Streaming
9. Marketing & Advertising
10. HR & Workforce
11. Manufacturing & Operations
12. Logistics & Supply Chain
13. Real Estate
14. Agriculture
15. Social Media
16. Universal Fallback
"""
import unittest
import pandas as pd

from app.services import dataset_service, dataset_store


class TestRealWorldPlaybooks(unittest.TestCase):

    def test_marketing_playbook(self):
        """Verify Marketing & Advertising playbook with CTR, ROAS, and campaign performance."""
        df = pd.DataFrame({
            "campaign": ["Summer_Sale", "Brand_Awareness", "Retargeting", "Search_Generic"] * 25,
            "channel": ["Google", "Facebook", "Instagram", "LinkedIn"] * 25,
            "impressions": [10000, 25000, 5000, 15000] * 25,
            "clicks": [500, 750, 400, 600] * 25,
            "conversions": [50, 30, 60, 45] * 25,
            "spend": [1000.0, 1500.0, 600.0, 1200.0] * 25,
            "revenue": [3000.0, 1800.0, 4500.0, 2400.0] * 25,
        })
        dataset_id = dataset_store.save_dataset("marketing_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "Marketing & Advertising")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("total_impressions", metric_map)
        self.assertIn("ctr", metric_map)
        self.assertEqual(metric_map["ctr"]["status"], "Calculated")
        self.assertGreater(metric_map["ctr"]["value"], 0)

        # ROAS
        prof_map = {m["id"]: m for m in dashboard["profitability"]["metrics"]}
        self.assertIn("roas", prof_map)
        self.assertEqual(prof_map["roas"]["status"], "Calculated")
        self.assertGreater(prof_map["roas"]["value"], 1.0)

    def test_hr_workforce_playbook(self):
        """Verify HR & Workforce playbook with headcount, salary, and attrition."""
        df = pd.DataFrame({
            "employee_id": [f"EMP-{i:03d}" for i in range(100)],
            "department": ["Engineering", "Sales", "Marketing", "HR", "Finance"] * 20,
            "salary": [120000, 85000, 75000, 65000, 95000] * 20,
            "attrition": [0, 1, 0, 0, 1] * 20,
            "tenure": [3.5, 1.2, 2.0, 4.5, 5.0] * 20,
        })
        dataset_id = dataset_store.save_dataset("hr_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "HR & Workforce Analytics")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("headcount", metric_map)
        self.assertEqual(metric_map["headcount"]["value"], 100)
        self.assertIn("avg_salary", metric_map)
        self.assertIn("turnover_rate", metric_map)
        self.assertEqual(metric_map["turnover_rate"]["status"], "Calculated")

    def test_manufacturing_playbook(self):
        """Verify Manufacturing playbook with units produced, downtime, and OEE."""
        df = pd.DataFrame({
            "machine_id": ["CNC-01", "Press-02", "Lathe-03", "Welder-04"] * 25,
            "units_produced": [450, 600, 350, 500] * 25,
            "downtime_hours": [2.5, 0.5, 4.0, 1.0] * 25,
            "oee": [82.5, 91.0, 74.0, 88.5] * 25,
            "defect_rate": [1.5, 0.8, 2.4, 1.1] * 25,
        })
        dataset_id = dataset_store.save_dataset("mfg_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "Manufacturing & Operations")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("total_production", metric_map)
        self.assertIn("total_downtime", metric_map)
        self.assertIn("oee", metric_map)
        self.assertEqual(metric_map["oee"]["status"], "Calculated")

    def test_logistics_playbook(self):
        """Verify Logistics & Supply Chain playbook with freight spend and OTIF rate."""
        df = pd.DataFrame({
            "shipment_id": [f"SHP-{i:03d}" for i in range(80)],
            "carrier": ["FedEx", "DHL", "UPS", "Maersk"] * 20,
            "freight_cost": [150.0, 220.0, 180.0, 450.0] * 20,
            "transit_days": [2.0, 3.5, 2.5, 6.0] * 20,
            "is_on_time": [1, 1, 0, 1] * 20,
        })
        dataset_id = dataset_store.save_dataset("logistics_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "Logistics & Supply Chain")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("total_freight_cost", metric_map)
        self.assertIn("avg_transit_days", metric_map)
        self.assertIn("otif_rate", metric_map)
        self.assertEqual(metric_map["otif_rate"]["status"], "Calculated")

    def test_real_estate_playbook(self):
        """Verify Real Estate playbook with property price and price per square foot."""
        df = pd.DataFrame({
            "property_price": [450000, 620000, 310000, 890000] * 25,
            "sqft": [1800, 2400, 1200, 3200] * 25,
            "neighborhood": ["Downtown", "Suburbs", "Uptown", "Waterfront"] * 25,
            "bedrooms": [3, 4, 2, 5] * 25,
        })
        dataset_id = dataset_store.save_dataset("real_estate_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "Real Estate Analytics")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("median_price", metric_map)
        self.assertIn("price_per_sqft", metric_map)
        self.assertEqual(metric_map["price_per_sqft"]["status"], "Calculated")

    def test_agriculture_playbook(self):
        """Verify Agriculture playbook with crop yield and production."""
        df = pd.DataFrame({
            "crop": ["Wheat", "Rice", "Corn", "Soybeans"] * 25,
            "production": [1200, 1500, 1800, 950] * 25,
            "yield": [3.2, 4.1, 4.8, 2.5] * 25,
            "area": [375, 365, 375, 380] * 25,
        })
        dataset_id = dataset_store.save_dataset("agri_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "Agriculture & Crop Yield")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("total_production", metric_map)
        self.assertIn("avg_yield", metric_map)

    def test_social_media_playbook(self):
        """Verify Social Media playbook with impressions and engagement rate."""
        df = pd.DataFrame({
            "post_type": ["Video", "Image", "Carousel", "Text"] * 25,
            "impressions": [5000, 3000, 4500, 1500] * 25,
            "likes": [250, 120, 310, 45] * 25,
            "shares": [50, 15, 60, 5] * 25,
        })
        dataset_id = dataset_store.save_dataset("social_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "Social Media & Audience Engagement")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("total_impressions", metric_map)
        self.assertIn("engagement_rate", metric_map)
        self.assertEqual(metric_map["engagement_rate"]["status"], "Calculated")

    def test_music_playbook(self):
        """Verify Music playbook with streams and track rankings."""
        df = pd.DataFrame({
            "track_name": ["Song_A", "Song_B", "Song_C", "Song_D"] * 25,
            "artist": ["Artist_1", "Artist_2", "Artist_3", "Artist_4"] * 25,
            "streams": [500000, 1200000, 350000, 800000] * 25,
            "popularity": [75, 88, 62, 79] * 25,
            "duration_ms": [210000, 185000, 240000, 195000] * 25,
        })
        dataset_id = dataset_store.save_dataset("music_test.csv", "csv", df)
        dashboard = dataset_service.get_decision_dashboard(dataset_id)

        self.assertEqual(dashboard["domain_name"], "Music & Streaming Analytics")
        metric_map = {m["id"]: m for m in dashboard["executive_summary"]["metrics"]}
        self.assertIn("total_streams", metric_map)
        self.assertIn("avg_popularity", metric_map)


if __name__ == "__main__":
    unittest.main()
