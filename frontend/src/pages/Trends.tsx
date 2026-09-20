import { Link } from "react-router-dom"
import { TrendingUp, Loader2 } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { TrendViewer } from "@/components/intelligence/TrendViewer"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDomainIntelligence } from "@/hooks/useDomainIntelligence"

export default function Trends() {
  const { activeDataset } = useActiveDataset()
  const intelState = useDomainIntelligence(activeDataset?.dataset_id ?? null)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Trend Intelligence"
        description="Factual time-series patterns, moving averages, growth trajectories, and peak/trough analysis calculated from your dataset."
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
            Computing time-series trends and moving averages...
          </div>
        </div>
      ) : intelState.status === "error" ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center text-sm text-rose-600">
          {intelState.message}
        </div>
      ) : intelState.status === "success" ? (
        <div className="space-y-6">
          <DomainHeader domain={intelState.data.domain} />
          <TrendViewer trends={intelState.data.trends} />
        </div>
      ) : null}
    </div>
  )
}
