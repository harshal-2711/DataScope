import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ChartRenderer } from "@/components/charts/ChartRenderer"
import { getColorSet, inferChartColorKind } from "@/lib/chartColors"
import type { ChartSpec } from "@/types/dataset"

const CHART_TYPE_LABEL: Record<ChartSpec["chart_type"], string> = {
  bar: "Bar",
  line: "Line",
  pie: "Pie",
  histogram: "Histogram",
  scatter: "Scatter",
}

export type ChartCardTier = "primary" | "secondary" | "supporting"

const TIER_HEIGHT: Record<ChartCardTier, number> = {
  primary: 360,
  secondary: 280,
  supporting: 220,
}

// Chart-type-specific adjustment layered on top of the tier height: a
// donut doesn't need as much vertical room as a wide category ranking,
// while a scatter benefits from a slightly taller, more square-ish area.
// Horizontal product-style bar charts still grow modestly with category
// count inside ChartRenderer, but only up to its own hard ceiling (see
// the "card" variant there) -- this value is a floor/starting point, not
// something that can compound into an unbounded card height anymore.
function resolveHeight(tier: ChartCardTier, chartType: ChartSpec["chart_type"]): number {
  const base = TIER_HEIGHT[tier]
  switch (chartType) {
    case "pie":
      return Math.min(base, 260)
    case "scatter":
      return Math.max(base, 300)
    default:
      return base
  }
}

const TIER_TITLE_CLASS: Record<ChartCardTier, string> = {
  primary: "text-base",
  secondary: "text-sm",
  supporting: "text-sm",
}

export function ChartCard({
  chart,
  onClick,
  tier = "secondary",
}: {
  chart: ChartSpec
  onClick?: () => void
  /** Visual hierarchy tier -- determines chart height/title size. Assigned
   * by the caller based on each chart's rank (score), which the backend
   * already computes from business relevance, so this stays data-driven
   * rather than hardcoded to specific chart titles. */
  tier?: ChartCardTier
}) {
  const colors = getColorSet(inferChartColorKind(`${chart.title} ${chart.y_label}`))

  return (
    <Card
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                onClick()
              }
            }
          : undefined
      }
      className={
        "relative flex flex-col overflow-hidden py-0 pt-1 transition-all duration-200" +
        (onClick
          ? " cursor-pointer hover:-translate-y-0.5 hover:border-primary/50 hover:bg-accent/40 hover:shadow-lg focus-visible:ring-ring/50 focus-visible:ring-2 focus-visible:outline-none"
          : "")
      }
    >
      <div className="absolute inset-x-0 top-0 h-1" style={{ background: colors.hex }} />
      <CardHeader className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <CardTitle className={TIER_TITLE_CLASS[tier]}>{chart.title}</CardTitle>
          <Badge variant="secondary" className="shrink-0">
            {CHART_TYPE_LABEL[chart.chart_type]}
          </Badge>
        </div>
        <CardDescription className={tier === "supporting" ? "line-clamp-2" : undefined}>
          {chart.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pb-6">
        <ChartRenderer chart={chart} height={resolveHeight(tier, chart.chart_type)} variant="card" />
      </CardContent>
    </Card>
  )
}
