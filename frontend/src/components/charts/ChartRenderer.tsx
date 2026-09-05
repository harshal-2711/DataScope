import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { CATEGORY_PALETTE, getColorSet, inferChartColorKind, OTHER_BUCKET_COLOR } from "@/lib/chartColors"
import { formatDateLabel, formatNumberCompact, formatNumberFull } from "@/lib/format"
import type { ChartSpec } from "@/types/dataset"

const AXIS_TICK_STYLE = { fontSize: 12, fill: "var(--muted-foreground)" }
const CHART_MARGIN = { top: 8, right: 12, left: 4, bottom: 8 }
const ANIMATION_DURATION = 400

const HISTOGRAM_COLOR = "#2dd4bf" // bright teal, per "distribution -> green/teal" convention
const SCATTER_COLOR = "#c084fc" // vivid violet, per "relationship -> cyan/purple" convention
const RANGE_DASH = "\u2013"

function truncateLabel(value: unknown, max = 14): string {
  const str = String(value)
  return str.length > max ? `${str.slice(0, max - 1)}\u2026` : str
}

/** Recharts tick formatters receive the raw value; keep both numeric axes
 * (compact, e.g. "125K") and readable value tooltips (full, comma-grouped)
 * consistent instead of falling back to the default scientific notation
 * recharts uses for large ranges. */
function numericTickFormatter(value: unknown): string {
  return formatNumberCompact(value)
}

/** Reduce how many x-axis ticks render on wide categorical/time axes so
 * labels never overlap, without hiding data points themselves. */
function adaptiveTickInterval(pointCount: number): number | "preserveStartEnd" {
  if (pointCount <= 8) return 0
  if (pointCount <= 20) return Math.ceil(pointCount / 8) - 1
  return "preserveStartEnd"
}

interface TooltipPayloadItem {
  value: number | string
  payload?: Record<string, unknown>
}

function TooltipCard({
  active,
  payload,
  label,
  variant = "default",
}: {
  active?: boolean
  payload?: TooltipPayloadItem[]
  label?: string | number
  variant?: "default" | "histogram" | "scatter" | "date" | "pie"
}) {
  if (!active || !payload?.length) return null
  const datum = payload[0]?.payload

  if (variant === "histogram" && datum) {
    const rangeLow = datum.range_low
    const rangeHigh = datum.range_high
    const freq = payload[0].value
    const pct = datum.percent
    return (
      <div className="rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
        <p className="mb-1 font-medium">
          Range: {formatNumberFull(rangeLow)}{RANGE_DASH}{formatNumberFull(rangeHigh)}
        </p>
        <p className="text-muted-foreground">Frequency: {formatNumberFull(freq)}</p>
        {typeof pct === "number" && (
          <p className="text-muted-foreground">Share: {pct}%</p>
        )}
      </div>
    )
  }

  if (variant === "scatter" && datum) {
    return (
      <div className="rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
        {datum.id !== undefined && (
          <p className="mb-1 font-medium">{String(datum.id)}</p>
        )}
        <p className="text-muted-foreground">X: {formatNumberFull(datum.x)}</p>
        <p className="text-muted-foreground">Y: {formatNumberFull(datum.y)}</p>
      </div>
    )
  }

  if (variant === "pie" && datum) {
    return (
      <div className="rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
        <p className="mb-1 font-medium">{String(datum.fullLabel ?? datum.label)}</p>
        <p className="text-muted-foreground">Value: {formatNumberFull(datum.value)}</p>
        {typeof datum.percent === "number" && (
          <p className="text-muted-foreground">Share: {datum.percent}%</p>
        )}
      </div>
    )
  }

  const displayLabel =
    label !== undefined ? (variant === "date" ? formatDateLabel(label) : String(label)) : undefined

  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
      {displayLabel !== undefined && <p className="mb-1 font-medium">{displayLabel}</p>}
      {payload.map((p, i) => (
        <p key={i} className="text-muted-foreground">
          {typeof p.value === "number" ? formatNumberFull(p.value) : String(p.value)}
        </p>
      ))}
    </div>
  )
}

interface BarClickPayload {
  rawX?: unknown
  payload?: { rawX?: unknown }
}

export function ChartRenderer({
  chart,
  height = 260,
  onCategoryClick,
  variant = "card",
}: {
  chart: ChartSpec
  height?: number
  /** Called with the RAW (untruncated) category value when a bar in a
   * dimension-breakdown bar chart is clicked. Only meaningful when
   * chart.chart_type === "bar" and chart.dimension_column is set — the
   * caller is responsible for deciding whether to react to it. */
  onCategoryClick?: (rawValue: string) => void
  /** "card" (default): compact dashboard-tile rendering -- caps how many
   * bars a high-cardinality breakdown actually draws and how tall the
   * card can grow, regardless of how much data the chart carries, so a
   * 42-category breakdown can't blow up into a 1000px-tall card next to
   * short ones. "detail": the large ChartDetailModal view -- allows
   * meaningfully more bars and height since that's the place explicitly
   * meant to show the fuller picture. Neither variant discards data on
   * the backend side; this only controls how much of it gets drawn. */
  variant?: "card" | "detail"
}) {
  const isDrillable = chart.chart_type === "bar" && Boolean(chart.dimension_column) && Boolean(onCategoryClick)
  const semanticColor = getColorSet(inferChartColorKind(`${chart.title} ${chart.y_label}`)).hex

  switch (chart.chart_type) {
    case "bar":
    case "histogram": {
      const isHistogram = chart.chart_type === "histogram"
      const data = chart.data.map((d) => ({
        label: truncateLabel(d.x),
        fullLabel: String(d.x),
        value: d.y,
        rawX: d.x,
        range_low: d.range_low,
        range_high: d.range_high,
        percent: d.percent,
      }))
      const barColor = isHistogram ? HISTOGRAM_COLOR : semanticColor
      const barCellColor = (i: number) =>
        data[i]?.rawX === "Other" ? OTHER_BUCKET_COLOR : CATEGORY_PALETTE[i % CATEGORY_PALETTE.length]

      // High-cardinality dimension breakdowns (e.g. "Total Sales by
      // Product") read far better as horizontal bars: product names get
      // full-width room instead of being rotated/truncated under a
      // crowded x-axis.
      const isHorizontal = !isHistogram && Boolean(chart.dimension_column) && data.length > 6
      if (isHorizontal) {
        // The card is a small dashboard tile -- it must NEVER grow
        // without bound just because a dimension happens to have 40+
        // distinct values (that was the actual bug: card height scaled
        // linearly with category count with no ceiling). The full data
        // is still on `chart` for the caller to use elsewhere (the detail
        // modal); this only limits what gets DRAWN in this render.
        const maxBars = variant === "card" ? 10 : 25
        const maxCardHeight = variant === "card" ? 400 : 640
        const shown = data.slice(0, maxBars)
        const hiddenCount = data.length - shown.length

        const longestLabel = Math.max(...shown.map((d) => d.label.length), 4)
        const yAxisWidth = Math.min(160, Math.max(70, longestLabel * 7))
        const rowHeight = 30
        const dynamicHeight = Math.min(
          maxCardHeight,
          Math.max(height, shown.length * rowHeight + 40)
        )
        return (
          <div>
            <ResponsiveContainer width="100%" height={dynamicHeight}>
              <BarChart data={shown} layout="vertical" margin={CHART_MARGIN}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" tick={AXIS_TICK_STYLE} tickFormatter={numericTickFormatter} />
                <YAxis
                  type="category"
                  dataKey="label"
                  tick={AXIS_TICK_STYLE}
                  width={yAxisWidth}
                />
                <Tooltip content={<TooltipCard />} cursor={{ fill: "var(--muted)" }} />
                <Bar
                  dataKey="value"
                  fill={barColor}
                  radius={[0, 4, 4, 0]}
                  isAnimationActive
                  animationDuration={ANIMATION_DURATION}
                  cursor={isDrillable ? "pointer" : undefined}
                  onClick={
                    isDrillable
                      ? (entry: BarClickPayload) => {
                          const raw = entry?.rawX ?? entry?.payload?.rawX
                          if (raw !== undefined && raw !== null && onCategoryClick) {
                            onCategoryClick(String(raw))
                          }
                        }
                      : undefined
                  }
                >
                  {!isHistogram &&
                    shown.map((_, i) => <Cell key={i} fill={barCellColor(i)} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            {hiddenCount > 0 && (
              <p className="mt-1 text-center text-[10px] text-muted-foreground">
                Showing top {shown.length} of {data.length}
                {variant === "card" ? " — open detail view for more" : ""}
              </p>
            )}
          </div>
        )
      }

      return (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data} margin={CHART_MARGIN}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={AXIS_TICK_STYLE}
              tickFormatter={isHistogram ? undefined : (v: string) => truncateLabel(v, 10)}
              interval={adaptiveTickInterval(data.length)}
              angle={data.length > 4 ? -30 : 0}
              textAnchor={data.length > 4 ? "end" : "middle"}
              height={data.length > 4 ? 52 : 24}
            />
            <YAxis tick={AXIS_TICK_STYLE} width={52} tickFormatter={numericTickFormatter} />
            <Tooltip
              content={<TooltipCard variant={isHistogram ? "histogram" : "default"} />}
              cursor={{ fill: "var(--muted)" }}
            />
            <Bar
              dataKey="value"
              fill={barColor}
              radius={[4, 4, 0, 0]}
              isAnimationActive
              animationDuration={ANIMATION_DURATION}
              cursor={isDrillable ? "pointer" : undefined}
              onClick={
                isDrillable
                  ? (entry: BarClickPayload) => {
                      const raw = entry?.rawX ?? entry?.payload?.rawX
                      if (raw !== undefined && raw !== null && onCategoryClick) {
                        onCategoryClick(String(raw))
                      }
                    }
                  : undefined
              }
            >
              {!isHistogram &&
                data.map((_, i) => <Cell key={i} fill={barCellColor(i)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )
    }

    case "line": {
      const data = chart.data.map((d) => ({ label: formatDateLabel(d.x), value: d.y }))
      const gradientId = `lineFill-${chart.id}`
      return (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={CHART_MARGIN}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={semanticColor} stopOpacity={0.28} />
                <stop offset="100%" stopColor={semanticColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={AXIS_TICK_STYLE}
              minTickGap={24}
              interval={adaptiveTickInterval(data.length)}
            />
            <YAxis tick={AXIS_TICK_STYLE} width={52} tickFormatter={numericTickFormatter} />
            <Tooltip content={<TooltipCard variant="date" />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke={semanticColor}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              dot={false}
              isAnimationActive
              animationDuration={ANIMATION_DURATION}
            />
          </AreaChart>
        </ResponsiveContainer>
      )
    }

    case "pie": {
      const raw = chart.data.map((d) => ({
        label: truncateLabel(d.x, 20),
        fullLabel: String(d.x),
        value: typeof d.y === "number" ? d.y : 0,
      }))
      const total = raw.reduce((sum, d) => sum + d.value, 0)
      const withPercent = raw.map((d) => ({
        ...d,
        percent: total > 0 ? Math.round((d.value / total) * 1000) / 10 : 0,
      }))
      return (
        <div className="flex h-full flex-col gap-3 sm:flex-row sm:items-center">
          <div className="sm:w-1/2 sm:shrink-0">
            <ResponsiveContainer width="100%" height={height}>
              <PieChart margin={CHART_MARGIN}>
                <Pie
                  data={withPercent}
                  dataKey="value"
                  nameKey="label"
                  innerRadius="55%"
                  outerRadius="85%"
                  paddingAngle={2}
                  isAnimationActive
                  animationDuration={ANIMATION_DURATION}
                >
                  {withPercent.map((_, i) => (
                    <Cell key={i} fill={CATEGORY_PALETTE[i % CATEGORY_PALETTE.length]} />
                  ))}
                </Pie>
                <Tooltip content={<TooltipCard variant="pie" />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="min-w-0 flex-1 space-y-2 text-xs">
            {withPercent.map((d, i) => (
              <li key={i} className="flex items-center justify-between gap-3">
                <span className="flex min-w-0 items-center gap-1.5">
                  <span
                    className="h-2.5 w-2.5 shrink-0 rounded-full"
                    style={{ background: CATEGORY_PALETTE[i % CATEGORY_PALETTE.length] }}
                  />
                  <span className="truncate" title={d.fullLabel}>
                    {d.label}
                  </span>
                </span>
                <span className="shrink-0 tabular-nums text-muted-foreground">
                  {formatNumberCompact(d.value)}
                  <span className="ml-1.5 text-foreground/70">{d.percent}%</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )
    }

    case "scatter": {
      const data = chart.data.map((d) => ({ x: d.x, y: d.y, id: d.id }))
      return (
        <ResponsiveContainer width="100%" height={height}>
          <ScatterChart margin={CHART_MARGIN}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="x"
              type="number"
              name={chart.x_label}
              tick={AXIS_TICK_STYLE}
              tickFormatter={numericTickFormatter}
            />
            <YAxis
              dataKey="y"
              type="number"
              name={chart.y_label}
              tick={AXIS_TICK_STYLE}
              width={52}
              tickFormatter={numericTickFormatter}
            />
            <Tooltip content={<TooltipCard variant="scatter" />} cursor={{ strokeDasharray: "3 3" }} />
            <Scatter
              data={data}
              fill={SCATTER_COLOR}
              fillOpacity={0.65}
              isAnimationActive
              animationDuration={ANIMATION_DURATION}
            />
          </ScatterChart>
        </ResponsiveContainer>
      )
    }

    default:
      return null
  }
}
