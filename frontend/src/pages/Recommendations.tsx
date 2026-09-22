import { Link } from "react-router-dom"
import { Lightbulb, Loader2 } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { RecommendationsViewer } from "@/components/intelligence/RecommendationsViewer"
import { useActiveDataset } from "@/context/DatasetContext"
import { useRecommendationsIntelligence } from "@/hooks/useRecommendationsIntelligence"

export default function Recommendations() {
  const { activeDataset } = useActiveDataset()
  const recState = useRecommendationsIntelligence(activeDataset?.dataset_id ?? null)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evidence-Based Recommendations"
        description="Universal, domain-aware recommendations converting verified statistical findings into structured, non-causal business actions."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={Lightbulb}
            title="No recommendations yet"
            description="Upload a dataset to generate evidence-backed recommendations."
          />
          <div className="flex justify-center">
            <Button asChild size="sm">
              <Link to="/dataset">Upload a dataset</Link>
            </Button>
          </div>
        </div>
      ) : recState.status === "loading" ? (
        <div className="flex h-64 items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            Synthesizing evidence-based recommendations across quality, trends, risks, and domain KPIs...
          </div>
        </div>
      ) : recState.status === "error" ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center text-sm text-rose-600">
          {recState.message}
        </div>
      ) : recState.status === "success" ? (
        <RecommendationsViewer data={recState.data} />
      ) : null}
    </div>
  )
}
