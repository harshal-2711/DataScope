import { useState } from "react"
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  HelpCircle,
  BarChart2,
  Calculator,
  Layers,
} from "lucide-react"
import type { ValidationReport, ValidationCheck } from "@/types/intelligence"

interface ValidationBannerProps {
  report?: ValidationReport
}

export function ValidationBanner({ report }: ValidationBannerProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [filter, setFilter] = useState<"all" | "Valid" | "Needs Review" | "Unsupported">("all")

  if (!report) return null

  const { overall_status, summary, counts, checks } = report

  const statusConfig = {
    Valid: {
      border: "border-emerald-500/30",
      bg: "bg-emerald-500/10",
      text: "text-emerald-600 dark:text-emerald-400",
      badgeBg: "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300",
      icon: CheckCircle2,
      label: "Analysis Validated",
      desc: "All calculations, aggregations, and data types passed rigorous mathematical checks.",
    },
    "Needs Review": {
      border: "border-amber-500/30",
      bg: "bg-amber-500/10",
      text: "text-amber-600 dark:text-amber-400",
      badgeBg: "bg-amber-500/20 text-amber-700 dark:text-amber-300",
      icon: AlertTriangle,
      label: "Needs Review",
      desc: "Some metrics or distributions require user attention or have high skewness.",
    },
    Unsupported: {
      border: "border-rose-500/30",
      bg: "bg-rose-500/10",
      text: "text-rose-600 dark:text-rose-400",
      badgeBg: "bg-rose-500/20 text-rose-700 dark:text-rose-300",
      icon: XCircle,
      label: "Unsupported",
      desc: "Key columns are missing or analyses conflict with the underlying data domain.",
    },
  }[overall_status] || {
    border: "border-border",
    bg: "bg-muted/40",
    text: "text-foreground",
    badgeBg: "bg-muted text-foreground",
    icon: HelpCircle,
    label: overall_status,
    desc: summary,
  }

  const StatusIcon = statusConfig.icon

  const filteredChecks = checks.filter((c) => {
    if (filter === "all") return true
    return c.status === filter
  })

  const getCheckIcon = (check: ValidationCheck) => {
    switch (check.component_type) {
      case "kpi":
        return <Calculator className="h-3.5 w-3.5 text-muted-foreground" />
      case "chart":
        return <BarChart2 className="h-3.5 w-3.5 text-muted-foreground" />
      case "relevance":
        return <Layers className="h-3.5 w-3.5 text-muted-foreground" />
      default:
        return <ShieldCheck className="h-3.5 w-3.5 text-muted-foreground" />
    }
  }

  return (
    <div
      className={`rounded-xl border ${statusConfig.border} ${statusConfig.bg} p-4 transition-all duration-200 shadow-xs`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-lg bg-card p-1.5 shadow-xs shrink-0">
            <StatusIcon className={`h-5 w-5 ${statusConfig.text}`} />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-foreground">
                Analysis Validation & Quality Checker
              </span>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${statusConfig.badgeBg}`}
              >
                {statusConfig.label}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">{summary}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          <div className="flex items-center gap-1.5 text-xs font-medium mr-2">
            <span className="inline-flex items-center rounded bg-emerald-500/15 px-2 py-0.5 text-emerald-700 dark:text-emerald-300">
              {counts.valid} Valid
            </span>
            {counts.needs_review > 0 && (
              <span className="inline-flex items-center rounded bg-amber-500/15 px-2 py-0.5 text-amber-700 dark:text-amber-300">
                {counts.needs_review} Review
              </span>
            )}
            {counts.unsupported > 0 && (
              <span className="inline-flex items-center rounded bg-rose-500/15 px-2 py-0.5 text-rose-700 dark:text-rose-300">
                {counts.unsupported} Unsupported
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="inline-flex items-center gap-1 rounded-lg border border-border/80 bg-card px-3 py-1.5 text-xs font-medium text-foreground hover:bg-accent transition-colors"
          >
            {isExpanded ? (
              <>
                Hide Details <ChevronUp className="h-3.5 w-3.5" />
              </>
            ) : (
              <>
                Inspect Checks <ChevronDown className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-3 pt-3 border-t border-border/50">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
              Verification Audit Log ({filteredChecks.length} checks)
            </span>
            <div className="flex gap-1">
              {(["all", "Valid", "Needs Review", "Unsupported"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setFilter(tab)}
                  className={`rounded-md px-2 py-0.5 text-[11px] font-medium transition-colors ${
                    filter === tab
                      ? "bg-foreground text-background"
                      : "bg-card text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {tab === "all" ? "All" : tab}
                </button>
              ))}
            </div>
          </div>

          <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1 text-xs">
            {filteredChecks.map((chk, idx) => {
              const badgeClass =
                chk.status === "Valid"
                  ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                  : chk.status === "Needs Review"
                  ? "bg-amber-500/15 text-amber-700 dark:text-amber-300"
                  : "bg-rose-500/15 text-rose-700 dark:text-rose-300"

              return (
                <div
                  key={idx}
                  className="flex items-start justify-between gap-3 rounded-lg border border-border/60 bg-card/80 p-2.5 hover:bg-card transition-colors"
                >
                  <div className="flex items-start gap-2 min-w-0">
                    <span className="mt-0.5 shrink-0">{getCheckIcon(chk)}</span>
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-foreground">{chk.title}</span>
                        <span className="rounded bg-muted px-1.5 py-0.2 font-mono text-[9px] uppercase text-muted-foreground">
                          {chk.component_type}
                        </span>
                      </div>
                      <p className="text-[11px] text-muted-foreground">{chk.reason}</p>
                    </div>
                  </div>

                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${badgeClass}`}
                  >
                    {chk.status}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
