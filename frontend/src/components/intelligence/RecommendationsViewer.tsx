import { useState, useMemo } from "react"
import { Link } from "react-router-dom"
import {
  Lightbulb,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  Activity,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Search,
  ArrowUpRight,
  Calendar,
  Compass,
  FileCheck2,
  Target,
  HelpCircle,
  ShieldAlert,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type {
  RecommendationsIntelligenceResponse,
  RecommendationCategory,
  RecommendationPriority,
} from "@/types/intelligence"

interface RecommendationsViewerProps {
  data: RecommendationsIntelligenceResponse
}

const CATEGORY_ICONS: Record<RecommendationCategory, any> = {
  performance_improvement: TrendingUp,
  risk_mitigation: ShieldAlert,
  cost_optimization: DollarSign,
  revenue_opportunities: Sparkles,
  data_quality: FileCheck2,
  operational_efficiency: Activity,
  market_competitive_actions: Compass,
}

const CATEGORY_COLORS: Record<RecommendationCategory, { badge: string; textClass: string; bgClass: string }> = {
  cost_optimization: {
    badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    textClass: "text-emerald-400",
    bgClass: "bg-emerald-500/5",
  },
  revenue_opportunities: {
    badge: "bg-sky-500/10 text-sky-400 border-sky-500/20",
    textClass: "text-sky-400",
    bgClass: "bg-sky-500/5",
  },
  risk_mitigation: {
    badge: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    textClass: "text-rose-400",
    bgClass: "bg-rose-500/5",
  },
  performance_improvement: {
    badge: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    textClass: "text-blue-400",
    bgClass: "bg-blue-500/5",
  },
  operational_efficiency: {
    badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    textClass: "text-amber-400",
    bgClass: "bg-amber-500/5",
  },
  data_quality: {
    badge: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    textClass: "text-indigo-400",
    bgClass: "bg-indigo-500/5",
  },
  market_competitive_actions: {
    badge: "bg-teal-500/10 text-teal-400 border-teal-500/20",
    textClass: "text-teal-400",
    bgClass: "bg-teal-500/5",
  },
}

const PRIORITY_BADGES: Record<RecommendationPriority, { badge: string; label: string; borderAccent: string }> = {
  critical: {
    badge: "bg-rose-500/15 text-rose-300 border border-rose-500/30 font-medium uppercase tracking-wider",
    label: "Critical Priority",
    borderAccent: "border-l-rose-500",
  },
  high: {
    badge: "bg-amber-500/15 text-amber-300 border border-amber-500/30 font-medium uppercase tracking-wider",
    label: "High Priority",
    borderAccent: "border-l-amber-500",
  },
  medium: {
    badge: "bg-blue-500/15 text-blue-300 border border-blue-500/30 font-medium uppercase tracking-wider",
    label: "Medium Priority",
    borderAccent: "border-l-blue-500",
  },
  low: {
    badge: "bg-secondary text-muted-foreground border border-border font-normal uppercase tracking-wider",
    label: "Low Priority",
    borderAccent: "border-l-muted-foreground",
  },
}

export function RecommendationsViewer({ data }: RecommendationsViewerProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [selectedPriority, setSelectedPriority] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [expandedDetails, setExpandedDetails] = useState<Record<string, boolean>>({})

  const overview = data.overview
  const recommendations = data.recommendations || []

  const toggleDetails = (recId: string) => {
    setExpandedDetails((prev) => ({
      ...prev,
      [recId]: !prev[recId],
    }))
  }

  // Filter recommendations
  const filteredRecs = useMemo(() => {
    return recommendations.filter((rec) => {
      const matchCategory = selectedCategory === "all" || rec.category === selectedCategory
      const matchPriority = selectedPriority === "all" || rec.priority === selectedPriority
      const probText = rec.short_summary || rec.business_problem || rec.problem_detected || ""
      const titleText = rec.title || ""
      const entText = rec.entity_name || ""

      const matchQuery =
        searchQuery === "" ||
        titleText.toLowerCase().includes(searchQuery.toLowerCase()) ||
        probText.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entText.toLowerCase().includes(searchQuery.toLowerCase())

      return matchCategory && matchPriority && matchQuery
    })
  }, [recommendations, selectedCategory, selectedPriority, searchQuery])

  // Insufficient evidence state
  if (!data.is_available || recommendations.length === 0) {
    return (
      <div className="space-y-6">
        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="pb-4">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-amber-500/10 p-2.5 text-amber-500 mt-0.5">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <CardTitle className="text-lg font-semibold">
                  Insufficient data for reliable recommendations
                </CardTitle>
                <CardDescription className="text-sm">
                  {overview.summary_statement || "The uploaded dataset does not contain sufficient verified dimensions to produce actionable business recommendations."}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-0">
            <div className="rounded-lg border border-border/50 bg-background/50 p-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                <HelpCircle className="h-3.5 w-3.5 text-primary" />
                Missing Required Dataset Dimensions:
              </h4>
              <ul className="space-y-1.5 text-xs text-muted-foreground list-disc list-inside">
                {overview?.data_limitations_summary && overview.data_limitations_summary.length > 0 ? (
                  overview.data_limitations_summary.map((lim, idx) => (
                    <li key={idx}><strong className="text-foreground">{lim}</strong></li>
                  ))
                ) : (
                  <>
                    <li><strong className="text-foreground">Time / Date column</strong> (e.g. Order Date, Month, Timestamp) for trend comparison.</li>
                    <li><strong className="text-foreground">Financial Metrics</strong> (Revenue, Profit, Sales, Unit Cost, Margin) for profitability analysis.</li>
                    <li><strong className="text-foreground">Entity Dimensions</strong> (Category, Product, Region, Department, Supplier) to isolate key drivers.</li>
                    <li><strong className="text-foreground">Sample Volume</strong>: At least 5-10 records to guarantee reliable calculations.</li>
                  </>
                )}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* 1. TOP EXECUTIVE STATS */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Total Recommendations
            </CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-foreground">{overview.total_recommendations}</div>
            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1.5">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Prioritized by potential business impact
            </p>
          </CardContent>
        </Card>

        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              High Priority
            </CardTitle>
            <ShieldAlert className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-amber-500">
              {overview.critical_count + overview.high_count}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Actions with highest profit or operational benefit
            </p>
          </CardContent>
        </Card>

        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Verified Calculations
            </CardTitle>
            <FileCheck2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-emerald-500">
              {overview.evidence_backed_count}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              100% verified from uploaded dataset
            </p>
          </CardContent>
        </Card>

        <Card className="border-border bg-card shadow-xs">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Medium / Advisory
            </CardTitle>
            <Sparkles className="h-4 w-4 text-sky-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold tracking-tight text-foreground">
              {overview.medium_count + overview.low_count}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Moderate impact or process improvements
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 2. EXECUTIVE SUMMARY */}
      <Card className="border-border bg-card shadow-xs">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-sm font-semibold">Executive Overview</CardTitle>
            </div>
            <Badge variant="outline" className="text-xs font-normal">
              Domain: {data.domain_name}
            </Badge>
          </div>
          <CardDescription className="text-sm mt-1 text-foreground/90 font-medium leading-relaxed">
            {overview.summary_statement}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* 3. FILTER CONTROLS & SEARCH */}
      <div className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Category Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => setSelectedCategory("all")}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                selectedCategory === "all"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              All Actions ({recommendations.length})
            </button>
            {data.categories_present?.map((cat) => {
              const count = recommendations.filter((r) => r.category === cat).length
              if (count === 0) return null
              const Icon = CATEGORY_ICONS[cat as RecommendationCategory] || Lightbulb
              const sampleRec = recommendations.find((r) => r.category === cat)
              const label = sampleRec?.category_label || cat.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")

              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    selectedCategory === cat
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>
                    {label} ({count})
                  </span>
                </button>
              )
            })}
          </div>

          {/* Priority & Search Filter */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1 sm:w-52">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search recommendations..."
                className="h-8 w-full rounded-md border border-input bg-background pl-8 pr-3 text-xs shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
            </div>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="all">All Priorities</option>
              <option value="critical">Critical Priority</option>
              <option value="high">High Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="low">Low Priority</option>
            </select>
          </div>
        </div>

        {/* 4. CLEAN, ACTIONABLE RECOMMENDATIONS LIST */}
        <div className="space-y-6">
          {filteredRecs.length === 0 ? (
            <Card className="border-dashed p-8 text-center">
              <p className="text-sm text-muted-foreground">
                No recommendations match the selected filters or search terms.
              </p>
            </Card>
          ) : (
            filteredRecs.map((rec, index) => {
              const isDetailsExpanded = !!expandedDetails[rec.rec_id]
              const catConfig = CATEGORY_COLORS[rec.category] || CATEGORY_COLORS.cost_optimization
              const prioConfig = PRIORITY_BADGES[rec.priority] || PRIORITY_BADGES.medium
              const CatIcon = CATEGORY_ICONS[rec.category] || Lightbulb

              const shortSummary = rec.short_summary || rec.business_problem || rec.problem_detected || ""
              const findings = rec.what_we_found && rec.what_we_found.length > 0
                ? rec.what_we_found
                : rec.evidence ? [rec.evidence] : []
              const actionSteps = rec.action_steps && rec.action_steps.length > 0
                ? rec.action_steps
                : rec.recommended_action ? [rec.recommended_action] : []
              const expectedResult = rec.expected_result || rec.expected_objective || rec.success_measure || "Improve overall business performance."
              const whyMatters = rec.why_it_matters || "Directly impacts overall operating performance and profit."

              return (
                <Card
                  key={rec.rec_id}
                  className={`border-border bg-card shadow-xs transition-all hover:border-border hover:bg-card/90 border-l-4 ${prioConfig.borderAccent}`}
                >
                  {/* Card Header: Priority, Title, Quick Meta */}
                  <CardHeader className="pb-3 pt-5 px-6">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                      <div className="space-y-2 flex-1">
                        {/* Meta Tags Row */}
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-bold text-muted-foreground font-mono">
                            RECOMMENDATION #{index + 1}
                          </span>
                          <span className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[11px] ${prioConfig.badge}`}>
                            {prioConfig.label}
                          </span>
                          <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[11px] font-medium ${catConfig.badge}`}>
                            <CatIcon className="h-3 w-3" />
                            {rec.category_label || "Action"}
                          </span>
                          {rec.entity_name && (
                            <span className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-0.5 text-[11px] font-medium text-foreground">
                              {rec.entity_name}
                            </span>
                          )}
                          {rec.time_period && (
                            <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                              <Calendar className="h-3 w-3" />
                              {rec.time_period}
                            </span>
                          )}
                        </div>

                        {/* Title */}
                        <CardTitle className="text-lg font-bold leading-snug text-foreground">
                          {rec.title}
                        </CardTitle>

                        {/* Short Summary */}
                        <p className="text-sm text-foreground/90 font-medium leading-relaxed">
                          {shortSummary}
                        </p>
                      </div>

                      {/* Evidence Module Link if available */}
                      {rec.suggested_investigation_route && (
                        <div className="self-start md:self-auto shrink-0">
                          <Button asChild size="sm" variant="outline" className="h-8 gap-1.5 text-xs">
                            <Link to={rec.suggested_investigation_route}>
                              <span>{rec.suggested_investigation_label || "View Details"}</span>
                              <ArrowUpRight className="h-3.5 w-3.5 text-muted-foreground" />
                            </Link>
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4 pt-1 pb-6 px-6">
                    {/* KEY NUMBERS STRIP (Max 4 Pills) */}
                    {rec.key_metrics && rec.key_metrics.length > 0 && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                        {rec.key_metrics.slice(0, 4).map((metric, mIdx) => (
                          <div
                            key={mIdx}
                            className="rounded-lg border border-border bg-secondary/30 px-3 py-2 text-left"
                          >
                            <span className="text-[11px] font-medium text-muted-foreground block truncate">
                              {metric.label}
                            </span>
                            <span className="text-base font-bold text-foreground block tracking-tight mt-0.5">
                              {metric.value}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* TWO-COLUMN CORE CONTENT: WHAT WE FOUND + WHAT YOU SHOULD DO */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                      {/* Left: What We Found & Why It Matters */}
                      <div className="rounded-lg border border-border bg-secondary/20 p-4 space-y-3">
                        <div className="space-y-2">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                            What We Found:
                          </h4>
                          <ul className="space-y-1.5 text-xs text-foreground/90">
                            {findings.map((finding, fIdx) => (
                              <li key={fIdx} className="flex items-start gap-2">
                                <span className="text-muted-foreground font-bold mt-0.5">•</span>
                                <span className="leading-relaxed">{finding}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {whyMatters && (
                          <div className="pt-2 border-t border-border/40">
                            <h5 className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground mb-1">
                              Why It Matters:
                            </h5>
                            <p className="text-xs text-foreground/80 leading-relaxed">
                              {whyMatters}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Right: What You Should Do */}
                      <div className="rounded-lg border border-border bg-secondary/20 p-4 space-y-3">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-foreground flex items-center gap-1.5">
                          <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
                          What You Should Do:
                        </h4>
                        <ol className="space-y-2 text-xs text-foreground font-medium">
                          {actionSteps.map((step, sIdx) => (
                            <li key={sIdx} className="flex items-start gap-2.5">
                              <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary text-[11px] font-bold text-foreground">
                                {sIdx + 1}
                              </span>
                              <span className="leading-relaxed pt-0.5">{step}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>

                    {/* EXPECTED RESULT BANNER */}
                    <div className="rounded-lg border border-border bg-secondary/30 px-4 py-2.5 flex items-center gap-2.5">
                      <Target className="h-4 w-4 text-emerald-400 shrink-0" />
                      <div className="text-xs">
                        <strong className="text-emerald-400 font-semibold mr-1.5">
                          Expected Result:
                        </strong>
                        <span className="text-foreground/90 font-medium">
                          {expectedResult}
                        </span>
                      </div>
                    </div>

                    {/* EXPANDABLE CALCULATION DETAILS & NOTES */}
                    <div className="pt-1">
                      <button
                        onClick={() => toggleDetails(rec.rec_id)}
                        className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {isDetailsExpanded ? (
                          <>
                            <ChevronUp className="h-3.5 w-3.5" />
                            Hide Calculation Details & Notes
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3.5 w-3.5" />
                            View Calculation Details & Notes
                          </>
                        )}
                      </button>

                      {isDetailsExpanded && (
                        <div className="mt-3 space-y-3 rounded-lg border border-border/50 bg-muted/20 p-4 text-xs animate-in fade-in-50 duration-200">
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pb-3 border-b border-border/40">
                            {/* Possible Reason */}
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-0.5">
                                Possible Reason:
                              </span>
                              <p className="text-foreground/90 font-medium leading-relaxed">
                                {rec.root_cause_signal || rec.interpretation || "Observed pattern in historical transactions."}
                              </p>
                            </div>

                            {/* What to Track */}
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-0.5">
                                What to Track:
                              </span>
                              <p className="text-foreground/90 font-medium leading-relaxed">
                                {rec.action_plan?.metric_to_monitor || rec.relevant_metric || "Profit margin and sales volume over next review period."}
                              </p>
                            </div>

                            {/* Next Step */}
                            <div>
                              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-0.5">
                                Next Step:
                              </span>
                              <p className="text-foreground/90 font-medium leading-relaxed">
                                {rec.action_plan?.follow_up_investigation || "Review product performance after initial adjustment."}
                              </p>
                            </div>
                          </div>

                          {/* Important Note */}
                          {rec.limitations && (
                            <div className="space-y-1">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-amber-500/90 flex items-center gap-1">
                                <AlertTriangle className="h-3 w-3" /> Important Note:
                              </span>
                              <p className="text-muted-foreground leading-relaxed">
                                {rec.limitations}
                              </p>
                            </div>
                          )}

                          {/* Source Columns */}
                          {rec.source_columns && rec.source_columns.length > 0 && (
                            <div className="flex flex-wrap items-center gap-1.5 pt-1">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                                Source Columns Used:
                              </span>
                              {rec.source_columns.map((col, cIdx) => (
                                <Badge key={cIdx} variant="outline" className="text-[10px] font-mono">
                                  {col}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}

