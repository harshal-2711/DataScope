"""Base dataclasses and builder definitions for domain blueprints.

A DomainBlueprint defines the complete analytical profile of an industry domain:
- Keywords and vocabulary for dynamic detection
- Entity definitions (e.g. Customer, Order, Patient, Sensor)
- Factual KPI rules with required/optional column roles and aggregation formulas
- Chart recommendations (strictly using supported chart types: bar, line, pie, histogram, scatter)
- Comparison intelligence (time, category, segment, entity)
- Trend intelligence (time-series, moving averages, growth)
- Risk and anomaly rules (neutral labels, thresholds)
- Evidence-based recommendation rules
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Tuple

ChartType = Literal["bar", "line", "pie", "histogram", "scatter"]
FormulaType = Literal["sum", "mean", "ratio", "count", "count_distinct", "min", "max", "rate"]
FormatType = Literal["currency", "percentage", "number", "duration"]


@dataclass
class EntityRule:
    entity_type: str
    label: str
    name_patterns: Tuple[str, ...]
    role_preference: Tuple[str, ...] = ("identifier", "categorical")
    min_uniqueness: float = 0.0
    max_uniqueness: float = 1.0


@dataclass
class KpiRule:
    id: str
    name: str
    description: str
    required_roles: Tuple[str, ...]  # e.g. ("numeric",) or ("numeric", "datetime")
    metric_patterns: Tuple[str, ...] = ()
    dimension_patterns: Tuple[str, ...] = ()
    date_patterns: Tuple[str, ...] = ()
    formula: FormulaType = "sum"
    format: FormatType = "number"
    business_meaning: str = ""
    is_reliable_condition: str = "Always reliable when metric is present"


@dataclass
class ChartRule:
    id: str
    title: str
    chart_type: ChartType
    dimension_patterns: Tuple[str, ...] = ()
    metric_patterns: Tuple[str, ...] = ()
    aggregation: str = "sum"
    sort_by: str = "desc"
    max_categories: int = 15
    business_question: str = ""


@dataclass
class ComparisonRule:
    comparison_type: str  # "category", "time", "segment", "entity"
    title: str
    dimension_patterns: Tuple[str, ...] = ()
    metric_patterns: Tuple[str, ...] = ()


@dataclass
class TrendRule:
    metric_patterns: Tuple[str, ...] = ()
    time_patterns: Tuple[str, ...] = ()
    description: str = ""


@dataclass
class RiskRule:
    risk_id: str
    category: str
    risk_type: str  # "outlier", "drop", "spike", "missing", "concentration"
    metric_patterns: Tuple[str, ...] = ()
    dimension_patterns: Tuple[str, ...] = ()
    threshold: float = 0.0
    label: str = "Potential anomaly"
    recommended_action: str = ""


@dataclass
class RecommendationRule:
    category: str  # "revenue_improvement", "cost_reduction", "operational_efficiency", "risk_mitigation", etc.
    trigger_metric_or_risk: str
    condition: str
    action_template: str
    limitation: str


@dataclass
class DomainBlueprint:
    id: str
    name: str
    description: str
    keywords: Tuple[str, ...]
    alternative_domains: Tuple[str, ...] = ()
    entities: Tuple[EntityRule, ...] = field(default_factory=tuple)
    kpis: Tuple[KpiRule, ...] = field(default_factory=tuple)
    charts: Tuple[ChartRule, ...] = field(default_factory=tuple)
    comparisons: Tuple[ComparisonRule, ...] = field(default_factory=tuple)
    trends: Tuple[TrendRule, ...] = field(default_factory=tuple)
    risks: Tuple[RiskRule, ...] = field(default_factory=tuple)
    recommendations: Tuple[RecommendationRule, ...] = field(default_factory=tuple)
