import { Target } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Competition() {
  return (
    <div>
      <PageHeader title="Competition" description="Compare your data against competitive benchmarks." />
      <EmptyState icon={Target} title="No comparison data yet" description="This module will be implemented in a future phase." />
    </div>
  )
}
