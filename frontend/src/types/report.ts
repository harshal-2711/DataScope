export interface ReportMetadata {
  report_title: string
  dataset_name: string
  dataset_id: string
  generated_at: string
  domain_id: string
  domain_name: string
  row_count: number
  column_count: number
  reporting_period: string
  currency_symbol?: string | null
  data_quality_score: number
  available_sections_count: number
  total_sections_count: number
}

export interface ExecutiveSummary {
  dataset_name: string
  row_count: number
  column_count: number
  domain_name: string
  reporting_period: string
  currency_symbol?: string | null
  overall_performance_summary: string
  overall_business_condition?: string
  total_sales_revenue?: string | null
  total_cost_expense?: string | null
  total_profit_loss?: string | null
  profit_margin_pct?: string | null
  growth_or_decline_text?: string | null
  total_orders_count?: string | null
  average_order_value?: string | null
  total_units_sold?: string | null
  average_discount_pct?: string | null
  overall_business_health: string
  major_positive_findings?: string[]
  major_negative_findings?: string[]
  key_findings: string[]
  most_important_risks: string[]
  priority_corrective_actions: string[]
  top_3_recommended_actions?: string[]
}

export interface ColumnSummaryItem {
  column_name: string
  dtype: string
  semantic_role: string
  missing_count: number
  missing_pct: number
  unique_count: number
  sample_values: string[]
}

export interface DatasetOverviewReport {
  dimensions_text: string
  row_count: number
  column_count: number
  columns_summary: ColumnSummaryItem[]
  detected_date_range?: string | null
  has_date_dimension: boolean
  data_quality_score: number
  data_quality_status: "Healthy" | "Warning" | "Critical"
  missing_cells_count: number
  missing_cells_pct: number
  duplicate_rows_count: number
  duplicate_rows_pct: number
  important_limitations: string[]
}

export interface SixPointFinding {
  observation_title: string
  what_happened: string
  business_meaning: string
  why_it_matters: string
  recommended_action: string
  evidence: string
  limitations: string
}

export interface PerformancePerformerItem {
  entity_type: string
  name: string
  metric_name: string
  formatted_value: string
  raw_value?: number | null
  percentage_share?: number | null
  note?: string | null
}

export interface PerformanceMetricItem {
  name: string
  formatted_value: string
  raw_value?: number | null
  unit?: string | null
  status: "Available" | "Calculated" | "Estimated" | "Unavailable"
  business_meaning: string
  source_column?: string | null
  comparison_with_previous?: string | null
  requires_attention?: boolean
  attention_reason?: string | null
}

export interface BusinessPerformanceReport {
  is_available: boolean
  unavailable_reason?: string | null
  total_sales_revenue?: string | null
  total_profit_loss?: string | null
  profit_margin_pct?: string | null
  average_order_value?: string | null
  growth_rate_pct?: string | null
  performance_direction?: "growth" | "decline" | "stable" | "neutral" | null
  metric_highlights: PerformanceMetricItem[]
  top_performers: PerformancePerformerItem[]
  underperformers: PerformancePerformerItem[]
  six_point_findings?: SixPointFinding[]
  summary_text: string
}

export interface ProfitLossSegmentItem {
  name: string
  segment_type: string
  revenue_formatted: string
  profit_loss_formatted: string
  profit_margin_pct: number
  discount_rate_pct?: number | null
  issue_type: "loss_maker" | "high_sales_low_profit" | "discount_bleed" | "healthy"
  explanation: string
  calculation_basis?: string | null
  status_type?: "confirmed_finding" | "signal_requiring_validation"
  actionable_response?: string | null
}

export interface ProfitLossReport {
  is_available: boolean
  unavailable_reason?: string | null
  revenue_trend_summary: string
  profit_trend_summary: string
  profit_margin_summary: string
  loss_making_segments: ProfitLossSegmentItem[]
  high_sales_low_profit_segments: ProfitLossSegmentItem[]
  discount_margin_observations: string[]
  changes_explanation: string[]
}

export interface CustomerSegmentItem {
  segment_name: string
  customer_count_formatted?: string | null
  revenue_formatted: string
  revenue_share_pct: number
  aov_formatted: string
  profit_formatted?: string | null
  profit_margin_pct?: number | null
  business_implication: string
  marketing_strategy: string
}

export interface CustomerSegmentAnalysis {
  is_available: boolean
  unavailable_reason?: string | null
  dimension_analyzed?: string | null
  segments: CustomerSegmentItem[]
  concentration_observation?: string | null
  strategic_summary: string
}

export interface RegionalChannelItem {
  name: string
  dimension_type: string
  revenue_formatted: string
  revenue_share_pct: number
  order_volume: number
  operational_observation: string
}

export interface RegionalChannelAnalysis {
  is_available: boolean
  unavailable_reason?: string | null
  dimension_name?: string | null
  items: RegionalChannelItem[]
  operational_takeaway: string
}

export interface RootCauseItem {
  issue_title: string
  confirmed_observation: string
  possible_contributing_factors: string[]
  data_needed_for_validation: string[]
  recommended_investigation: string
}

export interface RootCauseAnalysisReport {
  is_available: boolean
  summary_statement: string
  root_causes: RootCauseItem[]
}

export interface DiscountPricingReport {
  is_available: boolean
  unavailable_reason?: string | null
  average_discount_pct?: string | null
  high_discount_revenue?: string | null
  high_discount_transaction_count: number
  margin_erosion_estimate?: string | null
  discount_tier_observations: string[]
  suggested_controls: string[]
  validation_requirements?: string[]
}

export interface InventoryReport {
  is_available: boolean
  unavailable_reason?: string | null
  total_stock_units?: string | null
  low_stock_count: number
  overstocked_count: number
  inventory_turnover_observation: string
  reorder_alerts: string[]
  inventory_items: Array<Record<string, any>>
}

export interface TrendPeriodComparisonItem {
  metric: string
  time_period: string
  previous_value?: number | null
  previous_value_formatted: string
  current_value?: number | null
  current_value_formatted: string
  absolute_change?: number | null
  absolute_change_formatted: string
  pct_change?: number | null
  pct_change_formatted: string
  is_positive: boolean
  direction: "increasing" | "decreasing" | "stable" | "fluctuating"
}

export interface TrendsReport {
  is_available: boolean
  unavailable_reason?: string | null
  analyzed_metric?: string | null
  time_column?: string | null
  time_period?: string | null
  selected_granularity: string
  period_comparison?: TrendPeriodComparisonItem | null
  upward_trends: string[]
  downward_trends: string[]
  peak_period?: string | null
  peak_value_formatted?: string | null
  lowest_period?: string | null
  lowest_value_formatted?: string | null
  seasonality_notes?: string | null
  volatility_assessment: string
  plain_language_interpretation: string
  limitations: string[]
}

export interface ForecastPointItem {
  period: string
  forecast_formatted: string
  forecast_raw: number
  lower_bound_80_formatted: string
  upper_bound_80_formatted: string
  lower_bound_95_formatted: string
  upper_bound_95_formatted: string
}

export interface ForecastReport {
  is_available: boolean
  unavailable_reason?: string | null
  forecasted_metric?: string | null
  time_horizon_periods: number
  frequency_label: string
  method_used: string
  latest_actual_formatted?: string | null
  final_forecast_formatted?: string | null
  projected_change_formatted?: string | null
  projected_growth_pct?: number | null
  forecast_points: ForecastPointItem[]
  confidence_score: number
  forecast_limitations: string[]
  plain_language_interpretation: string
  disclaimer: string
}

export interface VerifiedRiskItem {
  risk_id: string
  title: string
  severity: "low" | "medium" | "high" | "critical"
  category: string
  evidence: string
  affected_metric_or_segment: string
  business_impact: string
  why_it_matters?: string
  recommended_action: string
  qualification?: string | null
  data_required_for_validation?: string
  confidence_level?: string
}

export interface RiskDistributionInsight {
  dimension: string
  dominant_category: string
  percentage: number
  description: string
  observation_note: string
}

export interface RisksReport {
  is_available: boolean
  unavailable_reason?: string | null
  health_status: "Healthy" | "Attention Required" | "Critical Risks Identified"
  summary_statement: string
  total_risks_count: number
  high_severity_count: number
  medium_severity_count: number
  low_severity_count: number
  verified_risks: VerifiedRiskItem[]
  distribution_insights: RiskDistributionInsight[]
  data_safety_notes: string[]
}

export interface CompetitorComparisonItem {
  rank: number
  name: string
  is_our_entity: boolean
  revenue_formatted: string
  profit_formatted: string
  profit_margin_pct?: number | null
  market_share_pct?: number | null
  growth_rate_pct?: number | null
  pricing_index_formatted: string
  status_label: string
}

export interface CompetitionReport {
  is_available: boolean
  status_title: string
  summary_statement: string
  unavailable_reason?: string | null
  has_external_benchmark: boolean
  benchmark_filename?: string | null
  total_competitors_tracked: number
  competitors: CompetitorComparisonItem[]
  market_gaps: string[]
  strategic_actions: string[]
  required_market_fields: Array<{
    field: string
    type: string
    importance: string
    purpose: string
  }>
  market_limitations: string[]
}

export interface UnifiedRecommendationItem {
  rec_id: string
  title: string
  category: string
  priority: "critical" | "high" | "medium" | "low"
  problem: string
  evidence: string
  business_impact: string
  exact_recommended_action: string
  action_steps?: string[]
  expected_objective: string
  suggested_owner_team: string
  metric_to_track: string
  suggested_review_period: string
  data_limitations: string
}

export interface RecommendationsReport {
  is_available: boolean
  unavailable_reason?: string | null
  total_recommendations: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  summary_statement: string
  recommendations_list: UnifiedRecommendationItem[]
}

export interface CorrectiveActionItem {
  priority: "Critical" | "High" | "Medium" | "Low"
  problem: string
  recommended_action: string
  owner_team: string
  metric_to_track: string
  review_period: string
}

export interface CorrectiveActionPlan {
  is_available: boolean
  action_items: CorrectiveActionItem[]
  disclaimer: string
}

export interface ConclusionReport {
  main_findings: string[]
  most_urgent_issues: string[]
  opportunities: string[]
  recommended_next_steps: string[]
  important_limitations: string[]
  areas_requiring_additional_data: string[]
}

export interface MethodologyAuditTrail {
  domain_rule_applied: string
  statistical_checks_performed: string[]
  granularity_grain_description: string
  evidence_baseline: string
  generated_timestamp: string
}

export interface ComprehensiveReport {
  metadata: ReportMetadata
  executive_summary: ExecutiveSummary
  business_performance: BusinessPerformanceReport
  profit_loss: ProfitLossReport
  customer_segment_analysis?: CustomerSegmentAnalysis | null
  regional_channel_analysis?: RegionalChannelAnalysis | null
  discount_pricing?: DiscountPricingReport | null
  inventory_analysis?: InventoryReport | null
  root_cause_analysis?: RootCauseAnalysisReport | null
  trends_intelligence: TrendsReport
  risks_anomalies: RisksReport
  market_competition: CompetitionReport
  recommendations: RecommendationsReport
  corrective_action_plan: CorrectiveActionPlan
  forecasting: ForecastReport
  data_driven_conclusion: ConclusionReport
  dataset_overview: DatasetOverviewReport
  methodology_audit?: MethodologyAuditTrail | null
}

export type ComprehensiveReportResponse = ComprehensiveReport

