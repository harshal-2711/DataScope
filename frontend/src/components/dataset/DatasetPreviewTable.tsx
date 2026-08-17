import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { DatasetSummary } from "@/types/dataset"

export function DatasetPreviewTable({ summary }: { summary: DatasetSummary }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Preview — first {summary.preview.length} of{" "}
          {summary.row_count.toLocaleString()} rows
        </CardTitle>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-max text-sm">
          <thead>
            <tr className="border-b">
              {summary.columns.map((col) => (
                <th
                  key={col}
                  className="whitespace-nowrap px-3 py-2 text-left font-medium"
                >
                  <div className="flex flex-col gap-1">
                    <span>{col}</span>
                    <Badge variant="secondary" className="w-fit font-normal">
                      {summary.dtypes[col]}
                    </Badge>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {summary.preview.map((row, i) => (
              <tr key={i} className="border-b last:border-0">
                {summary.columns.map((col) => (
                  <td
                    key={col}
                    className="whitespace-nowrap px-3 py-2 text-muted-foreground"
                  >
                    {row[col] === null || row[col] === undefined ? (
                      <span className="italic text-muted-foreground/60">
                        null
                      </span>
                    ) : (
                      String(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  )
}
