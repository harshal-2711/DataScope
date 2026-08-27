import {
  BarChart3,
  Calculator,
  DollarSign,
  Package,
  ShoppingCart,
  Tag,
  Wallet,
} from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { getColorSet, type ColorKind } from "@/lib/chartColors"
import { formatNumberCompact, formatNumberFull } from "@/lib/format"
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
  sales: "Total revenue across all rows",
  profit: "Overall profitability",
  quantity: "Total units across all rows",
  discount: "Total discount applied",
  orders: "Number of records in this dataset",
  average: "Typical value per row",
  generic: "Derived from the dataset",
}

export function KpiRow({ kpis }: { kpis: Kpi[] }) {
  if (kpis.length === 0) return null

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
      {kpis.map((kpi) => {
        const colors = getColorSet(kpi.kind)
        const Icon = KIND_ICON[kpi.kind] ?? BarChart3
        const formatted =
          kpi.format === "count"
            ? kpi.value.toLocaleString()
            : formatNumberCompact(kpi.value)
        return (
          <Card
            key={kpi.label}
            className="group relative gap-3 overflow-hidden py-4 transition-colors hover:border-border/80"
          >
            <div
              className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
              style={{
                background: `radial-gradient(120px circle at 20% 0%, ${colors.hex}14, transparent 70%)`,
              }}
            />
            <CardContent className="relative px-4">
              <div className="flex items-center gap-3">
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${colors.bg}`}>
                  <Icon className={`h-4.5 w-4.5 ${colors.text}`} />
                </div>
                <div className="min-w-0">
                  <p
                    className="truncate text-lg font-semibold tabular-nums"
                    title={formatNumberFull(kpi.value)}
                  >
                    {formatted}
                  </p>
                  <p className="truncate text-xs text-muted-foreground">{kpi.label}</p>
                </div>
              </div>
              <p className="mt-2 text-[11px] text-muted-foreground/80">
                {KIND_DESCRIPTION[kpi.kind]}
              </p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
