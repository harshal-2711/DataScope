import { useState, useMemo } from "react"
import {
  Building2,
  TrendingDown,
  Layers,
  Award,
  BarChart3,
  Sparkles,
  AlertTriangle,
  Info,
  ShieldCheck,
  Calendar,
  ChevronDown,
  ChevronUp,
  SortAsc,
  SortDesc,
  Flame,
  CheckCircle2,
  HelpCircle,
  FileSpreadsheet,
  ArrowUpRight,
  TrendingUp,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { CompetitionIntelligenceResponse } from "@/types/intelligence"

interface CompetitionViewerProps {
  data: CompetitionIntelligenceResponse
}

export function CompetitionViewer({ data }: CompetitionViewerProps) {
  const [sortOrder, setSortOrder] = useState<"desc" | "asc" | "alpha">("desc")
  const [showAllSegments, setShowAllSegments] = useState(false)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)

  const overview = data.overview
  const segments = data.segments || []
  const gaps = data.gaps || []
  const timeComp = data.time_comparison
  const strengths = data.areas_of_strength || []
  const improvements = data.areas_for_improvement || []

  // Sorting
  const sortedSegments = useMemo(() => {
    const list = [...segments]
    if (sortOrder === "asc") {
      return list.sort((a, b) => a.value - b.value)
    }
    if (sortOrder === "alpha") {
      return list.sort((a, b) => a.name.localeCompare(b.name))
    }
    return list.sort((a, b) => b.value - a.value)
  }, [segments, sortOrder])

  const displayedSegments = showAllSegments ? sortedSegments : sortedSegments.slice(0, 10)
  const maxValue = Math.max(...segments.map((s) => Math.abs(s.value)), 1)

  // ==========================================
  // STATE 1: UNAVAILABLE / SETUP STATE
  // ==========================================
  if (!data.is_available || data.competition_mode === "unavailable" || !overview) {
    return (
      <div className="space-y-6">
        {/* Availability Status Card */}
        <Card className="border-border/60 bg-gradient-to-br from-card via-card to-muted/20 shadow-sm">
          <CardHeader className="pb-4">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-amber-500/10 p-2 text-amber-500 mt-0.5">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-amber-600 dark:text-amber-400 border-amber-500/30 text-xs font-semibold uppercase">
                    Data Availability Check
                  </Badge>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground">Comparison Readiness: Incomplete</span>
                </div>
                <CardTitle className="text-lg font-bold text-foreground">
                  External Competition Analysis Unavailable
                </CardTitle>
                <CardDescription className="text-sm text-muted-foreground max-w-3xl leading-relaxed">
                  {data.summary_statement ||
                    "This dataset does not contain verified company, brand or competitor information. We cannot compare your business with other companies using this data alone."}
                </CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-5 pt-0">
            {/* Required Data Checklist */}
            <div className="rounded-lg border border-border/60 bg-muted/30 p-4 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-foreground">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                What is Required for Competitive Analysis
              </div>
              <ul className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-muted-foreground">
                <li className="flex items-start gap-2 bg-background/60 p-3 rounded-md border border-border/40">
                  <span className="font-bold text-primary shrink-0">1.</span>
                  <div>
                    <strong className="text-foreground block mb-0.5">Commercial Entity Column</strong>
                    A verified column identifying companies, brands, competitors, manufacturers, or product lines.
                  </div>
                </li>
                <li className="flex items-start gap-2 bg-background/60 p-3 rounded-md border border-border/40">
                  <span className="font-bold text-primary shrink-0">2.</span>
                  <div>
                    <strong className="text-foreground block mb-0.5">Comparable Performance Measures</strong>
                    Continuous numeric metrics such as Revenue, Profit, Unit Sales, Pricing, or Ratings across entities.
                  </div>
                </li>
                <li className="flex items-start gap-2 bg-background/60 p-3 rounded-md border border-border/40">
                  <span className="font-bold text-primary shrink-0">3.</span>
                  <div>
                    <strong className="text-foreground block mb-0.5">Multi-Entity Records</strong>
                    Observations from at least 2 distinct competing entities recorded across comparable time windows.
                  </div>
                </li>
              </ul>
            </div>

            {/* Why Operational Attributes Are Excluded */}
            <div className="flex items-start gap-3 rounded-lg border border-border/40 bg-muted/20 p-4 text-xs">
              <Info className="h-4 w-4 shrink-0 text-primary mt-0.5" />
              <div className="space-y-1">
                <span className="font-semibold text-foreground">
                  Strict Entity Protection Active
                </span>
                <p className="text-muted-foreground leading-relaxed">
                  DataScope strictly prevents operational attributes (such as Customer Login Type, Device Type, Demographics, or Regions) from being misclassified as competitors. These dimensions reflect internal customer distributions rather than competing commercial firms.
                </p>
              </div>
            </div>

            {/* External Setup Guide */}
            <div className="rounded-lg border border-border/60 bg-card p-4 space-y-3">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-foreground">
                <FileSpreadsheet className="h-4 w-4 text-primary" />
                External Competitor Comparison Setup Guide
              </div>
              <p className="text-xs text-muted-foreground">
                To evaluate competitive positioning against market peers, upload a CSV or Excel dataset containing one of the following structure patterns:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="bg-muted/40 p-3 rounded border border-border/40 space-y-1">
                  <span className="font-semibold text-foreground">Multi-Company Benchmark Table</span>
                  <code className="text-[11px] block font-mono text-muted-foreground bg-background/80 p-1.5 rounded">
                    company_name, fiscal_quarter, revenue, net_profit, market_share
                  </code>
                </div>
                <div className="bg-muted/40 p-3 rounded border border-border/40 space-y-1">
                  <span className="font-semibold text-foreground">Multi-Brand Product Catalog</span>
                  <code className="text-[11px] block font-mono text-muted-foreground bg-background/80 p-1.5 rounded">
                    brand_name, product_category, units_sold, avg_price, customer_rating
                  </code>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // ==========================================
  // STATE 2: MODE A — DATASET-BASED BENCHMARKING
  // ==========================================
  return (
    <div className="space-y-6">
      {/* 1. Mode Header Banner */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between rounded-xl border border-border/60 bg-gradient-to-r from-card via-card/90 to-primary/5 p-5 shadow-sm">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="default" className="text-xs font-semibold uppercase tracking-wider bg-primary/90 text-primary-foreground">
              {data.mode_label || "Dataset-Based Benchmarking"}
            </Badge>
            <span className="text-muted-foreground">•</span>
            <Badge variant="outline" className="text-xs font-medium">
              Entity Type: {overview.entity_type_label}
            </Badge>
            <Badge variant="secondary" className="text-xs font-medium">
              Dimension: {overview.comparison_dimension_label}
            </Badge>
            <Badge variant="secondary" className="text-xs font-medium">
              Metric: {overview.primary_metric_label} ({overview.aggregation_method.toUpperCase()})
            </Badge>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            {overview.entity_type_label} Performance Benchmarks
          </h2>
          <p className="text-sm text-muted-foreground max-w-3xl">
            {overview.summary_statement}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge className="bg-primary/10 text-primary border-primary/20 text-xs px-3 py-1">
            <Layers className="h-3.5 w-3.5 mr-1.5" />
            {overview.total_segments} {overview.entity_type_label}s Compared
          </Badge>
        </div>
      </div>

      {/* 2. Top-Level High-Impact Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Highest Recorded Value */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-emerald-500/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <Building2 className="h-4 w-4" />
                Highest Recorded
              </span>
              <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/30">
                Rank #1
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1" title={overview.top_segment_name}>
              {overview.top_segment_name}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.top_segment_formatted}
            </div>
            <p className="text-xs text-muted-foreground">
              Highest observed {overview.primary_metric_label.toLowerCase()} in dataset
            </p>
          </CardContent>
        </Card>

        {/* Lowest Recorded Value */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-rose-500/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
                <TrendingDown className="h-4 w-4" />
                Lowest Recorded
              </span>
              <Badge variant="outline" className="text-[10px] text-rose-600 border-rose-500/30">
                Rank #{overview.total_segments}
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1" title={overview.bottom_segment_name}>
              {overview.bottom_segment_name}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.bottom_segment_formatted}
            </div>
            <p className="text-xs text-muted-foreground">
              Lowest observed {overview.primary_metric_label.toLowerCase()} in dataset
            </p>
          </CardContent>
        </Card>

        {/* Performance Spread */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4" />
                Observed Variance
              </span>
              <Badge variant="outline" className="text-[10px] text-primary border-primary/30">
                Ratio
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1">
              {overview.performance_spread_ratio}x
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.performance_spread_ratio}x
            </div>
            <p className="text-xs text-muted-foreground">
              Highest entity exceeds lowest by {overview.performance_spread_ratio}x
            </p>
          </CardContent>
        </Card>

        {/* Cohort Benchmark Average */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <BarChart3 className="h-4 w-4" />
                Cohort Average
              </span>
              <Badge variant="outline" className="text-[10px]">
                Mean
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1">
              {overview.benchmark_average_formatted}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.benchmark_average_formatted}
            </div>
            <p className="text-xs text-muted-foreground">
              Median: {overview.benchmark_median_formatted} across {overview.total_segments} entities
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 3. Actionable Competitive Findings: Strengths & Improvement Opportunities */}
      {(strengths.length > 0 || improvements.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {strengths.length > 0 && (
            <Card className="border-emerald-500/20 bg-emerald-500/5 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold text-sm">
                  <ArrowUpRight className="h-4 w-4" />
                  Measurable Leading Indicators
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-foreground/85">
                <ul className="list-disc list-inside space-y-1.5">
                  {strengths.map((str, idx) => (
                    <li key={idx} className="leading-relaxed">{str}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {improvements.length > 0 && (
            <Card className="border-amber-500/20 bg-amber-500/5 shadow-sm">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-semibold text-sm">
                  <HelpCircle className="h-4 w-4" />
                  Evidence-Backed Improvement Opportunities
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-foreground/85">
                <ul className="list-disc list-inside space-y-1.5">
                  {improvements.map((imp, idx) => (
                    <li key={idx} className="leading-relaxed">{imp}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* 4. Performance Gaps & Differences */}
      {gaps.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">
              Measured Performance Differences
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {gaps.map((gap, idx) => (
              <Card key={idx} className="border-border/60 hover:border-primary/40 transition-colors shadow-sm">
                <CardHeader className="pb-2 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Badge variant="secondary" className="text-[10px] font-medium">
                      {gap.gap_type.replace(/_/g, " ").toUpperCase()}
                    </Badge>
                    <span className="text-xs font-bold text-primary">
                      {gap.pct_difference > 0 ? `+${gap.pct_difference}%` : `${gap.pct_difference}%`}
                    </span>
                  </div>
                  <CardTitle className="text-sm font-semibold leading-snug">
                    {gap.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                  <p className="text-muted-foreground leading-relaxed">
                    {gap.explanation}
                  </p>
                  <div className="rounded-md bg-muted/50 p-2.5 font-mono text-[11px] text-foreground/80 border border-border/40">
                    {gap.evidence}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* 5. Entity Leaderboard & Visual Comparison Bar Chart */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Award className="h-4 w-4 text-primary" />
              {overview.entity_type_label} Distribution Ranking
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Comparative ranking of {overview.comparison_dimension_label} by {overview.primary_metric_label} ({overview.aggregation_method.toUpperCase()})
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Sort:</span>
            <Button
              variant={sortOrder === "desc" ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setSortOrder("desc")}
            >
              <SortDesc className="h-3 w-3 mr-1" />
              Highest
            </Button>
            <Button
              variant={sortOrder === "asc" ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setSortOrder("asc")}
            >
              <SortAsc className="h-3 w-3 mr-1" />
              Lowest
            </Button>
            <Button
              variant={sortOrder === "alpha" ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setSortOrder("alpha")}
            >
              A-Z
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          <div className="space-y-2.5">
            {displayedSegments.map((seg) => {
              const barWidth = Math.max((Math.abs(seg.value) / maxValue) * 100, 2)
              const isTop = seg.status === "top"
              const isBottom = seg.status === "bottom"
              const isAbove = seg.status === "above_average"

              return (
                <div
                  key={seg.rank + seg.name}
                  className="group rounded-lg border border-border/40 hover:border-primary/40 bg-card p-3 transition-all space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted font-bold text-[10px] text-muted-foreground">
                        #{seg.rank}
                      </span>
                      <span className="font-semibold text-foreground truncate max-w-[220px] sm:max-w-[320px]" title={seg.name}>
                        {seg.name}
                      </span>
                      {isTop && (
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-[10px] py-0 px-1.5 h-4">
                          Highest
                        </Badge>
                      )}
                      {isBottom && (
                        <Badge variant="outline" className="text-rose-500 border-rose-500/30 text-[10px] py-0 px-1.5 h-4">
                          Lowest
                        </Badge>
                      )}
                      {!isTop && !isBottom && isAbove && (
                        <Badge variant="outline" className="text-primary border-primary/30 text-[10px] py-0 px-1.5 h-4">
                          Above Avg
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-3 shrink-0 font-mono">
                      {seg.share_pct !== null && (
                        <span className="text-xs text-muted-foreground">
                          {seg.share_pct}% share
                        </span>
                      )}
                      <span className="text-xs font-bold text-foreground">
                        {seg.formatted_value}
                      </span>
                    </div>
                  </div>

                  {/* Relative Bar Indicator */}
                  <div className="h-2 w-full rounded-full bg-muted/60 overflow-hidden relative">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isTop
                          ? "bg-emerald-500"
                          : isBottom
                          ? "bg-rose-500"
                          : isAbove
                          ? "bg-primary"
                          : "bg-muted-foreground/50"
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          {segments.length > 10 && (
            <div className="flex justify-center pt-2">
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-8"
                onClick={() => setShowAllSegments(!showAllSegments)}
              >
                {showAllSegments ? (
                  <>
                    <ChevronUp className="h-3.5 w-3.5 mr-1" />
                    Show Top 10 Entities
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3.5 w-3.5 mr-1" />
                    View All {segments.length} Entities
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 6. Longitudinal Momentum & Growth Trajectory (if available) */}
      {timeComp && timeComp.is_available && timeComp.segment_series.length > 0 && (
        <Card className="border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Longitudinal Momentum & Growth Trajectory
                </CardTitle>
              </div>
              <Badge variant="outline" className="text-xs">
                Granularity: {timeComp.granularity}
              </Badge>
            </div>
            <CardDescription className="text-xs">
              {timeComp.summary}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {timeComp.fastest_growing && (
                <div className="flex items-center gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
                  <div className="rounded-full bg-emerald-500/10 p-2 text-emerald-500">
                    <Flame className="h-4 w-4" />
                  </div>
                  <div className="space-y-0.5 text-xs">
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                      Fastest Growth: {timeComp.fastest_growing}
                    </span>
                    <p className="text-muted-foreground">
                      Expanded by {timeComp.fastest_growing_rate ? `${timeComp.fastest_growing_rate > 0 ? "+" : ""}${timeComp.fastest_growing_rate}%` : "highest rate"} across observed periods.
                    </p>
                  </div>
                </div>
              )}

              {timeComp.most_declining && (
                <div className="flex items-center gap-3 rounded-lg border border-rose-500/20 bg-rose-500/5 p-3">
                  <div className="rounded-full bg-rose-500/10 p-2 text-rose-500">
                    <TrendingDown className="h-4 w-4" />
                  </div>
                  <div className="space-y-0.5 text-xs">
                    <span className="font-semibold text-rose-600 dark:text-rose-400">
                      Steepest Decline: {timeComp.most_declining}
                    </span>
                    <p className="text-muted-foreground">
                      Contracted by {timeComp.most_declining_rate ? `${timeComp.most_declining_rate}%` : "steepest rate"} across observed periods.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Segment Period Series Preview */}
            <div className="rounded-lg border border-border/40 bg-muted/20 p-4 space-y-3">
              <span className="text-xs font-semibold text-foreground">
                Observed Period Values for Top {overview.entity_type_label}s ({timeComp.period_labels.join(", ")})
              </span>
              <div className="space-y-2">
                {timeComp.segment_series.map((s, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-1 border-b border-border/30 pb-1.5 last:border-0 last:pb-0">
                    <span className="font-medium text-foreground w-40 truncate">{s.segment}</span>
                    <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-muted-foreground">
                      {s.values.map((v, pIdx) => (
                        <span key={pIdx} className="bg-background/80 px-1.5 py-0.5 rounded border border-border/40">
                          {timeComp.period_labels[pIdx] || `P${pIdx+1}`}: {v.toLocaleString()}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 7. Technical Evidence & Methodology Accordion */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader
          className="cursor-pointer select-none py-3"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-primary" />
              <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                Technical Evidence, Methodology & Limitations
              </span>
            </div>
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
              {showTechnicalDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </CardHeader>

        {showTechnicalDetails && (
          <CardContent className="pt-0 space-y-4 text-xs border-t border-border/40 mt-1">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3">
              <div className="space-y-2">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Info className="h-3.5 w-3.5 text-primary" />
                  Calculation Methodology
                </span>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                  {data.methodology_notes.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              </div>

              <div className="space-y-2">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                  Data Limitations & Scope
                </span>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                  {data.data_limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  )
}
