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
} from "lucide-react"
import type { ForecastResponse } from "@/types/intelligence"
import { fetchForecast as apiFetchForecast } from "@/lib/datasetApi"

interface ForecastViewerProps {
  datasetId: string
}

export function ForecastViewer({ datasetId }: ForecastViewerProps) {
  const [data, setData] = useState<ForecastResponse | null>(null)
  const [horizon, setHorizon] = useState<number>(6)
  const [selectedMetric, setSelectedMetric] = useState<string>("")
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const loadForecast = async (h: number, m?: string) => {
    setLoading(true)
    setError(null)
    try {
      const json = await apiFetchForecast(datasetId, h, m)
      setData(json)
      if (json.metric) setSelectedMetric(json.metric)
    } catch (err: any) {
      setError(err.message || "Failed to load forecast.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadForecast(horizon)
  }, [datasetId])

  const handleHorizonChange = (newH: number) => {
    setHorizon(newH)
    loadForecast(newH, selectedMetric)
  }

  if (loading && !data) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Activity className="h-4 w-4 animate-spin text-primary" />
          Fitting exponential smoothing model and calculating confidence intervals...
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
      <div className="rounded-xl border border-dashed border-border bg-card/50 p-8 text-center space-y-3">
        <ForecastIcon className="mx-auto h-10 w-10 text-muted-foreground/60" />
        <h3 className="text-base font-semibold text-foreground">Forecasting Unavailable</h3>
        <p className="max-w-md mx-auto text-xs text-muted-foreground">
          {data?.unavailable_reason ??
            "Forecasting requires at least one parseable date column and a minimum of 6 sequential historical observations."}
        </p>
        {data?.limitations && data.limitations.length > 0 && (
          <div className="rounded-lg border border-border bg-muted/30 p-3 max-w-md mx-auto text-left text-xs text-muted-foreground">
            <span className="font-semibold text-foreground block mb-1">Prerequisites Checklist:</span>
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

  // Combine historical and forecast points for the chart
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
      // Connect the first forecast point to the last actual point
      actual: idx === 0 && data.historical_points.length > 0 ? data.historical_points[data.historical_points.length - 1].actual : null,
      forecast: p.forecast,
      lower_80: p.lower_bound_80,
      upper_80: p.upper_bound_80,
      lower_95: p.lower_bound_95,
      upper_95: p.upper_bound_95,
    })),
  ]

  const nextPeriodVal = data.forecast_points[0]?.forecast ?? 0
  const finalPeriodVal = data.forecast_points[data.forecast_points.length - 1]?.forecast ?? 0
  const growth = data.projected_growth_pct

  return (
    <div className="space-y-6">
      {/* 1. Header & Horizon Controls */}
      <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-foreground">
                  Statistical Forecast: <span className="font-mono text-primary">{data.metric}</span>
                </h3>
                <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-primary/10 text-primary">
                  {data.method_used}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Time column: <strong>{data.time_column}</strong> | Historical points: <strong>{data.historical_points.length}</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">Horizon:</span>
            <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border">
              {[3, 6, 12, 24].map((h) => (
                <button
                  key={h}
                  onClick={() => handleHorizonChange(h)}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                    horizon === h
                      ? "bg-background text-foreground shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  +{h} Periods
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Forecast Summary KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Projected Next Period</span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-foreground">{nextPeriodVal.toLocaleString()}</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Target date: <strong>{data.forecast_points[0]?.period}</strong>
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1">
          <span className="text-xs font-medium text-muted-foreground">End-of-Horizon Projection</span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-foreground">{finalPeriodVal.toLocaleString()}</span>
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
                {growth > 0 ? "+" : ""}{growth}%
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            At horizon +{horizon} periods ({data.forecast_points[data.forecast_points.length - 1]?.period})
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1">
          <span className="text-xs font-medium text-muted-foreground">In-Sample Fit Accuracy</span>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
            <span className="text-base font-semibold text-foreground">
              MAPE: {data.accuracy_metrics.mape !== undefined ? `${data.accuracy_metrics.mape}%` : "N/A"}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            RMSE: {data.accuracy_metrics.rmse?.toLocaleString() ?? "N/A"} | MAE: {data.accuracy_metrics.mae?.toLocaleString() ?? "N/A"}
          </p>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs space-y-1">
          <span className="text-xs font-medium text-muted-foreground">Model Confidence</span>
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
          <p className="text-xs text-muted-foreground">Derived from historical residual variance</p>
        </div>
      </div>

      {/* 3. Combined Forecast Chart */}
      <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-foreground capitalize">
              Historical Observation & Projected Horizon (+{horizon} periods)
            </h3>
            <p className="text-xs text-muted-foreground">
              Solid line represents recorded historical data. Dashed line represents mathematical forecast with 80% & 95% confidence intervals.
            </p>
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
                tickFormatter={(v) => Number(v).toLocaleString()}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--card)",
                  borderColor: "var(--border)",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                formatter={(val: any, name: any) => [
                  val !== null ? Number(val).toLocaleString() : "N/A",
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

      {/* 4. Forecast Limitations & Disclaimers */}
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
