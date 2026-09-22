import { Link } from "react-router-dom"
import { Search } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { RecommendationsGrid } from "@/components/charts/RecommendationsGrid"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
import { DatasetGrainBadge } from "@/components/intelligence/DatasetGrainBadge"
import { EntityBadges } from "@/components/intelligence/EntityBadges"
import { ValidationBanner } from "@/components/intelligence/ValidationBanner"
import { UniversalStatsViewer } from "@/components/intelligence/UniversalStatsViewer"
import { DecisionDashboard } from "@/components/intelligence/DecisionDashboard"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDomainIntelligence } from "@/hooks/useDomainIntelligence"

export default function Explore() {
  const { activeDataset } = useActiveDataset()
  const intelState = useDomainIntelligence(activeDataset?.dataset_id ?? null)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Decision Analytics & Intelligence"
        description="Real-world, decision-oriented analytics answering core business questions with dataset-aware metric validation."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={Search}
            title="Nothing to explore yet"
            description="Exploration tools appear once a dataset is loaded."
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
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            Computing domain intelligence, business entities, and decision dashboards...
          </div>
        </div>
      ) : intelState.status === "error" ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center space-y-3">
          <h3 className="text-base font-semibold text-foreground">Dataset Session Expired or Not Found</h3>
          <p className="max-w-md mx-auto text-xs text-rose-600 dark:text-rose-400">
            {intelState.message}
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <Button size="sm" variant="outline" onClick={() => window.location.reload()}>
              Retry
            </Button>
            <Button asChild size="sm">
              <Link to="/dataset">Upload Dataset</Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {intelState.status === "success" && (
            <div className="space-y-6">
              <ValidationBanner report={intelState.data.validation_report} />
              <DomainHeader domain={intelState.data.domain} />
              {intelState.data.dataset_grain && (
                <DatasetGrainBadge grain={intelState.data.dataset_grain} />
              )}
              <EntityBadges entities={intelState.data.entities} />
              <DecisionDashboard dashboard={intelState.data.decision_dashboard} />
              <UniversalStatsViewer statistics={intelState.data.universal_statistics} />
            </div>
          )}

          <div className="pt-4 border-t border-border">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
              Supplementary Exploratory Charts & Drilldown
            </h3>
            <RecommendationsGrid
              datasetId={activeDataset.dataset_id}
              datasetName={activeDataset.filename}
            />
          </div>
        </div>
      )}
    </div>
  )
}
