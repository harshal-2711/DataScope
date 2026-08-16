import { Database } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Dataset() {
  return (
    <div>
      <PageHeader title="Dataset" description="Upload and manage the dataset this workspace analyzes." />
      <EmptyState icon={Database} title="No dataset loaded" description="Dataset upload will be available in a future phase." />
    </div>
  )
}
