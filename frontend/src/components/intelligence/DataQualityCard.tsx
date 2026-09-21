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
      <div className="flex h-36 items-center justify-center rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Activity className="h-4 w-4 animate-spin text-primary" />
          Running data quality validation and hygiene inspection...
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

  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-11 w-11 items-center justify-center rounded-xl ${
              isHealthy
                ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                : isWarning
                ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
            }`}
          >
            {isHealthy ? (
              <ShieldCheck className="h-6 w-6" />
            ) : isWarning ? (
              <AlertTriangle className="h-6 w-6" />
            ) : (
              <AlertOctagon className="h-6 w-6" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-foreground">Data Quality & Hygiene Audit</h3>
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                  isHealthy
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : isWarning
                    ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                    : "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                }`}
              >
                {data.status.toUpperCase()} ({data.overall_score}/100)
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{data.summary}</p>
          </div>
        </div>

        {/* Issue counters */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1 rounded-md bg-rose-500/10 px-2.5 py-1 text-rose-600 font-medium">
            <AlertOctagon className="h-3 w-3" />
            <span>{data.issue_counts.critical} Critical</span>
          </div>
          <div className="flex items-center gap-1 rounded-md bg-amber-500/10 px-2.5 py-1 text-amber-600 font-medium">
            <AlertTriangle className="h-3 w-3" />
            <span>{data.issue_counts.warning} Warnings</span>
          </div>
          <div className="flex items-center gap-1 rounded-md bg-emerald-500/10 px-2.5 py-1 text-emerald-600 font-medium">
            <CheckCircle2 className="h-3 w-3" />
            <span>{data.issue_counts.info} Passed</span>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors ml-2"
          >
            {expanded ? "Hide Details" : "View Details"}
            {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="space-y-4 pt-3 border-t border-border">
          {/* Filter Pills */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Filter checks:</span>
            {["all", "critical", "warning", "info"].map((f) => (
              <button
                key={f}
                onClick={() => setFilterSeverity(f)}
                className={`px-2 py-0.5 rounded-md font-medium transition-colors ${
                  filterSeverity === f
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                {f.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Checks List */}
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {filteredChecks.map((chk) => {
              const isCrit = chk.severity === "critical"
              const isWarn = chk.severity === "warning"
              return (
                <div
                  key={chk.id}
                  className={`rounded-lg border p-3 text-xs space-y-1 transition-colors ${
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
                      <span className="font-mono text-xs text-muted-foreground">
                        Columns: {chk.affected_columns.join(", ")}
                      </span>
                    )}
                  </div>
                  <p className="text-muted-foreground">{chk.message}</p>
                  {chk.recommendation && (
                    <p className="text-foreground/90 font-medium pt-0.5">
                      Recommendation: {chk.recommendation}
                    </p>
                  )}
                </div>
              )
            })}
          </div>

          {/* Actionable Recommendations */}
          {data.recommendations.length > 0 && (
            <div className="rounded-lg border border-border bg-muted/30 p-3 text-xs space-y-1.5">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <Info className="h-3.5 w-3.5 text-primary" />
                Data Quality Improvement Recommendations
              </span>
              <ul className="list-disc list-inside space-y-1 pl-1 text-muted-foreground">
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
