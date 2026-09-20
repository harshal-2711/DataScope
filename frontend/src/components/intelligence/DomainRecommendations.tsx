import { Lightbulb, AlertCircle, ArrowUpRight } from "lucide-react"
import type { RecommendationItem } from "@/types/intelligence"

interface DomainRecommendationsProps {
  recommendations: RecommendationItem[]
}

export function DomainRecommendations({ recommendations }: DomainRecommendationsProps) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-8 text-center">
        <Lightbulb className="mx-auto h-8 w-8 text-muted-foreground/60 mb-2" />
        <h3 className="text-sm font-medium text-foreground">No recommendations generated yet</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Evidence-based recommendations will appear once a dataset is analyzed.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {recommendations.map((rec) => (
        <div
          key={rec.rec_id}
          className="rounded-xl border border-border bg-card p-5 shadow-xs flex flex-col justify-between space-y-4"
        >
          <div className="space-y-3">
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-1">
                <span className="inline-block rounded-md bg-primary/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-primary">
                  {rec.category.replace(/_/g, " ")}
                </span>
                <h4 className="text-sm font-semibold text-foreground leading-snug">{rec.title}</h4>
              </div>
              <span className="text-[11px] font-medium text-muted-foreground shrink-0">
                {Math.round(rec.confidence * 100)}% conf
              </span>
            </div>

            <div className="space-y-1.5 text-xs">
              <div>
                <span className="font-medium text-foreground">Verified Finding: </span>
                <span className="text-muted-foreground">{rec.finding}</span>
              </div>

              {rec.supporting_metric && (
                <div>
                  <span className="font-medium text-foreground">Metric Evidence: </span>
                  <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-foreground">
                    {rec.supporting_metric}
                  </code>
                </div>
              )}
            </div>

            <div className="rounded-lg bg-primary/5 border border-primary/15 p-3 text-xs">
              <div className="font-semibold text-primary mb-1 flex items-center gap-1.5">
                <ArrowUpRight className="h-3.5 w-3.5" />
                Actionable Recommendation:
              </div>
              <div className="text-foreground leading-relaxed">{rec.recommended_action}</div>
            </div>
          </div>

          {rec.limitations && (
            <div className="pt-2 border-t border-border/60 text-[11px] text-muted-foreground flex items-start gap-1.5">
              <AlertCircle className="h-3 w-3 text-muted-foreground shrink-0 mt-0.5" />
              <span>
                <strong className="font-medium">Limitation: </strong>
                {rec.limitations}
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
