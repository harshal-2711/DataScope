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
  category: string
  label: "Potential anomaly" | "Requires investigation" | "Unusual pattern detected"
  description: string
  severity: "low" | "medium" | "high"
  affected_column: string | null
  evidence: string
  recommended_action: string
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
}

export interface CategoricalStats {
  valid_count: number
  null_count: number
  null_pct: number
  unique_count: number
  cardinality_ratio: number
  mode?: string | null
  top_values: Array<{ value: string; count: number; pct: number }>
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

export interface DomainIntelligenceResponse {
  dataset_id: string
  domain: DomainIdentity
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
}
