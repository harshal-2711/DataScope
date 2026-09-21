import { useState, useEffect, useMemo } from "react"
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
  ComposedChart,
  BarChart,
  Bar,
} from "recharts"
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Calendar,
  Award,
  AlertTriangle,
  HelpCircle,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  CheckCircle2,
  Search,
  Sparkles,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Info,
  Compass,
  Check,
  FileText,
  X,
  ShieldAlert,
} from "lucide-react"
import type { TrendsIntelligenceResponse } from "@/types/intelligence"
import { fetchTrendsIntelligence } from "@/lib/datasetApi"

interface TrendsIntelligenceViewProps {
  datasetId: string
  initialData?: TrendsIntelligenceResponse | null
}

export function TrendsIntelligenceView({
  datasetId,
  initialData,
}: TrendsIntelligenceViewProps) {
  const [data, setData] = useState<TrendsIntelligenceResponse | null>(initialData ?? null)
  const [granularity, setGranularity] = useState<string>("auto")
  const [selectedMetric, setSelectedMetric] = useState<string>("")
  const [selectedCategory, setSelectedCategory] = useState<string>("")
  const [showMovingAverages, setShowMovingAverages] = useState<boolean>(false)
  const [explorerOpen, setExplorerOpen] = useState<boolean>(false)
  const [searchMetricQuery, setSearchMetricQuery] = useState<string>("")
  const [selectedGroupFilter, setSelectedGroupFilter] = useState<string>("all")
  const [showCalcDetails, setShowCalcDetails] = useState<boolean>(false)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTrends = async (g: string, m?: string, c?: string) => {
    setLoading(true)
    setError(null)
    try {
      const json = await fetchTrendsIntelligence(datasetId, g, m, c)
      setData(json)
      if (json.selected_metric) setSelectedMetric(json.selected_metric)
      if (json.selected_granularity) setGranularity(json.selected_granularity)
    } catch (err: any) {
      setError(err.message || "Failed to load trend analysis.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!initialData) {
      fetchTrends(granularity)
    } else {
      setData(initialData)
      if (initialData.selected_metric) setSelectedMetric(initialData.selected_metric)
      if (initialData.selected_granularity) setGranularity(initialData.selected_granularity)
    }
  }, [datasetId, initialData])

  const handleGranularityChange = (newG: string) => {
    setGranularity(newG)
    fetchTrends(newG, selectedMetric, selectedCategory)
  }

  const handleMetricSelect = (newM: string) => {
    setSelectedMetric(newM)
    setExplorerOpen(false)
    fetchTrends(granularity, newM, selectedCategory)
  }

  const handleResetToPrimary = () => {
    if (data?.primary_metric) {
      handleMetricSelect(data.primary_metric)
    }
  }

  const handleCategoryChange = (newC: string) => {
    setSelectedCategory(newC)
    fetchTrends(granularity, selectedMetric, newC)
  }

  // Filter metrics in catalog
  const filteredMetrics = useMemo(() => {
    if (!data?.metrics_catalog) return []
    return data.metrics_catalog.filter((m) => {
      const matchesSearch =
        m.display_name.toLowerCase().includes(searchMetricQuery.toLowerCase()) ||
        m.column_name.toLowerCase().includes(searchMetricQuery.toLowerCase()) ||
        m.description.toLowerCase().includes(searchMetricQuery.toLowerCase())
      const matchesGroup =
        selectedGroupFilter === "all" || m.group === selectedGroupFilter
      return matchesSearch && matchesGroup
    })
  }, [data?.metrics_catalog, searchMetricQuery, selectedGroupFilter])

  // Metric groups available
  const metricGroups = useMemo(() => {
    if (!data?.metrics_catalog) return []
    const groups = Array.from(new Set(data.metrics_catalog.map((m) => m.group)))
    return ["all", ...groups]
  }, [data?.metrics_catalog])

  if (loading && !data) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card p-6 shadow-xs">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Activity className="h-4 w-4 animate-spin text-primary" />
          Computing trends, moving averages, and period comparisons...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center space-y-3">
        <AlertTriangle className="mx-auto h-8 w-8 text-rose-500" />
        <h3 className="text-base font-semibold text-foreground">Trend Analysis Error</h3>
        <p className="max-w-md mx-auto text-xs text-rose-600 dark:text-rose-400">
          {error}
        </p>
        <div className="flex justify-center gap-3 pt-2">
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-md text-xs font-medium border border-border bg-card px-3 py-1.5 shadow-xs hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors"
            onClick={() => fetchTrends(granularity, selectedMetric, selectedCategory)}
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Retry Analysis
          </button>
        </div>
      </div>
    )
  }

  if (!data || !data.has_time_dimension) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card/50 p-8 text-center space-y-3">
        <Clock className="mx-auto h-10 w-10 text-muted-foreground/60" />
        <h3 className="text-base font-semibold text-foreground">No Valid Time Dimension Detected</h3>
        <p className="max-w-md mx-auto text-xs text-muted-foreground">
          {data?.time_validation.notes?.[0] ??
            "This dataset does not contain a recognizable date, timestamp, or year column. Time-series trends, period comparisons, and forecasting require at least one time dimension."}
        </p>
        {data?.available_metrics && data.available_metrics.length > 0 && (
          <div className="pt-2 text-xs text-muted-foreground">
            Available numerical measures found:{" "}
            <span className="font-mono text-foreground">{data.available_metrics.join(", ")}</span>
          </div>
        )}
      </div>
    )
  }

  const timeVal = data.time_validation
  const summary = data.trend_summary
  const activeDesc = data.selected_metric_descriptor
  const context = data.metric_context
  const answers = data.practical_answers
  const isPrimary = activeDesc?.is_primary_recommendation || data.selected_metric === data.primary_metric

  // Format chart title: "[Readable Metric Name] Over Time"
  const metricName = activeDesc?.display_name || "Trend Measure"
  const chartTitle = `${metricName} Over Time`
  const granWord =
    granularity === "D"
      ? "Daily"
      : granularity === "W"
      ? "Weekly"
      : granularity === "M"
      ? "Monthly"
      : granularity === "Q"
      ? "Quarterly"
      : granularity === "Y"
      ? "Yearly"
      : "Period"

  const aggWord = context?.aggregation_method?.toUpperCase() || "SUM"
  const chartSubtitle = `${granWord} ${aggWord} of ${metricName} using ${timeVal.time_column || "date column"}.`

  // Build formula text (e.g. SUM(sales) or AVG(order_aging))
  const formulaText = `${context?.aggregation_method?.toUpperCase() || "SUM"}(${context?.source_column || selectedMetric})`

  return (
    <div className="space-y-6">
      {/* 1. Page Heading Context: Time Dimension & Granularity Controls */}
      <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Calendar className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-sm font-semibold text-foreground">
                  Time Field: <span className="font-mono text-primary">{timeVal.time_column}</span>
                </h3>
                <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-3 w-3" />
                  {timeVal.detected_frequency?.toUpperCase()} FREQUENCY
                </span>
                {timeVal.has_irregular_intervals && (
                  <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400">
                    <AlertTriangle className="h-3 w-3" />
                    Irregular intervals
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Observed Timeline: <strong>{timeVal.date_range?.min_date}</strong> to{" "}
                <strong>{timeVal.date_range?.max_date}</strong> ({timeVal.date_range?.total_days} days,{" "}
                {timeVal.date_range?.observation_count?.toLocaleString()} records)
              </p>
            </div>
          </div>

          {/* Granularity Selector */}
          <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border">
            <span className="text-xs text-muted-foreground px-2 font-medium hidden sm:inline">Granularity:</span>
            {(["D", "W", "M", "Q", "Y"] as const).map((g) => (
              <button
                key={g}
                onClick={() => handleGranularityChange(g)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer ${
                  granularity === g
                    ? "bg-background text-foreground shadow-xs font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {g === "D"
                  ? "Daily"
                  : g === "W"
                  ? "Weekly"
                  : g === "M"
                  ? "Monthly"
                  : g === "Q"
                  ? "Quarterly"
                  : "Yearly"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Selected Primary Metric Experience & Metric Explorer Toggle */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1.5 flex-1 min-w-[280px]">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Primary Metric:
              </span>
              <span className="text-lg font-bold text-foreground">
                {activeDesc?.display_name || selectedMetric}
              </span>
              <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                {activeDesc?.group || "Measures"}
              </span>
              <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                Unit: {activeDesc?.unit || "Units"}
              </span>
              <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                {activeDesc?.data_availability || "100% Complete"}
              </span>
              {isPrimary && (
                <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/10 px-2 py-0.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
                  <Sparkles className="h-3.5 w-3.5" />
                  Recommended Primary Metric
                </span>
              )}
            </div>

            <p className="text-xs text-muted-foreground max-w-3xl">
              {activeDesc?.description}
            </p>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs pt-1">
              <span className="text-muted-foreground">
                <strong>Calculated as:</strong> <code className="font-mono bg-muted px-1.5 py-0.5 rounded text-foreground">{formulaText}</code>
              </span>
              {isPrimary && data.primary_metric_reason && (
                <span className="text-amber-700 dark:text-amber-300 italic">
                  <strong>Why this metric:</strong> {data.primary_metric_reason}
                </span>
              )}
            </div>
          </div>

          {/* Action buttons: Reset to primary & Explore other metrics */}
          <div className="flex items-center gap-2">
            {!isPrimary && (
              <button
                type="button"
                onClick={handleResetToPrimary}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors cursor-pointer"
              >
                <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                Reset to Recommended ({data.metrics_catalog?.find(m => m.column_name === data.primary_metric)?.display_name || "Primary"})
              </button>
            )}
            <button
              type="button"
              onClick={() => setExplorerOpen(!explorerOpen)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90 transition-colors shadow-xs cursor-pointer"
            >
              <Compass className="h-4 w-4" />
              {explorerOpen ? "Close Metric Explorer" : `Explore Another Metric (${data.metrics_catalog?.length || 0})`}
            </button>
          </div>
        </div>

        {/* Structured Metric Explorer Drawer / Modal */}
        {explorerOpen && (
          <div className="pt-4 border-t border-border space-y-4 animate-in fade-in-50 duration-200">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-foreground">Select a Metric to Investigate</h4>
                <p className="text-xs text-muted-foreground">
                  Browse detected numerical measures grouped by business purpose.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setExplorerOpen(false)}
                className="text-muted-foreground hover:text-foreground p-1 rounded-md"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
              {/* Search input */}
              {data.metrics_catalog && data.metrics_catalog.length > 4 && (
                <div className="relative flex-1 min-w-[240px] max-w-md">
                  <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
                  <input
                    type="text"
                    placeholder="Search metric name, column, or description..."
                    value={searchMetricQuery}
                    onChange={(e) => setSearchMetricQuery(e.target.value)}
                    className="w-full h-8 pl-8 pr-3 text-xs rounded-md border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-ring"
                  />
                </div>
              )}

              {/* Group filter pills */}
              <div className="flex flex-wrap items-center gap-1.5">
                {metricGroups.map((g) => (
                  <button
                    key={g}
                    onClick={() => setSelectedGroupFilter(g)}
                    className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors cursor-pointer ${
                      selectedGroupFilter === g
                        ? "bg-secondary text-secondary-foreground font-semibold shadow-xs"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
                    }`}
                  >
                    {g === "all" ? "All Categories" : g}
                  </button>
                ))}
              </div>
            </div>

            {/* Metric Card Grid */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 max-h-84 overflow-y-auto pr-1">
              {filteredMetrics.map((m) => {
                const isSelected = m.column_name === selectedMetric
                const isRec = m.is_primary_recommendation || m.column_name === data.primary_metric
                return (
                  <div
                    key={m.column_name}
                    onClick={() => handleMetricSelect(m.column_name)}
                    className={`p-3.5 rounded-lg border text-left cursor-pointer transition-all space-y-2 ${
                      isSelected
                        ? "border-primary bg-primary/5 ring-1 ring-primary shadow-xs"
                        : "border-border bg-card/60 hover:bg-card hover:border-primary/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <h5 className="text-xs font-bold text-foreground">
                            {m.display_name}
                          </h5>
                          {isRec && (
                            <span className="rounded bg-amber-500/10 px-1.5 py-0.2 text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                              ★ Recommended
                            </span>
                          )}
                        </div>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {m.column_name}
                        </span>
                      </div>
                      {isSelected && (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Check className="h-3 w-3" />
                        </div>
                      )}
                    </div>

                    <p className="text-[11px] text-muted-foreground line-clamp-2">
                      {m.description}
                    </p>

                    <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[10px] text-muted-foreground">
                      <span className="rounded bg-muted px-1.5 py-0.5 font-medium">
                        {m.group}
                      </span>
                      <span className="rounded bg-muted px-1.5 py-0.5 font-medium">
                        Agg: {m.recommended_aggregation.toUpperCase()}
                      </span>
                      <span className="rounded bg-muted px-1.5 py-0.5 font-medium">
                        Unit: {m.unit}
                      </span>
                      <span className="rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 font-medium">
                        {m.data_availability}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* 3. Metric Context & Calculation Transparency (Progressive Disclosure) */}
      {context && (
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-primary" />
              <h4 className="text-xs font-semibold text-foreground">
                Calculation Context: <span className="font-bold">{context.metric_display_name}</span>
              </h4>
            </div>
            <button
              type="button"
              onClick={() => setShowCalcDetails(!showCalcDetails)}
              className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline cursor-pointer"
            >
              {showCalcDetails ? "Hide Calculation Details" : "View Calculation Details"}
              {showCalcDetails ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            </button>
          </div>

          <div className="grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4 pt-1">
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border/40">
              <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Source Column</span>
              <strong className="font-mono text-foreground">{context.source_column}</strong>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border/40">
              <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Aggregation Method</span>
              <strong className="text-foreground">{context.aggregation_method.toUpperCase()}</strong>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border/40">
              <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Time Granularity</span>
              <strong className="text-foreground">{context.time_granularity}</strong>
            </div>
            <div className="p-2.5 rounded-lg bg-muted/40 border border-border/40">
              <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Record Coverage</span>
              <strong className="text-foreground">{context.records_included.toLocaleString()} rows</strong>{" "}
              <span className="text-muted-foreground">({context.missing_percentage}% missing)</span>
            </div>
          </div>

          {showCalcDetails && (
            <div className="pt-3 border-t border-border space-y-2 text-xs text-muted-foreground animate-in fade-in-50 duration-200">
              <p>
                <strong className="text-foreground">Mathematical Formula:</strong> <code className="font-mono bg-muted px-1.5 py-0.5 rounded text-foreground">{formulaText}</code>
              </p>
              <p>
                <strong className="text-foreground">Calculation Explanation:</strong> {context.calculation_explanation}
              </p>
              {context.limitations.length > 0 && (
                <div className="space-y-1 pt-1">
                  <strong className="text-foreground">Important Limitations:</strong>
                  <ul className="list-disc list-inside space-y-0.5">
                    {context.limitations.map((lim, i) => (
                      <li key={i}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 4. Plain-English Trend Summary */}
      {summary && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${
                  summary.trend_status === "Increasing"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : summary.trend_status === "Decreasing"
                    ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                    : summary.trend_status === "Fluctuating"
                    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                    : summary.trend_status === "Stable"
                    ? "bg-sky-500/10 text-sky-600 dark:text-sky-400"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {summary.trend_status === "Increasing" && <TrendingUp className="h-3.5 w-3.5" />}
                {summary.trend_status === "Decreasing" && <TrendingDown className="h-3.5 w-3.5" />}
                {summary.trend_status === "Stable" && <Minus className="h-3.5 w-3.5" />}
                {summary.trend_status === "Fluctuating" && <Activity className="h-3.5 w-3.5" />}
                {summary.trend_status === "Insufficient Data" && <Clock className="h-3.5 w-3.5" />}
                TREND STATUS: {summary.trend_status.toUpperCase()}
              </span>
              <span className="text-xs font-medium text-muted-foreground">
                {summary.status_description}
              </span>
            </div>

            <span className="text-xs text-muted-foreground">
              Data Sufficiency: <strong className="text-foreground">{summary.data_sufficiency}</strong> ({summary.data_sufficiency_note})
            </span>
          </div>

          <div className="p-4 rounded-lg bg-muted/30 border border-border/70 space-y-2">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-foreground">
                Executive Trend Summary
              </h4>
            </div>
            <p className="text-sm text-foreground/90 font-medium leading-relaxed">
              {summary.plain_english_summary}
            </p>
            <p className="text-xs text-muted-foreground italic pt-1">
              Note: This interpretation describes observed historical dataset patterns only and does not claim unrecorded external causes.
            </p>
          </div>

          {/* 5. Four Key Snapshot KPI Cards */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="p-3.5 rounded-lg border border-border/80 bg-background space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Current Period Value</span>
              <div className="text-lg font-bold text-foreground">
                {summary.latest_value.toLocaleString()}{" "}
                <span className="text-xs font-normal text-muted-foreground">
                  ({summary.latest_period})
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-border/80 bg-background space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Previous Period & Change</span>
              <div className="flex items-center gap-1.5">
                {summary.latest_change_pct != null ? (
                  <span
                    className={`text-lg font-bold flex items-center ${
                      summary.latest_change_pct > 0
                        ? "text-emerald-600 dark:text-emerald-400"
                        : summary.latest_change_pct < 0
                        ? "text-rose-600 dark:text-rose-400"
                        : "text-muted-foreground"
                    }`}
                  >
                    {summary.latest_change_pct > 0 ? (
                      <ArrowUpRight className="h-4 w-4 mr-0.5" />
                    ) : (
                      <ArrowDownRight className="h-4 w-4 mr-0.5" />
                    )}
                    {summary.latest_change_pct > 0 ? "+" : ""}
                    {summary.latest_change_pct}%
                  </span>
                ) : (
                  <span className="text-sm font-semibold text-muted-foreground">
                    N/A (Single Period)
                  </span>
                )}
                {summary.latest_change_absolute != null && (
                  <span className="text-xs text-muted-foreground">
                    (Δ {summary.latest_change_absolute > 0 ? "+" : ""}
                    {summary.latest_change_absolute.toLocaleString()})
                  </span>
                )}
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-border/80 bg-background space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Highest Recorded Period (Peak)</span>
              <div className="flex items-center gap-1.5">
                <Award className="h-4 w-4 text-amber-500" />
                <span className="text-lg font-bold text-foreground">
                  {summary.highest_value?.toLocaleString()}
                </span>
                <span className="text-xs text-muted-foreground">({summary.highest_period})</span>
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-border/80 bg-background space-y-1">
              <span className="text-xs text-muted-foreground font-medium">Lowest Recorded Period (Trough)</span>
              <div className="flex items-center gap-1.5">
                <TrendingDown className="h-4 w-4 text-muted-foreground" />
                <span className="text-lg font-bold text-foreground">
                  {summary.lowest_value?.toLocaleString()}
                </span>
                <span className="text-xs text-muted-foreground">({summary.lowest_period})</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. Main Trend Visualization Chart */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-foreground">{chartTitle}</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {chartSubtitle}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowMovingAverages(!showMovingAverages)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border font-medium transition-colors cursor-pointer ${
                showMovingAverages
                  ? "bg-primary/10 border-primary text-primary font-semibold"
                  : "border-border bg-background text-muted-foreground hover:text-foreground"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
              {showMovingAverages ? "Hide Moving Averages" : "Show Moving Averages (3 & 7 period)"}
            </button>
          </div>
        </div>

        {/* Time Series Chart */}
        <div className="h-[380px] w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={data.time_series}
              margin={{ top: 15, right: 25, left: 15, bottom: 25 }}
            >
              <defs>
                <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--color-primary, #6366f1)" stopOpacity={0.28} />
                  <stop offset="95%" stopColor="var(--color-primary, #6366f1)" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border, #e2e8f0)" opacity={0.6} />
              <XAxis
                dataKey="formatted_date"
                tick={{ fontSize: 11, fill: "var(--color-muted-foreground, #64748b)" }}
                tickMargin={10}
                axisLine={{ stroke: "var(--color-border, #e2e8f0)" }}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "var(--color-muted-foreground, #64748b)" }}
                tickMargin={10}
                tickFormatter={(v) => v >= 1000000 ? `${(v/1000000).toFixed(1)}M` : v >= 1000 ? `${(v/1000).toFixed(1)}k` : v}
                axisLine={{ stroke: "var(--color-border, #e2e8f0)" }}
              />
              <Tooltip
                formatter={(val: any, name: string) => {
                  const num = Number(val)
                  const label =
                    name === "value"
                      ? `${activeDesc?.display_name || "Value"} (${activeDesc?.unit || "Units"})`
                      : name === "moving_avg_3"
                      ? "3-Period Moving Avg"
                      : name === "moving_avg_7"
                      ? "7-Period Moving Avg"
                      : name
                  return [num.toLocaleString(undefined, { minimumFractionDigits: 2 }), label]
                }}
                labelFormatter={(label) => `Period: ${label}`}
                contentStyle={{
                  backgroundColor: "var(--color-card, #ffffff)",
                  borderColor: "var(--color-border, #e2e8f0)",
                  borderRadius: "0.5rem",
                  fontSize: "0.75rem",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                }}
              />
              <Legend
                verticalAlign="top"
                height={36}
                formatter={(val) =>
                  val === "value"
                    ? `${activeDesc?.display_name || "Observed Value"} (${activeDesc?.unit || "Units"})`
                    : val === "moving_avg_3"
                    ? "3-Period Moving Avg"
                    : val === "moving_avg_7"
                    ? "7-Period Moving Avg"
                    : val
                }
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="var(--color-primary, #6366f1)"
                strokeWidth={2.5}
                fill="url(#trendGradient)"
                dot={{ r: 3, fill: "var(--color-primary, #6366f1)" }}
                activeDot={{ r: 6 }}
              />
              {showMovingAverages && (
                <Line
                  type="monotone"
                  dataKey="moving_avg_3"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                  dot={false}
                />
              )}
              {showMovingAverages && (
                <Line
                  type="monotone"
                  dataKey="moving_avg_7"
                  stroke="#10b981"
                  strokeWidth={1.5}
                  strokeDasharray="2 2"
                  dot={false}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* What this chart tells you summary */}
        {data.what_this_chart_tells_you?.length > 0 && (
          <div className="pt-3 border-t border-border grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-foreground uppercase tracking-wider">
                <FileText className="h-3.5 w-3.5 text-primary" />
                What This Chart Shows
              </div>
              <ul className="space-y-1.5 text-xs text-muted-foreground">
                {data.what_this_chart_tells_you.map((bullet, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-foreground uppercase tracking-wider">
                <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                Analytical Interpretation
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {data.metric_interpretation ||
                  "Statistical descriptive movement across recorded timeline without speculative causal assumptions."}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 7. Category & Segment Analysis */}
      {data.category_trends && data.category_trends.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-foreground">
                Segment Contribution Analysis
              </h3>
              <p className="text-xs text-muted-foreground">
                Distribution of {activeDesc?.display_name} across leading categories.
              </p>
            </div>
            {data.available_categories?.length > 1 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground font-medium">Group by:</span>
                <select
                  value={selectedCategory}
                  onChange={(e) => handleCategoryChange(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background px-2.5 text-xs font-medium text-foreground cursor-pointer"
                >
                  {data.available_categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Bar Chart for category comparisons */}
          <div className="h-[260px] w-full pt-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.category_trends}
                margin={{ top: 10, right: 20, left: 10, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border, #e2e8f0)" opacity={0.6} />
                <XAxis
                  dataKey="category"
                  tick={{ fontSize: 11, fill: "var(--color-muted-foreground, #64748b)" }}
                  tickMargin={8}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "var(--color-muted-foreground, #64748b)" }}
                  tickFormatter={(v) => v >= 1000000 ? `${(v/1000000).toFixed(1)}M` : v >= 1000 ? `${(v/1000).toFixed(1)}k` : v}
                />
                <Tooltip
                  formatter={(val: any) => [Number(val).toLocaleString(), `${activeDesc?.display_name || "Value"} (${activeDesc?.unit || "Units"})`]}
                  contentStyle={{
                    backgroundColor: "var(--color-card, #ffffff)",
                    borderColor: "var(--color-border, #e2e8f0)",
                    borderRadius: "0.5rem",
                    fontSize: "0.75rem",
                  }}
                />
                <Bar
                  dataKey="current_val"
                  name="Current Period Value"
                  fill="var(--color-primary, #6366f1)"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Segment breakdown cards */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 pt-2">
            {data.category_trends.map((cat, i) => (
              <div key={i} className="p-3.5 rounded-lg border border-border bg-background space-y-1.5">
                <div className="flex items-center justify-between">
                  <h5 className="text-xs font-bold text-foreground truncate max-w-[180px]" title={cat.category}>
                    {cat.category}
                  </h5>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      cat.direction === "increasing"
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        : cat.direction === "decreasing"
                        ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {cat.direction.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm font-bold text-foreground">
                  Latest: {cat.current_val.toLocaleString()}{" "}
                  <span className="text-xs font-normal text-muted-foreground">
                    ({activeDesc?.unit || "Units"})
                  </span>
                  {cat.pct_change !== null && (
                    <span className="text-xs font-normal text-muted-foreground ml-1.5">
                      ({cat.pct_change > 0 ? "+" : ""}{cat.pct_change}%)
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 8. Practical Business Questions (Focused 3-5 Questions) */}
      {answers && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <HelpCircle className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold text-foreground">
              Practical Business Questions & Calculated Answers
            </h3>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                q: `Is ${activeDesc?.display_name || "the metric"} increasing or decreasing?`,
                a: summary ? `${summary.trend_status}: ${summary.status_description}` : "Insufficient data to determine direction.",
              },
              {
                q: "What was the latest period change?",
                a: answers.pct_change_text !== "Percentage change: N/A (single observation period)"
                  ? `${answers.absolute_change_text} (${answers.pct_change_text})`
                  : "Only one time period is available. Period-over-period change cannot be calculated.",
              },
              {
                q: "When were peak and trough recorded?",
                a: `${answers.best_period_text}. ${answers.worst_period_text}.`,
              },
              {
                q: "Is the data stable or volatile?",
                a: answers.stability_text,
              },
              {
                q: "Which segments contribute most?",
                a: data.category_trends && data.category_trends.length > 0
                  ? `Leading segment is '${data.category_trends[0]?.category}' with latest value of ${data.category_trends[0]?.current_val.toLocaleString()}.`
                  : "Insufficient categorical data in this dataset to perform segment attribution.",
              },
              {
                q: "What should be investigated next?",
                a: answers.next_investigation_text,
              },
            ].map((item, idx) => (
              <div key={idx} className="p-3.5 rounded-lg border border-border bg-muted/20 space-y-1.5">
                <span className="text-xs font-bold text-primary block leading-snug">{item.q}</span>
                <p className="text-xs text-foreground/90 leading-relaxed">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 9. Technical Details & Data Limitations (Expandable Progressive Disclosure) */}
      <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-muted-foreground" />
            <h4 className="text-xs font-semibold text-foreground">
              Technical Details & Data Limitations
            </h4>
          </div>
          <button
            type="button"
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline cursor-pointer"
          >
            {showTechnicalDetails ? "Hide Technical Details" : "View Technical Details"}
            {showTechnicalDetails ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>

        {showTechnicalDetails && (
          <div className="pt-3 border-t border-border space-y-3 text-xs text-muted-foreground animate-in fade-in-50 duration-200">
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <div className="p-2.5 rounded bg-muted/30">
                <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Stability Rating</span>
                <strong className="text-foreground">{data.stability_rating}</strong> (CV: {data.volatility_cv})
              </div>
              <div className="p-2.5 rounded bg-muted/30">
                <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Detected Anomalies</span>
                <strong className="text-foreground">{data.spikes_and_drops?.length || 0} statistical anomalies</strong>
              </div>
              <div className="p-2.5 rounded bg-muted/30">
                <span className="text-muted-foreground block text-[10px] uppercase font-semibold">Missing Dates Count</span>
                <strong className="text-foreground">{timeVal.missing_dates_count} records</strong>
              </div>
            </div>

            {data.limitations && data.limitations.length > 0 && (
              <div className="space-y-1 pt-1">
                <strong className="text-foreground">Statistical Guardrails & Limitations:</strong>
                <ul className="list-disc list-inside space-y-0.5">
                  {data.limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
