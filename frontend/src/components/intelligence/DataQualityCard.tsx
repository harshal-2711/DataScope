import { useState, useEffect } from "react"
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Info,
  ChevronDown,
  ChevronUp,
  Activity,
} from "lucide-react"
import type { DataQualityReportResponse } from "@/types/intelligence"
import { fetchDataQualityReport } from "@/lib/datasetApi"

interface DataQualityCardProps {
  datasetId: string
  initialData?: DataQualityReportResponse | null
}

export function DataQualityCard({ datasetId, initialData }: DataQualityCardProps) {
  const [data, setData] = useState<DataQualityReportResponse | null>(initialData ?? null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<boolean>(false)
  const [filterSeverity, setFilterSeverity] = useState<string>("all")

  useEffect(() => {
    if (!initialData) {
      setLoading(true)
      fetchDataQualityReport(datasetId)
        .then((json) => {
          setData(json)
          setLoading(false)
        })
        .catch((err) => {
          setError(err.message)
          setLoading(false)
        })
    } else {
      setData(initialData)
    }
  }, [datasetId, initialData])

  if (loading && !data) {
    return (
      <div className="flex h-24 items-center justify-center rounded-xl border border-border bg-card p-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Activity className="h-4 w-4 animate-spin text-primary" />
          Evaluating data reliability...
        </div>
      </div>
    )
  }

  if (error || !data) return null

  const isHealthy = data.status === "Healthy"
  const isWarning = data.status === "Warning"

  const filteredChecks = data.checks.filter((c) => {
    if (filterSeverity === "all") return true
    return c.severity === filterSeverity
  })

  // Calculate totals from diagnostics
  const diagValues = Object.values(data.column_diagnostics || {})
  const totalMissing = diagValues.reduce((acc, d) => acc + (d.missing_count || 0), 0)
  const totalDuplicates = diagValues.length > 0 ? (diagValues[0].duplicate_count || 0) : 0
  const totalCols = diagValues.length

  const reliabilityExplanation = totalMissing > 0
    ? `${totalMissing.toLocaleString()} missing cell values were detected across optional fields. This may affect isolated segment calculations, but core business measures remain reliable.`
    : "Data records are complete with no missing values or duplicate rows. Business metrics are fully supported."

  return (
    <div className="rounded-xl border border-border/80 bg-card p-4 shadow-xs space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-lg ${
              isHealthy
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : isWarning
                ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
            }`}
          >
            {isHealthy ? (
              <ShieldCheck className="h-5 w-5" />
            ) : isWarning ? (
              <AlertTriangle className="h-5 w-5" />
            ) : (
              <AlertOctagon className="h-5 w-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-foreground">Data Reliability</h3>
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.2 text-[10px] font-semibold uppercase tracking-wider ${
                  isHealthy
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : isWarning
                    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                    : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                }`}
              >
                {data.status}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{reliabilityExplanation}</p>
          </div>
        </div>

        {/* Issue counters & collapsible toggle */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 rounded-md bg-muted/50 px-2.5 py-1 text-muted-foreground text-[11px] font-medium">
            <span>{totalCols} Columns</span>
            <span>·</span>
            <span>{totalMissing.toLocaleString()} Missing Values</span>
            <span>·</span>
            <span>{totalDuplicates.toLocaleString()} Duplicates</span>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors ml-1"
          >
            {expanded ? "Hide Technical Details" : "Technical Details"}
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="space-y-4 pt-3 border-t border-border">
          {/* Filter Pills */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">Filter checks:</span>
              {["all", "critical", "warning", "info"].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilterSeverity(f)}
                  className={`px-2 py-0.5 rounded-md font-medium transition-colors text-[11px] ${
                    filterSeverity === f
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>
            <span className="text-[11px] text-muted-foreground">
              {data.issue_counts.critical} Critical · {data.issue_counts.warning} Warnings · {data.issue_counts.info} Passed
            </span>
          </div>

          {/* Checks List */}
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {filteredChecks.map((chk) => {
              const isCrit = chk.severity === "critical"
              const isWarn = chk.severity === "warning"
              return (
                <div
                  key={chk.id}
                  className={`rounded-lg border p-2.5 text-xs space-y-1 transition-colors ${
                    isCrit
                      ? "border-rose-500/30 bg-rose-500/5"
                      : isWarn
                      ? "border-amber-500/30 bg-amber-500/5"
                      : "border-border/70 bg-muted/20"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-semibold text-foreground">
                      {isCrit ? (
                        <AlertOctagon className="h-3.5 w-3.5 text-rose-500" />
                      ) : isWarn ? (
                        <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                      ) : (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                      )}
                      <span>{chk.name}</span>
                    </div>
                    {chk.affected_columns.length > 0 && (
                      <span className="font-mono text-[10px] text-muted-foreground">
                        Columns: {chk.affected_columns.join(", ")}
                      </span>
                    )}
                  </div>
                  <p className="text-muted-foreground text-[11px]">{chk.message}</p>
                  {chk.recommendation && (
                    <p className="text-foreground/90 font-medium pt-0.5 text-[11px]">
                      Action: {chk.recommendation}
                    </p>
                  )}
                </div>
              )
            })}
          </div>

          {/* Actionable Recommendations */}
          {data.recommendations.length > 0 && (
            <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs space-y-1.5">
              <span className="font-semibold text-foreground flex items-center gap-1.5 text-xs">
                <Info className="h-3.5 w-3.5 text-primary" />
                Data Hygiene Actions
              </span>
              <ul className="list-disc list-inside space-y-1 pl-1 text-[11px] text-muted-foreground">
                {data.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
