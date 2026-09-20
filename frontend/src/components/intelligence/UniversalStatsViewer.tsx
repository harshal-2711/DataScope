import { useState } from "react"
import {
  Table,
  Hash,
  Layers,
  ChevronDown,
  ChevronUp,
  Grid,
} from "lucide-react"
import type { UniversalStatistics, NumericStats, CategoricalStats } from "@/types/intelligence"

interface UniversalStatsViewerProps {
  statistics?: UniversalStatistics
}

export function UniversalStatsViewer({ statistics }: UniversalStatsViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState<"numeric" | "categorical" | "correlations">("numeric")
  const [selectedNumCol, setSelectedNumCol] = useState<string | null>(null)

  if (!statistics) return null

  const {
    dataset_summary,
    numeric_statistics,
    categorical_statistics,
    correlation_matrix,
  } = statistics

  const numColNames = Object.keys(numeric_statistics)
  const catColNames = Object.keys(categorical_statistics)
  const activeNumericCol = selectedNumCol || numColNames[0] || null
  const currentNumStats: NumericStats | undefined = activeNumericCol
    ? numeric_statistics[activeNumericCol]
    : undefined

  const corrCols = Object.keys(correlation_matrix)

  return (
    <div className="rounded-xl border border-border bg-card shadow-xs overflow-hidden">
      <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between border-b border-border/60">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary/10 p-2 text-primary">
            <Table className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-foreground">
                Universal Descriptive Statistics Engine
              </h3>
              <span className="rounded-md bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                Auto-calculated
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Parametric & non-parametric central tendency, dispersion, percentiles, and bivariate correlations.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
          >
            {isExpanded ? (
              <>
                Collapse Statistics <ChevronUp className="h-3.5 w-3.5" />
              </>
            ) : (
              <>
                View Full Statistics <ChevronDown className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Dataset hygiene summary strip */}
      <div className="grid grid-cols-2 gap-2 p-4 bg-muted/20 sm:grid-cols-4 md:grid-cols-6 border-b border-border/40 text-xs">
        <div>
          <span className="text-[11px] text-muted-foreground">Rows</span>
          <div className="font-semibold text-foreground">
            {dataset_summary.row_count.toLocaleString()}
          </div>
        </div>
        <div>
          <span className="text-[11px] text-muted-foreground">Columns</span>
          <div className="font-semibold text-foreground">
            {dataset_summary.column_count} ({numColNames.length} num / {catColNames.length} cat)
          </div>
        </div>
        <div>
          <span className="text-[11px] text-muted-foreground">Missing Cells</span>
          <div className="font-semibold text-foreground">
            {dataset_summary.missing_cells} ({dataset_summary.missing_pct}%)
          </div>
        </div>
        <div>
          <span className="text-[11px] text-muted-foreground">Duplicate Rows</span>
          <div className="font-semibold text-foreground">
            {dataset_summary.duplicate_rows} ({dataset_summary.duplicate_pct}%)
          </div>
        </div>
        <div>
          <span className="text-[11px] text-muted-foreground">Total Cells</span>
          <div className="font-semibold text-foreground">
            {dataset_summary.total_cells.toLocaleString()}
          </div>
        </div>
        <div>
          <span className="text-[11px] text-muted-foreground">Status</span>
          <div className="font-semibold text-emerald-600 dark:text-emerald-400">
            Profiled
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* Tab Navigation */}
          <div className="flex border-b border-border">
            <button
              type="button"
              onClick={() => setActiveTab("numeric")}
              className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
                activeTab === "numeric"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Hash className="h-3.5 w-3.5" />
              Numeric Columns ({numColNames.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("categorical")}
              className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
                activeTab === "categorical"
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              Categorical Columns ({catColNames.length})
            </button>
            {corrCols.length > 1 && (
              <button
                type="button"
                onClick={() => setActiveTab("correlations")}
                className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === "correlations"
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                <Grid className="h-3.5 w-3.5" />
                Correlation Matrix ({corrCols.length}x{corrCols.length})
              </button>
            )}
          </div>

          {/* Tab 1: Numeric Columns */}
          {activeTab === "numeric" && (
            <div className="space-y-4">
              {numColNames.length === 0 ? (
                <div className="p-6 text-center text-xs text-muted-foreground">
                  No continuous numeric columns found in this dataset.
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Column pills */}
                  <div className="flex flex-wrap gap-1.5">
                    {numColNames.map((col) => (
                      <button
                        key={col}
                        type="button"
                        onClick={() => setSelectedNumCol(col)}
                        className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                          activeNumericCol === col
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:bg-muted/80"
                        }`}
                      >
                        {col}
                      </button>
                    ))}
                  </div>

                  {currentNumStats && (
                    <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 pt-2">
                      <div className="rounded-lg border border-border/80 bg-muted/20 p-3 space-y-1">
                        <span className="text-[10px] font-semibold uppercase text-muted-foreground">
                          Central Tendency
                        </span>
                        <div className="space-y-1 text-xs pt-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Mean:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.mean?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Median:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.median?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Mode:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.mode?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-lg border border-border/80 bg-muted/20 p-3 space-y-1">
                        <span className="text-[10px] font-semibold uppercase text-muted-foreground">
                          Dispersion & Spread
                        </span>
                        <div className="space-y-1 text-xs pt-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Min - Max:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.min?.toLocaleString()} - {currentNumStats.max?.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Range:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.range?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Std Dev:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.std_dev?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">IQR:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.iqr?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-lg border border-border/80 bg-muted/20 p-3 space-y-1">
                        <span className="text-[10px] font-semibold uppercase text-muted-foreground">
                          Percentiles
                        </span>
                        <div className="space-y-1 text-xs pt-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">25th (P25):</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.p25?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">50th (P50):</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.p50?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">75th (P75):</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.p75?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">90th (P90):</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.p90?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">99th (P99):</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.p99?.toLocaleString() ?? "N/A"}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="rounded-lg border border-border/80 bg-muted/20 p-3 space-y-1">
                        <span className="text-[10px] font-semibold uppercase text-muted-foreground">
                          Outliers & Data Quality
                        </span>
                        <div className="space-y-1 text-xs pt-1">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Valid Rows:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.valid_count.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Missing / Null:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.null_count} ({currentNumStats.null_pct}%)
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">IQR Outliers (3x):</span>
                            <span
                              className={`font-semibold ${
                                (currentNumStats.outlier_count_iqr ?? 0) > 0
                                  ? "text-amber-500"
                                  : "text-foreground"
                              }`}
                            >
                              {currentNumStats.outlier_count_iqr ?? 0}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Z-Score Outliers:</span>
                            <span className="font-semibold text-foreground">
                              {currentNumStats.outlier_count_zscore ?? 0}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Categorical Columns */}
          {activeTab === "categorical" && (
            <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
              {catColNames.map((col) => {
                const stats: CategoricalStats = categorical_statistics[col]
                return (
                  <div
                    key={col}
                    className="rounded-lg border border-border/80 bg-muted/20 p-3 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between border-b border-border/50 pb-1.5">
                      <span className="font-semibold text-foreground truncate">{col}</span>
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                        {stats.unique_count} distinct
                      </span>
                    </div>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[11px] text-muted-foreground">
                        <span>Missing: {stats.null_pct}%</span>
                        <span>Mode: {stats.mode ?? "N/A"}</span>
                      </div>

                      {stats.top_values.length > 0 && (
                        <div className="space-y-1 pt-1">
                          <span className="text-[10px] font-semibold text-muted-foreground uppercase">
                            Top Frequencies:
                          </span>
                          {stats.top_values.map((item, idx) => (
                            <div key={idx} className="space-y-0.5">
                              <div className="flex justify-between text-[11px]">
                                <span className="text-foreground truncate max-w-[140px]">
                                  {item.value || "(empty)"}
                                </span>
                                <span className="text-muted-foreground">
                                  {item.count} ({item.pct}%)
                                </span>
                              </div>
                              <div className="h-1 w-full rounded-full bg-muted overflow-hidden">
                                <div
                                  className="h-full bg-primary/70 rounded-full"
                                  style={{ width: `${Math.min(item.pct, 100)}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Tab 3: Correlation Matrix */}
          {activeTab === "correlations" && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-center border-collapse">
                <thead>
                  <tr className="border-b border-border">
                    <th className="p-2 text-left text-muted-foreground font-medium">Variable</th>
                    {corrCols.map((col) => (
                      <th
                        key={col}
                        className="p-2 text-muted-foreground font-medium truncate max-w-[90px]"
                        title={col}
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {corrCols.map((colA) => (
                    <tr key={colA} className="border-b border-border/40 hover:bg-muted/10">
                      <td className="p-2 text-left font-semibold text-foreground truncate max-w-[120px]">
                        {colA}
                      </td>
                      {corrCols.map((colB) => {
                        const val = correlation_matrix[colA]?.[colB]
                        const numVal = typeof val === "number" ? val : null
                        const isSelf = colA === colB
                        let bg = ""
                        let textColor = "text-muted-foreground"

                        if (isSelf) {
                          bg = "bg-primary/15 font-semibold text-primary"
                        } else if (numVal !== null) {
                          if (numVal > 0.5) {
                            bg = "bg-emerald-500/20"
                            textColor = "text-emerald-700 dark:text-emerald-300 font-semibold"
                          } else if (numVal < -0.5) {
                            bg = "bg-rose-500/20"
                            textColor = "text-rose-700 dark:text-rose-300 font-semibold"
                          } else if (numVal > 0.2) {
                            bg = "bg-emerald-500/10"
                            textColor = "text-foreground"
                          } else if (numVal < -0.2) {
                            bg = "bg-rose-500/10"
                            textColor = "text-foreground"
                          }
                        }

                        return (
                          <td key={colB} className={`p-2 ${bg} ${textColor}`}>
                            {numVal !== null ? numVal.toFixed(2) : "-"}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
