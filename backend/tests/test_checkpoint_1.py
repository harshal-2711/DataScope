"""Unit tests for Checkpoint 1: Blueprint Schema and Registry."""
from __future__ import annotations

import unittest

from app.domains.base import (
    ChartRule,
    ComparisonRule,
    DomainBlueprint,
    EntityRule,
    KpiRule,
    RecommendationRule,
    RiskRule,
    TrendRule,
)
from app.domains.commerce import DOMAINS as COMMERCE_DOMAINS
from app.domains.education import DOMAINS as EDUCATION_DOMAINS
from app.domains.finance import DOMAINS as FINANCE_DOMAINS
from app.domains.healthcare_life import DOMAINS as HEALTHCARE_DOMAINS
from app.domains.logistics_travel import DOMAINS as LOGISTICS_DOMAINS
from app.domains.manufacturing_energy import DOMAINS as MANUFACTURING_DOMAINS
from app.domains.media_entertainment import DOMAINS as MEDIA_DOMAINS
from app.domains.people_hr import DOMAINS as PEOPLE_DOMAINS
from app.domains.procurement import DOMAINS as PROCUREMENT_DOMAINS
from app.domains.public_environment import DOMAINS as PUBLIC_DOMAINS
from app.domains.registry import (
    get_all_blueprints,
    get_blueprint_by_id,
    get_blueprint_by_name,
    get_fallback_blueprint,
)
from app.domains.sales_marketing import DOMAINS as SALES_DOMAINS
from app.domains.technology import DOMAINS as TECHNOLOGY_DOMAINS
from app.schemas.domain_blueprint import (
    ComparisonItemSchema,
    DetectedEntitySchema,
    DomainChartSpecSchema,
    DomainIdentitySchema,
    DomainIntelligenceResponse,
    DomainKpiSchema,
    RecommendationItemSchema,
    RiskItemSchema,
    SkippedAnalysisSchema,
    TrendItemSchema,
)

# All 75 required domain names
REQUIRED_75_DOMAINS = [
    "General Business Analytics",
    "Retail",
    "E-commerce",
    "Grocery",
    "FMCG",
    "Food and Restaurant",
    "Food Delivery",
    "Quick Commerce",
    "Sales and CRM",
    "Marketing and Advertising",
    "Finance",
    "Banking",
    "Insurance",
    "Investment and Stock Market",
    "FinTech and Payments",
    "Financial Risk and Credit",
    "Fraud and Anomaly Detection",
    "HR and Workforce Analytics",
    "Recruitment",
    "Education",
    "EdTech",
    "Academic and Student Performance",
    "Healthcare",
    "Hospital Management",
    "Healthcare Operations",
    "Pharmaceuticals",
    "Clinical Research",
    "Sports",
    "Sports Performance",
    "Music",
    "Movies and Entertainment",
    "OTT and Streaming",
    "Gaming",
    "Media and Publishing",
    "Social Media",
    "Real Estate",
    "Real Estate Investment",
    "Manufacturing",
    "Manufacturing Quality",
    "Production Analytics",
    "Logistics",
    "Supply Chain",
    "Delivery and Courier",
    "Transportation",
    "Public Transport",
    "Travel",
    "Tourism",
    "Airlines and Aviation",
    "Hospitality and Hotels",
    "Automotive",
    "Telecom",
    "Energy and Utilities",
    "Oil and Gas",
    "Agriculture",
    "Government and Public Data",
    "Government Finance and Public Finance",
    "IT and Software",
    "SaaS and Subscription",
    "Product Analytics",
    "Web Analytics",
    "Cybersecurity",
    "Customer Support and Service",
    "Construction",
    "Mining",
    "Environment and Climate",
    "Weather",
    "Science and Research",
    "IoT and Sensor Data",
    "Network and Infrastructure Monitoring",
    "Crime and Public Safety",
    "Population and Demographics",
    "Economics and Macroeconomics",
    "Restaurant Operations",
    "Retail Operations",
    "General / Unknown",
]


class TestCheckpoint1(unittest.TestCase):
    """Test suite for Checkpoint 1: Blueprint schema, base dataclasses, and registry."""

    def test_strongly_typed_structures_instantiation(self):
        """Verify that all blueprint rule dataclasses and Pydantic schemas can be instantiated."""
        entity = EntityRule("customer", "Customer", ("cust_id", "customer"))
        kpi = KpiRule("rev", "Revenue", "Gross sales", ("numeric",), ("revenue",), formula="sum", format="currency")
        chart = ChartRule("sales_by_cat", "Sales by Category", "bar", ("category",), ("revenue",))
        comp = ComparisonRule("category", "Category Breakdown", ("category",), ("revenue",))
        trend = TrendRule(("revenue",), ("date",), "Time trend")
        risk = RiskRule("outlier_rev", "Revenue Anomaly", "outlier", ("revenue",), threshold=3.0)
        rec = RecommendationRule("revenue_improvement", "rev", "trend", "Action", "Limitation")

        bp = DomainBlueprint(
            id="test_domain",
            name="Test Domain",
            description="Testing blueprint",
            keywords=("test", "sample"),
            entities=(entity,),
            kpis=(kpi,),
            charts=(chart,),
            comparisons=(comp,),
            trends=(trend,),
            risks=(risk,),
            recommendations=(rec,),
        )

        self.assertEqual(bp.id, "test_domain")
        self.assertEqual(len(bp.kpis), 1)

        # Test Pydantic schemas
        schema = DomainIntelligenceResponse(
            dataset_id="ds_123",
            domain=DomainIdentitySchema(domain_id="test", name="Test", description="Desc"),
            entities=[DetectedEntitySchema(entity_type="customer", label="Customer", confidence=0.9)],
            kpis=[DomainKpiSchema(id="rev", name="Revenue", description="Desc", value=100.0)],
            charts=[DomainChartSpecSchema(id="c1", title="Chart", chart_type="bar", x_label="X", y_label="Y", aggregation="sum")],
            comparisons=[ComparisonItemSchema(comparison_type="cat", title="Comp", baseline="B", target="T", metric="M")],
            trends=[TrendItemSchema(metric_name="M", time_column="T", trend_direction="increasing")],
            risks=[RiskItemSchema(risk_id="r1", category="Risk", description="Desc")],
            recommendations=[RecommendationItemSchema(rec_id="rc1", category="Cat", title="Title", finding="Find", supporting_metric="M", evidence="E", recommended_action="A", limitations="L")],
            skipped_analyses=[SkippedAnalysisSchema(analysis_type="kpi", item_id="k1", name="K", reason="R")],
        )
        self.assertEqual(schema.dataset_id, "ds_123")

    def test_domain_module_counts(self):
        """Verify the exact domain counts for all 11 modules."""
        self.assertEqual(len(COMMERCE_DOMAINS), 10, "commerce.py must contain exactly 10 domains")
        self.assertEqual(len(FINANCE_DOMAINS), 8, "finance.py must contain exactly 8 domains")
        self.assertEqual(len(TECHNOLOGY_DOMAINS), 7, "technology.py must contain exactly 7 domains")
        self.assertEqual(len(SALES_DOMAINS), 3, "sales_marketing.py must contain exactly 3 domains")
        self.assertEqual(len(PEOPLE_DOMAINS), 3, "people_hr.py must contain exactly 3 domains")
        self.assertEqual(len(HEALTHCARE_DOMAINS), 5, "healthcare_life.py must contain exactly 5 domains")
        self.assertEqual(len(EDUCATION_DOMAINS), 3, "education.py must contain exactly 3 domains")
        self.assertEqual(len(LOGISTICS_DOMAINS), 10, "logistics_travel.py must contain exactly 10 domains")
        self.assertEqual(len(MANUFACTURING_DOMAINS), 8, "manufacturing_energy.py must contain exactly 8 domains")
        self.assertEqual(len(MEDIA_DOMAINS), 7, "media_entertainment.py must contain exactly 7 domains")
        self.assertEqual(len(PUBLIC_DOMAINS), 11, "public_environment.py must contain exactly 11 domains")

        total = (
            len(COMMERCE_DOMAINS)
            + len(FINANCE_DOMAINS)
            + len(TECHNOLOGY_DOMAINS)
            + len(SALES_DOMAINS)
            + len(PEOPLE_DOMAINS)
            + len(HEALTHCARE_DOMAINS)
            + len(EDUCATION_DOMAINS)
            + len(LOGISTICS_DOMAINS)
            + len(MANUFACTURING_DOMAINS)
            + len(MEDIA_DOMAINS)
            + len(PUBLIC_DOMAINS)
            + len(PROCUREMENT_DOMAINS)
        )
        self.assertEqual(total, 77, "Total across all modules must equal 77")

    def test_registry_contains_all_75_domains_without_duplicates(self):
        """Verify that all domains are registered with unique IDs and names."""
        blueprints = get_all_blueprints()
        self.assertEqual(len(blueprints), 77)

        # Ensure all IDs are unique
        ids = [bp.id for bp in blueprints]
        self.assertEqual(len(ids), len(set(ids)), "Domain IDs must be strictly unique")

        # Ensure all names are unique
        names = [bp.name for bp in blueprints]
        self.assertEqual(len(names), len(set(names)), "Domain names must be strictly unique")

        # Verify every one of the 75 required domains exists
        for required_name in REQUIRED_75_DOMAINS:
            bp = get_blueprint_by_name(required_name)
            self.assertIsNotNone(bp, f"Missing required domain: '{required_name}'")

    def test_registry_lookups_and_fallback(self):
        """Verify get_blueprint_by_id, get_blueprint_by_name, and get_fallback_blueprint."""
        retail = get_blueprint_by_id("retail")
        self.assertIsNotNone(retail)
        self.assertEqual(retail.name, "Retail")

        # Case-insensitive lookup
        healthcare = get_blueprint_by_name("healthcare")
        self.assertIsNotNone(healthcare)
        self.assertEqual(healthcare.id, "healthcare")

        # Fallback blueprint
        fallback = get_fallback_blueprint()
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback.id, "general_unknown")


if __name__ == "__main__":
    unittest.main()
