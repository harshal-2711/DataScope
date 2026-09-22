import { useState, useEffect } from "react"
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import {
  LineChart as ForecastIcon,
  AlertTriangle,
  Activity,
  Sparkles,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  Cpu,
  Calendar,
  CheckCircle2,
  Sliders,
  HelpCircle,
} from "lucide-react"
import type { ForecastResponse } from "@/types/intelligence"
import { fetchForecast as apiFetchForecast } from "@/lib/datasetApi"
import { formatMetricValue, detectColumnUnit, formatColumnLabel } from "@/lib/format"

interface ForecastViewerProps {
  datasetId: string
}

export function ForecastViewer({ datasetId }: ForecastViewerProps) {
  const [data, setData] = useState<ForecastResponse | null>(null)
  const [horizon, setHorizon] = useState<number>(7)
  const [customHorizon, setCustomHorizon] = useState<string>("")
  const [selectedMetric, setSelectedMetric] = useState<string>("")
  const [selectedMethod, setSelectedMethod] = useState<string>("auto")
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const loadForecast = async (h: number, m?: string, meth: string = "auto") => {
    setLoading(true)
    setError(null)
    try {
      const json = await apiFetchForecast(datasetId, h, m || undefined, undefined, meth)
      setData(json)
      if (json.metric && !selectedMetric) {
        setSelectedMetric(json.metric)
      }
    } catch (err: any) {
      setError(err.message || "Failed to load forecast.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadForecast(horizon, selectedMetric || undefined, selectedMethod)
  }, [datasetId])

  const handleMetricChange = (newMetric: string) => {
    setSelectedMetric(newMetric)
    loadForecast(horizon, newMetric, selectedMethod)
  }

  const handleMethodChange = (newMethod: string) => {
    setSelectedMethod(newMethod)
    loadForecast(horizon, selectedMetric, newMethod)
  }

  const handleHorizonPreset = (newH: number) => {
    setHorizon(newH)
    setCustomHorizon("")
    loadForecast(newH, selectedMetric, selectedMethod)
  }

  const handleCustomHorizonSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const val = parseInt(customHorizon, 10)
    if (!isNaN(val) && val >= 1 && val <= 60) {
      setHorizon(val)
      loadForecast(val, selectedMetric, selectedMethod)
    }
  }

  if (loading && !data) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card p-6 shadow-xs">
        <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground text-center">
          <Activity className="h-6 w-6 animate-spin text-primary mb-1" />
          <p className="font-semibold text-foreground">Fitting Statistical Forecasting Models</p>
          <p className="text-xs max-w-sm">
            Evaluating Naive, Moving Average, Holt's Exponential Smoothing, and Linear Trend trajectories with confidence intervals...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center text-sm text-rose-600">
        {error}
      </div>
    )
  }

  if (!data || !data.is_available) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-card/50 p-8 text-center space-y-4">
        <ForecastIcon className="mx-auto h-10 w-10 text-muted-foreground/60" />
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-foreground">Forecasting Unavailable</h3>
          <p className="max-w-md mx-auto text-xs text-muted-foreground">
            {data?.unavailable_reason ??
              "Forecasting requires at least one parseable date column and a minimum of 6 sequential historical observations."}
          </p>
        </div>
        {data?.limitations && data.limitations.length > 0 && (
          <div className="rounded-lg border border-border bg-muted/30 p-3 max-w-md mx-auto text-left text-xs text-muted-foreground">
            <span className="font-semibold text-foreground block mb-1.5 flex items-center gap-1.5">
              <HelpCircle className="h-3.5 w-3.5 text-primary" /> Prerequisites Checklist:
            </span>
            <ul className="list-disc list-inside space-y-1">
              {data.limitations.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )
  }

  // Combine historical and forecast points for Recharts
  const combinedChartData = [
    ...data.historical_points.map((p) => ({
      period: p.period,
      actual: p.actual,
      forecast: null as number | null,
      lower_80: null as number | null,
      upper_80: null as number | null,
      lower_95: null as number | null,
      upper_95: null as number | null,
    })),
    ...data.forecast_points.map((p, idx) => ({
      period: p.period,
      // Connect first forecast point to the last actual point for visual continuity
      actual:
        idx === 0 && data.historical_points.length > 0
          ? data.historical_points[data.historical_points.length - 1].actual
          : null,
      forecast: p.forecast,
      lower_80: p.lower_bound_80,
      upper_80: p.upper_bound_80,
      lower_95: p.lower_bound_95,
      upper_95: p.upper_bound_95,
    })),
  ]

  const nextPeriodVal = data.forecast_points[0]?.forecast ?? 0
  const finalPeriodVal = data.final_forecast ?? (data.forecast_points[data.forecast_points.length - 1]?.forecast ?? 0)
  const growth = data.projected_growth_pct

  const detectedUnit = data.unit || (data.metric ? detectColumnUnit(data.metric).unit : "")
  const fmtOpts = {
    column: data.metric || undefined,
    unit: detectedUnit,
    currencySymbol: data.currency_symbol || undefined,
  }

  const availableMetrics = data.available_metrics || (data.metric ? [data.metric] : [])

  return (
    <div className="space-y-6">
      {/* 1. Header & Interactive Controls */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-base font-semibold text-foreground">
                  Statistical Forecasting:{" "}
                  <span className="font-mono text-primary">
                    {formatColumnLabel(data.metric)}
                  </span>
                </h3>
                {detectedUnit && (
                  <span className="inline-flex items-center rounded-md bg-secondary px-2 py-0.5 text-xs font-semibold text-secondary-foreground border border-border">
                    Unit: {detectedUnit}
                  </span>
                )}
                {data.frequency_label && (
                  <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-foreground">
                    <Calendar className="h-3 w-3 text-muted-foreground" />
                    {data.frequency_label} Series
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Time column: <strong>{data.time_column}</strong> | Historical points:{" "}
                <strong>{data.historical_points.length}</strong> | Horizon: <strong>+{horizon} {data.frequency_label?.toLowerCase()} periods</strong>
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Target Metric Selector */}
            {availableMetrics.length > 1 && (
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">Metric:</span>
                <select
                  value={selectedMetric || data.metric || ""}
                  onChange={(e) => handleMetricChange(e.target.value)}
                  className="rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs font-medium text-foreground shadow-xs focus:outline-hidden focus:ring-2 focus:ring-primary"
                >
                  {availableMetrics.map((m) => (
                    <option key={m} value={m}>
                      {formatColumnLabel(m)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Model Method Selector */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-medium text-muted-foreground">Model:</span>
              <select
                value={selectedMethod}
                onChange={(e) => handleMethodChange(e.target.value)}
                className="rounded-lg border border-border bg-background px-2.5 py-1.5 text-xs font-medium text-foreground shadow-xs focus:outline-hidden focus:ring-2 focus:ring-primary"
              >
                <option value="auto">Auto (Best Fit)</option>
                <option value="holt_linear">Holt's Exponential Smoothing</option>
                <option value="linear_trend">Linear Trend Extrapolation</option>
                <option value="moving_average">Moving Average</option>
                <option value="naive">Naive Baseline</option>
              </select>
            </div>
          </div>
        </div>

        {/* Horizon Presets & Custom Input */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border/60">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground flex items-center gap-1">
              <Sliders className="h-3.5 w-3.5" /> Forecast Horizon:
            </span>
            <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border">
              {[7, 14, 30].map((h) => (
                <button
                  key={h}
                  onClick={() => handleHorizonPreset(h)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    horizon === h && !customHorizon
                      ? "bg-background text-foreground shadow-xs font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  +{h} {data.frequency_label || "Periods"}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleCustomHorizonSubmit} className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground">Custom:</span>
            <input
              type="number"
              min="1"
              max="60"
              placeholder="1-60"
              value={customHorizon}
              onChange={(e) => setCustomHorizon(e.target.value)}
              className="w-16 rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground focus:outline-hidden focus:ring-2 focus:ring-primary"
            />
            <button
              type="submit"
              className="rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Apply
            </button>
          </form>
        </div>
      </div>

      {/* Horizon Warning Alert */}
      {data.horizon_warning && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 text-xs text-amber-700 dark:text-amber-400 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <strong>Horizon Notice: </strong>
            {data.horizon_warning}
          </div>
        </div>
      )}

      {/* 2. Executive KPI Row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Next Period */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Projected Next Period</span>
            {detectedUnit && (
              <span className="text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {detectedUnit}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-foreground">
              {formatMetricValue(nextPeriodVal, fmtOpts)}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Target date: <strong>{data.forecast_points[0]?.period}</strong>
          </p>
        </div>

        {/* End of Horizon */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">End-of-Horizon Projection</span>
            {detectedUnit && (
              <span className="text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {detectedUnit}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-foreground">
              {formatMetricValue(finalPeriodVal, fmtOpts)}
            </span>
            {growth != null && (
              <span
                className={`inline-flex items-center text-xs font-semibold ${
                  growth > 0
                    ? "text-emerald-600 dark:text-emerald-400"
                    : growth < 0
                    ? "text-rose-600 dark:text-rose-400"
                    : "text-muted-foreground"
                }`}
              >
                {growth > 0 ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
                {growth > 0 ? "+" : ""}
                {growth}%
              </span>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground">
            At horizon +{horizon} periods ({data.forecast_points[data.forecast_points.length - 1]?.period})
          </p>
        </div>

        {/* Validation Accuracy */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Forecast Fit Accuracy</span>
            <span className="text-[10px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
              {data.validation_summary?.has_holdout ? "Holdout Validated" : "In-Sample Fit"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span className="text-base font-bold text-foreground">
              MAPE: {data.accuracy_metrics.mape !== undefined ? `${data.accuracy_metrics.mape}%` : "N/A"}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            RMSE: {data.accuracy_metrics.rmse != null ? formatMetricValue(data.accuracy_metrics.rmse, fmtOpts) : "N/A"} | MAE: {data.accuracy_metrics.mae != null ? formatMetricValue(data.accuracy_metrics.mae, fmtOpts) : "N/A"}
          </p>
        </div>

        {/* Model Confidence */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Model Confidence</span>
            <span className="text-[10px] font-mono text-muted-foreground">
              {data.method_used.split("(")[0].trim()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all"
                style={{ width: `${Math.round(data.confidence_score * 100)}%` }}
              />
            </div>
            <span className="text-xs font-bold text-foreground font-mono">
              {Math.round(data.confidence_score * 100)}%
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground">Derived from historical residual dispersion</p>
        </div>
      </div>

      {/* 3. Combined Forecast Chart */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-foreground">
              Historical Trajectory & Statistical Projections (+{horizon} {data.frequency_label?.toLowerCase()} periods)
            </h3>
            <p className="text-xs text-muted-foreground">
              Solid blue line represents historical data. Dashed purple line represents statistical projections with shaded 80% & 95% analytical confidence bands.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-[#2563eb]" /> Actual
            </span>
            <span className="inline-flex items-center gap-1.5 text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-[#9333ea]" /> Projected
            </span>
            <span className="inline-flex items-center gap-1.5 text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-[#3b82f6]/40" /> 80% / 95% Confidence
            </span>
          </div>
        </div>

        <div className="h-80 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={combinedChartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
              <XAxis
                dataKey="period"
                stroke="var(--muted-foreground)"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="var(--muted-foreground)"
                fontSize={11}
                tickLine={false}
                tickFormatter={(v) => formatMetricValue(Number(v), { ...fmtOpts, maximumFractionDigits: 0 })}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--card)",
                  borderColor: "var(--border)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                formatter={(val: any, name: any) => [
                  val !== null ? formatMetricValue(Number(val), fmtOpts) : "N/A",
                  name,
                ]}
              />
              <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />

              {/* 95% Confidence Interval Band */}
              <Area
                type="monotone"
                dataKey="upper_95"
                name="95% Upper Bound"
                stroke="transparent"
                fill="#3b82f6"
                fillOpacity={0.08}
              />
              <Area
                type="monotone"
                dataKey="lower_95"
                name="95% Lower Bound"
                stroke="transparent"
                fill="#3b82f6"
                fillOpacity={0.08}
              />

              {/* 80% Confidence Interval Band */}
              <Area
                type="monotone"
                dataKey="upper_80"
                name="80% Upper Bound"
                stroke="transparent"
                fill="#9333ea"
                fillOpacity={0.08}
              />
              <Area
                type="monotone"
                dataKey="lower_80"
                name="80% Lower Bound"
                stroke="transparent"
                fill="#9333ea"
                fillOpacity={0.08}
              />

              {/* Actual Historical Line */}
              <Line
                type="monotone"
                dataKey="actual"
                name="Actual Historical"
                stroke="#2563eb"
                strokeWidth={2.5}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />

              {/* Forecast Line */}
              <Line
                type="monotone"
                dataKey="forecast"
                name="Projected Forecast"
                stroke="#9333ea"
                strokeWidth={2.5}
                strokeDasharray="4 4"
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 4. Domain-Aware Interpretation Card */}
      {data.domain_interpretation && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-5 shadow-xs space-y-2">
          <div className="flex items-center gap-2 text-primary font-semibold text-sm">
            <TrendingUp className="h-4 w-4" />
            <span>Domain-Aware Analytical Interpretation</span>
          </div>
          <p className="text-xs text-foreground/90 leading-relaxed">
            {data.domain_interpretation}
          </p>
        </div>
      )}

      {/* 5. Multi-Model Evaluation & Comparison Matrix */}
      {data.method_comparison && data.method_comparison.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-primary" />
              <h4 className="text-sm font-semibold text-foreground">
                Statistical Model Comparison & Validation Matrix
              </h4>
            </div>
            <span className="text-xs text-muted-foreground">
              {data.validation_summary?.validation_strategy}
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/40 font-medium text-muted-foreground">
                <tr>
                  <th className="py-2.5 px-3">Forecasting Model</th>
                  <th className="py-2.5 px-3">In-Sample MAE</th>
                  <th className="py-2.5 px-3">In-Sample RMSE</th>
                  <th className="py-2.5 px-3">In-Sample MAPE</th>
                  {data.validation_summary?.has_holdout && (
                    <>
                      <th className="py-2.5 px-3">Holdout RMSE</th>
                      <th className="py-2.5 px-3">Holdout MAE</th>
                    </>
                  )}
                  <th className="py-2.5 px-3 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.method_comparison.map((m) => (
                  <tr
                    key={m.method_key}
                    className={`hover:bg-muted/20 transition-colors ${
                      m.is_selected ? "bg-primary/5 font-semibold" : ""
                    }`}
                  >
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-1.5">
                        <span className="text-foreground">{m.method_name}</span>
                        {m.is_selected && (
                          <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0" />
                        )}
                      </div>
                      <span className="text-[11px] text-muted-foreground font-normal block">
                        {m.description}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono">
                      {m.in_sample_metrics.mae != null
                        ? formatMetricValue(m.in_sample_metrics.mae, fmtOpts)
                        : "N/A"}
                    </td>
                    <td className="py-2.5 px-3 font-mono">
                      {m.in_sample_metrics.rmse != null
                        ? formatMetricValue(m.in_sample_metrics.rmse, fmtOpts)
                        : "N/A"}
                    </td>
                    <td className="py-2.5 px-3 font-mono">
                      {m.in_sample_metrics.mape != null ? `${m.in_sample_metrics.mape}%` : "N/A"}
                    </td>
                    {data.validation_summary?.has_holdout && (
                      <>
                        <td className="py-2.5 px-3 font-mono">
                          {m.holdout_metrics?.rmse != null
                            ? formatMetricValue(m.holdout_metrics.rmse, fmtOpts)
                            : "N/A"}
                        </td>
                        <td className="py-2.5 px-3 font-mono">
                          {m.holdout_metrics?.mae != null
                            ? formatMetricValue(m.holdout_metrics.mae, fmtOpts)
                            : "N/A"}
                        </td>
                      </>
                    )}
                    <td className="py-2.5 px-3 text-right">
                      {m.is_selected ? (
                        <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">
                          Active Model
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleMethodChange(m.method_key)}
                          className="text-[11px] text-muted-foreground hover:text-primary underline cursor-pointer"
                        >
                          Select
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 6. Forecast Limitations & Disclaimers */}
      <div className="rounded-xl border border-border bg-muted/30 p-4 text-xs text-muted-foreground space-y-2">
        <div className="flex items-center gap-1.5 font-semibold text-foreground">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
          <span>Forecasting Limitations & Analytical Disclaimer</span>
        </div>
        <p className="font-medium text-foreground/90">{data.disclaimer}</p>
        <ul className="list-disc list-inside space-y-1 pl-1">
          {data.limitations.map((lim, i) => (
            <li key={i}>{lim}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
