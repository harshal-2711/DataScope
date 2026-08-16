import { LineChart } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Forecast() {
  return (
    <div>
      <PageHeader title="Forecast" description="Projected outcomes based on historical data." />
      <EmptyState icon={LineChart} title="Forecasting not yet available" description="This module will be implemented in a future phase." />
    </div>
  )
}
