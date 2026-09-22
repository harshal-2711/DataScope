import { Link } from "react-router-dom"
import { Target, Trophy, Info } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDomainIntelligence } from "@/hooks/useDomainIntelligence"

export default function Competition() {
  const { activeDataset } = useActiveDataset()
  const intelState = useDomainIntelligence(activeDataset?.dataset_id ?? null)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Competition & Benchmarking"
        description="Compare your dataset metrics and performance distributions against domain standards and category peers."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={Target}
            title="No dataset loaded"
            description="Upload a dataset first to enable competitive benchmark analysis and category comparisons."
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
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="rounded-lg bg-primary/10 p-2 text-primary">
                <Trophy className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base">
                  Competitive Benchmarks for {activeDataset.filename}
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Dataset containing {activeDataset.row_count.toLocaleString()} records across {activeDataset.column_count} columns
                </p>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3 rounded-lg border border-border bg-muted/40 p-4 text-sm">
                <Info className="h-5 w-5 shrink-0 text-primary mt-0.5" />
                <div className="space-y-1">
                  <p className="font-medium text-foreground">Domain Benchmark Alignment Active</p>
                  <p className="text-xs text-muted-foreground">
                    Peer industry quartile metrics and competitive intelligence indexes for this domain are being synchronized with the active dataset.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
