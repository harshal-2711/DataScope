import { useState } from "react"
import {
  BarChart3,
  Calculator,
  DollarSign,
  Package,
  ShoppingCart,
  Tag,
  Wallet,
  Info,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { getColorSet, type ColorKind } from "@/lib/chartColors"
import { formatMetricValue, detectColumnUnit } from "@/lib/format"
import type { Kpi } from "@/types/dataset"

const KIND_ICON: Record<ColorKind, React.ComponentType<{ className?: string }>> = {
  sales: DollarSign,
  profit: Wallet,
  quantity: Package,
  discount: Tag,
  orders: ShoppingCart,
  average: Calculator,
  generic: BarChart3,
}

const KIND_DESCRIPTION: Record<ColorKind, string> = {
  sales: "Monetary value & revenue generated",
  profit: "Net earnings and financial return",
  quantity: "Discrete units and item volume",
  discount: "Rate or markdown applied",
  orders: "Discrete count of records in dataset",
  average: "Typical measure per row observation",
  generic: "Derived numerical measurement",
}

export function KpiRow({ kpis }: { kpis: Kpi[] }) {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null)

  if (kpis.length === 0) return null

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
      {kpis.map((kpi, index) => {
        const colors = getColorSet(kpi.kind)
        const Icon = KIND_ICON[kpi.kind] ?? BarChart3

        // Determine unit and semantic type
        const fallback = detectColumnUnit(kpi.source_column || kpi.label)
        const unit = kpi.unit || (kpi.kind === "sales" || kpi.kind === "profit" ? "₹" : kpi.kind === "discount" ? "%" : kpi.kind === "quantity" ? "units" : kpi.kind === "orders" ? "records" : fallback.unit)
        const semType = kpi.semantic_type || (kpi.kind === "sales" || kpi.kind === "profit" ? "currency" : kpi.kind === "discount" ? "percentage" : kpi.kind === "quantity" ? "quantity" : kpi.kind === "orders" ? "count" : fallback.semanticType)

        const formatted =
          kpi.formatted_value ||
          formatMetricValue(kpi.value, {
            unit,
            semanticType: semType,
            compact: true,
          })

        const fullFormatted = formatMetricValue(kpi.value, {
          unit,
          semanticType: semType,
          compact: false,
          precision: 4,
        })

        const agg = kpi.aggregation?.toUpperCase() || (kpi.label.toLowerCase().startsWith("average") ? "MEAN" : kpi.label.toLowerCase().startsWith("total") ? "SUM" : "AGGREGATION")
        const sourceCol = kpi.source_column || kpi.label
        const isTooltipOpen = activeTooltip === kpi.label

        return (
          <Card
            key={`${kpi.label}-${index}`}
            className="group relative gap-3 overflow-visible py-4 transition-all hover:border-border hover:bg-card/80"
          >
            <CardContent className="relative px-4">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${colors.bg}`}>
                    <Icon className={`h-4.5 w-4.5 ${colors.text}`} />
                  </div>
                  <div className="min-w-0">
                    <p
                      className="truncate text-lg font-bold tabular-nums text-foreground"
                      title={fullFormatted}
                    >
                      {formatted}
                    </p>
                    <p className="truncate text-xs text-muted-foreground font-medium" title={kpi.label}>
                      {kpi.label}
                    </p>
                  </div>
                </div>

                {/* Info Tooltip Trigger */}
                <button
                  type="button"
                  onClick={() => setActiveTooltip(isTooltipOpen ? null : kpi.label)}
                  onMouseEnter={() => setActiveTooltip(kpi.label)}
                  onMouseLeave={() => setActiveTooltip(null)}
                  className="text-muted-foreground/60 hover:text-foreground transition-colors p-0.5 rounded-md relative cursor-help"
                  title="View metric details and formatting rule"
                >
                  <Info className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Unit Tag & Quick Description */}
              <div className="mt-3 flex items-center justify-between gap-2 border-t border-border/40 pt-2 text-[11px]">
                <span className="text-muted-foreground/80 truncate">
                  {KIND_DESCRIPTION[kpi.kind]}
                </span>
                <span className="shrink-0 rounded bg-muted/80 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-muted-foreground">
                  {unit}
                </span>
              </div>

              {/* Rich Tooltip Popover */}
              {isTooltipOpen && (
                <div className="absolute left-0 right-0 top-full z-50 mt-1 rounded-xl border border-border bg-popover p-3.5 text-popover-foreground shadow-lg animate-in fade-in-50 duration-150 text-xs space-y-2">
                  <div className="flex items-center justify-between border-b border-border/60 pb-1.5">
                    <span className="font-bold text-foreground truncate">{kpi.label}</span>
                    <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                      {unit}
                    </span>
                  </div>

                  <div className="space-y-1 text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Calculated Value:</span>
                      <strong className="text-foreground font-mono">{fullFormatted}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Measurement Unit:</span>
                      <strong className="text-foreground font-mono">{unit}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Aggregation Method:</span>
                      <strong className="text-foreground uppercase">{agg}</strong>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Source Column:</span>
                      <span className="font-mono text-muted-foreground truncate max-w-[120px]" title={sourceCol}>
                        {sourceCol}
                      </span>
                    </div>
                  </div>

                  <div className="border-t border-border/40 pt-1.5 text-[10px] text-muted-foreground italic leading-tight">
                    {kpi.formatting_rule || `Calculated using ${agg} over column '${sourceCol}' and formatted with ${unit}.`}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

