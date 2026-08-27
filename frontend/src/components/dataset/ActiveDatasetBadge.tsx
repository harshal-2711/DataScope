import { Database } from "lucide-react"
import { useActiveDataset } from "@/context/DatasetContext"

export function ActiveDatasetBadge() {
  const { activeDataset } = useActiveDataset()

  if (!activeDataset) {
    return (
      <p className="text-sm text-muted-foreground">No dataset loaded</p>
    )
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <Database className="h-4 w-4 text-muted-foreground" />
      <span className="font-medium">{activeDataset.filename}</span>
      <span className="text-muted-foreground">
        {activeDataset.row_count.toLocaleString()} rows ·{" "}
        {activeDataset.column_count.toLocaleString()} columns
      </span>
    </div>
  )
}
