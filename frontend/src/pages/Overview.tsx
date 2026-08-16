import { PageHeader } from "@/components/shared/PageHeader"
import { ConnectionStatus } from "@/components/shared/ConnectionStatus"

export default function Overview() {
  return (
    <div>
      <PageHeader
        title="Overview"
        description="A summary view of your workspace. Load a dataset to get started."
      />
      <div className="grid gap-4 md:grid-cols-2">
        <ConnectionStatus />
      </div>
    </div>
  )
}
