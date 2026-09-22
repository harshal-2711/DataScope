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
  ChevronDown,
  ChevronUp,
  Sparkles,
  HelpCircle,
  Clock,
} from "lucide-react"
import type { RiskIntelligenceResponse, RiskItem } from "@/types/intelligence"

interface RiskViewerProps {
  data?: RiskIntelligenceResponse | null
  risks?: RiskItem[]
}

function MiniSparkline({ points, isNegative }: { points: Array<{ period: string; value: number }>; isNegative?: boolean }) {
  if (!points || points.length < 2) return null

  const values = points.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const width = 110
  const height = 28
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
      <span className="text-[10px] text-muted-foreground font-mono">Trend</span>
    </div>
  )
}

function RiskCardItem({ risk }: { risk: RiskItem }) {
  const [showTechnical, setShowTechnical] = useState(false)

  const isHigh = risk.severity === "high"
  const isMed = risk.severity === "medium"
  const hasValues = risk.current_value !== undefined && risk.current_value !== null
  const isNegativeChange = risk.pct_change !== undefined && risk.pct_change !== null && risk.pct_change < 0
  const isPositiveChange = risk.pct_change !== undefined && risk.pct_change !== null && risk.pct_change > 0

  return (
    <div
      className={`flex flex-col justify-between rounded-xl border bg-card p-5 shadow-xs transition-all hover:border-border/80 ${
        isHigh
          ? "border-rose-500/30 hover:shadow-rose-500/5"
          : isMed
          ? "border-amber-500/30 hover:shadow-amber-500/5"
          : "border-border"
      }`}
    >
      <div className="space-y-4">
        {/* Header: Title & Badges */}
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {risk.category}
              </span>
              {risk.time_period && (
                <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  {risk.time_period}
                </span>
              )}
            </div>
            <h4 className="text-sm font-bold text-foreground leading-snug">{risk.title || risk.category}</h4>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                isHigh
                  ? "bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/20"
                  : isMed
                  ? "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                  : "bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/20"
              }`}
            >
              {risk.severity === "high" ? "High Priority" : risk.severity === "medium" ? "Moderate" : "Informational"}
            </span>
          </div>
        </div>

        {/* Value Comparison Block */}
        {hasValues && (
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-muted/40 p-3 border border-border/50">
            <div className="space-y-0.5">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Metric Comparison</div>
              <div className="flex items-baseline gap-2">
                <span className="text-sm font-bold text-foreground">
                  {risk.current_value_formatted || risk.current_value}
                </span>
                {risk.previous_value_formatted && (
                  <span className="text-xs text-muted-foreground">
                    (vs {risk.previous_value_formatted})
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3">
              {risk.pct_change !== undefined && risk.pct_change !== null && (
                <div
                  className={`flex items-center gap-1 rounded-md px-2 py-1 text-xs font-bold ${
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

        {/* Explanation / What Happened */}
        <p className="text-xs text-muted-foreground leading-relaxed">{risk.description}</p>

        {/* Why It Matters */}
        {risk.why_it_matters && (
          <div className="rounded-lg bg-card border border-border/80 p-3 text-xs space-y-1">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-foreground flex items-center gap-1">
              <HelpCircle className="h-3.5 w-3.5 text-primary" />
              Why this matters
            </div>
            <div className="text-muted-foreground leading-relaxed">{risk.why_it_matters}</div>
          </div>
        )}

        {/* Recommended Investigation */}
        {risk.recommended_action && (
          <div className="rounded-lg bg-primary/5 border border-primary/15 p-3 text-xs space-y-1">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-primary flex items-center gap-1">
              <ArrowRight className="h-3.5 w-3.5" />
              Recommended Investigation
            </div>
            <div className="text-foreground/90 leading-relaxed">{risk.recommended_action}</div>
          </div>
        )}
      </div>

      {/* Expandable Technical Evidence Section */}
      <div className="mt-4 pt-3 border-t border-border/60">
        <button
          onClick={() => setShowTechnical(!showTechnical)}
          className="flex w-full items-center justify-between text-left text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <span>Technical Evidence & Qualification</span>
          {showTechnical ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>

        {showTechnical && (
          <div className="mt-2.5 rounded-lg bg-muted/40 p-3 text-xs space-y-2 border border-border/40">
            <div>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Factual Evidence</div>
              <div className="font-mono text-xs text-foreground mt-0.5">{risk.evidence}</div>
            </div>
            {risk.severity_reason && (
              <div>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Severity Justification</div>
                <div className="text-muted-foreground text-xs mt-0.5">{risk.severity_reason}</div>
              </div>
            )}
            {risk.qualification && (
              <div className="text-[10px] text-muted-foreground/80 italic">
                Methodology: {risk.qualification}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function DistributionInsightsSection({ insights }: { insights: import("@/types/intelligence").DistributionInsight[] }) {
  if (!insights || insights.length === 0) return null

  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-bold text-foreground">Dataset Distribution Insights</h4>
            <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-semibold text-muted-foreground border border-border">
              Descriptive Observations Only
            </span>
          </div>
          <p className="text-xs text-muted-foreground">
            Dominant categorical patterns in the dataset. These reflect population composition, not operational risks or vulnerabilities.
          </p>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {insights.map((ins) => (
          <div
            key={ins.insight_id}
            className="rounded-lg border border-border/70 bg-muted/20 p-4 space-y-2.5 transition-colors hover:bg-muted/30"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-foreground">{ins.dimension_label}</span>
              <span className="font-mono text-xs font-bold text-primary">{ins.percentage}%</span>
            </div>

            {/* Progress / Distribution Bar */}
            <div className="space-y-1">
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary/70"
                  style={{ width: `${Math.min(ins.percentage, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Dominant: <strong className="text-foreground">{ins.dominant_category}</strong></span>
                <span>{ins.category_count.toLocaleString()} of {ins.total_records.toLocaleString()} rows</span>
              </div>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">{ins.description}</p>
            <div className="rounded-md bg-muted/60 p-2 text-[11px] text-muted-foreground italic">
              {ins.observation_note}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function RiskViewer({ data, risks: legacyRisks }: RiskViewerProps) {
  const allRisks = data?.risks ?? legacyRisks ?? []
  const distributionInsights = data?.distribution_insights ?? []
  const overview = data?.overview

  const [severityFilter, setSeverityFilter] = useState<"all" | "high" | "medium" | "low">("all")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState<string>("")

  // Extract unique categories for filters
  const categories = useMemo(() => {
    const set = new Set<string>()
    allRisks.forEach((r) => {
      if (r.category) set.add(r.category)
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
  }, [allRisks, severityFilter, selectedCategory, searchQuery])

  const highCount = overview?.high_count ?? allRisks.filter((r) => r.severity === "high").length
  const medCount = overview?.medium_count ?? allRisks.filter((r) => r.severity === "medium").length
  const lowCount = overview?.low_count ?? allRisks.filter((r) => r.severity === "low").length
  const healthStatus = overview?.health_status ?? (highCount >= 2 ? "Critical Risks Identified" : (highCount === 1 || medCount > 0) ? "Attention Required" : "Healthy")
  
  // Top 3-5 key findings
  const keyFindings = useMemo(() => {
    return allRisks.slice(0, 4)
  }, [allRisks])

  if (!allRisks || allRisks.length === 0) {
    return (
      <div className="space-y-6">
        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-8 text-center shadow-xs">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500 mb-3">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <h3 className="text-base font-semibold text-foreground">No significant risks detected in the available data.</h3>
          <p className="mx-auto max-w-xl text-xs text-muted-foreground mt-2 leading-relaxed">
            {overview?.summary_statement ||
              "Evaluated metrics fall within standard operational and statistical ranges. No severe performance contractions or major data hygiene issues were identified."}
          </p>
          <div className="mt-4 inline-flex items-center gap-1.5 rounded-md bg-muted px-3 py-1.5 text-[11px] text-muted-foreground">
            <Info className="h-3.5 w-3.5" />
            <span>Note: Some risks may not be detectable from this dataset alone.</span>
          </div>
        </div>

        {distributionInsights.length > 0 && (
          <DistributionInsightsSection insights={distributionInsights} />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* SECTION A: OVERALL STATUS SUMMARY */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Overall Status</span>
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
            {allRisks.length} evaluated finding{allRisks.length === 1 ? "" : "s"}
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>High Priority</span>
            <ShieldAlert className="h-4 w-4 text-rose-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-rose-600 dark:text-rose-400">
            {highCount}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Requires primary attention</div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Moderate</span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
            {medCount}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Notable shifts / patterns</div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Informational</span>
            <Info className="h-4 w-4 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-blue-600 dark:text-blue-400">
            {lowCount}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Observations & notes</div>
        </div>

        <div className="rounded-xl border border-border bg-card p-4 shadow-xs col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Data Quality</span>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-foreground">
            {overview?.data_quality_warnings_count ?? 0}
          </div>
          <div className="text-[11px] text-muted-foreground mt-1">Missing/duplicate checks</div>
        </div>
      </div>

      {/* SECTION B: KEY FINDINGS DIGEST */}
      {keyFindings.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-foreground">
            <Sparkles className="h-4 w-4 text-primary" />
            Key Findings Digest
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {keyFindings.map((kf, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 rounded-lg bg-muted/40 p-3 border border-border/40 text-xs"
              >
                <div
                  className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${
                    kf.severity === "high"
                      ? "bg-rose-500"
                      : kf.severity === "medium"
                      ? "bg-amber-500"
                      : "bg-blue-500"
                  }`}
                />
                <div className="space-y-0.5">
                  <span className="font-semibold text-foreground">{kf.title}</span>
                  <p className="text-[11px] text-muted-foreground line-clamp-2">{kf.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SECTION C: FILTERS & SEARCH */}
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
            High Priority ({highCount})
          </button>
          <button
            onClick={() => setSeverityFilter("medium")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              severityFilter === "medium"
                ? "bg-amber-500 text-white shadow-xs"
                : "bg-amber-500/10 text-amber-600 dark:text-amber-400 hover:bg-amber-500/20"
            }`}
          >
            Moderate ({medCount})
          </button>
          <button
            onClick={() => setSeverityFilter("low")}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              severityFilter === "low"
                ? "bg-blue-500 text-white shadow-xs"
                : "bg-blue-500/10 text-blue-600 dark:text-blue-400 hover:bg-blue-500/20"
            }`}
          >
            Informational ({lowCount})
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

          <div className="relative flex-1 sm:w-48">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search findings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 w-full rounded-lg border border-border bg-background pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {/* SECTION D: HUMAN-READABLE RISK CARDS */}
      {filteredRisks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border p-8 text-center">
          <Filter className="mx-auto h-6 w-6 text-muted-foreground mb-2" />
          <h4 className="text-sm font-medium text-foreground">No matching findings</h4>
          <p className="text-xs text-muted-foreground mt-1">
            No risk signals match your active filter criteria. Try resetting the category or search filters.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {filteredRisks.map((risk) => (
            <RiskCardItem key={risk.risk_id} risk={risk} />
          ))}
        </div>
      )}

      {/* SECTION E: DATASET DISTRIBUTION INSIGHTS (SEPARATE DESCRIPTIVE SECTION) */}
      {distributionInsights.length > 0 && (
        <DistributionInsightsSection insights={distributionInsights} />
      )}

      {/* Dataset Safety Note */}
      <div className="text-center pt-2">
        <p className="text-[11px] text-muted-foreground">
          Note: Risk intelligence analyzes empirical patterns in the uploaded file. Some external business risks may not be detectable from this dataset alone.
        </p>
      </div>
    </div>
  )
}


