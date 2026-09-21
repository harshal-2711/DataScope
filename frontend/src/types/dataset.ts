export type FileType = "csv" | "xlsx" | "xls"

export interface DatasetPreviewRow {
  [column: string]: string | number | boolean | null
}

export interface ColumnInference {
  name: string
  original_type: string
  inferred_type: string
  confidence: number
  missing_count: number
  missing_percentage: number
  unique_count: number
  sample_values: any[]
  warnings: string[]
}

export interface FileDiagnostics {
  encoding_used: string
  delimiter_used: string
  duplicate_columns_renamed: string[]
  malformed_rows_skipped: number
  warnings: string[]
}

export interface DatasetSummary {
  dataset_id: string
  filename: string
  file_type: FileType
  row_count: number
  column_count: number
  columns: string[]
  dtypes: Record<string, string>
  inferred_columns?: ColumnInference[]
  diagnostics?: FileDiagnostics | null
  preview: DatasetPreviewRow[]
}

export type UploadState =
  | { status: "idle" }
  | { status: "selected"; file: File }
  | { status: "processing"; file: File }
  | { status: "success"; file: File; summary: DatasetSummary }
  | { status: "error"; file: File | null; message: string }

// ---- Phase 3: automatic visualization ----------------------------------

export type ColumnRole =
  | "numeric"
  | "categorical"
  | "datetime"
  | "boolean"
  | "identifier"
  | "high_cardinality"
  | "ignore"

export interface ColumnProfile {
  name: string
  role: ColumnRole
  dtype: string
  non_null_count: number
  null_count: number
  distinct_count: number
  reason: string
}

export type ChartType = "bar" | "line" | "pie" | "histogram" | "scatter"

export interface ChartDataPoint {
  x: string | number | boolean | null
  y: string | number | boolean | null
  range_low?: number
  range_high?: number
  percent?: number
  id?: string
}

export interface ChartSpec {
  id: string
  chart_type: ChartType
  title: string
  description: string
  x_label: string
  y_label: string
  data: ChartDataPoint[]
  dimension_column?: string | null
  metric_column?: string | null
  analytical_question?: string | null
  metric_definition?: string | null
  unit?: string | null
  aggregation?: string | null
  grouping?: string | null
  time_granularity?: string | null
  dataset_grain?: string | null
  data_coverage?: string | null
  explanation?: string | null
  limitations?: string | null
}

export interface Kpi {
  label: string
  value: number
  kind: "sales" | "profit" | "quantity" | "discount" | "orders" | "average" | "generic"
  format: "number" | "count"
}

export interface RecommendationsResponse {
  dataset_id: string
  chart_count: number
  charts: ChartSpec[]
  column_profiles: ColumnProfile[]
  kpis: Kpi[]
}

export interface DrilldownResponse {
  dataset_id: string
  dimension: string
  dimension_label: string
  value: string
  row_count: number
  kpis: Kpi[]
  trend_chart: ChartSpec | null
  secondary_chart: ChartSpec | null
  // Present when secondary_chart's bars can themselves be drilled into a
  // further level; null when no further meaningful dimension exists.
  secondary_dimension: string | null
  applied_filters: { dimension: string; value: string }[]
}
