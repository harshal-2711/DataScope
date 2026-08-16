import { Lightbulb } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Recommendations() {
  return (
    <div>
      <PageHeader title="Recommendations" description="Actionable suggestions derived from your data." />
      <EmptyState icon={Lightbulb} title="No recommendations yet" description="Recommendations will appear here in a later phase." />
    </div>
  )
}
