import { useState } from "react"
import { Sparkles, Info, ChevronDown, ChevronUp, CheckCircle2 } from "lucide-react"
import type { DomainIdentity } from "@/types/intelligence"

interface DomainHeaderProps {
  domain: DomainIdentity
}

export function DomainHeader({ domain }: DomainHeaderProps) {
  const [showEvidence, setShowEvidence] = useState(false)
  const confidencePercent = Math.round(domain.confidence * 100)

  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-xs">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1.5 max-w-2xl">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold tracking-tight text-foreground">
                  {domain.name}
                </h2>
                <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
                  <CheckCircle2 className="h-3 w-3" />
                  {confidencePercent}% confidence
                </span>
              </div>
            </div>
          </div>
          <p className="text-xs text-muted-foreground leading-relaxed pl-10">
            {domain.description}
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          {domain.evidence.length > 0 && (
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <Info className="h-3.5 w-3.5" />
              <span>{showEvidence ? "Hide detection evidence" : `View evidence (${domain.evidence.length})`}</span>
              {showEvidence ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
          )}

          {domain.alternative_domains.length > 0 && (
            <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span>Alternatives:</span>
              <div className="flex flex-wrap gap-1">
                {domain.alternative_domains.map((alt) => (
                  <span
                    key={alt}
                    className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground"
                  >
                    {alt}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {showEvidence && domain.evidence.length > 0 && (
        <div className="mt-4 pt-3 border-t border-border/60">
          <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground mb-2">
            Supporting Evidence Extracted from Dataset:
          </p>
          <div className="grid gap-1.5 sm:grid-cols-2 md:grid-cols-3">
            {domain.evidence.map((ev, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 rounded-md bg-muted/50 px-2.5 py-1.5 text-xs text-muted-foreground border border-border/40"
              >
                <div className="h-1.5 w-1.5 rounded-full bg-primary/60 shrink-0" />
                <span className="truncate">{ev}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
