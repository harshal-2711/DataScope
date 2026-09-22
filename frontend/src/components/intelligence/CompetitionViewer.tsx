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
  SortDesc,
  Flame,
  CheckCircle2,
  FileSpreadsheet,
  Compass,
  Lightbulb,
  Upload,
  Trash2,
  RefreshCw,
  FileUp,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { removeMarketBenchmark } from "@/lib/datasetApi"
import { MarketBenchmarkModal } from "@/components/intelligence/MarketBenchmarkModal"
import type { CompetitionIntelligenceResponse } from "@/types/intelligence"

interface CompetitionViewerProps {
  data: CompetitionIntelligenceResponse
  datasetId?: string
  onBenchmarkUpdated?: (data: CompetitionIntelligenceResponse) => void
}

export function CompetitionViewer({ data, datasetId, onBenchmarkUpdated }: CompetitionViewerProps) {
  const [sortKey, setSortKey] = useState<"revenue" | "margin" | "share" | "alpha">("revenue")
  const [showAllCompetitors, setShowAllCompetitors] = useState(false)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)
  const [isBenchmarkModalOpen, setIsBenchmarkModalOpen] = useState(false)
  const [isRemovingBenchmark, setIsRemovingBenchmark] = useState(false)

  const activeDatasetId = datasetId || data.dataset_id

  const handleRemoveBenchmark = async () => {
    if (!activeDatasetId) return
    setIsRemovingBenchmark(true)
    try {
      const res = await removeMarketBenchmark(activeDatasetId)
      onBenchmarkUpdated?.(res)
    } catch (err) {
      console.error("Failed to remove benchmark", err)
    } finally {
      setIsRemovingBenchmark(false)
    }
  }

  const overview = data.overview
  const competitors = data.competitors || []
  const marketGaps = data.market_gaps || []
  const recommendations = data.strategic_recommendations || []
  const timeComp = data.time_comparison

  // Sorting
  const sortedCompetitors = useMemo(() => {
    const list = [...competitors]
    if (sortKey === "margin") {
      return list.sort((a, b) => (b.profit_margin_pct ?? -999) - (a.profit_margin_pct ?? -999))
    }
    if (sortKey === "share") {
      return list.sort((a, b) => (b.market_share_pct ?? 0) - (a.market_share_pct ?? 0))
    }
    if (sortKey === "alpha") {
      return list.sort((a, b) => a.name.localeCompare(b.name))
    }
    return list.sort((a, b) => (b.revenue ?? b.units_sold ?? 0) - (a.revenue ?? a.units_sold ?? 0))
  }, [competitors, sortKey])

  const displayedCompetitors = showAllCompetitors ? sortedCompetitors : sortedCompetitors.slice(0, 10)
  const maxRevenue = Math.max(...competitors.map((c) => Math.abs(c.revenue ?? c.units_sold ?? 0)), 1)

  // ==========================================
  // STATE 1: MARKET DATA ABSENT / UNAVAILABLE
  // ==========================================
  if (!data.is_available || data.market_data_status !== "market_data_detected" || !overview) {
    return (
      <div className="space-y-6">
        {/* Availability Status Card */}
        <Card className="border-border/60 bg-gradient-to-br from-card via-card to-muted/20 shadow-sm">
          <CardHeader className="pb-4">
            <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-amber-500/10 p-2 text-amber-500 mt-0.5">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-amber-600 dark:text-amber-400 border-amber-500/30 text-xs font-semibold uppercase">
                      Market Competition Status
                    </Badge>
                    <span className="text-muted-foreground">•</span>
                    <span className="text-xs text-muted-foreground">Competitor Data: Absent</span>
                  </div>
                  <CardTitle className="text-lg font-bold text-foreground">
                    {data.status_title || "Market competition analysis is not available yet."}
                  </CardTitle>
                  <CardDescription className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
                    {data.summary_statement}
                  </CardDescription>
                </div>
              </div>

              {/* Upload Market Benchmark Button */}
              <div className="shrink-0">
                <Button
                  onClick={() => setIsBenchmarkModalOpen(true)}
                  className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
                >
                  <FileUp className="h-4 w-4" />
                  Upload Market Benchmark Dataset
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-5 pt-0">
            {/* Required Market Data Fields */}
            <div className="rounded-lg border border-border/60 bg-muted/30 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-foreground">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                  Required Market & Competitor Data Fields
                </div>
                <span className="text-[11px] text-muted-foreground">CSV, Excel (.xlsx), or JSON</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                {data.required_market_fields && data.required_market_fields.map((field, idx) => (
                  <div key={idx} className="bg-background/70 p-3 rounded-md border border-border/40 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground font-mono">{field.field_name}</span>
                      <Badge variant={field.required ? "default" : "outline"} className="text-[10px] py-0 px-1.5 h-4">
                        {field.required ? "Required" : "Optional"}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground">{field.description}</p>
                    <p className="text-[11px] text-foreground/70 font-mono">e.g. {field.example}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Why Internal Transaction Data Cannot Determine Market Share */}
            <div className="flex items-start gap-3 rounded-lg border border-border/40 bg-muted/20 p-4 text-xs">
              <Info className="h-4 w-4 shrink-0 text-primary mt-0.5" />
              <div className="space-y-1">
                <span className="font-semibold text-foreground">
                  Market vs Internal Transaction Boundary
                </span>
                <p className="text-muted-foreground leading-relaxed">
                  A single internal sales dataset contains transactional logs (such as Customer Login Types, Device Types, Orders, and Product Sales) for your business only. It does not disclose external competitor revenues, industry market shares, or peer growth rates. DataScope strictly prevents internal customer categories from being mislabelled as market competitors.
                </p>
              </div>
            </div>

            {/* Recommended Market Benchmark Format */}
            <div className="rounded-lg border border-border/60 bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-foreground">
                  <FileSpreadsheet className="h-4 w-4 text-primary" />
                  How to Provide Market Competitor Data
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsBenchmarkModalOpen(true)}
                  className="h-7 text-xs gap-1.5"
                >
                  <Upload className="h-3.5 w-3.5" />
                  Upload Benchmark
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                To evaluate market positioning and strategic competitive gaps, upload a benchmark dataset containing competitor disclosures:
              </p>
              <div className="bg-muted/40 p-3 rounded border border-border/40 space-y-1 text-xs">
                <span className="font-semibold text-foreground">Sample Competitor Benchmark Schema</span>
                <code className="text-[11px] block font-mono text-muted-foreground bg-background/80 p-2 rounded border border-border/30">
                  competitor_name, industry, period, revenue, profit, market_share_pct, growth_rate_pct
                </code>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Modal */}
        {activeDatasetId && (
          <MarketBenchmarkModal
            isOpen={isBenchmarkModalOpen}
            onClose={() => setIsBenchmarkModalOpen(false)}
            datasetId={activeDatasetId}
            onBenchmarkApplied={(updated) => {
              onBenchmarkUpdated?.(updated)
            }}
          />
        )}
      </div>
    )
  }

  // ==========================================
  // STATE 2: MARKET COMPETITOR DATA DETECTED
  // ==========================================
  return (
    <div className="space-y-6">
      {/* External Benchmark Attached Banner */}
      {data.has_external_benchmark && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-emerald-500/20 p-2 text-emerald-600 dark:text-emerald-400">
              <FileSpreadsheet className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
                  External Market Benchmark Active
                </span>
                <Badge variant="outline" className="text-[11px] font-mono border-emerald-500/40 text-emerald-700 dark:text-emerald-300">
                  {data.benchmark_filename || "External Benchmark"}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Competitor metrics are provided by this verified external benchmark dataset. Internal sales data is preserved.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsBenchmarkModalOpen(true)}
              className="h-8 text-xs gap-1.5 border-emerald-500/30 hover:bg-emerald-500/10"
            >
              <Upload className="h-3.5 w-3.5" />
              Change Benchmark
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRemoveBenchmark}
              disabled={isRemovingBenchmark}
              className="h-8 text-xs gap-1.5 text-muted-foreground hover:text-destructive"
            >
              {isRemovingBenchmark ? (
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Trash2 className="h-3.5 w-3.5" />
              )}
              Remove
            </Button>
          </div>
        </div>
      )}

      {/* 1. Market Overview Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between rounded-xl border border-border/60 bg-gradient-to-r from-card via-card/90 to-primary/5 p-5 shadow-sm">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="default" className="text-xs font-semibold uppercase tracking-wider bg-primary/90 text-primary-foreground">
              Market Competition Intelligence
            </Badge>
            <span className="text-muted-foreground">•</span>
            <Badge variant="outline" className="text-xs font-medium">
              Market: {overview.industry_market_name}
            </Badge>
            <Badge variant="secondary" className="text-xs font-medium">
              Entity: {overview.competitor_column_label}
            </Badge>
            <Badge variant="secondary" className="text-xs font-medium">
              Measure: {overview.primary_metric_label}
            </Badge>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-foreground">
            Market Competitor Benchmarks & Positioning
          </h2>
          <p className="text-sm text-muted-foreground max-w-3xl">
            {overview.summary_statement}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge className="bg-primary/10 text-primary border-primary/20 text-xs px-3 py-1">
            <Building2 className="h-3.5 w-3.5 mr-1.5" />
            {overview.total_competitors_tracked} Competitors Tracked
          </Badge>
          {!data.has_external_benchmark && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsBenchmarkModalOpen(true)}
              className="h-8 text-xs gap-1.5 shadow-sm"
            >
              <Upload className="h-3.5 w-3.5" />
              Upload Market Benchmark
            </Button>
          )}
        </div>
      </div>

      {/* 2. Top-Level Market Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Market Leader */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-emerald-500/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                <Award className="h-4 w-4" />
                Highest Reported
              </span>
              <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/30">
                Rank #1
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1" title={overview.top_competitor_name}>
              {overview.top_competitor_name}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.top_competitor_metric_formatted}
            </div>
            <p className="text-xs text-muted-foreground">
              Highest reported {overview.primary_metric_label.toLowerCase()} in dataset
            </p>
          </CardContent>
        </Card>

        {/* Total Tracked Market Revenue */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden bg-gradient-to-br from-primary/5 to-transparent">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <BarChart3 className="h-4 w-4" />
                Reported Market Volume
              </span>
              <Badge variant="outline" className="text-[10px] text-primary border-primary/30">
                Dataset Total
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1">
              {overview.total_reported_market_revenue_formatted || `${overview.total_competitors_tracked} Peers`}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.total_reported_market_revenue_formatted || `${overview.total_competitors_tracked} Peers`}
            </div>
            <p className="text-xs text-muted-foreground">
              Combined reported turnover across tracked competitors
            </p>
          </CardContent>
        </Card>

        {/* Cohort Average */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Compass className="h-4 w-4" />
                Competitor Average
              </span>
              <Badge variant="outline" className="text-[10px]">
                Mean
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1">
              {overview.benchmark_average_revenue_formatted || "N/A"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.benchmark_average_revenue_formatted || "N/A"}
            </div>
            <p className="text-xs text-muted-foreground">
              Average turnover across {overview.total_competitors_tracked} tracked firms
            </p>
          </CardContent>
        </Card>

        {/* Market Coverage */}
        <Card className="border-border/60 shadow-sm relative overflow-hidden">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Layers className="h-4 w-4" />
                Market Coverage
              </span>
              <Badge variant="outline" className="text-[10px]">
                Scope
              </Badge>
            </div>
            <CardTitle className="text-lg font-bold truncate mt-1">
              {overview.total_competitors_tracked} Firms
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="text-2xl font-extrabold text-foreground">
              {overview.total_competitors_tracked} Firms
            </div>
            <p className="text-xs text-muted-foreground truncate">
              {overview.industry_market_name}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 3. Strategic Recommendations: How to Get Ahead */}
      {recommendations.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">
              Strategic Actions & Opportunities
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec, idx) => (
              <Card key={idx} className="border-border/60 hover:border-primary/40 transition-colors shadow-sm bg-card">
                <CardHeader className="pb-2 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Badge variant={rec.priority === "high" ? "default" : "secondary"} className="text-[10px] font-medium uppercase">
                      {rec.category.replace(/_/g, " ")}
                    </Badge>
                    <span className="text-[11px] font-mono text-muted-foreground">
                      Metric: {rec.metric}
                    </span>
                  </div>
                  <CardTitle className="text-sm font-semibold leading-snug">
                    {rec.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5 text-xs">
                  <div className="space-y-1 text-foreground/90">
                    <strong className="text-foreground block">Suggested Investigation:</strong>
                    <p className="text-muted-foreground leading-relaxed">{rec.suggested_investigation}</p>
                  </div>
                  <div className="rounded-md bg-muted/40 p-2 font-mono text-[11px] text-muted-foreground border border-border/30">
                    Evidence: {rec.evidence}
                  </div>
                  <p className="text-[10px] text-muted-foreground italic">
                    Limitation: {rec.limitation}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* 4. Measured Competitive Gaps */}
      {marketGaps.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h3 className="text-base font-semibold text-foreground">
              Measured Market Gaps
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {marketGaps.map((gap, idx) => (
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
                    {gap.factual_statement}
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

      {/* 5. Competitor Leaderboard Table & Market Share Progress */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Building2 className="h-4 w-4 text-primary" />
              Competitor Comparison & Market Share
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Comparative ranking of {overview.competitor_column_label} by {overview.primary_metric_label}
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Sort:</span>
            <Button
              variant={sortKey === "revenue" ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setSortKey("revenue")}
            >
              <SortDesc className="h-3 w-3 mr-1" />
              Revenue
            </Button>
            <Button
              variant={sortKey === "margin" ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setSortKey("margin")}
            >
              Margin
            </Button>
            <Button
              variant={sortKey === "share" ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setSortKey("share")}
            >
              Share
            </Button>
            <Button
              variant={sortKey === "alpha" ? "secondary" : "ghost"}
              size="sm"
              className="h-7 text-xs px-2"
              onClick={() => setSortKey("alpha")}
            >
              A-Z
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          <div className="space-y-2.5">
            {displayedCompetitors.map((comp) => {
              const barWidth = Math.max((Math.abs(comp.revenue ?? comp.units_sold ?? 0) / maxRevenue) * 100, 2)
              const isTop = comp.rank === 1

              return (
                <div
                  key={comp.rank + comp.name}
                  className="group rounded-lg border border-border/40 hover:border-primary/40 bg-card p-3 transition-all space-y-2"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-muted font-bold text-[10px] text-muted-foreground">
                        #{comp.rank}
                      </span>
                      <span className="font-semibold text-foreground truncate max-w-[200px] sm:max-w-[280px]" title={comp.name}>
                        {comp.name}
                      </span>
                      {isTop && (
                        <Badge className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-[10px] py-0 px-1.5 h-4">
                          Top Reported
                        </Badge>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 shrink-0 font-mono text-xs">
                      {comp.market_share_pct !== null && (
                        <span className="text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded border border-border/40 text-[11px]">
                          {comp.market_share_pct}% Share
                        </span>
                      )}
                      {comp.profit_margin_pct !== null && (
                        <span className="text-muted-foreground bg-muted/50 px-1.5 py-0.5 rounded border border-border/40 text-[11px]">
                          {comp.profit_margin_pct}% Margin
                        </span>
                      )}
                      <span className="font-bold text-foreground">
                        {comp.revenue_formatted || comp.units_sold_formatted || `${comp.records_count} records`}
                      </span>
                    </div>
                  </div>

                  {/* Relative Bar Indicator */}
                  <div className="h-2 w-full rounded-full bg-muted/60 overflow-hidden relative">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isTop ? "bg-emerald-500" : "bg-primary/80"
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>

          {competitors.length > 10 && (
            <div className="flex justify-center pt-2">
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-8"
                onClick={() => setShowAllCompetitors(!showAllCompetitors)}
              >
                {showAllCompetitors ? (
                  <>
                    <ChevronUp className="h-3.5 w-3.5 mr-1" />
                    Show Top 10 Competitors
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3.5 w-3.5 mr-1" />
                    View All {competitors.length} Competitors
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 6. Longitudinal Market Momentum (if available) */}
      {timeComp && timeComp.is_available && timeComp.segment_series.length > 0 && (
        <Card className="border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-primary" />
                <CardTitle className="text-base font-semibold">
                  Competitor Trajectory Over Time
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
                      Expanded by {timeComp.fastest_growing_rate ? `${timeComp.fastest_growing_rate > 0 ? "+" : ""}${timeComp.fastest_growing_rate}%` : "highest rate"} across periods.
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
                      Contracted by {timeComp.most_declining_rate ? `${timeComp.most_declining_rate}%` : "steepest rate"} across periods.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Segment Period Series Preview */}
            <div className="rounded-lg border border-border/40 bg-muted/20 p-4 space-y-3">
              <span className="text-xs font-semibold text-foreground">
                Observed Period Values for Top Competitors ({timeComp.period_labels.join(", ")})
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

      {/* 7. Technical Evidence & Market Scope Accordion */}
      <Card className="border-border/60 shadow-sm">
        <CardHeader
          className="cursor-pointer select-none py-3"
          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-primary" />
              <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                Market Scope, Calculation Methodology & Limitations
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
                  Market Data Limitations
                </span>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                  {data.market_limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Modal for Benchmark Upload / Change */}
      {activeDatasetId && (
        <MarketBenchmarkModal
          isOpen={isBenchmarkModalOpen}
          onClose={() => setIsBenchmarkModalOpen(false)}
          datasetId={activeDatasetId}
          onBenchmarkApplied={(updated) => {
            onBenchmarkUpdated?.(updated)
          }}
        />
      )}
    </div>
  )
}
