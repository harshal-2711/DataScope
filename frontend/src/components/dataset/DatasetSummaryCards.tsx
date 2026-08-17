import { Card, CardContent } from "@/components/ui/card"
import type { DatasetSummary } from "@/types/dataset"

export function DatasetSummaryCards({ summary }: { summary: DatasetSummary }) {
  const items = [
    { label: "Filename", value: summary.filename },
    { label: "File Type", value: summary.file_type.toUpperCase() },
    { label: "Rows", value: summary.row_count.toLocaleString() },
    { label: "Columns", value: summary.column_count.toLocaleString() },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label}>
          <CardContent className="py-4">
            <p className="text-xs text-muted-foreground">{item.label}</p>
            <p className="mt-1 truncate text-lg font-semibold">{item.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
