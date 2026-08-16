import { FileText } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Reports() {
  return (
    <div>
      <PageHeader title="Reports" description="Generate and export shareable reports." />
      <EmptyState icon={FileText} title="No reports yet" description="Report generation will be implemented in a future phase." />
    </div>
  )
}
