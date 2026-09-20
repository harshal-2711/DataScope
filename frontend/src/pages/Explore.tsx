import { Link } from "react-router-dom"
import { Search } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { RecommendationsGrid } from "@/components/charts/RecommendationsGrid"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
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
      ) : (
        <div className="space-y-6">
          {intelState.status === "success" && (
            <div className="space-y-6">
              <ValidationBanner report={intelState.data.validation_report} />
              <DomainHeader domain={intelState.data.domain} />
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
