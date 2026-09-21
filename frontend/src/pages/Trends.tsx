import { Link } from "react-router-dom"
import { TrendingUp, Loader2 } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { TrendsIntelligenceView } from "@/components/intelligence/TrendsIntelligenceView"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDomainIntelligence } from "@/hooks/useDomainIntelligence"

export default function Trends() {
  const { activeDataset } = useActiveDataset()
  const intelState = useDomainIntelligence(activeDataset?.dataset_id ?? null)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Trends Intelligence"
        description="Factual time-series patterns, period comparisons, moving averages, category growth, volatility, and practical answers calculated from your dataset."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={TrendingUp}
            title="No trend data yet"
            description="Upload a dataset with date and metric columns to view dynamic time-series trends."
          />
          <div className="flex justify-center">
            <Button asChild size="sm">
              <Link to="/dataset">Upload a dataset</Link>
            </Button>
          </div>
        </div>
      ) : intelState.status === "loading" ? (
        <div className="flex h-64 items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            Computing time-series trends, moving averages, and period comparisons...
          </div>
        </div>
      ) : intelState.status === "error" ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center space-y-3">
          <div className="flex justify-center text-rose-500">
            <TrendingUp className="h-8 w-8 rotate-180 opacity-70" />
          </div>
          <h3 className="text-base font-semibold text-foreground">Failed to Load Trends Intelligence</h3>
          <p className="max-w-md mx-auto text-xs text-rose-600 dark:text-rose-400">
            {intelState.message}
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <Button size="sm" variant="outline" onClick={() => window.location.reload()}>
              Retry
            </Button>
            <Button asChild size="sm">
              <Link to="/dataset">Upload New Dataset</Link>
            </Button>
          </div>
        </div>
      ) : intelState.status === "success" ? (
        <div className="space-y-6">
          <DomainHeader domain={intelState.data.domain} />
          <TrendsIntelligenceView datasetId={activeDataset.dataset_id} />
        </div>
      ) : null}
    </div>
  )
}

