import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import { TrendingUp, TrendingDown, Minus, Calendar, Award } from "lucide-react"
import type { TrendItem } from "@/types/intelligence"

interface TrendViewerProps {
  trends: TrendItem[]
}

export function TrendViewer({ trends }: TrendViewerProps) {
  if (!trends || trends.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-8 text-center">
        <TrendingUp className="mx-auto h-8 w-8 text-muted-foreground/60 mb-2" />
        <h3 className="text-sm font-medium text-foreground">No time-series trends detected</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Trend analysis requires at least one parseable date column and a continuous numeric measure.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {trends.map((trend, idx) => {
        const isUp = trend.trend_direction === "increasing"
        const isDown = trend.trend_direction === "decreasing"

        return (
          <div key={idx} className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-semibold text-foreground capitalize">
                    {trend.metric_name.replace(/_/g, " ")} Trend
                  </h3>
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      isUp
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                        : isDown
                        ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {isUp ? <TrendingUp className="h-3 w-3" /> : isDown ? <TrendingDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                    {trend.trend_direction}
                    {trend.growth_rate_pct !== null && ` (${trend.growth_rate_pct > 0 ? "+" : ""}${trend.growth_rate_pct}%)`}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">{trend.description}</p>
              </div>

              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                {trend.peak_period && (
                  <div className="flex items-center gap-1.5 bg-muted/40 px-2.5 py-1 rounded-md border border-border/60">
                    <Award className="h-3.5 w-3.5 text-amber-500" />
                    <span>Peak: <strong className="text-foreground">{trend.peak_period}</strong></span>
                  </div>
                )}
                {trend.trough_period && (
                  <div className="flex items-center gap-1.5 bg-muted/40 px-2.5 py-1 rounded-md border border-border/60">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    <span>Trough: <strong className="text-foreground">{trend.trough_period}</strong></span>
                  </div>
                )}
              </div>
            </div>

            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend.data_points} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                  <XAxis
                    dataKey="date"
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
                    formatter={(value: any) => [Number(value).toLocaleString(), ""]}
                  />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name="Actual Value"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="moving_avg"
                    name="3-Period Moving Average"
                    stroke="#9333ea"
                    strokeWidth={2}
                    strokeDasharray="4 4"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )
      })}
    </div>
  )
}
