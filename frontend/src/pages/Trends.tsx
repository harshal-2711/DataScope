import { TrendingUp } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Trends() {
  return (
    <div>
      <PageHeader title="Trends" description="Identify patterns and movement over time." />
      <EmptyState icon={TrendingUp} title="No trend data yet" description="Trend analysis will appear here in a later phase." />
    </div>
  )
}
