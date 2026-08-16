import { Search } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"

export default function Explore() {
  return (
    <div>
      <PageHeader title="Explore" description="Browse and inspect your dataset interactively." />
      <EmptyState icon={Search} title="Nothing to explore yet" description="Exploration tools appear once a dataset is loaded." />
    </div>
  )
}
