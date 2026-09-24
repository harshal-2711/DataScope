import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import type { DatasetGrain } from "@/types/intelligence"
import {
  Layers,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from "lucide-react"

interface DatasetGrainBadgeProps {
  grain: DatasetGrain
}

export function DatasetGrainBadge({ grain }: DatasetGrainBadgeProps) {
  const [expanded, setExpanded] = useState(false)

  const isOneToOne = grain.is_one_to_one
  const hasGuardrails = grain.aggregation_guardrails && grain.aggregation_guardrails.length > 0

  return (
    <Card className="border-border/80 bg-card/60 shadow-xs">
      <CardContent className="p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Left: Grain Identification */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-secondary text-foreground">
              <Layers className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Dataset Grain:
                </span>
                <Badge variant="secondary" className="font-semibold text-xs px-2 py-0.5 bg-secondary text-foreground border border-border">
                  {grain.grain_label}
                </Badge>
                {isOneToOne ? (
                  <Badge variant="outline" className="text-[11px] font-normal text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                    1 row = 1 unique entity
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-[11px] font-normal text-amber-400 border-amber-500/30 bg-amber-500/10">
                    Repeated observations (multi-row entities)
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {grain.description}
              </p>
            </div>
          </div>

          {/* Right: Quick Stats & Toggle */}
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-3">
              <div className="text-right">
                <span className="text-muted-foreground block text-[10px]">Total Observations</span>
                <span className="font-semibold text-foreground">{grain.row_count.toLocaleString()} rows</span>
              </div>
              <div className="h-6 w-px bg-border" />
              <div className="text-right">
                <span className="text-muted-foreground block text-[10px]">Unique Entities</span>
                <span className="font-semibold text-foreground">
                  {grain.unique_entity_count.toLocaleString()} {grain.primary_entity_column ? `(${grain.primary_entity_column})` : ""}
                </span>
              </div>
            </div>

            <button
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors ml-2"
            >
              <span>{expanded ? "Less details" : "Grain details"}</span>
              {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>

        {/* Aggregation Guardrail Banner */}
        {hasGuardrails && (
          <div className="p-2.5 rounded-md border border-amber-500/30 bg-amber-500/5 text-amber-900 dark:text-amber-200 flex items-start gap-2.5 text-xs">
            <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-semibold">Aggregation Guardrail:</span>
              <p className="text-muted-foreground leading-relaxed">
                {grain.aggregation_guardrails[0]}
              </p>
            </div>
          </div>
        )}

        {/* Expanded Details */}
        {expanded && (
          <div className="pt-3 border-t border-border/60 grid gap-3 sm:grid-cols-2 text-xs">
            <div>
              <span className="font-semibold text-muted-foreground block mb-1">
                Candidate Entity Identifiers:
              </span>
              <div className="space-y-1">
                {grain.candidate_entities && grain.candidate_entities.length > 0 ? (
                  grain.candidate_entities.map((cand, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between px-2.5 py-1 rounded bg-muted/40 text-muted-foreground"
                    >
                      <span className="font-mono text-[11px] text-foreground">{cand.column}</span>
                      <span>
                        {cand.unique_count.toLocaleString()} unique ({Math.round(cand.uniqueness_ratio * 100)}%)
                      </span>
                    </div>
                  ))
                ) : (
                  <span className="text-muted-foreground italic">None detected</span>
                )}
              </div>
            </div>

            <div>
              <span className="font-semibold text-muted-foreground block mb-1">
                Identified Measures & Dimensions:
              </span>
              <div className="space-y-1.5">
                <div className="flex flex-wrap gap-1 items-center">
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground w-16">Measures:</span>
                  {grain.measures && grain.measures.length > 0 ? (
                    grain.measures.slice(0, 6).map((m) => (
                      <span key={m} className="px-1.5 py-0.5 rounded bg-secondary text-foreground text-[10px] font-mono border border-border">
                        {m}
                      </span>
                    ))
                  ) : (
                    <span className="text-muted-foreground italic text-[11px]">none</span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 items-center">
                  <span className="text-[10px] uppercase tracking-wider text-muted-foreground w-16">Dimensions:</span>
                  {grain.dimensions && grain.dimensions.length > 0 ? (
                    grain.dimensions.slice(0, 6).map((d) => (
                      <span key={d} className="px-1.5 py-0.5 rounded bg-secondary text-foreground text-[10px] font-mono border border-border">
                        {d}
                      </span>
                    ))
                  ) : (
                    <span className="text-muted-foreground italic text-[11px]">none</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
