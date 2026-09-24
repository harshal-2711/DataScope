import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ChartRenderer } from "@/components/charts/ChartRenderer"
import { getColorSet, inferChartColorKind } from "@/lib/chartColors"
import type { ChartSpec } from "@/types/dataset"
import { Info, HelpCircle, ChevronDown, ChevronUp } from "lucide-react"

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
  tier?: ChartCardTier
}) {
  const [showMetadata, setShowMetadata] = useState(false)
  const colors = getColorSet(inferChartColorKind(`${chart.title} ${chart.y_label}`))

  const hasAnalyticalDetails = Boolean(
    chart.analytical_question ||
    chart.metric_definition ||
    chart.unit ||
    chart.dataset_grain ||
    chart.limitations
  )

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
      
      <CardHeader className="pt-5 pb-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className={TIER_TITLE_CLASS[tier]}>{chart.title}</CardTitle>
            {chart.analytical_question && (
              <p className="text-xs font-medium text-primary/90 mt-1 flex items-center gap-1.5">
                <HelpCircle className="h-3 w-3 shrink-0" />
                {chart.analytical_question}
              </p>
            )}
          </div>
          <Badge variant="secondary" className="shrink-0 font-normal text-xs">
            {CHART_TYPE_LABEL[chart.chart_type]}
          </Badge>
        </div>
        <CardDescription className={tier === "supporting" ? "line-clamp-2 mt-1" : "mt-1"}>
          {chart.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 pb-4 flex flex-col justify-between">
        <ChartRenderer chart={chart} height={resolveHeight(tier, chart.chart_type)} variant="card" />

        {/* Analytical Hierarchy Footer */}
        {hasAnalyticalDetails && (
          <div className="mt-3 pt-2.5 border-t border-border/50 text-xs">
            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
              <div className="flex flex-wrap gap-1.5 items-center">
                {chart.unit && (
                  <span className="px-1.5 py-0.5 rounded bg-muted/70 text-muted-foreground font-medium">
                    Unit: {chart.unit}
                  </span>
                )}
                {chart.aggregation && (
                  <span className="px-1.5 py-0.5 rounded bg-muted/70 text-muted-foreground font-medium">
                    Agg: {chart.aggregation}
                  </span>
                )}
                {chart.dataset_grain && (
                  <span className="px-1.5 py-0.5 rounded bg-muted/70 text-muted-foreground font-medium">
                    {chart.dataset_grain}
                  </span>
                )}
              </div>

              {(chart.explanation || chart.limitations) && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowMetadata(!showMetadata)
                  }}
                  className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors ml-auto"
                >
                  <Info className="h-3 w-3" />
                  <span>{showMetadata ? "Less" : "Methodology"}</span>
                  {showMetadata ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>
              )}
            </div>

            {showMetadata && (
              <div className="mt-2 p-2 rounded-md bg-muted/40 border border-border/60 space-y-1 text-[11px] text-muted-foreground">
                {chart.explanation && (
                  <p><span className="font-semibold text-foreground">Meaning:</span> {chart.explanation}</p>
                )}
                {chart.limitations && (
                  <p><span className="font-semibold text-foreground">Limitations:</span> {chart.limitations}</p>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
