import { Link } from "react-router-dom"
import { Search } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { RecommendationsGrid } from "@/components/charts/RecommendationsGrid"
import { useActiveDataset } from "@/context/DatasetContext"

export default function Explore() {
  const { activeDataset } = useActiveDataset()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Analytics Overview"
        description="AI-generated insights and visualizations from your uploaded dataset — no manual chart setup required."
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
        <RecommendationsGrid
          datasetId={activeDataset.dataset_id}
          datasetName={activeDataset.filename}
        />
      )}
    </div>
  )
}
