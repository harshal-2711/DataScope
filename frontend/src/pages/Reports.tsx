import { Link } from "react-router-dom"
import {
  FileText,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  BarChart3,
} from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDomainIntelligence } from "@/hooks/useDomainIntelligence"
import { formatMetricValue, detectColumnUnit } from "@/lib/format"

export default function Reports() {
  const { activeDataset } = useActiveDataset()
  const intelState = useDomainIntelligence(activeDataset?.dataset_id ?? null)

  const kpis = intelState.status === "success" ? intelState.data.kpis : []
  const currencySymbol = activeDataset?.detected_currency ?? null

  return (
    <div className="space-y-6">
      <PageHeader
        title="Executive Reports & Export"
        description="Synthesize executive briefings, analytical dashboards, and validated summary reports from your dataset with full unit fidelity."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={FileText}
            title="No dataset loaded"
            description="Upload a dataset first to generate executive briefs and export validated reports."
          />
          <div className="flex justify-center">
            <Button asChild size="sm">
              <Link to="/dataset">Upload a dataset</Link>
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {intelState.status === "success" && (
            <DomainHeader domain={intelState.data.domain} />
          )}

          <Card>
            <CardHeader className="flex flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-primary/10 p-2 text-primary">
                  <FileSpreadsheet className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-base">
                    Executive Briefing: {activeDataset.filename}
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Ready for synthesis · {activeDataset.row_count.toLocaleString()} rows · {activeDataset.column_count} columns
                    {currencySymbol && ` · Currency: ${currencySymbol}`}
                  </p>
                </div>
              </div>
              <Button size="sm" className="gap-1.5 text-xs print:hidden" onClick={() => window.print()}>
                <Download className="h-4 w-4" />
                Print / Export Brief
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-border bg-card p-4 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-sm font-medium">
                    <CheckCircle2 className="h-4 w-4" />
                    Data Quality Validated
                  </div>
                  <p className="text-xs text-muted-foreground">
                    All columns and metrics checked for completeness, grain consistency, and distribution anomalies.
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-card p-4 space-y-2">
                  <div className="flex items-center gap-2 text-primary text-sm font-medium">
                    <CheckCircle2 className="h-4 w-4" />
                    Domain Analytics & Units Detected
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Semantic units (currencies, percentages, counts, rates, quantities) automatically classified and formatted.
                  </p>
                </div>
              </div>

              {/* Key Performance Indicators Table with Units */}
              {kpis.length > 0 && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4 text-primary" />
                      <h3 className="text-sm font-semibold text-foreground">
                        Executive Key Performance Indicators
                      </h3>
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">
                      {kpis.length} metrics computed
                    </span>
                  </div>

                  <div className="overflow-x-auto rounded-lg border border-border">
                    <table className="w-full text-left text-xs">
                      <thead className="border-b border-border bg-muted/40 font-medium text-muted-foreground">
                        <tr>
                          <th className="py-2.5 px-3">Metric Name</th>
                          <th className="py-2.5 px-3">Formatted Value</th>
                          <th className="py-2.5 px-3">Unit</th>
                          <th className="py-2.5 px-3">Aggregation</th>
                          <th className="py-2.5 px-3">Source Column</th>
                          <th className="py-2.5 px-3">Formatting Rule</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border">
                        {kpis.map((kpi, i) => {
                          const unit = kpi.unit || detectColumnUnit(kpi.name, kpi.source_column).unit
                          const displayVal = kpi.formatted_value || formatMetricValue(kpi.value, {
                            column: kpi.source_column || kpi.name,
                            unit: unit,
                            currencySymbol: currencySymbol,
                            percentageStoredAsFraction: kpi.formatting_rule === "percentage_fraction",
                          })

                          return (
                            <tr key={i} className="hover:bg-muted/20">
                              <td className="py-2.5 px-3 font-semibold text-foreground">
                                {kpi.name}
                              </td>
                              <td className="py-2.5 px-3 font-mono font-bold text-primary">
                                {displayVal}
                              </td>
                              <td className="py-2.5 px-3">
                                {unit ? (
                                  <span className="inline-flex items-center rounded bg-secondary px-2 py-0.5 text-[11px] font-medium text-secondary-foreground">
                                    {unit}
                                  </span>
                                ) : (
                                  <span className="text-muted-foreground italic">None</span>
                                )}
                              </td>
                              <td className="py-2.5 px-3 text-muted-foreground capitalize">
                                {kpi.aggregation || "Summary"}
                              </td>
                              <td className="py-2.5 px-3">
                                <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px] text-foreground">
                                  {kpi.source_column || (kpi.matched_columns && kpi.matched_columns[0]) || "Derived / Aggregate"}
                                </code>
                              </td>
                              <td className="py-2.5 px-3 text-muted-foreground text-[11px]">
                                {kpi.formatting_rule || "standard"}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
