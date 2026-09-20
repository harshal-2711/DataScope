"""Comprehensive unit tests for domain intelligence, entity detection, and field validation."""
from __future__ import annotations

import unittest
import pandas as pd

from app.domains.registry import get_all_blueprints, get_blueprint_by_id
from app.services.column_profiler import profile_dataset
from app.services.comparison_engine import compute_comparisons
from app.services.domain_detector import detect_domain
from app.services.entity_detector import detect_entities
from app.services.field_validator import validate_blueprint_fields
from app.services.insight_engine import generate_evidence_based_recommendations
from app.services.kpi_engine import compute_domain_kpis
from app.services.risk_engine import detect_risks_and_anomalies
from app.services.trend_engine import compute_trends


class TestDomainIntelligence(unittest.TestCase):

    def test_registry_contains_75_domains(self):
        """Verify that all 75 domains are registered in the registry."""
        blueprints = get_all_blueprints()
        self.assertEqual(len(blueprints), 75)
        # Ensure key domains exist
        self.assertIsNotNone(get_blueprint_by_id("retail"))
        self.assertIsNotNone(get_blueprint_by_id("ecommerce"))
        self.assertIsNotNone(get_blueprint_by_id("healthcare"))
        self.assertIsNotNone(get_blueprint_by_id("hospital_management"))
        self.assertIsNotNone(get_blueprint_by_id("saas_subscription"))
        self.assertIsNotNone(get_blueprint_by_id("iot_sensor"))
        self.assertIsNotNone(get_blueprint_by_id("general_business"))
        self.assertIsNotNone(get_blueprint_by_id("general_unknown"))

    def test_ecommerce_domain_detection(self):
        """Verify accurate detection of an E-commerce dataset."""
        df = pd.DataFrame({
            "order_id": ["ORD-1001", "ORD-1002", "ORD-1003", "ORD-1004"],
            "customer_id": ["CUST-1", "CUST-2", "CUST-3", "CUST-4"],
            "product_name": ["T-Shirt", "Jeans", "Sneakers", "Jacket"],
            "order_total": [29.99, 59.99, 89.99, 120.00],
            "shipping_fee": [5.00, 5.00, 0.00, 10.00],
            "order_date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        })
        profiles = profile_dataset(df)
        domain = detect_domain(df, profiles)

        self.assertIn(domain.domain_id, ("ecommerce", "retail", "general_business"))
        self.assertGreaterEqual(domain.confidence, 0.5)
        self.assertGreater(len(domain.evidence), 0)

        entities = detect_entities(df, profiles)
        entity_types = {e.entity_type for e in entities}
        self.assertTrue("order" in entity_types or "customer" in entity_types or "product" in entity_types)

    def test_healthcare_domain_detection(self):
        """Verify accurate detection of a Healthcare / Hospital dataset."""
        df = pd.DataFrame({
            "patient_id": [f"PAT-{i}" for i in range(50)],
            "diagnosis": ["Hypertension" if i % 2 == 0 else "Diabetes" for i in range(50)],
            "los": [3, 4, 2, 5, 7, 2, 3, 4, 6, 2] * 5,
            "treatment_cost": [1200.0, 2400.0, 800.0, 3100.0, 5400.0] * 10,
            "admission_date": [f"2026-01-{i%28+1:02d}" for i in range(50)],
        })
        profiles = profile_dataset(df)
        domain = detect_domain(df, profiles)

        self.assertIn(domain.domain_id, ("healthcare", "hospital_management"))
        self.assertGreaterEqual(domain.confidence, 0.5)

        entities = detect_entities(df, profiles)
        entity_types = {e.entity_type for e in entities}
        self.assertIn("patient", entity_types)

    def test_field_validation_and_skipped_analyses(self):
        """Verify that field validator validates available rules and tracks skipped ones."""
        df = pd.DataFrame({
            "category": ["Electronics", "Clothing", "Home", "Garden"] * 5,
            "quantity": [10, 20, 15, 30] * 5,
        })
        profiles = profile_dataset(df)
        blueprint = get_blueprint_by_id("retail")
        self.assertIsNotNone(blueprint)

        entities = detect_entities(df, profiles, blueprint)
        capabilities = validate_blueprint_fields(df, profiles, blueprint, entities)

        self.assertGreater(len(capabilities.skipped), 0)
        skipped_types = {s.analysis_type for s in capabilities.skipped}
        self.assertTrue("trend" in skipped_types or "kpi" in skipped_types)

        kpis = compute_domain_kpis(df, capabilities.kpis)
        self.assertGreater(len(kpis), 0)

    def test_risks_and_evidence_recommendations(self):
        """Verify statistical anomaly detection and evidence-based recommendations."""
        values = [100.0] * 30 + [10000.0]
        df = pd.DataFrame({
            "customer_id": [f"CUST-{i}" for i in range(31)],
            "amount": values,
            "category": ["Regular"] * 30 + ["VIP"],
        })
        profiles = profile_dataset(df)
        blueprint = get_blueprint_by_id("general_business")
        self.assertIsNotNone(blueprint)

        entities = detect_entities(df, profiles, blueprint)
        capabilities = validate_blueprint_fields(df, profiles, blueprint, entities)

        risks = detect_risks_and_anomalies(df, profiles, capabilities.risks)
        self.assertGreater(len(risks), 0)
        self.assertTrue(any(r.label in ("Potential anomaly", "Requires investigation", "Unusual pattern detected") for r in risks))

        recs = generate_evidence_based_recommendations(
            blueprint=blueprint,
            kpis=[],
            trends=[],
            risks=risks,
            comparisons=[],
            entities=entities,
        )
        self.assertGreater(len(recs), 0)
        self.assertTrue(all(r.limitations != "" for r in recs))
        self.assertTrue(all(r.evidence != "" for r in recs))

    def test_get_domain_intelligence_end_to_end(self):
        """Verify the full 15-step domain intelligence pipeline on a stored dataset."""
        from app.services import dataset_service, dataset_store

        df = pd.DataFrame({
            "order_id": [f"ORD-{i:04d}" for i in range(1, 101)],
            "customer_id": [f"CUST-{i%15+1:03d}" for i in range(1, 101)],
            "product_name": ["Laptop", "Monitor", "Keyboard", "Mouse", "Desk"] * 20,
            "category": ["Electronics", "Electronics", "Accessories", "Accessories", "Furniture"] * 20,
            "order_total": [899.99, 299.99, 79.99, 29.99, 399.99] * 20,
            "order_date": [f"2026-01-{i%28+1:02d}" for i in range(1, 101)],
        })
        dataset_id = dataset_store.save_dataset("sales_orders.csv", "csv", df)
        intel = dataset_service.get_domain_intelligence(dataset_id)

        self.assertEqual(intel["dataset_id"], dataset_id)
        self.assertIn("domain", intel)
        self.assertIn(intel["domain"]["domain_id"], ("ecommerce", "retail", "general_business"))
        self.assertGreater(len(intel["entities"]), 0)
        self.assertGreater(len(intel["kpis"]), 0)
        self.assertGreater(len(intel["charts"]), 0)
        self.assertGreater(len(intel["trends"]), 0)
        self.assertIn("recommendations", intel)


if __name__ == "__main__":
    unittest.main()
