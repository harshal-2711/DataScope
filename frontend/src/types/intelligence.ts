export interface DomainIdentity {
  domain_id: string
  name: string
  description: string
  keywords: string[]
  confidence: number
  evidence: string[]
  alternative_domains: string[]
}

export interface DetectedEntity {
  entity_type: string
  label: string
  matched_column: string | null
  confidence: number
  evidence: string
}

export interface DomainKpi {
  id: string
  name: string
  description: string
  value: number | string | null
  format: "currency" | "percentage" | "number" | "duration"
  aggregation: string
  matched_columns: string[]
  business_meaning: string
  is_reliable: boolean
  skip_reason?: string | null
  unit?: string | null
  formatted_value?: string | null
  source_column?: string | null
  formatting_rule?: string | null
}

export interface DomainChartSpec {
  id: string
  title: string
  chart_type: "bar" | "line" | "pie" | "histogram" | "scatter"
  x_label: string
  y_label: string
  dimension_column?: string | null
  metric_column?: string | null
  aggregation: string
  data: Array<{ x: string | number | boolean | null; y: string | number | boolean | null }>
  business_question: string
  skip_reason?: string | null
  analytical_question?: string | null
  metric_definition?: string | null
  unit?: string | null
  grouping?: string | null
  time_granularity?: string | null
  dataset_grain?: string | null
  data_coverage?: string | null
  explanation?: string | null
  limitations?: string | null
}

export interface ComparisonItem {
  comparison_type: string
  title: string
  baseline: string
  target: string
  metric: string
  baseline_value: number | null
  target_value: number | null
  difference: number | null
  pct_change: number | null
  insight: string
  data: Array<{ category: string; value: number }>
}

export interface TrendDataPoint {
  date: string
  value: number
  moving_avg: number
}

export interface TrendItem {
  metric_name: string
  time_column: string
  trend_direction: "increasing" | "decreasing" | "stable" | "fluctuating" | "insufficient_data"
  growth_rate_pct: number | null
  peak_period: string | null
  trough_period: string | null
  seasonality_detected: boolean
  description: string
  data_points: TrendDataPoint[]
}

export interface RiskItem {
  risk_id: string
  title?: string
  category: string
  label: "Potential anomaly" | "Requires investigation" | "Unusual pattern detected" | string
  description: string
  severity: "low" | "medium" | "high"
  severity_reason?: string
  affected_metric?: string | null
  affected_column?: string | null
  current_value?: number | null
  current_value_formatted?: string | null
  previous_value?: number | null
  previous_value_formatted?: string | null
  absolute_change?: number | null
  absolute_change_formatted?: string | null
  pct_change?: number | null
  unit?: string | null
  time_period?: string | null
  evidence: string
  why_it_matters?: string | null
  confidence?: number
  qualification?: string | null
  recommended_action: string
  risk_type?: string
  time_series_preview?: Array<{ period: string; value: number }>
}

export interface RiskOverview {
  total_risks: number
  high_count: number
  medium_count: number
  low_count: number
  most_significant_risk?: RiskItem | null
  data_quality_warnings_count: number
  health_status: "Healthy" | "Attention Required" | "Critical Risks Identified"
  summary_statement: string
}

export interface DistributionInsight {
  insight_id: string
  dimension: string
  dimension_label: string
  dominant_category: string
  category_count: number
  total_records: number
  percentage: number
  description: string
  observation_note: string
}

export interface RiskIntelligenceResponse {
  dataset_id: string
  domain_id: string
  domain_name: string
  overview: RiskOverview
  risks: RiskItem[]
  distribution_insights?: DistributionInsight[]
  categories: string[]
  affected_metrics: string[]
  has_time_dimension: boolean
  data_safety_notes: string[]
}


export interface RecommendationItem {
  rec_id: string
  category: string
  title: string
  finding: string
  supporting_metric: string
  relevant_columns: string[]
  time_period: string | null
  entities_involved: string[]
  severity: string | null
  confidence: number
  evidence: string
  recommended_action: string
  limitations: string
}

export interface SkippedAnalysis {
  analysis_type: string
  item_id: string
  name: string
  reason: string
}

export interface ValidationCheck {
  component_type: string
  component_id: string
  title: string
  status: "Valid" | "Needs Review" | "Unsupported"
  reason: string
  details?: Record<string, any>
}

export interface ValidationReport {
  overall_status: "Valid" | "Needs Review" | "Unsupported"
  summary: string
  counts: {
    valid: number
    needs_review: number
    unsupported: number
    total_evaluated: number
  }
  checks: ValidationCheck[]
}

export interface NumericStats {
  valid_count: number
  null_count: number
  null_pct: number
  mean?: number | null
  median?: number | null
  mode?: number | null
  min?: number | null
  max?: number | null
  range?: number | null
  variance?: number | null
  std_dev?: number | null
  iqr?: number | null
  p25?: number | null
  p50?: number | null
  p75?: number | null
  p90?: number | null
  p99?: number | null
  outlier_count_iqr?: number
  outlier_count_zscore?: number
  unit?: string
  semantic_type?: string
  currency_symbol?: string | null
}

export interface CategoricalStats {
  valid_count: number
  null_count: number
  null_pct: number
  unique_count: number
  cardinality_ratio: number
  mode?: string | null
  top_values: Array<{ value: string; count: number; pct: number }>
  unit?: string
  semantic_type?: string
}

export interface UniversalStatistics {
  dataset_summary: {
    row_count: number
    column_count: number
    total_cells: number
    missing_cells: number
    missing_pct: number
    duplicate_rows: number
    duplicate_pct: number
    numeric_column_count: number
    categorical_column_count: number
  }
  numeric_statistics: Record<string, NumericStats>
  categorical_statistics: Record<string, CategoricalStats>
  correlation_matrix: Record<string, Record<string, number | null>>
}

export interface MetricStatus {
  id: string
  name: string
  value: number | string | null
  formatted_value?: string | null
  status: "Available" | "Calculated" | "Estimated" | "Unavailable"
  explanation: string
  category: string
  business_meaning: string
  formula?: string | null
  unit?: string | null
  source_column?: string | null
  aggregation_method?: string | null
}

export interface SectionChart {
  id: string
  title: string
  business_question: string
  chart_type: "bar" | "line" | "pie" | "histogram" | "scatter"
  metric: string
  grouping: string
  explanation: string
  data: Array<{ x: string | number; y?: number | null; revenue?: number | null; cost?: number | null }>
  x_label?: string | null
  y_label?: string | null
}

export interface DashboardSection {
  section_id: string
  title: string
  description: string
  is_available: boolean
  unavailable_reason?: string | null
  metrics: MetricStatus[]
  charts: SectionChart[]
  highlights: string[]
  insights: Array<{
    finding?: string
    impact?: string
    action?: string
    what_happened?: string
    why_it_happened?: string
    what_to_investigate?: string
    limitations?: string
  }>
}

export interface DecisionDashboardResponse {
  dataset_id: string
  domain_name: string
  executive_summary: DashboardSection
  sales_performance: DashboardSection
  profitability: DashboardSection
  product_analysis: DashboardSection
  operations_inventory: DashboardSection
  insights_recommendations: DashboardSection
}

export interface DatasetGrain {
  grain_type: string
  grain_label: string
  description: string
  primary_entity_column?: string | null
  row_count: number
  unique_entity_count: number
  repeated_observations_count: number
  repetition_ratio: number
  is_one_to_one: boolean
  candidate_entities: Array<{
    column: string
    unique_count: number
    uniqueness_ratio: number
    is_unique_per_row: boolean
  }>
  measures: string[]
  dimensions: string[]
  aggregation_guardrails: string[]
}

export interface DomainIntelligenceResponse {
  dataset_id: string
  domain: DomainIdentity
  dataset_grain?: DatasetGrain
  entities: DetectedEntity[]
  kpis: DomainKpi[]
  charts: DomainChartSpec[]
  comparisons: ComparisonItem[]
  trends: TrendItem[]
  risks: RiskItem[]
  recommendations: RecommendationItem[]
  skipped_analyses: SkippedAnalysis[]
  validation_report?: ValidationReport
  universal_statistics?: UniversalStatistics
  decision_dashboard?: DecisionDashboardResponse
  data_quality_report?: DataQualityReportResponse
}

export interface TimeDimensionValidation {
  has_time_dimension: boolean
  time_column?: string | null
  date_range?: {
    min_date: string
    max_date: string
    total_days: number
    observation_count: number
  } | null
  detected_frequency?: string | null
  missing_dates_count: number
  invalid_dates_count: number
  duplicate_dates_count: number
  has_irregular_intervals: boolean
  quality_status: string
  notes: string[]
}

export interface PeriodComparison {
  current_period: string
  previous_period: string
  current_val: number
  previous_val: number
  absolute_change: number
  pct_change: number | null
  growth_direction: string
  best_period?: string | null
  best_val?: number | null
  worst_period?: string | null
  worst_val?: number | null
}

export interface TrendPoint {
  date: string
  formatted_date: string
  value: number
  moving_avg_3?: number | null
  moving_avg_7?: number | null
  is_spike: boolean
  is_drop: boolean
  anomaly_score?: number | null
}

export interface CategoryTrend {
  category: string
  previous_val: number
  current_val: number
  absolute_change: number
  pct_change: number | null
  direction: string
  series: Array<{ date: string; value: number }>
}

export interface SpikeDrop {
  date: string
  value: number
  expected_value: number
  deviation_sigma: number
  type: "spike" | "drop"
  description: string
}

export interface PracticalTrendAnswers {
  metric_analyzed: string
  previous_value_text: string
  current_value_text: string
  absolute_change_text: string
  pct_change_text: string
  best_period_text: string
  worst_period_text: string
  categories_increased: string[]
  categories_declined: string[]
  stability_text: string
  outliers_text: string
  next_investigation_text: string
}

export interface MetricDescriptor {
  column_name: string
  display_name: string
  description: string
  semantic_type: string
  group: string
  recommended_aggregation: "sum" | "mean" | "median" | "count"
  unit: string
  confidence: number
  missing_count: number
  missing_percentage: number
  data_availability: string
  preview_value?: number | null
  is_primary_recommendation: boolean
  recommendation_reason?: string | null
}

export interface MetricContext {
  metric_display_name: string
  source_column: string
  semantic_type: string
  aggregation_method: string
  time_column: string
  time_granularity: string
  records_included: number
  records_excluded: number
  missing_percentage: number
  calculation_explanation: string
  limitations: string[]
}

export interface TrendSummary {
  trend_status: "Increasing" | "Decreasing" | "Stable" | "Fluctuating" | "Insufficient Data"
  status_description: string
  plain_english_summary: string
  latest_period: string
  latest_value: number
  previous_period?: string | null
  previous_value?: number | null
  latest_change_absolute?: number | null
  latest_change_pct?: number | null
  overall_period_change_pct?: number | null
  highest_period?: string | null
  highest_value?: number | null
  lowest_period?: string | null
  lowest_value?: number | null
  data_sufficiency: "Robust" | "Moderate" | "Limited" | "Insufficient"
  data_sufficiency_note: string
}

export interface DomainTrendInterpretation {
  domain_id: string
  domain_name: string
  metric_name: string
  metric_role: string
  direction: "increasing" | "decreasing" | "stable" | "fluctuating" | "insufficient_data"
  actual_change_text: string
  contextual_interpretation: string
  business_sentiment: "positive" | "negative" | "neutral" | "warning" | "concern" | "improvement" | "informational"
  confidence: number
  confidence_level: "High" | "Moderate" | "Neutral / Unassumed"
  qualification: string
  distinction_note?: string | null
}

export interface TrendsIntelligenceResponse {
  dataset_id: string
  has_time_dimension: boolean
  time_validation: TimeDimensionValidation
  metrics_catalog: MetricDescriptor[]
  primary_metric?: string | null
  primary_metric_reason?: string | null
  selected_metric?: string | null
  selected_metric_descriptor?: MetricDescriptor | null
  metric_context?: MetricContext | null
  domain_interpretation?: DomainTrendInterpretation | null
  trend_summary?: TrendSummary | null
  what_this_chart_tells_you: string[]
  metric_interpretation?: string | null
  available_metrics: string[]
  available_categories: string[]
  selected_granularity: string
  available_granularities: string[]
  period_comparison?: PeriodComparison | null
  volatility_cv?: number | null
  stability_rating: string
  time_series: TrendPoint[]
  category_trends: CategoryTrend[]
  spikes_and_drops: SpikeDrop[]
  practical_answers?: PracticalTrendAnswers | null
  limitations: string[]
}

export interface ForecastPoint {
  period: string
  forecast: number
  lower_bound_80: number
  upper_bound_80: number
  lower_bound_95: number
  upper_bound_95: number
}

export interface HistoricalPoint {
  period: string
  actual: number
}

export interface ForecastMethodEvaluation {
  method_key: string
  method_name: string
  description: string
  in_sample_metrics: {
    mae?: number | null
    rmse?: number | null
    mape?: number | null
  }
  holdout_metrics?: {
    mae?: number | null
    rmse?: number | null
    mape?: number | null
  } | null
  eval_score: number
  is_selected: boolean
}

export interface ForecastResponse {
  dataset_id: string
  is_available: boolean
  unavailable_reason?: string | null
  metric?: string | null
  metric_label?: string | null
  selection_rationale?: string | null
  available_metrics: string[]
  time_column?: string | null
  horizon: number
  frequency?: string | null
  frequency_label?: string | null
  method_used: string
  historical_points: HistoricalPoint[]
  forecast_points: ForecastPoint[]
  historical_range?: {
    start_date: string
    end_date: string
    total_periods: number
  }
  forecast_range?: {
    start_date: string
    end_date: string
    total_periods: number
  }
  latest_actual?: number | null
  final_forecast?: number | null
  absolute_change?: number | null
  projected_growth_pct?: number | null
  accuracy_metrics: {
    mape?: number | null
    rmse?: number | null
    mae?: number | null
  }
  validation_summary?: {
    has_holdout: boolean
    holdout_periods: number
    total_historical_periods: number
    validation_strategy: string
    in_sample_accuracy: {
      mae?: number | null
      rmse?: number | null
      mape?: number | null
    }
    holdout_accuracy?: {
      mae?: number | null
      rmse?: number | null
      mape?: number | null
    } | null
  }
  method_comparison?: ForecastMethodEvaluation[]
  confidence_score: number
  domain_interpretation?: string | null
  unit?: string | null
  currency_symbol?: string | null
  horizon_warning?: string | null
  limitations: string[]
  disclaimer: string
}

export interface DataQualityCheck {
  id: string
  name: string
  category: string
  status: "Pass" | "Warning" | "Critical"
  severity: "info" | "warning" | "critical"
  affected_columns: string[]
  message: string
  recommendation: string
}

export interface ColumnQualityDiagnostic {
  column_name: string
  dtype: string
  total_count: number
  missing_count: number
  missing_pct: number
  unique_count: number
  duplicate_count: number
  negative_count: number
  zero_count: number
  outlier_count: number
  issues: string[]
}

export interface DataQualityReportResponse {
  dataset_id: string
  overall_score: number
  status: "Healthy" | "Warning" | "Critical"
  summary: string
  issue_counts: {
    critical: number
    warning: number
    info: number
  }
  checks: DataQualityCheck[]
  column_diagnostics: Record<string, ColumnQualityDiagnostic>
  recommendations: string[]
}

