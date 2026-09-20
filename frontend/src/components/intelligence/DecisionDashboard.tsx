import { useState } from "react"
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import {
  Briefcase,
  TrendingUp,
  DollarSign,
  Package,
  Boxes,
  HelpCircle,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
  Info,
  ArrowUpRight,
  ShieldAlert,
} from "lucide-react"
import type {
  DecisionDashboardResponse,
  MetricStatus,
  SectionChart,
} from "@/types/intelligence"

interface DecisionDashboardProps {
  dashboard?: DecisionDashboardResponse | null
  onDrilldown?: (dimension: string, value: string) => void
}

type TabType =
  | "executive_summary"
  | "sales_performance"
  | "profitability"
  | "product_analysis"
  | "operations_inventory"
  | "insights_recommendations"

export function DecisionDashboard({ dashboard, onDrilldown }: DecisionDashboardProps) {
  const [activeTab, setActiveTab] = useState<TabType>("executive_summary")

  if (!dashboard) return null

  const {
    domain_name,
    executive_summary,
    sales_performance,
    profitability,
    product_analysis,
    operations_inventory,
    insights_recommendations,
  } = dashboard

  const tabs: Array<{ id: TabType; label: string; icon: any; available: boolean }> = [
    {
      id: "executive_summary",
      label: "Executive Summary",
      icon: Briefcase,
      available: executive_summary.is_available,
    },
    {
      id: "sales_performance",
      label: "Performance",
      icon: TrendingUp,
      available: sales_performance.is_available,
    },
    {
      id: "profitability",
      label: "Profitability",
      icon: DollarSign,
      available: profitability.is_available,
    },
    {
      id: "product_analysis",
      label: "Product / Entity Analysis",
      icon: Package,
      available: product_analysis.is_available,
    },
    {
      id: "operations_inventory",
      label: "Operations & Inventory",
      icon: Boxes,
      available: operations_inventory.is_available,
    },
    {
      id: "insights_recommendations",
      label: "Insights & Actions",
      icon: Lightbulb,
      available: insights_recommendations.is_available,
    },
  ]

  const getStatusBadge = (status: MetricStatus["status"]) => {
    switch (status) {
      case "Calculated":
        return "bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-500/20"
      case "Available":
        return "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/20"
      case "Estimated":
        return "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/20"
      case "Unavailable":
        return "bg-zinc-500/15 text-zinc-600 dark:text-zinc-400 border-zinc-500/20"
    }
  }

  const renderMetricCard = (metric: MetricStatus) => (
    <div
      key={metric.id}
      className="rounded-xl border border-border bg-card p-4 shadow-xs flex flex-col justify-between space-y-3"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-0.5">
          <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">
            {metric.name}
          </span>
          <div className="text-xl font-bold text-foreground">
            {metric.formatted_value ?? "N/A"}
          </div>
        </div>
        <span
          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${getStatusBadge(
            metric.status
          )}`}
        >
          {metric.status}
        </span>
      </div>

      <div className="space-y-1 pt-1 border-t border-border/40 text-[11px]">
        <p className="text-muted-foreground leading-snug">{metric.explanation}</p>
        {metric.formula && (
          <div className="text-[10px] text-muted-foreground/80 font-mono">
            Formula: {metric.formula}
          </div>
        )}
      </div>
    </div>
  )

  const renderChartCard = (chart: SectionChart) => {
    const isLine = chart.chart_type === "line"
    const isScatter = chart.chart_type === "scatter"

    return (
      <div
        key={chart.id}
        className="rounded-xl border border-border bg-card p-5 shadow-xs space-y-4"
      >
        <div className="flex flex-col gap-1.5 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-foreground">{chart.title}</h4>
            <div className="inline-flex items-center gap-1.5 rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
              <HelpCircle className="h-3.5 w-3.5" />
              <span>{chart.business_question}</span>
            </div>
          </div>
        </div>

        <div className="h-64 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            {isLine ? (
              <LineChart data={chart.data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                <XAxis dataKey="x" stroke="var(--muted-foreground)" fontSize={11} tickLine={false} />
                <YAxis
                  stroke="var(--muted-foreground)"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => Number(v).toLocaleString()}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    borderColor: "var(--border)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  formatter={(value: any) => [Number(value).toLocaleString(), chart.metric]}
                />
                <Line
                  type="monotone"
                  dataKey="y"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            ) : isScatter ? (
              <ScatterChart margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                <XAxis
                  dataKey="x"
                  name={chart.x_label || "X"}
                  stroke="var(--muted-foreground)"
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis
                  dataKey="y"
                  name={chart.y_label || "Y"}
                  stroke="var(--muted-foreground)"
                  fontSize={11}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ strokeDasharray: "3 3" }}
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    borderColor: "var(--border)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Scatter name={chart.title} data={chart.data} fill="#8b5cf6" />
              </ScatterChart>
            ) : (
              <BarChart data={chart.data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
                <XAxis
                  dataKey="x"
                  stroke="var(--muted-foreground)"
                  fontSize={11}
                  tickLine={false}
                  interval={0}
                  tickFormatter={(val) =>
                    String(val).length > 12 ? `${String(val).substring(0, 10)}...` : String(val)
                  }
                />
                <YAxis
                  stroke="var(--muted-foreground)"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(v) => Number(v).toLocaleString()}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--card)",
                    borderColor: "var(--border)",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  formatter={(value: any) => [Number(value).toLocaleString(), chart.metric]}
                />
                {chart.data[0]?.cost !== undefined ? (
                  <>
                    <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
                    <Bar dataKey="revenue" name="Revenue" fill="#2563eb" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="cost" name="Cost" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                  </>
                ) : (
                  <Bar
                    dataKey="y"
                    fill="#3b82f6"
                    radius={[4, 4, 0, 0]}
                    onClick={(entry: any) => {
                      if (onDrilldown && entry?.x && chart.grouping) {
                        onDrilldown(chart.grouping, String(entry.x))
                      }
                    }}
                  />
                )}
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>

        <div className="rounded-lg bg-muted/40 p-3 text-xs border border-border/50 flex items-start gap-2">
          <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
          <p className="text-muted-foreground leading-relaxed">
            <strong className="text-foreground font-medium">Business Takeaway: </strong>
            {chart.explanation}
          </p>
        </div>
      </div>
    )
  }

  const renderUnavailableBanner = (reason?: string | null) => (
    <div className="rounded-xl border border-dashed border-border bg-muted/20 p-8 text-center space-y-2">
      <AlertTriangle className="mx-auto h-8 w-8 text-amber-500/80 mb-1" />
      <h4 className="text-sm font-semibold text-foreground">Section Unavailable</h4>
      <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
        {reason || "This analytical section cannot be calculated because required fields were not found in the dataset."}
      </p>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-foreground tracking-tight">
              Executive & Decision Dashboard
            </h2>
            <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
              {domain_name}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Real-world, decision-oriented analytics answering core business and operational questions.
          </p>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="flex flex-wrap gap-1.5 border-b border-border pb-2">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium transition-all ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "bg-card text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
              {!tab.available && (
                <span className="rounded bg-muted px-1.5 py-0.2 text-[9px] uppercase tracking-wider text-muted-foreground">
                  N/A
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab 1: Executive Summary */}
      {activeTab === "executive_summary" && (
        <div className="space-y-6">
          {executive_summary.highlights.length > 0 && (
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-primary uppercase tracking-wider">
                <Lightbulb className="h-4 w-4" />
                Executive Highlights
              </div>
              <div className="grid gap-2 sm:grid-cols-2 text-xs text-foreground leading-relaxed">
                {executive_summary.highlights.map((h, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
            {executive_summary.metrics.map(renderMetricCard)}
          </div>
        </div>
      )}

      {/* Tab 2: Sales / Primary Performance */}
      {activeTab === "sales_performance" && (
        <div className="space-y-6">
          {!sales_performance.is_available ? (
            renderUnavailableBanner(sales_performance.unavailable_reason)
          ) : (
            <div className="grid gap-6 md:grid-cols-2">
              {sales_performance.charts.map(renderChartCard)}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Profitability */}
      {activeTab === "profitability" && (
        <div className="space-y-6">
          {!profitability.is_available ? (
            renderUnavailableBanner(profitability.unavailable_reason)
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                {profitability.metrics.map(renderMetricCard)}
              </div>
              {profitability.charts.length > 0 && (
                <div className="grid gap-6 md:grid-cols-2">
                  {profitability.charts.map(renderChartCard)}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Product / Entity Analysis */}
      {activeTab === "product_analysis" && (
        <div className="space-y-6">
          {!product_analysis.is_available ? (
            renderUnavailableBanner(product_analysis.unavailable_reason)
          ) : (
            <div className="space-y-6">
              {product_analysis.metrics.length > 0 && (
                <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
                  {product_analysis.metrics.map(renderMetricCard)}
                </div>
              )}

              {product_analysis.charts.length > 0 && (
                <div className="grid gap-6 md:grid-cols-2">
                  {product_analysis.charts.map(renderChartCard)}
                </div>
              )}

              {product_analysis.insights.length > 0 && (
                <div className="rounded-xl border border-border bg-card p-5 space-y-3">
                  <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                    Catalog & Concentration Insights
                  </h4>
                  <div className="space-y-2 text-xs">
                    {product_analysis.insights.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-muted/30 border border-border/50 space-y-1">
                        <div className="font-semibold text-foreground">{item.finding}</div>
                        {item.impact && <div className="text-muted-foreground">{item.impact}</div>}
                        {item.action && (
                          <div className="text-primary font-medium flex items-center gap-1.5 pt-1">
                            <ArrowUpRight className="h-3.5 w-3.5" />
                            Action: {item.action}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 5: Operations & Inventory */}
      {activeTab === "operations_inventory" && (
        <div className="space-y-6">
          {!operations_inventory.is_available ? (
            renderUnavailableBanner(operations_inventory.unavailable_reason)
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                {operations_inventory.metrics.map(renderMetricCard)}
              </div>
              {operations_inventory.charts.length > 0 && (
                <div className="grid gap-6 md:grid-cols-2">
                  {operations_inventory.charts.map(renderChartCard)}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 6: Insights & Management Actions */}
      {activeTab === "insights_recommendations" && (
        <div className="space-y-6">
          {insights_recommendations.insights.map((ins, idx) => (
            <div
              key={idx}
              className="rounded-xl border border-border bg-card p-6 shadow-xs space-y-4"
            >
              <div className="space-y-1">
                <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">
                  Verified Executive Finding
                </span>
                <h4 className="text-base font-semibold text-foreground leading-snug">
                  {ins.what_happened}
                </h4>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 text-xs pt-1">
                <div className="rounded-lg bg-muted/40 p-3 border border-border/50 space-y-1">
                  <span className="font-semibold text-foreground">Data-Supported Drivers:</span>
                  <p className="text-muted-foreground leading-relaxed">{ins.why_it_happened}</p>
                </div>

                <div className="rounded-lg bg-primary/5 p-3 border border-primary/20 space-y-1">
                  <span className="font-semibold text-primary flex items-center gap-1">
                    <ArrowUpRight className="h-3.5 w-3.5" />
                    Management Investigation:
                  </span>
                  <p className="text-foreground leading-relaxed">{ins.what_to_investigate}</p>
                </div>
              </div>

              {ins.limitations && (
                <div className="pt-3 border-t border-border/60 text-[11px] text-muted-foreground flex items-start gap-1.5">
                  <ShieldAlert className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
                  <span>
                    <strong className="font-medium">Data Boundary & Limitation: </strong>
                    {ins.limitations}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
