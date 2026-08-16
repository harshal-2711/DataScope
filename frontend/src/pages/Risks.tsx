import { ShieldAlert } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Risks() {
  return (
    <div>
      <PageHeader title="Risks" description="Surface anomalies and risk signals in your data." />
      <EmptyState icon={ShieldAlert} title="No risks identified" description="Risk detection will appear here in a later phase." />
    </div>
  )
}
