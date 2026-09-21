import { Link } from "react-router-dom"
import { LineChart } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { ForecastViewer } from "@/components/intelligence/ForecastViewer"
import { useActiveDataset } from "@/context/DatasetContext"

export default function Forecast() {
  const { activeDataset } = useActiveDataset()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Predictive Forecasting"
        description="Statistically verified projections using Holt's Linear Exponential Smoothing with 80% and 95% confidence intervals."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={LineChart}
            title="No dataset loaded"
            description="Upload a dataset with time-series records to generate statistical forecasts."
          />
          <div className="flex justify-center">
            <Button asChild size="sm">
              <Link to="/dataset">Upload a dataset</Link>
            </Button>
          </div>
        </div>
      ) : (
        <ForecastViewer datasetId={activeDataset.dataset_id} />
      )}
    </div>
  )
}

