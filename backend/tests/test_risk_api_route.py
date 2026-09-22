"""
Regression test suite for Risk Intelligence API route:
GET /api/dataset/{dataset_id}/risk
"""
import io
import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.services import dataset_store


class TestRiskApiRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Clear store between tests if needed or create fresh test datasets
        pass

    def test_01_openapi_schema_contains_risk_endpoint(self):
        """Verify GET /api/dataset/{dataset_id}/risk exists in OpenAPI specification."""
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        openapi = response.json()
        paths = openapi.get("paths", {})

        expected_path = "/api/dataset/{dataset_id}/risk"
        self.assertIn(expected_path, paths, f"Route {expected_path} missing from OpenAPI schema!")
        self.assertIn("get", paths[expected_path], f"GET method missing from {expected_path}!")

        # Verify summary or operationId
        get_op = paths[expected_path]["get"]
        self.assertEqual(get_op.get("operationId"), "get_dataset_risk_intelligence_api_dataset__dataset_id__risk_get")

    def test_02_nonexistent_dataset_returns_application_404(self):
        """Verify non-existent dataset ID returns HTTP 404 with 'Dataset ... not found' detail (application 404)."""
        fake_id = "nonexistent_dataset_12345"
        response = self.client.get(f"/api/dataset/{fake_id}/risk")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("not found", data["detail"].lower())

    def test_03_uploaded_dataset_returns_200_and_risk_intelligence(self):
        """Verify valid uploaded dataset returns HTTP 200 and complete Risk Intelligence payload."""
        csv_content = (
            "order_date,sales,profit,customer_type,region\n"
            "2024-01-01,10000,2000,Member,North\n"
            "2024-02-01,9500,1800,Member,North\n"
            "2024-03-01,9000,1500,Member,South\n"
            "2024-04-01,8500,1200,Member,East\n"
            "2024-05-01,7000,500,Guest,West\n"
            "2024-06-01,5000,-300,Guest,West\n"
        )
        file_obj = io.BytesIO(csv_content.encode("utf-8"))

        upload_res = self.client.post(
            "/api/dataset/upload",
            files={"file": ("test_sales.csv", file_obj, "text/csv")}
        )
        self.assertEqual(upload_res.status_code, 200)
        upload_data = upload_res.json()
        dataset_id = upload_data["dataset_id"]
        self.assertTrue(dataset_id)

        # Call Risk API
        risk_res = self.client.get(f"/api/dataset/{dataset_id}/risk")
        self.assertEqual(risk_res.status_code, 200)
        risk_data = risk_res.json()

        # Validate response structure
        self.assertEqual(risk_data["dataset_id"], dataset_id)
        self.assertIn("overview", risk_data)
        self.assertIn("risks", risk_data)
        self.assertIn("distribution_insights", risk_data)
        self.assertIn("domain_id", risk_data)
        self.assertIn("domain_name", risk_data)

        # Verify overview fields
        overview = risk_data["overview"]
        self.assertIn("total_risks", overview)
        self.assertIn("high_count", overview)
        self.assertIn("medium_count", overview)
        self.assertIn("low_count", overview)
        self.assertIn("health_status", overview)
        self.assertIn("summary_statement", overview)

    def test_04_invalid_http_method_returns_405(self):
        """Verify POST to risk endpoint is disallowed (405 Method Not Allowed), confirming route exists."""
        response = self.client.post("/api/dataset/fake_id/risk", json={})
        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
