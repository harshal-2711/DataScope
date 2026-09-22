import { Link } from "react-router-dom"
import { Database, Search, TrendingUp, LineChart, ShieldAlert, ArrowRight, Sparkles } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { ConnectionStatus } from "@/components/shared/ConnectionStatus"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { KpiRow } from "@/components/dashboard/KpiRow"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDatasetRecommendations } from "@/hooks/useDatasetRecommendations"

export default function Overview() {
  const { activeDataset } = useActiveDataset()
  const recState = useDatasetRecommendations(activeDataset?.dataset_id ?? null)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workspace Overview"
        description="A summary view of your active workspace, backend connection status, and analytical modules."
      />

      <div className="grid gap-4 md:grid-cols-2">
        <ConnectionStatus />

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Dataset Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {activeDataset ? (
              <div>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <span className="font-semibold text-foreground">{activeDataset.filename}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {activeDataset.row_count.toLocaleString()} rows · {activeDataset.column_count.toLocaleString()} columns loaded
                </p>
                <div className="pt-3">
                  <Button asChild size="sm" variant="outline" className="gap-1.5 text-xs">
                    <Link to="/dataset">
                      Manage Dataset <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </Button>
                </div>
              </div>
            ) : (
              <div>
                <p className="text-muted-foreground">No dataset currently loaded.</p>
                <div className="pt-3">
                  <Button asChild size="sm" className="gap-1.5 text-xs">
                    <Link to="/dataset">
                      Upload Dataset <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {activeDataset && (
        <div className="space-y-4">
          {recState.status === "success" && recState.data.kpis.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-semibold text-foreground">
                    Executive Key Performance Indicators
                  </h3>
                </div>
                <span className="text-xs text-muted-foreground font-mono">
                  {activeDataset.row_count.toLocaleString()} rows analyzed
                </span>
              </div>
              <KpiRow kpis={recState.data.kpis} />
            </div>
          )}
        </div>
      )}

      {activeDataset && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Quick Navigation
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link
              to="/explore"
              className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-muted/50"
            >
              <div className="rounded-md bg-blue-500/10 p-2 text-blue-500">
                <Search className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium">Explore & Decisions</p>
                <p className="text-xs text-muted-foreground">Key business questions</p>
              </div>
            </Link>

            <Link
              to="/trends"
              className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-muted/50"
            >
              <div className="rounded-md bg-emerald-500/10 p-2 text-emerald-500">
                <TrendingUp className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium">Trends Intelligence</p>
                <p className="text-xs text-muted-foreground">Domain time-series</p>
              </div>
            </Link>

            <Link
              to="/forecast"
              className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-muted/50"
            >
              <div className="rounded-md bg-purple-500/10 p-2 text-purple-500">
                <LineChart className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium">Forecast</p>
                <p className="text-xs text-muted-foreground">Statistical projections</p>
              </div>
            </Link>

            <Link
              to="/risks"
              className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-muted/50"
            >
              <div className="rounded-md bg-rose-500/10 p-2 text-rose-500">
                <ShieldAlert className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium">Risks & Anomalies</p>
                <p className="text-xs text-muted-foreground">Outlier detection</p>
              </div>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
