"""Report Schemas for DataScope Unified Comprehensive Reporting Engine.

Defines Pydantic data structures for executive summaries, dataset overviews,
business performance, profit & loss, discount dynamics, inventory analysis,
trends, forecasting, risks, market competition, recommendations, corrective action plans,
conclusions, and document export metadata.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class ReportMetadataSchema(BaseModel):
    report_title: str
    dataset_name: str
    dataset_id: str
    generated_at: str
    domain_id: str
    domain_name: str
    row_count: int = 0
    column_count: int = 0
    reporting_period: str
    currency_symbol: Optional[str] = None
    data_quality_score: int = 100
    available_sections_count: int = 0
    total_sections_count: int = 14


class ExecutiveSummarySchema(BaseModel):
    dataset_name: str
    row_count: int = 0
    column_count: int = 0
    domain_name: str
    reporting_period: str
    currency_symbol: Optional[str] = None
    overall_performance_summary: str
    overall_business_condition: str = "Healthy"
    total_sales_revenue: Optional[str] = None
    total_cost_expense: Optional[str] = None
    total_profit_loss: Optional[str] = None
    profit_margin_pct: Optional[str] = None
    growth_or_decline_text: Optional[str] = None
    total_orders_count: Optional[str] = None
    average_order_value: Optional[str] = None
    total_units_sold: Optional[str] = None
    average_discount_pct: Optional[str] = None
    overall_business_health: str = "Healthy"
    major_positive_findings: List[str] = Field(default_factory=list)
    major_negative_findings: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    most_important_risks: List[str] = Field(default_factory=list)
    priority_corrective_actions: List[str] = Field(default_factory=list)
    top_3_recommended_actions: List[str] = Field(default_factory=list)


class ColumnSummaryItemSchema(BaseModel):
    column_name: str
    dtype: str
    semantic_role: str = "general"
    missing_count: int = 0
    missing_pct: float = 0.0
    unique_count: int = 0
    sample_values: List[str] = Field(default_factory=list)


class DatasetOverviewReportSchema(BaseModel):
    dimensions_text: str = ""
    row_count: int = 0
    column_count: int = 0
    columns_summary: List[ColumnSummaryItemSchema] = Field(default_factory=list)
    detected_date_range: Optional[str] = None
    has_date_dimension: bool = False
    data_quality_score: int = 100
    data_quality_status: Literal["Healthy", "Warning", "Critical"] = "Healthy"
    missing_cells_count: int = 0
    missing_cells_pct: float = 0.0
    duplicate_rows_count: int = 0
    duplicate_rows_pct: float = 0.0
    important_limitations: List[str] = Field(default_factory=list)


class SixPointFindingSchema(BaseModel):
    observation_title: str
    what_happened: str
    business_meaning: str
    why_it_matters: str
    recommended_action: str
    evidence: str
    limitations: str


class PerformancePerformerItemSchema(BaseModel):
    entity_type: str  # e.g., "Category", "Product", "Region", "Team", "Segment"
    name: str
    metric_name: str
    formatted_value: str
    raw_value: Optional[float] = None
    percentage_share: Optional[float] = None
    note: Optional[str] = None


class PerformanceMetricItemSchema(BaseModel):
    name: str
    formatted_value: str
    raw_value: Optional[float] = None
    unit: Optional[str] = None
    status: Literal["Available", "Calculated", "Estimated", "Unavailable"] = "Available"
    business_meaning: str = ""
    source_column: Optional[str] = None
    comparison_with_previous: Optional[str] = None
    requires_attention: bool = False
    attention_reason: Optional[str] = None


class BusinessPerformanceReportSchema(BaseModel):
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    total_sales_revenue: Optional[str] = None
    total_profit_loss: Optional[str] = None
    profit_margin_pct: Optional[str] = None
    average_order_value: Optional[str] = None
    growth_rate_pct: Optional[str] = None
    performance_direction: Optional[Literal["growth", "decline", "stable", "neutral"]] = None
    metric_highlights: List[PerformanceMetricItemSchema] = Field(default_factory=list)
    top_performers: List[PerformancePerformerItemSchema] = Field(default_factory=list)
    underperformers: List[PerformancePerformerItemSchema] = Field(default_factory=list)
    six_point_findings: List[SixPointFindingSchema] = Field(default_factory=list)
    summary_text: str = ""


class ProfitLossSegmentItemSchema(BaseModel):
    name: str
    segment_type: str  # "Product", "Category", "Region", "Sub-Category"
    revenue_formatted: str
    profit_loss_formatted: str
    profit_margin_pct: float
    discount_rate_pct: Optional[float] = None
    issue_type: Literal["loss_maker", "high_sales_low_profit", "discount_bleed", "healthy"] = "loss_maker"
    explanation: str
    calculation_basis: Optional[str] = None
    status_type: Literal["confirmed_finding", "signal_requiring_validation"] = "confirmed_finding"
    actionable_response: Optional[str] = None


class ProfitLossReportSchema(BaseModel):
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    revenue_trend_summary: str = ""
    profit_trend_summary: str = ""
    profit_margin_summary: str = ""
    loss_making_segments: List[ProfitLossSegmentItemSchema] = Field(default_factory=list)
    high_sales_low_profit_segments: List[ProfitLossSegmentItemSchema] = Field(default_factory=list)
    discount_margin_observations: List[str] = Field(default_factory=list)
    changes_explanation: List[str] = Field(default_factory=list)


class CustomerSegmentItemSchema(BaseModel):
    segment_name: str
    customer_count_formatted: Optional[str] = None
    revenue_formatted: str
    revenue_share_pct: float
    aov_formatted: str
    profit_formatted: Optional[str] = None
    profit_margin_pct: Optional[float] = None
    business_implication: str
    marketing_strategy: str


class CustomerSegmentAnalysisSchema(BaseModel):
    is_available: bool = False
    unavailable_reason: Optional[str] = None
    dimension_analyzed: Optional[str] = None
    segments: List[CustomerSegmentItemSchema] = Field(default_factory=list)
    concentration_observation: Optional[str] = None
    strategic_summary: str = ""


class RegionalChannelItemSchema(BaseModel):
    name: str
    dimension_type: str  # "Region", "Channel", "Device"
    revenue_formatted: str
    revenue_share_pct: float
    order_volume: int
    operational_observation: str


class RegionalChannelAnalysisSchema(BaseModel):
    is_available: bool = False
    unavailable_reason: Optional[str] = None
    dimension_name: Optional[str] = None
    items: List[RegionalChannelItemSchema] = Field(default_factory=list)
    operational_takeaway: str = ""


class RootCauseItemSchema(BaseModel):
    issue_title: str
    confirmed_observation: str
    possible_contributing_factors: List[str] = Field(default_factory=list)
    data_needed_for_validation: List[str] = Field(default_factory=list)
    recommended_investigation: str


class RootCauseAnalysisReportSchema(BaseModel):
    is_available: bool = True
    summary_statement: str = ""
    root_causes: List[RootCauseItemSchema] = Field(default_factory=list)


class DiscountPricingReportSchema(BaseModel):
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    average_discount_pct: Optional[str] = None
    high_discount_revenue: Optional[str] = None
    high_discount_transaction_count: int = 0
    margin_erosion_estimate: Optional[str] = None
    discount_tier_observations: List[str] = Field(default_factory=list)
    suggested_controls: List[str] = Field(default_factory=list)
    validation_requirements: List[str] = Field(default_factory=list)


class InventoryReportSchema(BaseModel):
    is_available: bool = False
    unavailable_reason: Optional[str] = None
    total_stock_units: Optional[str] = None
    low_stock_count: int = 0
    overstocked_count: int = 0
    inventory_turnover_observation: str = ""
    reorder_alerts: List[str] = Field(default_factory=list)
    inventory_items: List[Dict[str, Any]] = Field(default_factory=list)


class TrendPeriodComparisonItemSchema(BaseModel):
    metric: str
    time_period: str
    previous_value: Optional[float] = None
    previous_value_formatted: str = "N/A"
    current_value: Optional[float] = None
    current_value_formatted: str = "N/A"
    absolute_change: Optional[float] = None
    absolute_change_formatted: str = "N/A"
    pct_change: Optional[float] = None
    pct_change_formatted: str = "N/A"
    is_positive: bool = True
    direction: Literal["increasing", "decreasing", "stable", "fluctuating"] = "stable"


class TrendsReportSchema(BaseModel):
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    analyzed_metric: Optional[str] = None
    time_column: Optional[str] = None
    time_period: Optional[str] = None
    selected_granularity: str = "auto"
    period_comparison: Optional[TrendPeriodComparisonItemSchema] = None
    upward_trends: List[str] = Field(default_factory=list)
    downward_trends: List[str] = Field(default_factory=list)
    peak_period: Optional[str] = None
    peak_value_formatted: Optional[str] = None
    lowest_period: Optional[str] = None
    lowest_value_formatted: Optional[str] = None
    seasonality_notes: Optional[str] = None
    volatility_assessment: str = "Stable"
    plain_language_interpretation: str = ""
    limitations: List[str] = Field(default_factory=list)


class ForecastPointItemSchema(BaseModel):
    period: str
    forecast_formatted: str
    forecast_raw: float
    lower_bound_80_formatted: str
    upper_bound_80_formatted: str
    lower_bound_95_formatted: str
    upper_bound_95_formatted: str


class ForecastReportSchema(BaseModel):
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    forecasted_metric: Optional[str] = None
    time_horizon_periods: int = 7
    frequency_label: str = "Daily"
    method_used: str = "Statistical Holt's Smoothing"
    latest_actual_formatted: Optional[str] = None
    final_forecast_formatted: Optional[str] = None
    projected_change_formatted: Optional[str] = None
    projected_growth_pct: Optional[float] = None
    forecast_points: List[ForecastPointItemSchema] = Field(default_factory=list)
    confidence_score: float = 0.85
    forecast_limitations: List[str] = Field(default_factory=list)
    plain_language_interpretation: str = ""
    disclaimer: str = (
        "Statistical forecasts extrapolate historical patterns without guaranteeing future outcomes or modeling unpredictable external factors."
    )


class VerifiedRiskItemSchema(BaseModel):
    risk_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    category: str
    evidence: str
    affected_metric_or_segment: str
    business_impact: str
    why_it_matters: str = ""
    recommended_action: str
    qualification: Optional[str] = None
    data_required_for_validation: str = ""
    confidence_level: str = "High (Verified from Dataset Evidence)"


class RiskDistributionInsightSchema(BaseModel):
    dimension: str
    dominant_category: str
    percentage: float
    description: str
    observation_note: str


class RisksReportSchema(BaseModel):
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    health_status: Literal["Healthy", "Attention Required", "Critical Risks Identified"] = "Healthy"
    summary_statement: str = ""
    total_risks_count: int = 0
    high_severity_count: int = 0
    medium_severity_count: int = 0
    low_severity_count: int = 0
    verified_risks: List[VerifiedRiskItemSchema] = Field(default_factory=list)
    distribution_insights: List[RiskDistributionInsightSchema] = Field(default_factory=list)
    data_safety_notes: List[str] = Field(default_factory=list)


class CompetitorComparisonItemSchema(BaseModel):
    rank: int
    name: str
    is_our_entity: bool = False
    revenue_formatted: str = "N/A"
    profit_formatted: str = "N/A"
    profit_margin_pct: Optional[float] = None
    market_share_pct: Optional[float] = None
    growth_rate_pct: Optional[float] = None
    pricing_index_formatted: str = "N/A"
    status_label: str = "Reported Competitor"


class CompetitionReportSchema(BaseModel):
    is_available: bool = False
    status_title: str = "Market competition analysis is not available."
    summary_statement: str = "No external market competitor data was provided."
    unavailable_reason: Optional[str] = None
    has_external_benchmark: bool = False
    benchmark_filename: Optional[str] = None
    total_competitors_tracked: int = 0
    competitors: List[CompetitorComparisonItemSchema] = Field(default_factory=list)
    market_gaps: List[str] = Field(default_factory=list)
    strategic_actions: List[str] = Field(default_factory=list)
    required_market_fields: List[Dict[str, Any]] = Field(default_factory=list)
    market_limitations: List[str] = Field(default_factory=list)


class UnifiedRecommendationItemSchema(BaseModel):
    rec_id: str
    title: str
    category: str
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    problem: str
    evidence: str
    business_impact: str
    exact_recommended_action: str
    action_steps: List[str] = Field(default_factory=list)
    expected_objective: str
    suggested_owner_team: str = "Operations"
    metric_to_track: str = "General Performance"
    suggested_review_period: str = "Monthly"
    data_limitations: str = ""


class RecommendationsReportSchema(BaseModel):
    is_available: bool = True
    unavailable_reason: Optional[str] = None
    total_recommendations: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary_statement: str = ""
    recommendations_list: List[UnifiedRecommendationItemSchema] = Field(default_factory=list)


class CorrectiveActionItemSchema(BaseModel):
    priority: Literal["Critical", "High", "Medium", "Low"] = "Medium"
    problem: str
    recommended_action: str
    owner_team: str  # e.g., "Marketing", "Finance", "Operations", "Sales", "Engineering"
    metric_to_track: str
    review_period: str  # e.g., "Immediate / 7 Days", "30 Days", "Quarterly"


class CorrectiveActionPlanSchema(BaseModel):
    is_available: bool = True
    action_items: List[CorrectiveActionItemSchema] = Field(default_factory=list)
    disclaimer: str = (
        "Responsibility areas are recommended strategic operational divisions rather than individual employee assignments."
    )


class ConclusionReportSchema(BaseModel):
    main_findings: List[str] = Field(default_factory=list)
    most_urgent_issues: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    important_limitations: List[str] = Field(default_factory=list)
    areas_requiring_additional_data: List[str] = Field(default_factory=list)


class MethodologyAuditTrailSchema(BaseModel):
    domain_rule_applied: str
    statistical_checks_performed: List[str] = Field(default_factory=list)
    granularity_grain_description: str
    evidence_baseline: str
    generated_timestamp: str


class ComprehensiveReportResponse(BaseModel):
    metadata: ReportMetadataSchema
    executive_summary: ExecutiveSummarySchema
    business_performance: BusinessPerformanceReportSchema
    profit_loss: ProfitLossReportSchema
    customer_segment_analysis: Optional[CustomerSegmentAnalysisSchema] = None
    regional_channel_analysis: Optional[RegionalChannelAnalysisSchema] = None
    discount_pricing: Optional[DiscountPricingReportSchema] = None
    inventory_analysis: Optional[InventoryReportSchema] = None
    root_cause_analysis: Optional[RootCauseAnalysisReportSchema] = None
    trends_intelligence: TrendsReportSchema
    risks_anomalies: RisksReportSchema
    market_competition: CompetitionReportSchema
    recommendations: RecommendationsReportSchema
    corrective_action_plan: CorrectiveActionPlanSchema
    forecasting: ForecastReportSchema
    data_driven_conclusion: ConclusionReportSchema
    dataset_overview: DatasetOverviewReportSchema
    methodology_audit: Optional[MethodologyAuditTrailSchema] = None
