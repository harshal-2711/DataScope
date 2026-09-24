import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import {
  FileText,
  Download,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  ShieldAlert,
  Target,
  Sparkles,
  Calendar,
  Database,
  Building2,
  DollarSign,
  Briefcase,
  SlidersHorizontal,
  Info,
  CheckSquare,
  Square,
  AlertOctagon,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  Package,
  Percent,
  Tag,
  Users,
  MapPin,
  HelpCircle,
  ListOrdered,
  Search,
} from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useActiveDataset } from "@/context/DatasetContext"
import { fetchComprehensiveReport, downloadReportDocx, downloadReportPdf } from "@/lib/datasetApi"
import type { ComprehensiveReport } from "@/types/report"

const AVAILABLE_SECTIONS = [
  { id: "executive_summary", label: "1. Executive Summary" },
  { id: "business_performance", label: "2. Business Performance & KPIs" },
  { id: "sales_in_depth", label: "3. 6-Point Sales Analysis" },
  { id: "profit_loss", label: "4. Profit & Loss Analysis" },
  { id: "customer_segments", label: "5. Customer & Segment Analysis" },
  { id: "regional_channels", label: "6. Regional & Channel Distribution" },
  { id: "discount_pricing", label: "7. Discount & Pricing Controls" },
  { id: "inventory_analysis", label: "8. Inventory & Stock Analysis" },
  { id: "root_cause_analysis", label: "9. Root Cause Analysis" },
  { id: "risks_anomalies", label: "10. Business Risk Register" },
  { id: "market_competition", label: "11. Market Competition" },
  { id: "trends_forecasting", label: "12. Trends & Forecasting" },
  { id: "recommendations", label: "13. Strategic Recommendations" },
  { id: "priority_action_plan", label: "14. Priority Action Plan Table" },
  { id: "limitations_conclusion", label: "15. Limitations & Next Steps" },
  { id: "technical_validation", label: "16. Technical Data Validation" },
]

export default function Reports() {
  const { activeDataset } = useActiveDataset()
  const [report, setReport] = useState<ComprehensiveReport | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadingDocx, setDownloadingDocx] = useState<boolean>(false)
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false)
  const [exportSuccess, setExportSuccess] = useState<string | null>(null)
  const [activeNav, setActiveNav] = useState<string>("executive_summary")
  const [selectedSections, setSelectedSections] = useState<string[]>(
    AVAILABLE_SECTIONS.map((s) => s.id)
  )
  const [showSectionFilter, setShowSectionFilter] = useState<boolean>(false)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false)

  const loadReport = async () => {
    if (!activeDataset?.dataset_id) return
    setLoading(true)
    setError(null)
    setExportSuccess(null)
    try {
      const data = await fetchComprehensiveReport(activeDataset.dataset_id)
      setReport(data as ComprehensiveReport)
    } catch (err: any) {
      setError(err?.message || "Failed to generate comprehensive business report.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeDataset?.dataset_id) {
      loadReport()
    } else {
      setReport(null)
      setError(null)
    }
  }, [activeDataset?.dataset_id])

  const handleDownloadDocx = async () => {
    if (!activeDataset?.dataset_id) return
    setDownloadingDocx(true)
    setError(null)
    setExportSuccess(null)
    try {
      const isCustom = selectedSections.length < AVAILABLE_SECTIONS.length
      const filter = isCustom ? selectedSections : undefined
      await downloadReportDocx(activeDataset.dataset_id, filter)
      setExportSuccess("Word document (.docx) generated and downloaded successfully!")
      setTimeout(() => setExportSuccess(null), 5000)
    } catch (err: any) {
      setError(err?.message || "Could not generate Word export.")
    } finally {
      setDownloadingDocx(false)
    }
  }

  const handleDownloadPdf = async () => {
    if (!activeDataset?.dataset_id) return
    setDownloadingPdf(true)
    setError(null)
    setExportSuccess(null)
    try {
      const isCustom = selectedSections.length < AVAILABLE_SECTIONS.length
      const filter = isCustom ? selectedSections : undefined
      await downloadReportPdf(activeDataset.dataset_id, filter)
      setExportSuccess("PDF report document (.pdf) generated and downloaded successfully!")
      setTimeout(() => setExportSuccess(null), 5000)
    } catch (err: any) {
      setError(err?.message || "Could not generate PDF export.")
    } finally {
      setDownloadingPdf(false)
    }
  }

  const toggleSection = (sectionId: string) => {
    setSelectedSections((prev) =>
      prev.includes(sectionId) ? prev.filter((id) => id !== sectionId) : [...prev, sectionId]
    )
  }

  const toggleSelectAll = () => {
    if (selectedSections.length === AVAILABLE_SECTIONS.length) {
      setSelectedSections(["executive_summary"])
    } else {
      setSelectedSections(AVAILABLE_SECTIONS.map((s) => s.id))
    }
  }

  const scrollToSection = (id: string) => {
    setActiveNav(id)
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  const isSectionVisible = (id: string) => selectedSections.includes(id)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Business Intelligence & Decision Report"
        description="Boardroom-ready executive intelligence synthesizing commercial performance, profitability, customer dynamics, risks, and prioritized operational roadmap."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={FileText}
            title="No dataset active"
            description="Upload or select a dataset to synthesize a complete boardroom business report."
          />
          <div className="flex justify-center">
            <Button asChild size="sm">
              <Link to="/dataset">Upload a dataset</Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between rounded-xl border border-border bg-card p-4 shadow-sm">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold text-foreground text-sm flex items-center gap-1.5">
                  <FileSpreadsheet className="h-4 w-4 text-primary" />
                  {report?.metadata.report_title || `Business Report: ${activeDataset.filename}`}
                </span>
                <Badge variant="secondary" className="text-[11px] font-normal">
                  {report?.metadata.domain_name || "Detecting Domain"}
                </Badge>
                {report?.metadata.currency_symbol && (
                  <Badge variant="outline" className="text-[11px] font-mono">
                    Currency: {report.metadata.currency_symbol}
                  </Badge>
                )}
                {report?.executive_summary.overall_business_health && (
                  <Badge
                    variant="secondary"
                    className={`text-[11px] ${
                      report.executive_summary.overall_business_health === "Healthy"
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold"
                        : "bg-amber-500/10 text-amber-600 dark:text-amber-400 font-semibold"
                    }`}
                  >
                    Health: {report.executive_summary.overall_business_health}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground flex flex-wrap items-center gap-x-3 gap-y-1">
                <span>Dataset: <b className="text-foreground">{activeDataset.filename}</b></span>
                {report?.metadata.reporting_period && (
                  <>
                    <span>·</span>
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {report.metadata.reporting_period}
                    </span>
                  </>
                )}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-xs"
                onClick={() => setShowSectionFilter(!showSectionFilter)}
              >
                <SlidersHorizontal className="h-3.5 w-3.5" />
                Sections ({selectedSections.length}/{AVAILABLE_SECTIONS.length})
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-xs"
                onClick={loadReport}
                disabled={loading}
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                {loading ? "Generating..." : "Regenerate"}
              </Button>

              <Button
                variant="default"
                size="sm"
                className="gap-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white shadow-sm"
                onClick={handleDownloadDocx}
                disabled={loading || downloadingDocx || downloadingPdf}
              >
                <Download className={`h-3.5 w-3.5 ${downloadingDocx ? "animate-bounce" : ""}`} />
                {downloadingDocx ? "Exporting DOCX..." : "Download DOCX"}
              </Button>

              <Button
                variant="default"
                size="sm"
                className="gap-1.5 text-xs bg-slate-900 hover:bg-slate-800 text-white shadow-sm dark:bg-slate-100 dark:text-slate-900"
                onClick={handleDownloadPdf}
                disabled={loading || downloadingDocx || downloadingPdf}
              >
                <FileText className={`h-3.5 w-3.5 ${downloadingPdf ? "animate-bounce" : ""}`} />
                {downloadingPdf ? "Exporting PDF..." : "Download PDF"}
              </Button>
            </div>
          </div>

          {/* Section Filter Drawer */}
          {showSectionFilter && (
            <Card className="border-primary/20 bg-primary/5">
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-primary" />
                    <h4 className="text-xs font-semibold text-foreground">
                      Select Report Sections to Display & Export
                    </h4>
                  </div>
                  <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={toggleSelectAll}>
                    {selectedSections.length === AVAILABLE_SECTIONS.length ? "Deselect All" : "Select All"}
                  </Button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 pt-1">
                  {AVAILABLE_SECTIONS.map((sec) => {
                    const isChecked = selectedSections.includes(sec.id)
                    return (
                      <button
                        key={sec.id}
                        type="button"
                        onClick={() => toggleSection(sec.id)}
                        className={`flex items-center gap-2 p-2 rounded-md border text-left text-xs transition-colors ${
                          isChecked
                            ? "border-primary/40 bg-card text-foreground font-medium shadow-xs"
                            : "border-border/60 bg-muted/30 text-muted-foreground hover:bg-muted/60"
                        }`}
                      >
                        {isChecked ? (
                          <CheckSquare className="h-3.5 w-3.5 text-primary shrink-0" />
                        ) : (
                          <Square className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        )}
                        <span className="truncate">{sec.label}</span>
                      </button>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Feedback Messages */}
          {exportSuccess && (
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/30 p-3 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>{exportSuccess}</span>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive flex items-center gap-2">
              <AlertOctagon className="h-4 w-4 text-destructive shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading && !report && (
            <div className="space-y-4 py-8">
              <div className="flex flex-col items-center justify-center space-y-3 text-center">
                <RefreshCw className="h-8 w-8 animate-spin text-primary" />
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold">Synthesizing Business Intelligence Report...</h3>
                  <p className="text-xs text-muted-foreground">
                    Calculating revenue trends, profit & loss, customer segments, discount dynamics, and prioritized recommendations.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Main Report Body Layout */}
          {report && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
              {/* Sticky Navigation */}
              <div className="hidden lg:block lg:sticky lg:top-4 space-y-2">
                <Card className="shadow-xs">
                  <CardHeader className="py-3 px-4 border-b">
                    <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      Report Navigation
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-2 space-y-0.5">
                    {AVAILABLE_SECTIONS.map((sec) => {
                      const isSelected = selectedSections.includes(sec.id)
                      if (!isSelected) return null
                      return (
                        <button
                          key={sec.id}
                          onClick={() => scrollToSection(sec.id)}
                          className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs transition-colors flex items-center justify-between ${
                            activeNav === sec.id
                              ? "bg-primary text-primary-foreground font-semibold"
                              : "text-muted-foreground hover:bg-muted hover:text-foreground"
                          }`}
                        >
                          <span className="truncate">{sec.label}</span>
                          <ChevronRight className="h-3 w-3 shrink-0 opacity-60" />
                        </button>
                      )
                    })}
                  </CardContent>
                </Card>

                <Card className="bg-muted/20 border-dashed">
                  <CardContent className="p-3.5 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-muted-foreground">Condition:</span>
                      <Badge
                        variant="secondary"
                        className={
                          report.executive_summary.overall_business_condition === "Strong"
                            ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-semibold text-[11px]"
                            : report.executive_summary.overall_business_condition === "Healthy"
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 font-semibold text-[11px]"
                            : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 font-semibold text-[11px]"
                        }
                      >
                        {report.executive_summary.overall_business_condition || report.executive_summary.overall_business_health}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>Generated:</span>
                      <span className="font-mono text-[10px] text-foreground truncate max-w-[130px]">
                        {report.metadata.generated_at}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Main Content Stream */}
              <div className="lg:col-span-3 space-y-8">
                {/* 1. EXECUTIVE BUSINESS SUMMARY */}
                {isSectionVisible("executive_summary") && (
                  <section id="executive_summary" className="space-y-4">
                    <Card className="border-border shadow-xs overflow-hidden">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Sparkles className="h-4 w-4" />
                          Section 1
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Executive Business Summary
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Core commercial KPIs, written executive assessment, verified findings, and priority interventions.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-5">
                        {/* Executive KPI Matrix */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Total Revenue</span>
                            <div className="text-base font-bold text-foreground font-mono">
                              {report.executive_summary.total_sales_revenue || "N/A"}
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Gross sales volume</span>
                          </div>
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Total Net Profit</span>
                            <div className="text-base font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                              {report.executive_summary.total_profit_loss || "Unavailable"}
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Bottom-line earnings</span>
                          </div>
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Profit Margin</span>
                            <div className="text-base font-bold text-foreground font-mono">
                              {report.executive_summary.profit_margin_pct || "Unavailable"}
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Return on sales</span>
                          </div>
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Total Orders</span>
                            <div className="text-base font-bold text-foreground font-mono">
                              {report.executive_summary.total_orders_count || "N/A"}
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Recorded transactions</span>
                          </div>
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Avg Order Value (AOV)</span>
                            <div className="text-base font-bold text-foreground font-mono">
                              {report.executive_summary.average_order_value || "N/A"}
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Spend per transaction</span>
                          </div>
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Total Units Sold</span>
                            <div className="text-base font-bold text-foreground font-mono">
                              {report.executive_summary.total_units_sold || "N/A"}
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Physical item count</span>
                          </div>
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Average Discount</span>
                            <div className="text-base font-bold text-amber-600 dark:text-amber-400 font-mono">
                              {report.executive_summary.average_discount_pct || "N/A"}
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Mean promotional cut</span>
                          </div>
                          <div className="p-3 rounded-lg border bg-card space-y-1">
                            <span className="text-[11px] text-muted-foreground">Business Condition</span>
                            <div className="text-base font-bold text-foreground">
                              <Badge
                                variant="secondary"
                                className={
                                  report.executive_summary.overall_business_condition === "Strong"
                                    ? "bg-emerald-500/10 text-emerald-600 font-semibold"
                                    : "bg-blue-500/10 text-blue-600 font-semibold"
                                }
                              >
                                {report.executive_summary.overall_business_condition || "Healthy"}
                              </Badge>
                            </div>
                            <span className="text-[10px] text-muted-foreground block">Operational rating</span>
                          </div>
                        </div>

                        {/* Written Narrative Callout */}
                        <div className="rounded-lg bg-blue-500/5 p-4 border border-blue-500/20 text-xs leading-relaxed text-foreground space-y-1">
                          <span className="font-semibold text-blue-700 dark:text-blue-400 block text-[11px] uppercase tracking-wider">
                            Executive Narrative Briefing
                          </span>
                          <p className="text-xs text-foreground leading-relaxed">
                            {report.executive_summary.overall_performance_summary}
                          </p>
                        </div>

                        {/* Positives vs Negatives */}
                        {(report.executive_summary.major_positive_findings || report.executive_summary.major_negative_findings) && (
                          <div className="grid sm:grid-cols-2 gap-3 pt-1">
                            {report.executive_summary.major_positive_findings && (
                              <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5 space-y-1.5">
                                <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                                  <CheckCircle2 className="h-4 w-4" />
                                  Major Positive Drivers
                                </span>
                                <ul className="space-y-1 text-xs text-muted-foreground">
                                  {report.executive_summary.major_positive_findings.map((pos, idx) => (
                                    <li key={idx} className="flex items-start gap-1.5 leading-snug">
                                      <span className="text-emerald-600 font-bold">•</span>
                                      <span>{pos}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {report.executive_summary.major_negative_findings && (
                              <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-500/5 space-y-1.5">
                                <span className="text-xs font-semibold text-rose-700 dark:text-rose-400 flex items-center gap-1.5">
                                  <AlertTriangle className="h-4 w-4" />
                                  Areas Requiring Attention
                                </span>
                                <ul className="space-y-1 text-xs text-muted-foreground">
                                  {report.executive_summary.major_negative_findings.map((neg, idx) => (
                                    <li key={idx} className="flex items-start gap-1.5 leading-snug">
                                      <span className="text-rose-600 font-bold">•</span>
                                      <span>{neg}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Top 3 Management Actions */}
                        {report.executive_summary.top_3_recommended_actions && (
                          <div className="p-3.5 rounded-lg border border-blue-500/30 bg-blue-500/5 space-y-2">
                            <span className="text-xs font-semibold text-blue-700 dark:text-blue-400 flex items-center gap-1.5">
                              <Target className="h-4 w-4" />
                              Top Priority Management Actions
                            </span>
                            <div className="space-y-1.5">
                              {report.executive_summary.top_3_recommended_actions.map((act, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-xs text-foreground bg-card/60 p-2 rounded border border-border/50">
                                  <span className="font-bold text-primary shrink-0">{idx + 1}.</span>
                                  <span>{act}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 2. BUSINESS PERFORMANCE & OPERATIONAL KPIS */}
                {isSectionVisible("business_performance") && (
                  <section id="business_performance" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Briefcase className="h-4 w-4" />
                          Section 2
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Business Performance & Operational KPIs
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Operational metric table, interpretation benchmarks, and commercial performance rankings.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {!report.business_performance.is_available ? (
                          <div className="p-4 rounded-lg bg-muted/30 border text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4 text-muted-foreground shrink-0" />
                            <span>
                              {report.business_performance.unavailable_reason || "Category-level performance analysis is unavailable."}
                            </span>
                          </div>
                        ) : (
                          <>
                            <p className="text-xs text-foreground bg-muted/30 p-3 rounded-lg border border-border/60">
                              {report.business_performance.summary_text}
                            </p>

                            {/* Operational Metric Highlights Table */}
                            {report.business_performance.metric_highlights.length > 0 && (
                              <div className="space-y-2">
                                <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                                  Key Operational Performance Indicators
                                </h4>
                                <div className="overflow-x-auto rounded-lg border">
                                  <table className="w-full text-left text-xs">
                                    <thead className="bg-muted/60 text-muted-foreground font-medium border-b">
                                      <tr>
                                        <th className="py-2.5 px-3">Metric Name</th>
                                        <th className="py-2.5 px-3">Observed Value</th>
                                        <th className="py-2.5 px-3">Business Meaning</th>
                                        <th className="py-2.5 px-3">Status</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                      {report.business_performance.metric_highlights.map((m, idx) => (
                                        <tr key={idx} className="hover:bg-muted/30">
                                          <td className="py-2 px-3 font-semibold text-foreground">{m.name}</td>
                                          <td className="py-2 px-3 font-mono font-bold">{m.formatted_value}</td>
                                          <td className="py-2 px-3 text-muted-foreground">{m.business_meaning}</td>
                                          <td className="py-2 px-3">
                                            {m.requires_attention ? (
                                              <Badge variant="destructive" className="text-[10px]">
                                                Attention
                                              </Badge>
                                            ) : (
                                              <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-300">
                                                Normal
                                              </Badge>
                                            )}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}

                            {/* Top vs Under Performers */}
                            <div className="grid sm:grid-cols-2 gap-4 pt-1">
                              {report.business_performance.top_performers.length > 0 && (
                                <div className="space-y-2">
                                  <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                                    <ArrowUpRight className="h-4 w-4 text-emerald-600" />
                                    Top Performing Commercial Entities
                                  </h4>
                                  <div className="space-y-1.5">
                                    {report.business_performance.top_performers.map((tp, i) => (
                                      <div
                                        key={i}
                                        className="flex items-center justify-between p-2.5 rounded-lg border bg-card text-xs"
                                      >
                                        <div>
                                          <span className="font-semibold text-foreground">{tp.name}</span>
                                          <p className="text-[10px] text-muted-foreground">{tp.entity_type} · {tp.note}</p>
                                        </div>
                                        <span className="font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                                          {tp.formatted_value}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {report.business_performance.underperformers.length > 0 && (
                                <div className="space-y-2">
                                  <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                                    <ArrowDownRight className="h-4 w-4 text-amber-600" />
                                    Underperforming Commercial Segments
                                  </h4>
                                  <div className="space-y-1.5">
                                    {report.business_performance.underperformers.map((up, i) => (
                                      <div
                                        key={i}
                                        className="flex items-center justify-between p-2.5 rounded-lg border bg-card text-xs"
                                      >
                                        <div>
                                          <span className="font-semibold text-foreground">{up.name}</span>
                                          <p className="text-[10px] text-muted-foreground">{up.entity_type} · {up.note}</p>
                                        </div>
                                        <span className="font-bold text-amber-600 dark:text-amber-400 font-mono">
                                          {up.formatted_value}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 3. 6-POINT REVENUE & SALES ANALYSIS */}
                {isSectionVisible("sales_in_depth") && report.business_performance.six_point_findings && report.business_performance.six_point_findings.length > 0 && (
                  <section id="sales_in_depth" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <DollarSign className="h-4 w-4" />
                          Section 3
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Revenue & Sales In-Depth Analysis (6-Question Framework)
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Rigorous breakdown answering: What happened, business meaning, why it matters, action, evidence, and limitations.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {report.business_performance.six_point_findings.map((finding, idx) => (
                          <div key={idx} className="p-4 rounded-lg border bg-card space-y-3">
                            <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
                              <span className="h-2 w-2 rounded-full bg-primary" />
                              {finding.observation_title}
                            </h4>
                            <div className="grid sm:grid-cols-2 gap-3 text-xs">
                              <div className="space-y-1 p-2.5 rounded bg-muted/30 border border-border/50">
                                <span className="font-semibold text-foreground block">1. What was observed?</span>
                                <p className="text-muted-foreground">{finding.what_happened}</p>
                              </div>
                              <div className="space-y-1 p-2.5 rounded bg-muted/30 border border-border/50">
                                <span className="font-semibold text-foreground block">2. Business meaning</span>
                                <p className="text-muted-foreground">{finding.business_meaning}</p>
                              </div>
                              <div className="space-y-1 p-2.5 rounded bg-muted/30 border border-border/50">
                                <span className="font-semibold text-foreground block">3. Why it matters</span>
                                <p className="text-muted-foreground">{finding.why_it_matters}</p>
                              </div>
                              <div className="space-y-1 p-2.5 rounded bg-blue-500/10 border border-blue-500/20">
                                <span className="font-semibold text-blue-700 dark:text-blue-400 block">4. Recommended action</span>
                                <p className="text-foreground">{finding.recommended_action}</p>
                              </div>
                            </div>
                            <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground pt-1 border-t">
                              <span><b>Data Evidence:</b> {finding.evidence}</span>
                              <span className="italic"><b>Limitation:</b> {finding.limitations}</span>
                            </div>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 4. PROFIT & LOSS ANALYSIS */}
                {isSectionVisible("profit_loss") && (
                  <section id="profit_loss" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <DollarSign className="h-4 w-4" />
                          Section 4
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Profit & Loss Analysis
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Gross margins, bottom-line earnings, loss-making categories, and discount concessions.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {!report.profit_loss.is_available ? (
                          <div className="p-4 rounded-lg bg-muted/30 border text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4 text-muted-foreground shrink-0" />
                            <span>
                              {report.profit_loss.unavailable_reason || "Reliable profit and loss analysis is unavailable because sufficient financial fields were not found in the dataset."}
                            </span>
                          </div>
                        ) : (
                          <>
                            <div className="flex flex-wrap items-center gap-4 text-xs font-mono p-3 bg-muted/30 rounded-lg border">
                              <span>Revenue: <b>{report.profit_loss.revenue_trend_summary}</b></span>
                              <span>·</span>
                              <span>Net Profit: <b>{report.profit_loss.profit_trend_summary}</b></span>
                              <span>·</span>
                              <span>Margin: <b>{report.profit_loss.profit_margin_summary}</b></span>
                            </div>

                            {/* Loss-making segments table */}
                            {report.profit_loss.loss_making_segments.length > 0 && (
                              <div className="space-y-2">
                                <h4 className="text-xs font-semibold text-destructive flex items-center gap-1.5">
                                  <AlertTriangle className="h-4 w-4" />
                                  Loss-Making Segments (Direct Margin Leakage)
                                </h4>
                                <div className="overflow-x-auto rounded-lg border border-destructive/30">
                                  <table className="w-full text-left text-xs">
                                    <thead className="bg-destructive/10 text-destructive font-medium border-b border-destructive/20">
                                      <tr>
                                        <th className="py-2 px-3">Segment Name</th>
                                        <th className="py-2 px-3">Revenue</th>
                                        <th className="py-2 px-3">Loss Amount</th>
                                        <th className="py-2 px-3">Margin %</th>
                                        <th className="py-2 px-3">Calculation Basis</th>
                                        <th className="py-2 px-3">Actionable Response</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                      {report.profit_loss.loss_making_segments.map((seg, idx) => (
                                        <tr key={idx} className="hover:bg-destructive/5">
                                          <td className="py-2 px-3 font-semibold text-foreground">{seg.name}</td>
                                          <td className="py-2 px-3 font-mono">{seg.revenue_formatted}</td>
                                          <td className="py-2 px-3 font-mono font-bold text-destructive">{seg.profit_loss_formatted}</td>
                                          <td className="py-2 px-3 font-mono text-destructive">{seg.profit_margin_pct}%</td>
                                          <td className="py-2 px-3 text-[11px] text-muted-foreground">{seg.calculation_basis || seg.explanation}</td>
                                          <td className="py-2 px-3 text-foreground font-medium">{seg.actionable_response || "Conduct pricing review."}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}

                            {/* High sales low profit segments */}
                            {report.profit_loss.high_sales_low_profit_segments.length > 0 && (
                              <div className="space-y-2">
                                <h4 className="text-xs font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                                  <Tag className="h-4 w-4" />
                                  High-Volume Low-Margin Products (&lt;10% Margin)
                                </h4>
                                <div className="overflow-x-auto rounded-lg border border-amber-500/30">
                                  <table className="w-full text-left text-xs">
                                    <thead className="bg-amber-500/10 text-amber-800 dark:text-amber-300 font-medium border-b border-amber-500/20">
                                      <tr>
                                        <th className="py-2 px-3">Segment Name</th>
                                        <th className="py-2 px-3">Revenue</th>
                                        <th className="py-2 px-3">Profit</th>
                                        <th className="py-2 px-3">Margin %</th>
                                        <th className="py-2 px-3">Actionable Response</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                      {report.profit_loss.high_sales_low_profit_segments.map((seg, idx) => (
                                        <tr key={idx} className="hover:bg-amber-500/5">
                                          <td className="py-2 px-3 font-semibold text-foreground">{seg.name}</td>
                                          <td className="py-2 px-3 font-mono">{seg.revenue_formatted}</td>
                                          <td className="py-2 px-3 font-mono font-bold text-amber-600">{seg.profit_loss_formatted}</td>
                                          <td className="py-2 px-3 font-mono">{seg.profit_margin_pct}%</td>
                                          <td className="py-2 px-3 text-foreground font-medium">{seg.actionable_response || "Audit supplier costs."}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            )}
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 5. CUSTOMER & SEGMENT ANALYSIS */}
                {isSectionVisible("customer_segments") && (
                  <section id="customer_segments" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Users className="h-4 w-4" />
                          Section 5
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Customer & Segment Analysis
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Customer classifications, revenue contributions, average order values, and retention strategies.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {!report.customer_segment_analysis || !report.customer_segment_analysis.is_available ? (
                          <div className="p-4 rounded-lg bg-muted/30 border text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4 text-muted-foreground shrink-0" />
                            <span>
                              {report.customer_segment_analysis?.unavailable_reason || "Customer segment analysis is unavailable because customer classification fields were not detected in the dataset."}
                            </span>
                          </div>
                        ) : (
                          <>
                            <p className="text-xs text-foreground bg-muted/30 p-3 rounded-lg border border-border/60">
                              {report.customer_segment_analysis.strategic_summary} {report.customer_segment_analysis.concentration_observation}
                            </p>

                            <div className="overflow-x-auto rounded-lg border">
                              <table className="w-full text-left text-xs">
                                <thead className="bg-muted/60 text-muted-foreground font-medium border-b">
                                  <tr>
                                    <th className="py-2 px-3">Segment Name</th>
                                    <th className="py-2 px-3">Order Volume</th>
                                    <th className="py-2 px-3">Revenue</th>
                                    <th className="py-2 px-3">Share %</th>
                                    <th className="py-2 px-3">AOV</th>
                                    <th className="py-2 px-3">Marketing / Retention Strategy</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y">
                                  {report.customer_segment_analysis.segments.map((s, idx) => (
                                    <tr key={idx} className="hover:bg-muted/30">
                                      <td className="py-2 px-3 font-semibold text-foreground">{s.segment_name}</td>
                                      <td className="py-2 px-3 text-muted-foreground">{s.customer_count_formatted}</td>
                                      <td className="py-2 px-3 font-mono font-bold">{s.revenue_formatted}</td>
                                      <td className="py-2 px-3 font-mono">{s.revenue_share_pct}%</td>
                                      <td className="py-2 px-3 font-mono">{s.aov_formatted}</td>
                                      <td className="py-2 px-3 text-foreground">{s.marketing_strategy}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 6. REGIONAL & CHANNEL DISTRIBUTION */}
                {isSectionVisible("regional_channels") && (
                  <section id="regional_channels" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <MapPin className="h-4 w-4" />
                          Section 6
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Regional & Distribution Channels
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Geographical and channel performance with operational volume observations.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {!report.regional_channel_analysis || !report.regional_channel_analysis.is_available ? (
                          <div className="p-4 rounded-lg bg-muted/30 border text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4 text-muted-foreground shrink-0" />
                            <span>
                              {report.regional_channel_analysis?.unavailable_reason || "Regional/channel analysis is unavailable because geographical or distribution channel dimensions were not detected."}
                            </span>
                          </div>
                        ) : (
                          <>
                            <p className="text-xs text-foreground bg-muted/30 p-3 rounded-lg border border-border/60">
                              {report.regional_channel_analysis.operational_takeaway}
                            </p>

                            <div className="overflow-x-auto rounded-lg border">
                              <table className="w-full text-left text-xs">
                                <thead className="bg-muted/60 text-muted-foreground font-medium border-b">
                                  <tr>
                                    <th className="py-2 px-3">{report.regional_channel_analysis.dimension_name || "Distribution Hub"}</th>
                                    <th className="py-2 px-3">Revenue</th>
                                    <th className="py-2 px-3">Share %</th>
                                    <th className="py-2 px-3">Order Volume</th>
                                    <th className="py-2 px-3">Operational Observation</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y">
                                  {report.regional_channel_analysis.items.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-muted/30">
                                      <td className="py-2 px-3 font-semibold text-foreground">{item.name}</td>
                                      <td className="py-2 px-3 font-mono font-bold">{item.revenue_formatted}</td>
                                      <td className="py-2 px-3 font-mono">{item.revenue_share_pct}%</td>
                                      <td className="py-2 px-3 font-mono text-muted-foreground">{item.order_volume}</td>
                                      <td className="py-2 px-3 text-foreground">{item.operational_observation}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 7. DISCOUNT & PRICING CONTROLS */}
                {isSectionVisible("discount_pricing") && (
                  <section id="discount_pricing" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Percent className="h-4 w-4" />
                          Section 7
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Discount & Pricing Dynamics
                        </CardTitle>
                        <CardDescription className="text-xs">
                          High-discount order volumes, margin erosion estimates, suggested governance controls, and validation requirements.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {!report.discount_pricing || !report.discount_pricing.is_available ? (
                          <div className="p-4 rounded-lg bg-muted/30 border text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4 text-muted-foreground shrink-0" />
                            <span>
                              {report.discount_pricing?.unavailable_reason || "Discount and pricing analysis is unavailable."}
                            </span>
                          </div>
                        ) : (
                          <>
                            {report.discount_pricing.margin_erosion_estimate && (
                              <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-xs font-semibold text-amber-800 dark:text-amber-300">
                                {report.discount_pricing.margin_erosion_estimate}
                              </div>
                            )}

                            <div className="space-y-2">
                              <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                                Promotional Tier Observations
                              </h4>
                              <div className="grid gap-1.5">
                                {report.discount_pricing.discount_tier_observations.map((obs, idx) => (
                                  <div key={idx} className="p-2.5 rounded bg-muted/30 border border-border/50 text-xs text-foreground">
                                    {obs}
                                  </div>
                                ))}
                              </div>
                            </div>

                            {report.discount_pricing.suggested_controls.length > 0 && (
                              <div className="p-3.5 rounded-lg border border-blue-500/30 bg-blue-500/5 space-y-2">
                                <span className="text-xs font-semibold text-blue-700 dark:text-blue-400">
                                  Suggested Promotional Controls:
                                </span>
                                <ul className="space-y-1 text-xs text-muted-foreground">
                                  {report.discount_pricing.suggested_controls.map((ctrl, idx) => (
                                    <li key={idx} className="flex items-start gap-1.5">
                                      <span className="text-blue-600 font-bold">•</span>
                                      <span>{ctrl}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 8. INVENTORY / STOCK ANALYSIS */}
                {isSectionVisible("inventory_analysis") && (
                  <section id="inventory_analysis" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Package className="h-4 w-4" />
                          Section 8
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Inventory & Stock Analysis
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Stock level alerts, replenishment priorities, and warehouse holding observations.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {!report.inventory_analysis || !report.inventory_analysis.is_available ? (
                          <div className="p-4 rounded-lg bg-muted/30 border text-xs text-muted-foreground flex items-center gap-2">
                            <Info className="h-4 w-4 text-muted-foreground shrink-0" />
                            <span>
                              {report.inventory_analysis?.unavailable_reason || "Inventory analysis cannot be performed because stock-level and inventory movement data is not available."}
                            </span>
                          </div>
                        ) : (
                          <>
                            <p className="text-xs text-foreground bg-muted/30 p-3 rounded-lg border border-border/60">
                              {report.inventory_analysis.inventory_turnover_observation}
                            </p>
                            <div className="grid gap-2">
                              {report.inventory_analysis.reorder_alerts.map((alert, idx) => (
                                <div key={idx} className="p-2.5 rounded border border-amber-500/30 bg-amber-500/5 text-xs text-foreground">
                                  {alert}
                                </div>
                              ))}
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 9. ROOT CAUSE ANALYSIS */}
                {isSectionVisible("root_cause_analysis") && report.root_cause_analysis && (
                  <section id="root_cause_analysis" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Search className="h-4 w-4" />
                          Section 9
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Root Cause Analysis
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Structured breakdown distinguishing confirmed observations from contributing hypotheses and validation requirements.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-xs text-muted-foreground">
                          {report.root_cause_analysis.summary_statement}
                        </p>

                        <div className="space-y-3">
                          {report.root_cause_analysis.root_causes.map((rc, idx) => (
                            <div key={idx} className="p-4 rounded-lg border bg-card space-y-2">
                              <h4 className="text-xs font-bold text-foreground flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-amber-500" />
                                {rc.issue_title}
                              </h4>
                              <div className="grid sm:grid-cols-2 gap-2 text-xs">
                                <div className="p-2 rounded bg-muted/30 border border-border/50">
                                  <span className="font-semibold text-foreground block">Confirmed Observation:</span>
                                  <span className="text-muted-foreground">{rc.confirmed_observation}</span>
                                </div>
                                <div className="p-2 rounded bg-muted/30 border border-border/50">
                                  <span className="font-semibold text-foreground block">Contributing Factors:</span>
                                  <span className="text-muted-foreground">{rc.possible_contributing_factors.join(", ")}</span>
                                </div>
                                <div className="p-2 rounded bg-muted/30 border border-border/50">
                                  <span className="font-semibold text-foreground block">Data Needed for Validation:</span>
                                  <span className="text-muted-foreground">{rc.data_needed_for_validation.join(", ")}</span>
                                </div>
                                <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
                                  <span className="font-semibold text-blue-700 dark:text-blue-400 block">Recommended Action:</span>
                                  <span className="text-foreground">{rc.recommended_investigation}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 10. BUSINESS RISK REGISTER */}
                {isSectionVisible("risks_anomalies") && (
                  <section id="risks_anomalies" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <ShieldAlert className="h-4 w-4" />
                          Section 10
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Business Risk & Anomaly Register
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Verified operational risks evaluated across financial, inventory, customer, and data reliability dimensions.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="grid gap-3">
                          {report.risks_anomalies.verified_risks.map((risk, idx) => (
                            <div
                              key={idx}
                              className={`p-4 rounded-lg border space-y-2 ${
                                risk.severity === "critical" || risk.severity === "high"
                                  ? "border-rose-500/40 bg-rose-500/5"
                                  : "border-amber-500/30 bg-amber-500/5"
                              }`}
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <h4 className="text-xs font-bold text-foreground flex items-center gap-2">
                                  <Badge
                                    variant="secondary"
                                    className={
                                      risk.severity === "critical" || risk.severity === "high"
                                        ? "bg-rose-500 text-white text-[10px]"
                                        : "bg-amber-500 text-white text-[10px]"
                                    }
                                  >
                                    {risk.severity.toUpperCase()}
                                  </Badge>
                                  {risk.title}
                                </h4>
                                <span className="text-[11px] text-muted-foreground font-mono">{risk.category}</span>
                              </div>

                              <p className="text-xs text-foreground leading-relaxed">{risk.business_impact}</p>
                              
                              <div className="p-2 rounded bg-card/60 border border-border/50 text-xs flex items-start gap-2">
                                <Target className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                                <span><b>Recommended Action:</b> {risk.recommended_action}</span>
                              </div>

                              <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-muted-foreground pt-1 border-t">
                                <span><b>Evidence:</b> {risk.evidence}</span>
                                <span><b>Confidence:</b> {risk.confidence_level || "High (Verified Evidence)"}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 11. MARKET COMPETITION ANALYSIS */}
                {isSectionVisible("market_competition") && (
                  <section id="market_competition" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Building2 className="h-4 w-4" />
                          Section 11
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Market Competition Analysis
                        </CardTitle>
                        <CardDescription className="text-xs">
                          External industry benchmarking vs internal operational category comparisons.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {!report.market_competition.is_available ? (
                          <div className="p-4 rounded-lg bg-muted/30 border space-y-3">
                            <div className="flex items-start gap-2 text-xs text-muted-foreground">
                              <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                              <span className="leading-relaxed">
                                {report.market_competition.summary_statement}
                              </span>
                            </div>

                            <div className="p-3 rounded bg-card border text-xs space-y-2">
                              <span className="font-semibold text-foreground text-[11px] uppercase tracking-wider block">
                                Required External Market Data Fields for Industry Benchmarking:
                              </span>
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                                {report.market_competition.required_market_fields.map((f, i) => (
                                  <div key={i} className="p-2 rounded bg-muted/40 border text-[11px] space-y-0.5">
                                    <span className="font-semibold text-foreground block">{f.field}</span>
                                    <span className="text-muted-foreground text-[10px] block">{f.type} · {f.purpose}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        ) : (
                          <p className="text-xs text-foreground">Market competition data active.</p>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 12. TRENDS & FORECASTING */}
                {isSectionVisible("trends_forecasting") && (
                  <section id="trends_forecasting" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <TrendingUp className="h-4 w-4" />
                          Section 12
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Trends & Growth Projections
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Historical momentum and forward projections with statistical confidence intervals.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {report.trends_intelligence.is_available && (
                          <p className="text-xs text-foreground bg-muted/30 p-3 rounded-lg border border-border/60">
                            {report.trends_intelligence.plain_language_interpretation}
                          </p>
                        )}

                        {report.forecasting.is_available && report.forecasting.forecast_points.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                              Forecast Projections ({report.forecasting.forecasted_metric})
                            </h4>
                            <div className="overflow-x-auto rounded-lg border">
                              <table className="w-full text-left text-xs">
                                <thead className="bg-muted/60 text-muted-foreground font-medium border-b">
                                  <tr>
                                    <th className="py-2 px-3">Horizon Period</th>
                                    <th className="py-2 px-3">Projected Value</th>
                                    <th className="py-2 px-3">80% Confidence Band</th>
                                    <th className="py-2 px-3">95% Confidence Band</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y">
                                  {report.forecasting.forecast_points.map((pt, idx) => (
                                    <tr key={idx} className="hover:bg-muted/30">
                                      <td className="py-2 px-3 font-semibold text-foreground">{pt.period}</td>
                                      <td className="py-2 px-3 font-mono font-bold text-blue-600">{pt.forecast_formatted}</td>
                                      <td className="py-2 px-3 font-mono text-muted-foreground">{pt.lower_bound_80_formatted} to {pt.upper_bound_80_formatted}</td>
                                      <td className="py-2 px-3 font-mono text-muted-foreground">{pt.lower_bound_95_formatted} to {pt.upper_bound_95_formatted}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            <p className="text-[11px] text-muted-foreground italic">
                              {report.forecasting.disclaimer}
                            </p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 13. STRATEGIC RECOMMENDATIONS */}
                {isSectionVisible("recommendations") && (
                  <section id="recommendations" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <Target className="h-4 w-4" />
                          Section 13
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Evidence-Based Strategic Recommendations
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Operational guidance structured with problem evidence, 5-step action plan, owners, KPIs, and review timeframes.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-4">
                          {report.recommendations.recommendations_list.map((rec, idx) => (
                            <div key={idx} className="p-4 rounded-lg border bg-card space-y-3">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <h4 className="text-xs font-bold text-foreground flex items-center gap-2">
                                  <Badge
                                    variant="secondary"
                                    className={
                                      rec.priority === "critical"
                                        ? "bg-rose-500 text-white text-[10px]"
                                        : rec.priority === "high"
                                        ? "bg-amber-500 text-white text-[10px]"
                                        : "bg-blue-500 text-white text-[10px]"
                                    }
                                  >
                                    {rec.priority.toUpperCase()}
                                  </Badge>
                                  {rec.title}
                                </h4>
                                <span className="text-[11px] text-muted-foreground font-semibold">
                                  Owner: <b className="text-foreground">{rec.suggested_owner_team}</b>
                                </span>
                              </div>

                              <div className="grid sm:grid-cols-2 gap-2 text-xs">
                                <div className="p-2.5 rounded bg-muted/30 border border-border/50">
                                  <span className="font-semibold text-foreground block">Business Problem:</span>
                                  <p className="text-muted-foreground">{rec.problem}</p>
                                </div>
                                <div className="p-2.5 rounded bg-muted/30 border border-border/50">
                                  <span className="font-semibold text-foreground block">Observed Evidence:</span>
                                  <p className="text-muted-foreground">{rec.evidence}</p>
                                </div>
                              </div>

                              {/* 5-Step Action Plan */}
                              <div className="p-3 rounded-lg border border-blue-500/20 bg-blue-500/5 space-y-1.5 text-xs">
                                <span className="font-semibold text-blue-700 dark:text-blue-400 block text-[11px] uppercase tracking-wider">
                                  Action Execution Roadmap:
                                </span>
                                <p className="text-foreground font-medium">{rec.exact_recommended_action}</p>
                                {rec.action_steps && rec.action_steps.length > 0 && (
                                  <ul className="space-y-1 text-muted-foreground pt-1">
                                    {rec.action_steps.map((step, sIdx) => (
                                      <li key={sIdx} className="leading-snug">{step}</li>
                                    ))}
                                  </ul>
                                )}
                              </div>

                              <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground pt-1 border-t">
                                <span><b>Target KPI:</b> {rec.metric_to_track}</span>
                                <span><b>Review Period:</b> {rec.suggested_review_period}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 14. PRIORITY ACTION PLAN TABLE */}
                {isSectionVisible("priority_action_plan") && report.corrective_action_plan && (
                  <section id="priority_action_plan" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <ListOrdered className="h-4 w-4" />
                          Section 14
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Priority Action Plan Table
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Operational roadmap ordered by business urgency and evidence strength.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="overflow-x-auto rounded-lg border">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-muted/60 text-muted-foreground font-medium border-b">
                              <tr>
                                <th className="py-2.5 px-3">Priority</th>
                                <th className="py-2.5 px-3">Business Issue</th>
                                <th className="py-2.5 px-3">Recommended Action</th>
                                <th className="py-2.5 px-3">Owner</th>
                                <th className="py-2.5 px-3">Target KPI</th>
                                <th className="py-2.5 px-3">Timeframe</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y">
                              {report.corrective_action_plan.action_items.map((act, idx) => (
                                <tr key={idx} className="hover:bg-muted/30">
                                  <td className="py-2 px-3">
                                    <Badge
                                      variant="secondary"
                                      className={
                                        act.priority === "Critical"
                                          ? "bg-rose-500 text-white text-[10px]"
                                          : act.priority === "High"
                                          ? "bg-amber-500 text-white text-[10px]"
                                          : "bg-blue-500 text-white text-[10px]"
                                      }
                                    >
                                      {act.priority}
                                    </Badge>
                                  </td>
                                  <td className="py-2 px-3 font-semibold text-foreground">{act.problem}</td>
                                  <td className="py-2 px-3 text-foreground">{act.recommended_action}</td>
                                  <td className="py-2 px-3 text-muted-foreground font-medium">{act.owner_team}</td>
                                  <td className="py-2 px-3 text-muted-foreground">{act.metric_to_track}</td>
                                  <td className="py-2 px-3 font-mono text-muted-foreground">{act.review_period}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 15. LIMITATIONS & DECISION BOUNDARIES */}
                {isSectionVisible("limitations_conclusion") && (
                  <section id="limitations_conclusion" className="space-y-4">
                    <Card className="border-border shadow-xs">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider">
                          <HelpCircle className="h-4 w-4" />
                          Section 15
                        </div>
                        <CardTitle className="text-lg font-bold text-foreground">
                          Business Limitations & Decision Boundaries
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Scope constraints, required additional information, and confidence bounds.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4 text-xs text-muted-foreground">
                        <ul className="space-y-1.5 list-disc pl-5">
                          {report.data_driven_conclusion.important_limitations.map((lim, idx) => (
                            <li key={idx} className="leading-snug">{lim}</li>
                          ))}
                        </ul>

                        <div className="p-3 rounded-lg bg-muted/30 border space-y-1">
                          <span className="font-semibold text-foreground block text-[11px] uppercase tracking-wider">
                            Areas Requiring Supplementary Business Tracking:
                          </span>
                          <ul className="space-y-1 text-muted-foreground">
                            {report.data_driven_conclusion.areas_requiring_additional_data.map((item, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span className="text-primary font-bold">•</span>
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  </section>
                )}

                {/* 16. TECHNICAL DATA VALIDATION (BOTTOM COLLAPSIBLE DRAWER) */}
                {isSectionVisible("technical_validation") && (
                  <section id="technical_validation" className="space-y-4 pt-4 border-t">
                    <div className="rounded-xl border border-dashed border-border/80 bg-muted/10 p-4">
                      <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                          <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                            <Database className="h-4 w-4 text-muted-foreground" />
                            Technical Data Validation (Supporting Profiling)
                          </span>
                          <p className="text-[11px] text-muted-foreground">
                            Secondary schema checks, data health score ({report.dataset_overview.data_quality_score}/100), and missing cell audits.
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-xs gap-1"
                          onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                        >
                          {showTechnicalDetails ? "Collapse" : "View Technical Diagnostics"}
                          {showTechnicalDetails ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                        </Button>
                      </div>

                      {showTechnicalDetails && (
                        <div className="mt-4 pt-4 border-t space-y-3 text-xs">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div className="p-2.5 rounded bg-card border space-y-0.5">
                              <span className="text-[10px] text-muted-foreground">Dimensions</span>
                              <div className="font-mono font-bold text-foreground">{report.dataset_overview.dimensions_text}</div>
                            </div>
                            <div className="p-2.5 rounded bg-card border space-y-0.5">
                              <span className="text-[10px] text-muted-foreground">Data Quality Score</span>
                              <div className="font-mono font-bold text-emerald-600">{report.dataset_overview.data_quality_score}/100</div>
                            </div>
                            <div className="p-2.5 rounded bg-card border space-y-0.5">
                              <span className="text-[10px] text-muted-foreground">Duplicate Records</span>
                              <div className="font-mono font-bold text-foreground">{report.dataset_overview.duplicate_rows_count.toLocaleString()} ({report.dataset_overview.duplicate_rows_pct}%)</div>
                            </div>
                            <div className="p-2.5 rounded bg-card border space-y-0.5">
                              <span className="text-[10px] text-muted-foreground">Missing Cells</span>
                              <div className="font-mono font-bold text-foreground">{report.dataset_overview.missing_cells_count.toLocaleString()} ({report.dataset_overview.missing_cells_pct}%)</div>
                            </div>
                          </div>

                          <div className="overflow-x-auto rounded border">
                            <table className="w-full text-left text-[11px]">
                              <thead className="bg-muted/40 text-muted-foreground font-medium border-b">
                                <tr>
                                  <th className="py-1.5 px-2.5">Column Name</th>
                                  <th className="py-1.5 px-2.5">Data Type</th>
                                  <th className="py-1.5 px-2.5">Inferred Role</th>
                                  <th className="py-1.5 px-2.5">Missing Count</th>
                                  <th className="py-1.5 px-2.5">Unique Values</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y font-mono">
                                {report.dataset_overview.columns_summary.slice(0, 8).map((col, i) => (
                                  <tr key={i}>
                                    <td className="py-1.5 px-2.5 text-foreground font-sans font-medium">{col.column_name}</td>
                                    <td className="py-1.5 px-2.5 text-muted-foreground">{col.dtype}</td>
                                    <td className="py-1.5 px-2.5 text-muted-foreground">{col.semantic_role}</td>
                                    <td className="py-1.5 px-2.5 text-muted-foreground">{col.missing_count}</td>
                                    <td className="py-1.5 px-2.5 text-muted-foreground">{col.unique_count}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  </section>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
