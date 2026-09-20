from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class DomainIdentitySchema(BaseModel):
    domain_id: str
    name: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    alternative_domains: List[str] = Field(default_factory=list)


class DetectedEntitySchema(BaseModel):
    entity_type: str
    label: str
    matched_column: Optional[str] = None
    confidence: float = 0.0
    evidence: str = ""


class DomainKpiSchema(BaseModel):
    id: str
    name: str
    description: str
    value: Union[float, int, str, None] = None
    format: str = "number"  # "currency", "percentage", "number", "duration"
    aggregation: str = "sum"
    matched_columns: List[str] = Field(default_factory=list)
    business_meaning: str = ""
    is_reliable: bool = True
    skip_reason: Optional[str] = None


class DomainChartSpecSchema(BaseModel):
    id: str
    title: str
    chart_type: Literal["bar", "line", "pie", "histogram", "scatter"]
    x_label: str
    y_label: str
    dimension_column: Optional[str] = None
    metric_column: Optional[str] = None
    aggregation: str = "sum"
    data: List[Dict[str, Any]] = Field(default_factory=list)
    business_question: str = ""
    skip_reason: Optional[str] = None


class ComparisonItemSchema(BaseModel):
    comparison_type: str
    title: str
    baseline: str
    target: str
    metric: str
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    difference: Optional[float] = None
    pct_change: Optional[float] = None
    insight: str = ""
    data: List[Dict[str, Any]] = Field(default_factory=list)


class TrendItemSchema(BaseModel):
    metric_name: str
    time_column: str
    trend_direction: Literal["increasing", "decreasing", "stable", "fluctuating", "insufficient_data"]
    growth_rate_pct: Optional[float] = None
    peak_period: Optional[str] = None
    trough_period: Optional[str] = None
    seasonality_detected: bool = False
    description: str = ""
    data_points: List[Dict[str, Any]] = Field(default_factory=list)


class RiskItemSchema(BaseModel):
    risk_id: str
    category: str
    label: str = "Potential anomaly"  # Neutral wording: "Potential anomaly", "Requires investigation", "Unusual pattern detected"
    description: str
    severity: Literal["low", "medium", "high"] = "medium"
    affected_column: Optional[str] = None
    evidence: str = ""
    recommended_action: str = ""


class RecommendationItemSchema(BaseModel):
    rec_id: str
    category: str
    title: str
    finding: str
    supporting_metric: str
    relevant_columns: List[str] = Field(default_factory=list)
    time_period: Optional[str] = None
    entities_involved: List[str] = Field(default_factory=list)
    severity: Optional[str] = None
    confidence: float = 1.0
    evidence: str = ""
    recommended_action: str = ""
    limitations: str = ""


class SkippedAnalysisSchema(BaseModel):
    analysis_type: str  # "kpi", "chart", "comparison", "trend", "risk"
    item_id: str
    name: str
    reason: str


class MetricStatusSchema(BaseModel):
    id: str
    name: str
    value: Optional[Union[float, int, str]] = None
    formatted_value: Optional[str] = None
    status: Literal["Available", "Calculated", "Estimated", "Unavailable"]
    explanation: str
    category: str
    business_meaning: str
    formula: Optional[str] = None


class SectionChartSchema(BaseModel):
    id: str
    title: str
    business_question: str
    chart_type: Literal["bar", "line", "pie", "histogram", "scatter"]
    metric: str
    grouping: str
    explanation: str
    data: List[Dict[str, Any]] = Field(default_factory=list)
    x_label: Optional[str] = None
    y_label: Optional[str] = None


class DashboardSectionSchema(BaseModel):
    section_id: str
    title: str
    description: str
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    metrics: List[MetricStatusSchema] = Field(default_factory=list)
    charts: List[SectionChartSchema] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    insights: List[Dict[str, Any]] = Field(default_factory=list)


class DecisionDashboardResponse(BaseModel):
    dataset_id: str
    domain_name: str
    executive_summary: DashboardSectionSchema
    sales_performance: DashboardSectionSchema
    profitability: DashboardSectionSchema
    product_analysis: DashboardSectionSchema
    operations_inventory: DashboardSectionSchema
    insights_recommendations: DashboardSectionSchema


class DomainIntelligenceResponse(BaseModel):
    dataset_id: str
    domain: DomainIdentitySchema
    entities: List[DetectedEntitySchema] = Field(default_factory=list)
    kpis: List[DomainKpiSchema] = Field(default_factory=list)
    charts: List[DomainChartSpecSchema] = Field(default_factory=list)
    comparisons: List[ComparisonItemSchema] = Field(default_factory=list)
    trends: List[TrendItemSchema] = Field(default_factory=list)
    risks: List[RiskItemSchema] = Field(default_factory=list)
    recommendations: List[RecommendationItemSchema] = Field(default_factory=list)
    skipped_analyses: List[SkippedAnalysisSchema] = Field(default_factory=list)
    decision_dashboard: Optional[DecisionDashboardResponse] = None
