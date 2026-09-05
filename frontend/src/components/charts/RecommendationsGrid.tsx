import { useState } from "react"
import { AlertCircle, Loader2, Sparkles } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { ChartCard, type ChartCardTier } from "@/components/charts/ChartCard"
import { ChartDetailModal } from "@/components/charts/ChartDetailModal"
import { KpiRow } from "@/components/dashboard/KpiRow"
import { useDatasetRecommendations } from "@/hooks/useDatasetRecommendations"
import type { ChartSpec } from "@/types/dataset"

/**
 * Structured, row-based dashboard composition -- deliberately NOT a
 * masonry/auto-packing layout.
 *
 * Earlier attempts at algorithmic gap-free packing (CSS Grid with
 * JS-measured row-spans, CSS multi-column, a third-party masonry library,
 * and a height-class-aware row-splitting variant of this same approach)
 * were all reported as making the dashboard look worse in one way or
 * another -- gaps, clipped cards, isolated cards, or (in the
 * height-class-splitting case) charts ending up full-width and the whole
 * page becoming excessively vertical. This is the version that was
 * confirmed to look right: every row is a plain N-column grid containing
 * exactly N cards, in rank order, with no per-chart logic deciding row
 * breaks. Visual hierarchy comes from WHICH row a chart lands in (rows
 * are filled in the recommendation engine's own business-relevance rank
 * order) and from each card's own content-aware height (see ChartCard's
 * resolveHeight), not from asymmetric spans or row-splitting rules. A
 * small gap where row heights don't perfectly match is an accepted,
 * intentional tradeoff here -- not a bug to keep chasing.
 */

// Row composition pattern: first row has 3 slots, second row has 2
// (larger) slots, and every row after that falls back to 3 -- this
// mirrors a typical BI dashboard's "3 medium panels, then 2 larger
// analytical panels, then supporting panels" structure without ever
// hardcoding *which* chart goes where; only chart *rank* (already
// determined by recommendation score) decides placement.
const ROW_SIZE_PATTERN = [3, 2]
const DEFAULT_ROW_SIZE = 3

function chunkIntoRows(charts: ChartSpec[]): ChartSpec[][] {
  const rows: ChartSpec[][] = []
  let i = 0
  let patternIndex = 0
  while (i < charts.length) {
    const size = ROW_SIZE_PATTERN[patternIndex] ?? DEFAULT_ROW_SIZE
    rows.push(charts.slice(i, i + size))
    i += size
    patternIndex++
  }
  return rows
}

// Every row uses this same small set of column-count classes, keyed only
// by how many cards actually landed in that row (1, 2, or 3+) -- never by
// what those cards are. A row is always fully occupied (no dangling empty
// cell), because the number of grid columns always exactly matches the
// number of cards placed in it.
function rowGridClass(cardCount: number): string {
  if (cardCount >= 3) return "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
  if (cardCount === 2) return "grid-cols-1 lg:grid-cols-2"
  return "grid-cols-1"
}

// Rank-based tier still drives each card's own height/title-size (see
// ChartCard) -- unrelated to which row it's placed in.
function assignTier(index: number, total: number): ChartCardTier {
  const primaryCount = Math.min(2, total)
  const secondaryCount = Math.min(3, Math.max(0, total - primaryCount))
  if (index < primaryCount) return "primary"
  if (index < primaryCount + secondaryCount) return "secondary"
  return "supporting"
}

export function RecommendationsGrid({
  datasetId,
  datasetName,
}: {
  datasetId: string
  datasetName: string
}) {
  const state = useDatasetRecommendations(datasetId)
  const [selectedChart, setSelectedChart] = useState<ChartSpec | null>(null)

  if (state.status === "idle" || state.status === "loading") {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Analyzing columns and building visualizations…
          </p>
        </CardContent>
      </Card>
    )
  }

  if (state.status === "error") {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Couldn't generate visualizations</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    )
  }

  const { charts, kpis } = state.data
  const rows = chunkIntoRows(charts)

  return (
    <div className="min-w-0 space-y-6 overflow-x-hidden">
      <KpiRow kpis={kpis} />

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Click a chart to explore it in detail; click a bar to drill into that value.
        </p>
        <Badge variant="secondary" className="gap-1.5 whitespace-nowrap">
          <Sparkles className="h-3 w-3" />
          {charts.length} Smart Chart{charts.length === 1 ? "" : "s"}
        </Badge>
      </div>

      <div className="space-y-4">
        {rows.map((row, rowIndex) => (
          <div key={rowIndex} className={`grid min-w-0 gap-4 ${rowGridClass(row.length)}`}>
            {row.map((chart, indexInRow) => {
              const globalIndex = rows
                .slice(0, rowIndex)
                .reduce((sum, r) => sum + r.length, 0) + indexInRow
              const tier = assignTier(globalIndex, charts.length)
              return (
                <div key={chart.id} className="min-w-0">
                  <ChartCard chart={chart} tier={tier} onClick={() => setSelectedChart(chart)} />
                </div>
              )
            })}
          </div>
        ))}
      </div>

      <ChartDetailModal
        chart={selectedChart}
        datasetId={datasetId}
        datasetName={datasetName}
        open={selectedChart !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedChart(null)
        }}
      />
    </div>
  )
}
