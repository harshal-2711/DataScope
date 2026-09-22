import { useState, useMemo } from "react"
import {
  Trophy,
  TrendingDown,
  Layers,
  Award,
  BarChart3,
  Sparkles,
  AlertTriangle,
  Info,
  ShieldCheck,
  Percent,
  Calendar,
  ChevronDown,
  ChevronUp,
  SortAsc,
  SortDesc,
  Flame,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type {
  CompetitionIntelligenceResponse,
} from "@/types/intelligence"

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

  // Empty / Unavailable State
  if (!data.is_available || !overview) {
    return (
      <div className="space-y-6">
        <Card className="border-amber-500/20 bg-amber-500/5">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-amber-500/10 p-2 text-amber-500">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base text-amber-600 dark:text-amber-400">
                  Competitive Comparison Unavailable
                </CardTitle>
                <CardDescription>
                  {data.unavailable_reason || "Competitive comparison cannot be reliably calculated from this dataset."}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {data.missing_requirements && data.missing_requirements.length > 0 && (
              <div className="rounded-md border border-border/50 bg-background/50 p-3 space-y-2">
                <p className="font-medium text-xs text-muted-foreground uppercase tracking-wider">
                  Missing Requirements
                </p>
                <ul className="list-disc list-inside space-y-1 text-xs text-foreground/80">
                  {data.missing_requirements.map((req, i) => (
                    <li key={i}>{req}</li>
                  ))}
                </ul>
              </div>
            )}
            {data.data_limitations && data.data_limitations.length > 0 && (
              <div className="space-y-1 text-xs text-muted-foreground">
                <p className="font-medium">Data Observations:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {data.data_limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 1. Header Banner & Context Metadata */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between rounded-xl border border-border/60 bg-gradient-to-r from-card via-card/90 to-primary/5 p-5 shadow-sm">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-primary">
              Domain Intelligence
            </span>
            <span className="text-muted-foreground">•</span>
            <Badge variant="outline" className="text-xs font-medium">
              {data.domain_name || "General Analytics"}
            </Badge>
            <Badge variant="secondary" className="text-xs font-medium">
              Dimension: {overview.comparison_dimension_label}
            </Badge>
            <Badge variant="secondary" className="text-xs font-medium">
              Metric: {overview.primary_metric_label} ({overview.aggregation_method.toUpperCase()})
            </Badge>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            Segment Performance & Competitive Benchmarks
          </h2>
          <p className="text-sm text-muted-foreground">
            {overview.summary_statement}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge className="bg-primary/10 text-primary border-primary/20 text-xs px-3 py-1">
            <Layers className="h-3.5 w-3.5 mr-1.5" />
            {overview.total_segments} Segments Compared
          </Badge>
        </div>
      </div>

      {/* 2. Top-Level High-Impact Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Top Performer Card */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-emerald-500/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <Trophy className="h-4 w-4" />
                Cohort Leader
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
              Highest recorded value in {overview.comparison_dimension_label.toLowerCase()}
            </p>
          </CardContent>
        </Card>

        {/* Lowest Performer Card */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-rose-500/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
                <TrendingDown className="h-4 w-4" />
                Trailing Segment
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
              Lowest recorded value in {overview.comparison_dimension_label.toLowerCase()}
            </p>
          </CardContent>
        </Card>

        {/* Performance Spread / Gap */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <Percent className="h-4 w-4" />
                Spread Multiplier
              </span>
              <Badge variant="outline" className="text-[10px] text-primary border-primary/30">
                Gap Ratio
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
              Top segment exceeds lowest by {overview.performance_spread_ratio}x
            </p>
          </CardContent>
        </Card>

        {/* Benchmark Cohort Average */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <BarChart3 className="h-4 w-4" />
                Cohort Benchmark
              </span>
              <Badge variant="outline" className="text-[10px]">
                Mean / Median
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
              Median: {overview.benchmark_median_formatted} across {overview.total_segments} cohorts
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 3. Performance Gaps & Key Findings Cards */}
      {gaps.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">
              Measurable Performance Gaps & Findings
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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

      {/* 4. Segment Leaderboard & Visual Comparison Bar Chart */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Award className="h-4 w-4 text-primary" />
              Segment Performance Ranking
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Ranked distribution of {overview.comparison_dimension_label} by {overview.primary_metric_label} ({overview.aggregation_method.toUpperCase()})
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
                          Leader
                        </Badge>
                      )}
                      {isBottom && (
                        <Badge variant="outline" className="text-rose-500 border-rose-500/30 text-[10px] py-0 px-1.5 h-4">
                          Trailing
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
                    Show Top 10 Segments
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3.5 w-3.5 mr-1" />
                    View All {segments.length} Segments
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 5. Longitudinal Momentum & Trend Comparison (if available) */}
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
                Period Trends for Top Segments ({timeComp.period_labels.join(", ")})
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

      {/* 6. Technical Evidence & Methodology Accordion */}
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
                  Data Limitations & Disclaimers
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
