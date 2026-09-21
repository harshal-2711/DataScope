import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { DatasetSummary, ColumnInference } from "@/types/dataset"
import {
  Calendar,
  DollarSign,
  Percent,
  Hash,
  Key,
  Clock,
  Layers,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Table as TableIcon,
  Columns,
} from "lucide-react"

function getTypeBadgeColor(inferredType: string) {
  switch (inferredType) {
    case "Date":
    case "Datetime":
      return "bg-purple-500/10 text-purple-700 border-purple-200 dark:text-purple-300 dark:border-purple-800"
    case "Currency":
      return "bg-emerald-500/10 text-emerald-700 border-emerald-200 dark:text-emerald-300 dark:border-emerald-800"
    case "Percentage":
      return "bg-cyan-500/10 text-cyan-700 border-cyan-200 dark:text-cyan-300 dark:border-cyan-800"
    case "Integer":
    case "Float":
      return "bg-amber-500/10 text-amber-700 border-amber-200 dark:text-amber-300 dark:border-amber-800"
    case "Category":
      return "bg-indigo-500/10 text-indigo-700 border-indigo-200 dark:text-indigo-300 dark:border-indigo-800"
    case "Identifier":
      return "bg-slate-500/10 text-slate-700 border-slate-200 dark:text-slate-300 dark:border-slate-800"
    case "Duration":
      return "bg-orange-500/10 text-orange-700 border-orange-200 dark:text-orange-300 dark:border-orange-800"
    case "Timestamp":
      return "bg-blue-500/10 text-blue-700 border-blue-200 dark:text-blue-300 dark:border-blue-800"
    case "Boolean":
      return "bg-teal-500/10 text-teal-700 border-teal-200 dark:text-teal-300 dark:border-teal-800"
    default:
      return "bg-muted text-muted-foreground border-border"
  }
}

function getTypeIcon(inferredType: string) {
  switch (inferredType) {
    case "Date":
    case "Datetime":
      return <Calendar className="h-3 w-3 mr-1" />
    case "Currency":
      return <DollarSign className="h-3 w-3 mr-1" />
    case "Percentage":
      return <Percent className="h-3 w-3 mr-1" />
    case "Integer":
    case "Float":
      return <Hash className="h-3 w-3 mr-1" />
    case "Identifier":
      return <Key className="h-3 w-3 mr-1" />
    case "Duration":
      return <Clock className="h-3 w-3 mr-1" />
    case "Category":
      return <Layers className="h-3 w-3 mr-1" />
    default:
      return <FileText className="h-3 w-3 mr-1" />
  }
}

export function DatasetPreviewTable({ summary }: { summary: DatasetSummary }) {
  const [activeTab, setActiveTab] = useState<"profiling" | "rows">("profiling")
  const inferredMap = new Map<string, ColumnInference>()

  if (summary.inferred_columns) {
    for (const col of summary.inferred_columns) {
      inferredMap.set(col.name, col)
    }
  }

  const diagnostics = summary.diagnostics

  return (
    <div className="space-y-4">
      {/* File Parsing Diagnostics Banner */}
      {diagnostics && (diagnostics.warnings.length > 0 || diagnostics.duplicate_columns_renamed.length > 0) && (
        <div className="p-3.5 rounded-lg border border-amber-500/30 bg-amber-500/5 text-amber-900 dark:text-amber-200 flex items-start gap-3 text-xs">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold">File Parsing Intelligence:</span>
            <ul className="list-disc list-inside space-y-0.5">
              {diagnostics.warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
              {diagnostics.duplicate_columns_renamed.length > 0 && (
                <li>
                  Normalized duplicate headers: {diagnostics.duplicate_columns_renamed.join(", ")}
                </li>
              )}
            </ul>
          </div>
        </div>
      )}

      {/* Main Preview Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              Dataset Understanding & Preview
              <Badge variant="outline" className="font-normal text-xs">
                {summary.row_count.toLocaleString()} rows × {summary.column_count} columns
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground mt-0.5">
              Inspecting semantic types, missing values, cardinality, and data preview.
            </CardDescription>
          </div>

          <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-md border text-xs">
            <Button
              variant={activeTab === "profiling" ? "default" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2.5 gap-1.5"
              onClick={() => setActiveTab("profiling")}
            >
              <Columns className="h-3.5 w-3.5" />
              Column Profiling
            </Button>
            <Button
              variant={activeTab === "rows" ? "default" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2.5 gap-1.5"
              onClick={() => setActiveTab("rows")}
            >
              <TableIcon className="h-3.5 w-3.5" />
              Raw Rows ({summary.preview.length})
            </Button>
          </div>
        </CardHeader>

        <CardContent className="overflow-x-auto p-0">
          {activeTab === "profiling" ? (
            /* Column Profiling View */
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-y bg-muted/40 text-muted-foreground font-medium">
                  <th className="py-2.5 px-4">Column Name</th>
                  <th className="py-2.5 px-3">Inferred Semantic Type</th>
                  <th className="py-2.5 px-3">Original Type</th>
                  <th className="py-2.5 px-3">Confidence</th>
                  <th className="py-2.5 px-3">Missing Values</th>
                  <th className="py-2.5 px-3">Unique Values</th>
                  <th className="py-2.5 px-4">Sample Values</th>
                  <th className="py-2.5 px-3">Warnings</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {summary.columns.map((colName) => {
                  const inf = inferredMap.get(colName)
                  const originalType = summary.dtypes[colName] || "unknown"
                  const inferredType = inf ? inf.inferred_type : originalType
                  const confidence = inf ? Math.round(inf.confidence * 100) : 100
                  const missingCount = inf ? inf.missing_count : 0
                  const missingPct = inf ? inf.missing_percentage : 0
                  const uniqueCount = inf ? inf.unique_count : 0
                  const sampleValues = inf ? inf.sample_values : []
                  const warnings = inf ? inf.warnings : []

                  return (
                    <tr key={colName} className="hover:bg-muted/30 transition-colors">
                      <td className="py-2.5 px-4 font-medium text-foreground">
                        {colName}
                      </td>
                      <td className="py-2.5 px-3">
                        <Badge
                          variant="outline"
                          className={`inline-flex items-center text-[11px] font-medium border ${getTypeBadgeColor(inferredType)}`}
                        >
                          {getTypeIcon(inferredType)}
                          {inferredType}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[11px] text-muted-foreground">
                        {originalType}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="font-medium text-muted-foreground">
                          {confidence}%
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        {missingCount > 0 ? (
                          <span className="text-amber-600 dark:text-amber-400 font-medium">
                            {missingCount} ({missingPct}%)
                          </span>
                        ) : (
                          <span className="text-muted-foreground/60 flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                            0 (0%)
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-foreground">
                        {uniqueCount.toLocaleString()}
                      </td>
                      <td className="py-2.5 px-4">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {sampleValues.length > 0 ? (
                            sampleValues.slice(0, 3).map((val, idx) => (
                              <span
                                key={idx}
                                className="px-1.5 py-0.5 rounded bg-muted/60 text-muted-foreground font-mono text-[10px] truncate max-w-[120px]"
                              >
                                {String(val)}
                              </span>
                            ))
                          ) : (
                            <span className="text-muted-foreground/40 italic">none</span>
                          )}
                        </div>
                      </td>
                      <td className="py-2.5 px-3">
                        {warnings.length > 0 ? (
                          <div className="flex items-center gap-1 text-amber-600 text-[11px]">
                            <AlertTriangle className="h-3 w-3 shrink-0" />
                            <span>{warnings[0]}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground/40 text-[11px]">—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          ) : (
            /* Raw Rows Preview View */
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-y bg-muted/40">
                  {summary.columns.map((col) => {
                    const inf = inferredMap.get(col)
                    const inferredType = inf ? inf.inferred_type : summary.dtypes[col]
                    return (
                      <th
                        key={col}
                        className="whitespace-nowrap px-3.5 py-2.5 font-medium"
                      >
                        <div className="flex flex-col gap-1">
                          <span className="text-foreground">{col}</span>
                          <Badge
                            variant="outline"
                            className={`w-fit text-[10px] font-normal border ${getTypeBadgeColor(inferredType)}`}
                          >
                            {inferredType}
                          </Badge>
                        </div>
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody className="divide-y">
                {summary.preview.map((row, i) => (
                  <tr key={i} className="hover:bg-muted/30 transition-colors">
                    {summary.columns.map((col) => (
                      <td
                        key={col}
                        className="whitespace-nowrap px-3.5 py-2 text-muted-foreground font-mono text-[11px]"
                      >
                        {row[col] === null || row[col] === undefined ? (
                          <span className="italic text-muted-foreground/40 font-sans">
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
          )}
        </CardContent>
      </Card>
    </div>
  )
}
