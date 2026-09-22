from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator



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
    unit: Optional[str] = None
    formatted_value: Optional[str] = None
    source_column: Optional[str] = None
    formatting_rule: Optional[str] = None


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
    analytical_question: Optional[str] = None
    metric_definition: Optional[str] = None
    unit: Optional[str] = None
    grouping: Optional[str] = None
    time_granularity: Optional[str] = None
    dataset_grain: Optional[str] = None
    data_coverage: Optional[str] = None
    explanation: Optional[str] = None
    limitations: Optional[str] = None


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
    title: str = "Potential Risk"
    category: str
    label: str = "Potential anomaly"  # "Potential anomaly", "Requires investigation", "Unusual pattern detected"
    description: str
    severity: Literal["low", "medium", "high"] = "medium"
    severity_reason: str = ""
    affected_metric: Optional[str] = None
    affected_column: Optional[str] = None
    current_value: Optional[float] = None
    current_value_formatted: Optional[str] = None
    previous_value: Optional[float] = None
    previous_value_formatted: Optional[str] = None
    absolute_change: Optional[float] = None
    absolute_change_formatted: Optional[str] = None
    pct_change: Optional[float] = None
    unit: Optional[str] = None
    time_period: Optional[str] = None
    evidence: str = ""
    why_it_matters: Optional[str] = None
    confidence: float = 0.90
    qualification: Optional[str] = None
    recommended_action: str = ""
    risk_type: str = "general"
    time_series_preview: List[Dict[str, Any]] = Field(default_factory=list)


class RiskOverviewSchema(BaseModel):
    total_risks: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    most_significant_risk: Optional[RiskItemSchema] = None
    data_quality_warnings_count: int = 0
    health_status: Literal["Healthy", "Attention Required", "Critical Risks Identified"] = "Healthy"
    summary_statement: str = ""


class DistributionInsightSchema(BaseModel):
    insight_id: str
    dimension: str
    dimension_label: str
    dominant_category: str
    category_count: int
    total_records: int
    percentage: float
    description: str
    observation_note: str


class RiskIntelligenceResponse(BaseModel):
    dataset_id: str
    domain_id: str
    domain_name: str
    overview: RiskOverviewSchema
    risks: List[RiskItemSchema] = Field(default_factory=list)
    distribution_insights: List[DistributionInsightSchema] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    affected_metrics: List[str] = Field(default_factory=list)
    has_time_dimension: bool = False
    data_safety_notes: List[str] = Field(default_factory=list)




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
    unit: Optional[str] = None
    source_column: Optional[str] = None
    aggregation_method: Optional[str] = None


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


class DatasetGrainSchema(BaseModel):
    grain_type: str
    grain_label: str
    description: str
    primary_entity_column: Optional[str] = None
    row_count: int
    unique_entity_count: int
    repeated_observations_count: int
    repetition_ratio: float
    is_one_to_one: bool
    candidate_entities: List[Dict[str, Any]] = Field(default_factory=list)
    measures: List[str] = Field(default_factory=list)
    dimensions: List[str] = Field(default_factory=list)
    aggregation_guardrails: List[str] = Field(default_factory=list)


class DomainIntelligenceResponse(BaseModel):
    dataset_id: str
    domain: DomainIdentitySchema
    dataset_grain: Optional[DatasetGrainSchema] = None
    entities: List[DetectedEntitySchema] = Field(default_factory=list)
    kpis: List[DomainKpiSchema] = Field(default_factory=list)
    charts: List[DomainChartSpecSchema] = Field(default_factory=list)
    comparisons: List[ComparisonItemSchema] = Field(default_factory=list)
    trends: List[TrendItemSchema] = Field(default_factory=list)
    risks: List[RiskItemSchema] = Field(default_factory=list)
    recommendations: List[RecommendationItemSchema] = Field(default_factory=list)
    skipped_analyses: List[SkippedAnalysisSchema] = Field(default_factory=list)
    decision_dashboard: Optional[DecisionDashboardResponse] = None


class TimeDimensionValidationSchema(BaseModel):
    has_time_dimension: bool = False
    time_column: Optional[str] = None
    date_range: Optional[Dict[str, Any]] = None
    detected_frequency: Optional[str] = None
    missing_dates_count: int = 0
    invalid_dates_count: int = 0
    duplicate_dates_count: int = 0
    has_irregular_intervals: bool = False
    quality_status: str = "Healthy"
    notes: List[str] = Field(default_factory=list)


class PeriodComparisonSchema(BaseModel):
    current_period: str
    previous_period: str
    current_val: float
    previous_val: float
    absolute_change: float
    pct_change: Optional[float] = None
    growth_direction: str
    best_period: Optional[str] = None
    best_val: Optional[float] = None
    worst_period: Optional[str] = None
    worst_val: Optional[float] = None


class TrendPointSchema(BaseModel):
    date: str
    formatted_date: str
    value: float
    moving_avg_3: Optional[float] = None
    moving_avg_7: Optional[float] = None
    is_spike: bool = False
    is_drop: bool = False
    anomaly_score: Optional[float] = None


class CategoryTrendSchema(BaseModel):
    category: str
    previous_val: float
    current_val: float
    absolute_change: float
    pct_change: Optional[float] = None
    direction: str
    series: List[Dict[str, Any]] = Field(default_factory=list)


class SpikeDropSchema(BaseModel):
    date: str
    value: float
    expected_value: float
    deviation_sigma: float
    type: Literal["spike", "drop"]
    description: str


class PracticalTrendAnswersSchema(BaseModel):
    metric_analyzed: str
    previous_value_text: str
    current_value_text: str
    absolute_change_text: str
    pct_change_text: str
    best_period_text: str
    worst_period_text: str
    categories_increased: List[str] = Field(default_factory=list)
    categories_declined: List[str] = Field(default_factory=list)
    stability_text: str
    outliers_text: str
    next_investigation_text: str


class MetricDescriptorSchema(BaseModel):
    column_name: str
    display_name: str
    description: str
    semantic_type: str
    group: str  # "Performance Metrics", "Volume Metrics", "Cost Metrics", "Operations Metrics", "Other Measures"
    recommended_aggregation: Literal["sum", "mean", "median", "count"]
    unit: str  # "Currency", "Count", "Days", "Percentage", "Units", "Score", "Rating", "None"
    confidence: float = 1.0
    missing_count: int = 0
    missing_percentage: float = 0.0
    data_availability: str = "100% Complete"
    preview_value: Optional[float] = None
    is_primary_recommendation: bool = False
    recommendation_reason: Optional[str] = None


class MetricContextSchema(BaseModel):
    metric_display_name: str
    source_column: str
    semantic_type: str
    aggregation_method: str
    time_column: str
    time_granularity: str
    records_included: int
    records_excluded: int
    missing_percentage: float
    calculation_explanation: str
    limitations: List[str] = Field(default_factory=list)


class DomainTrendInterpretationSchema(BaseModel):
    domain_id: str
    domain_name: str
    metric_name: str
    metric_role: str
    direction: Literal["increasing", "decreasing", "stable", "fluctuating", "insufficient_data"]
    actual_change_text: str
    contextual_interpretation: str
    business_sentiment: Literal["positive", "negative", "neutral", "warning", "concern", "improvement", "informational"]
    confidence: float = 0.85
    confidence_level: Literal["High", "Moderate", "Neutral / Unassumed"] = "High"
    qualification: str = ""
    distinction_note: Optional[str] = None


class TrendSummarySchema(BaseModel):
    trend_status: Literal["Increasing", "Decreasing", "Stable", "Fluctuating", "Insufficient Data"]
    status_description: str
    plain_english_summary: str
    latest_period: str
    latest_value: float
    previous_period: Optional[str] = None
    previous_value: Optional[float] = None
    latest_change_absolute: Optional[float] = None
    latest_change_pct: Optional[float] = None
    overall_period_change_pct: Optional[float] = None
    highest_period: Optional[str] = None
    highest_value: Optional[float] = None
    lowest_period: Optional[str] = None
    lowest_value: Optional[float] = None
    data_sufficiency: Literal["Robust", "Moderate", "Limited", "Insufficient"]
    data_sufficiency_note: str


class TrendsIntelligenceResponse(BaseModel):
    dataset_id: str
    has_time_dimension: bool
    time_validation: TimeDimensionValidationSchema
    # Structured Metric Explorer
    metrics_catalog: List[MetricDescriptorSchema] = Field(default_factory=list)
    primary_metric: Optional[str] = None
    primary_metric_reason: Optional[str] = None
    selected_metric: Optional[str] = None
    selected_metric_descriptor: Optional[MetricDescriptorSchema] = None
    metric_context: Optional[MetricContextSchema] = None
    # Domain-Aware Interpretation
    domain_interpretation: Optional[DomainTrendInterpretationSchema] = None
    # Trend Summary & Insights
    trend_summary: Optional[TrendSummarySchema] = None
    what_this_chart_tells_you: List[str] = Field(default_factory=list)
    metric_interpretation: Optional[str] = None
    # Backward compatibility & Granularity
    available_metrics: List[str] = Field(default_factory=list)
    available_categories: List[str] = Field(default_factory=list)
    selected_granularity: str = "auto"
    available_granularities: List[str] = Field(default_factory=lambda: ["D", "W", "M", "Q", "Y"])
    period_comparison: Optional[PeriodComparisonSchema] = None
    volatility_cv: Optional[float] = None
    stability_rating: str = "Stable"
    time_series: List[TrendPointSchema] = Field(default_factory=list)
    category_trends: List[CategoryTrendSchema] = Field(default_factory=list)
    spikes_and_drops: List[SpikeDropSchema] = Field(default_factory=list)
    practical_answers: Optional[PracticalTrendAnswersSchema] = None
    limitations: List[str] = Field(default_factory=list)


class ForecastPointSchema(BaseModel):
    period: str
    forecast: float
    lower_bound_80: float
    upper_bound_80: float
    lower_bound_95: float
    upper_bound_95: float


class HistoricalPointSchema(BaseModel):
    period: str
    actual: float


class ForecastResponse(BaseModel):
    dataset_id: str
    is_available: bool
    unavailable_reason: Optional[str] = None
    metric: Optional[str] = None
    metric_label: Optional[str] = None
    selection_rationale: Optional[str] = None
    available_metrics: List[str] = Field(default_factory=list)
    time_column: Optional[str] = None
    horizon: int = 6
    frequency: Optional[str] = "D"
    frequency_label: Optional[str] = "Daily"
    method_used: str = "Holt's Linear Exponential Smoothing"
    historical_points: List[HistoricalPointSchema] = Field(default_factory=list)
    forecast_points: List[ForecastPointSchema] = Field(default_factory=list)
    historical_range: Dict[str, Any] = Field(default_factory=dict)
    forecast_range: Dict[str, Any] = Field(default_factory=dict)
    latest_actual: Optional[float] = None
    final_forecast: Optional[float] = None
    absolute_change: Optional[float] = None
    projected_growth_pct: Optional[float] = None
    accuracy_metrics: Dict[str, Optional[float]] = Field(default_factory=dict)
    validation_summary: Dict[str, Any] = Field(default_factory=dict)
    method_comparison: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = 0.85
    domain_interpretation: Optional[str] = None
    unit: Optional[str] = None
    currency_symbol: Optional[str] = None
    horizon_warning: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Forecasts are mathematical extrapolations of historical patterns based on in-sample data. "
        "They do not account for unforeseen external events or structural market shifts. Not guaranteed outcomes."
    )


class DataQualityCheckSchema(BaseModel):
    id: str
    name: str
    category: str
    status: Literal["Pass", "Warning", "Critical"]
    severity: Literal["info", "warning", "critical"]
    affected_columns: List[str] = Field(default_factory=list)
    message: str
    recommendation: str


class ColumnQualityDiagnosticSchema(BaseModel):
    column_name: str
    dtype: str
    total_count: int
    missing_count: int
    missing_pct: float
    unique_count: int
    duplicate_count: int
    negative_count: int
    zero_count: int
    outlier_count: int
    issues: List[str] = Field(default_factory=list)


class DataQualityReportResponse(BaseModel):
    dataset_id: str
    overall_score: int
    status: Literal["Healthy", "Warning", "Critical"]
    summary: str
    issue_counts: Dict[str, int] = Field(default_factory=lambda: {"critical": 0, "warning": 0, "info": 0})
    checks: List[DataQualityCheckSchema] = Field(default_factory=list)
    column_diagnostics: Dict[str, ColumnQualityDiagnosticSchema] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class CompetitorEntitySchema(BaseModel):
    rank: int
    name: str
    is_our_entity: bool = False
    revenue: Optional[float] = None
    revenue_formatted: Optional[str] = None
    profit: Optional[float] = None
    profit_formatted: Optional[str] = None
    profit_margin_pct: Optional[float] = None
    market_share_pct: Optional[float] = None
    units_sold: Optional[float] = None
    units_sold_formatted: Optional[str] = None
    growth_rate_pct: Optional[float] = None
    pricing_index: Optional[float] = None
    pricing_index_formatted: Optional[str] = None
    records_count: int = 0
    status_label: str = "Reported Competitor"


class MarketGapSchema(BaseModel):
    title: str
    gap_type: Literal["revenue_gap", "margin_gap", "growth_gap", "pricing_gap", "share_gap"]
    metric_name: str
    leader_entity: str
    trailing_entity: str
    absolute_difference: float
    formatted_difference: str
    pct_difference: float
    factual_statement: str
    evidence: str


class MarketStrategyRecommendationSchema(BaseModel):
    title: str
    category: Literal["pricing_strategy", "cost_efficiency", "growth_expansion", "product_focus", "market_share"]
    priority: Literal["high", "medium", "low"]
    metric: str
    comparison: str
    evidence: str
    suggested_investigation: str
    limitation: str


class CompetitionTimeComparisonSchema(BaseModel):
    is_available: bool = False
    time_column: Optional[str] = None
    granularity: Optional[str] = None
    period_labels: List[str] = Field(default_factory=list)
    segment_series: List[Dict[str, Any]] = Field(default_factory=list)
    fastest_growing: Optional[str] = None
    fastest_growing_rate: Optional[float] = None
    most_declining: Optional[str] = None
    most_declining_rate: Optional[float] = None
    summary: Optional[str] = None


class MarketOverviewSchema(BaseModel):
    industry_market_name: str
    competitor_column: str
    competitor_column_label: str
    total_competitors_tracked: int
    total_reported_market_revenue: Optional[float] = None
    total_reported_market_revenue_formatted: Optional[str] = None
    reporting_period: Optional[str] = None
    data_coverage_description: str
    top_competitor_name: str
    top_competitor_metric_value: float
    top_competitor_metric_formatted: str
    benchmark_average_revenue: Optional[float] = None
    benchmark_average_revenue_formatted: Optional[str] = None
    primary_metric: str
    primary_metric_label: str
    summary_statement: str


class MarketBenchmarkPreviewResponse(BaseModel):
    is_valid: bool
    filename: str
    company_count: int
    companies_sample: List[str] = Field(default_factory=list)
    industry: Optional[str] = None
    reporting_period: Optional[str] = None
    detected_fields: List[str] = Field(default_factory=list)
    missing_required_fields: List[str] = Field(default_factory=list)
    missing_optional_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    sample_records: List[Dict[str, Any]] = Field(default_factory=list)
    validation_summary: str


class CompetitionIntelligenceResponse(BaseModel):
    dataset_id: str
    is_available: bool = False
    market_data_status: Literal["market_data_detected", "market_data_absent", "insufficient_data"] = "market_data_absent"
    status_title: str = "Market competition analysis is not available yet."
    unavailable_reason: Optional[str] = None
    summary_statement: str = "Your current dataset contains internal transaction data, but no verified competitor or market benchmark data."
    domain_id: Optional[str] = None
    domain_name: Optional[str] = None
    currency_symbol: Optional[str] = None
    has_external_benchmark: bool = False
    benchmark_filename: Optional[str] = None
    overview: Optional[MarketOverviewSchema] = None
    competitors: List[CompetitorEntitySchema] = Field(default_factory=list)
    market_gaps: List[MarketGapSchema] = Field(default_factory=list)
    strategic_recommendations: List[MarketStrategyRecommendationSchema] = Field(default_factory=list)
    time_comparison: Optional[CompetitionTimeComparisonSchema] = None
    missing_requirements: List[str] = Field(default_factory=list)
    required_market_fields: List[Dict[str, Any]] = Field(default_factory=list)
    market_limitations: List[str] = Field(default_factory=list)
    methodology_notes: List[str] = Field(default_factory=list)
class RecommendationsOverviewSchema(BaseModel):
    total_recommendations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    evidence_backed_count: int
    data_limitations_summary: List[str] = Field(default_factory=list)
    summary_statement: str


class ActionPlanSchema(BaseModel):
    immediate_action: str
    follow_up_investigation: str
    metric_to_monitor: str
    suggested_review_period: Optional[str] = None
    data_required: str


class EvidenceRecommendationSchema(BaseModel):
    rec_id: str
    title: str
    category: Literal[
        "performance_improvement",
        "risk_mitigation",
        "cost_optimization",
        "revenue_opportunities",
        "data_quality",
        "operational_efficiency",
        "market_competitive_actions",
    ]
    category_label: str
    priority: Literal["critical", "high", "medium", "low"]
    priority_reason: str
    business_problem: str
    why_it_matters: str
    evidence: str
    short_summary: Optional[str] = None
    what_we_found: List[str] = Field(default_factory=list)
    action_steps: List[str] = Field(default_factory=list)
    expected_result: Optional[str] = None
    key_metrics: List[Dict[str, str]] = Field(default_factory=list)
    metric_name: Optional[str] = None
    entity_name: Optional[str] = None
    current_value: Optional[str] = None
    baseline_value: Optional[str] = None
    pct_change: Optional[str] = None
    root_cause_signal: str
    recommended_action: str
    expected_objective: str
    data_required: str
    limitations: str
    problem_detected: Optional[str] = None
    observation: Optional[str] = None
    interpretation: Optional[str] = None
    success_measure: Optional[str] = None
    action_plan: Optional[ActionPlanSchema] = None
    suggested_investigation_route: Optional[str] = None
    suggested_investigation_label: Optional[str] = None
    relevant_metric: Optional[str] = None
    source_columns: List[str] = Field(default_factory=list)
    time_period: Optional[str] = None
    evidence_strength: Literal[
        "verified_statistical_finding",
        "strong_trend_correlation",
        "data_hygiene_warning",
        "exploratory_pattern",
    ] = "verified_statistical_finding"

    @model_validator(mode="after")
    def populate_backwards_compat_fields(self) -> "EvidenceRecommendationSchema":
        if not self.problem_detected:
            self.problem_detected = self.business_problem
        if not self.observation:
            self.observation = self.evidence
        if not self.interpretation:
            self.interpretation = self.root_cause_signal
        if not self.success_measure:
            self.success_measure = self.expected_result or self.expected_objective
        return self



class RecommendationsIntelligenceResponse(BaseModel):
    dataset_id: str
    is_available: bool = True
    domain_id: str = "general"
    domain_name: str = "General Analytics"
    currency_symbol: Optional[str] = None
    overview: RecommendationsOverviewSchema
    recommendations: List[EvidenceRecommendationSchema] = Field(default_factory=list)
    categories_present: List[str] = Field(default_factory=list)
    has_time_dimension: bool = False
    analyzed_at: Optional[str] = None





