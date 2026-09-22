import { useState, useMemo } from "react"
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  ArrowRight,
  Filter,
  Search,
  TrendingDown,
  TrendingUp,
  Activity,
  Zap,
  HelpCircle,
} from "lucide-react"
import type { RiskIntelligenceResponse, RiskItem } from "@/types/intelligence"

interface RiskViewerProps {
  data?: RiskIntelligenceResponse | null
  risks?: RiskItem[] // For backward compatibility if passed directly
}

function MiniSparkline({ points, isNegative }: { points: Array<{ period: string; value: number }>; isNegative?: boolean }) {
  if (!points || points.length < 2) return null

  const values = points.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 120
  const height = 32
  const padding = 4

  const coords = values.map((v, i) => {
    const x = padding + (i / (values.length - 1)) * (width - 2 * padding)
    const y = height - padding - ((v - min) / range) * (height - 2 * padding)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const pathD = `M ${coords.join(" L ")}`
  const strokeColor = isNegative ? "rgb(244 63 94)" : "rgb(59 130 246)"

  return (
    <div className="flex items-center gap-2">
      <svg width={width} height={height} className="overflow-visible">
        <path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {coords.map((c, idx) => {
          if (idx === coords.length - 1 || idx === 0) {
            const [cx, cy] = c.split(",")
            return (
              <circle
                key={idx}
                cx={cx}
                cy={cy}
                r="3"
                className={idx === coords.length - 1 ? (isNegative ? "fill-rose-500" : "fill-blue-500") : "fill-muted-foreground"}
              />
            )
          }
          return null
        })}
      </svg>
      <span className="text-[10px] text-muted-foreground font-mono">Trend Spark</span>
    </div>
  )
}

export function RiskViewer({ data, risks: legacyRisks }: RiskViewerProps) {
  const allRisks = data?.risks ?? legacyRisks ?? []
  const overview = data?.overview

  const [severityFilter, setSeverityFilter] = useState<"all" | "high" | "medium" | "low">("all")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [selectedMetric, setSelectedMetric] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState<string>("")

  // Extract unique categories & metrics for filters
  const categories = useMemo(() => {
    const set = new Set<string>()
    allRisks.forEach((r) => {
      if (r.category) set.add(r.category)
    })
    return Array.from(set).sort()
  }, [allRisks])

  const metrics = useMemo(() => {
    const set = new Set<string>()
    allRisks.forEach((r) => {
      if (r.affected_metric) set.add(r.affected_metric)
      else if (r.affected_column) set.add(r.affected_column)
    })
    return Array.from(set).sort()
  }, [allRisks])

  // Filtered risks
  const filteredRisks = useMemo(() => {
    return allRisks.filter((risk) => {
      if (severityFilter !== "all" && risk.severity !== severityFilter) {
        return false
      }
      if (selectedCategory !== "all" && risk.category !== selectedCategory) {
        return false
      }
      if (selectedMetric !== "all") {
        const metricName = risk.affected_metric || risk.affected_column
        if (metricName !== selectedMetric) return false
      }
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        const matchTitle = (risk.title || "").toLowerCase().includes(query)
        const matchDesc = risk.description.toLowerCase().includes(query)
        const matchEv = risk.evidence.toLowerCase().includes(query)
        const matchCol = (risk.affected_column || "").toLowerCase().includes(query)
        if (!matchTitle && !matchDesc && !matchEv && !matchCol) {
          return false
        }
      }
      return true
    })
  }, [allRisks, severityFilter, selectedCategory, selectedMetric, searchQuery])

  const highCount = overview?.high_count ?? allRisks.filter((r) => r.severity === "high").length
  const medCount = overview?.medium_count ?? allRisks.filter((r) => r.severity === "medium").length
  const lowCount = overview?.low_count ?? allRisks.filter((r) => r.severity === "low").length
  const healthStatus = overview?.health_status ?? (highCount > 0 ? "Critical Risks Identified" : medCount > 0 ? "Attention Required" : "Healthy")
  const topRisk = overview?.most_significant_risk ?? (allRisks.length > 0 ? allRisks[0] : null)

  if (!allRisks || allRisks.length === 0) {
    return (
      <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-8 text-center shadow-xs">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500 mb-3">
          <CheckCircle2 className="h-6 w-6" />
        </div>
        <h3 className="text-base font-semibold text-foreground">No Statistical Anomalies or Critical Risks Detected</h3>
        <p className="mx-auto max-w-xl text-xs text-muted-foreground mt-2 leading-relaxed">
          {overview?.summary_statement ||
            "Evaluated metrics fall within standard statistical dispersion fences. No severe entity concentration, abrupt performance contractions, or critical data quality violations were identified."}
        </p>
        <div className="mt-4 inline-flex items-center gap-1.5 rounded-md bg-muted px-3 py-1 text-[11px] text-muted-foreground">
          <Info className="h-3.5 w-3.5" />
          <span>Reflects empirical historical data stability. Does not guarantee external market certainty.</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 1. OVERVIEW & HEALTH STATUS CARDS */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Health Status</span>
            <Activity className="h-4 w-4 text-primary" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                healthStatus === "Critical Risks Identified"
                  ? "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20"
                  : healthStatus === "Attention Required"
                  ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                  : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
              }`}
            >
              {healthStatus}
            </span>
          </div>
          <div className="text-[11px] text-muted-foreground mt-1 truncate">
            {allRisks.length} evaluated signal{allRisks.length === 1 ? "" : "s"}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>High Severity</span>
            <ShieldAlert className="h-4 w-4 text-rose-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-rose-600 dark:text-rose-400">
            {highCount}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Requires primary action</div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Medium Severity</span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
            {medCount}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Moderate dispersion / drops</div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Low Severity</span>
            <Info className="h-4 w-4 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-blue-600 dark:text-blue-400">
            {lowCount}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Informational signals</div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Data Quality</span>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-foreground">
            {overview?.data_quality_warnings_count ?? 0}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Integrity warning signals</div>
        </div>
      </div>

      {/* 2. MOST SIGNIFICANT RISK SPOTLIGHT BANNER */}
      {topRisk && (topRisk.severity === "high" || topRisk.severity === "medium") && (
        <div className="relative overflow-hidden rounded-xl border border-rose-500/20 bg-rose-500/5 p-5 shadow-xs">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded bg-rose-500/20 px-2 py-0.5 text-[11px] font-semibold text-rose-600 dark:text-rose-300 uppercase tracking-wider">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  Primary Risk Spotlight
                </span>
                <span className="text-xs text-muted-foreground">|</span>
                <span className="text-xs font-medium text-muted-foreground">{topRisk.category}</span>
              </div>
              <h3 className="text-base font-bold text-foreground">{topRisk.title || topRisk.category}</h3>
              <p className="text-xs text-muted-foreground max-w-2xl leading-relaxed">{topRisk.description}</p>
            </div>

            {topRisk.recommended_action && (
              <div className="rounded-lg bg-card/80 border border-border/70 p-3 text-xs md:max-w-xs shrink-0">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-primary mb-1">
                  Immediate Action:
                </div>
                <div className="text-muted-foreground line-clamp-3">{topRisk.recommended_action}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 3. FILTER & SEARCH CONTROLS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 rounded-xl border border-border bg-card p-3 shadow-xs">
        {/* Severity filter pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setSeverityFilter("all")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              severityFilter === "all"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            All ({allRisks.length})
          </button>
          <button
            onClick={() => setSeverityFilter("high")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              severityFilter === "high"
                ? "bg-rose-500 text-white shadow-xs"
                : "bg-rose-500/10 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20"
            }`}
          >
            High ({highCount})
          </button>
          <button
            onClick={() => setSeverityFilter("medium")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              severityFilter === "medium"
                ? "bg-amber-500 text-white shadow-xs"
                : "bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20"
            }`}
          >
            Medium ({medCount})
          </button>
          <button
            onClick={() => setSeverityFilter("low")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              severityFilter === "low"
                ? "bg-blue-500 text-white shadow-xs"
                : "bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20"
            }`}
          >
            Low ({lowCount})
          </button>
        </div>

        {/* Dropdowns & Search */}
        <div className="flex flex-wrap items-center gap-2">
          {categories.length > 1 && (
            <div className="relative">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="h-8 rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="all">All Categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          )}

          {metrics.length > 1 && (
            <div className="relative">
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                className="h-8 rounded-lg border border-border bg-background px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary max-w-[150px] truncate"
              >
                <option value="all">All Metrics</option>
                {metrics.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="relative flex-1 sm:w-48">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search risk evidence..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 w-full rounded-lg border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {/* 4. RISK CARDS GRID */}
      {filteredRisks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-8 text-center">
          <Filter className="mx-auto h-6 w-6 text-muted-foreground mb-2" />
          <h4 className="text-sm font-medium text-foreground">No matching risks</h4>
          <p className="text-xs text-muted-foreground mt-1">
            No risk signals match your active filter criteria. Try resetting filters or search queries.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {filteredRisks.map((risk) => {
            const isHigh = risk.severity === "high"
            const isMed = risk.severity === "medium"
            const hasValues = risk.current_value !== undefined && risk.current_value !== null
            const isNegativeChange = risk.pct_change !== undefined && risk.pct_change !== null && risk.pct_change < 0
            const isPositiveChange = risk.pct_change !== undefined && risk.pct_change !== null && risk.pct_change > 0

            return (
              <div
                key={risk.risk_id}
                className={`flex flex-col justify-between rounded-xl border bg-card p-5 shadow-xs transition-all hover:border-border/80 ${
                  isHigh
                    ? "border-rose-500/30 hover:shadow-rose-500/5"
                    : isMed
                    ? "border-amber-500/30 hover:shadow-amber-500/5"
                    : "border-border"
                }`}
              >
                <div className="space-y-3">
                  {/* Top Bar: Category & Severity */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div
                        className={`flex h-7 w-7 items-center justify-center rounded-lg ${
                          isHigh
                            ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                            : isMed
                            ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                            : "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                        }`}
                      >
                        {isHigh ? (
                          <ShieldAlert className="h-4 w-4" />
                        ) : isMed ? (
                          <AlertTriangle className="h-4 w-4" />
                        ) : (
                          <Info className="h-4 w-4" />
                        )}
                      </div>
                      <div>
                        <div className="text-[11px] font-medium text-muted-foreground">{risk.category}</div>
                        <h4 className="text-sm font-bold text-foreground">{risk.title || risk.category}</h4>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                          isHigh
                            ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/20"
                            : isMed
                            ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                            : "bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/20"
                        }`}
                      >
                        {risk.severity}
                      </span>
                      <span className="rounded bg-muted px-2 py-0.5 text-[10px] text-muted-foreground font-medium">
                        {risk.label}
                      </span>
                    </div>
                  </div>

                  {/* Value Comparison Block (if values present) */}
                  {hasValues && (
                    <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-muted/40 p-3 border border-border/40">
                      <div className="space-y-0.5">
                        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Observed Level</div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-sm font-bold text-foreground">
                            {risk.current_value_formatted || risk.current_value}
                          </span>
                          {risk.previous_value_formatted && (
                            <span className="text-xs text-muted-foreground line-through">
                              from {risk.previous_value_formatted}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {risk.pct_change !== undefined && risk.pct_change !== null && (
                          <div
                            className={`flex items-center gap-1 rounded px-2 py-1 text-xs font-bold ${
                              isNegativeChange
                                ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                                : isPositiveChange
                                ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {isNegativeChange ? (
                              <TrendingDown className="h-3.5 w-3.5" />
                            ) : (
                              <TrendingUp className="h-3.5 w-3.5" />
                            )}
                            <span>{risk.pct_change > 0 ? `+${risk.pct_change}%` : `${risk.pct_change}%`}</span>
                          </div>
                        )}

                        {risk.time_series_preview && risk.time_series_preview.length >= 2 && (
                          <MiniSparkline points={risk.time_series_preview} isNegative={isNegativeChange} />
                        )}
                      </div>
                    </div>
                  )}

                  {/* Narrative Description */}
                  <p className="text-xs text-muted-foreground leading-relaxed">{risk.description}</p>

                  {/* Severity Justification */}
                  {risk.severity_reason && (
                    <div className="text-[11px] text-muted-foreground/90 italic flex items-center gap-1">
                      <HelpCircle className="h-3 w-3 text-muted-foreground shrink-0" />
                      <span>{risk.severity_reason}</span>
                    </div>
                  )}

                  {/* Evidence Box */}
                  <div className="rounded-lg bg-card border border-border/80 p-2.5 text-xs text-muted-foreground space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      <span>Factual Evidence</span>
                      {risk.time_period && <span className="font-mono text-[10px] lowercase">{risk.time_period}</span>}
                    </div>
                    <div className="font-mono text-xs text-foreground/90 leading-snug">{risk.evidence}</div>
                  </div>

                  {/* Affected Column Badge */}
                  {risk.affected_column && (
                    <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                      <span>Target dimension:</span>
                      <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-foreground">
                        {risk.affected_column}
                      </code>
                    </div>
                  )}
                </div>

                {/* Footer: Recommended Action */}
                <div className="mt-4 pt-3 border-t border-border/60 space-y-2">
                  {risk.recommended_action && (
                    <div className="flex items-start gap-2 text-xs text-foreground">
                      <ArrowRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-primary">Recommended Action: </span>
                        <span className="text-muted-foreground">{risk.recommended_action}</span>
                      </div>
                    </div>
                  )}

                  {risk.qualification && (
                    <div className="text-[10px] text-muted-foreground/80 pl-5">
                      Note: {risk.qualification}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

