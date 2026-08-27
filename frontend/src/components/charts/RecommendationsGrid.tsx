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

// Column span (out of a 6-col grid) per hierarchy tier. Primary charts get
// half the row each (two side by side on a wide screen, matching "Total
// Sales by Product | Sales Over Time" style reference layouts); secondary
// charts get half a row too but shorter; supporting charts get a third of
// a row. Data-driven: which chart lands in which tier depends entirely on
// its rank in the already business-relevance-sorted `charts` array coming
// back from the recommendation engine -- nothing here is hardcoded to a
// specific chart title or dataset.
const TIER_SPAN: Record<ChartCardTier, string> = {
  primary: "col-span-6 lg:col-span-3",
  secondary: "col-span-6 sm:col-span-3",
  supporting: "col-span-6 sm:col-span-3 lg:col-span-2",
}

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

  return (
    <div className="space-y-6">
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

      <div className="grid grid-cols-6 gap-4">
        {charts.map((chart, index) => {
          const tier = assignTier(index, charts.length)
          return (
            <div key={chart.id} className={TIER_SPAN[tier]}>
              <ChartCard chart={chart} tier={tier} onClick={() => setSelectedChart(chart)} />
            </div>
          )
        })}
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
