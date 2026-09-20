import { Tag, Database } from "lucide-react"
import type { DetectedEntity } from "@/types/intelligence"

interface EntityBadgesProps {
  entities: DetectedEntity[]
}

export function EntityBadges({ entities }: EntityBadgesProps) {
  if (!entities || entities.length === 0) return null

  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-xs">
      <div className="flex items-center gap-2 mb-3">
        <Database className="h-4 w-4 text-primary" />
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Detected Dataset Entities ({entities.length})
        </h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {entities.map((ent) => (
          <div
            key={ent.entity_type}
            className="flex items-center gap-1.5 rounded-lg border border-border/80 bg-muted/40 px-3 py-1.5 text-xs text-foreground shadow-2xs"
            title={ent.evidence}
          >
            <Tag className="h-3 w-3 text-muted-foreground" />
            <span className="font-medium">{ent.label}</span>
            {ent.matched_column && (
              <span className="rounded bg-background/80 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground border border-border/60">
                {ent.matched_column}
              </span>
            )}
            <span className="text-[10px] text-primary/80 font-medium ml-0.5">
              {Math.round(ent.confidence * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
