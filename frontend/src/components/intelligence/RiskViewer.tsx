import { ShieldAlert, CheckCircle2, ArrowRight } from "lucide-react"
import type { RiskItem } from "@/types/intelligence"

interface RiskViewerProps {
  risks: RiskItem[]
}

export function RiskViewer({ risks }: RiskViewerProps) {
  if (!risks || risks.length === 0) {
    return (
      <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-8 text-center">
        <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500 mb-2" />
        <h3 className="text-sm font-medium text-foreground">No statistical anomalies detected</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Values are within expected dispersion thresholds with low missingness and no severe concentration.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {risks.map((risk) => {
        const isHigh = risk.severity === "high"
        const isMed = risk.severity === "medium"

        return (
          <div
            key={risk.risk_id}
            className="rounded-xl border border-border bg-card p-5 shadow-xs flex flex-col justify-between space-y-4"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <ShieldAlert
                    className={`h-4 w-4 ${
                      isHigh ? "text-rose-500" : isMed ? "text-amber-500" : "text-blue-500"
                    }`}
                  />
                  <h4 className="text-sm font-semibold text-foreground">{risk.category}</h4>
                </div>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium ${
                    isHigh
                      ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                      : isMed
                      ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                      : "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                  }`}
                >
                  {risk.label}
                </span>
              </div>

              <p className="text-xs text-muted-foreground leading-relaxed">
                {risk.description}
              </p>

              {risk.affected_column && (
                <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <span>Affected column:</span>
                  <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-foreground">
                    {risk.affected_column}
                  </code>
                </div>
              )}

              <div className="rounded-lg bg-muted/40 p-2.5 text-xs text-muted-foreground border border-border/50">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Evidence:
                </div>
                <div className="text-foreground/90 text-xs font-mono">{risk.evidence}</div>
              </div>
            </div>

            {risk.recommended_action && (
              <div className="pt-3 border-t border-border/60">
                <div className="flex items-start gap-2 text-xs text-foreground">
                  <ArrowRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-primary">Recommended Action: </span>
                    <span className="text-muted-foreground">{risk.recommended_action}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
