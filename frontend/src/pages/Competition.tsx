import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { Target, Loader2, RefreshCw, Upload } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { CompetitionViewer } from "@/components/intelligence/CompetitionViewer"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDomainIntelligence } from "@/hooks/useDomainIntelligence"
import { fetchCompetitionIntelligence } from "@/lib/datasetApi"
import type { CompetitionIntelligenceResponse } from "@/types/intelligence"

export default function Competition() {
  const { activeDataset, removeDataset } = useActiveDataset()
  const intelState = useDomainIntelligence(activeDataset?.dataset_id ?? null)

  const [compData, setCompData] = useState<CompetitionIntelligenceResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const loadData = () => {
    if (!activeDataset?.dataset_id) {
      setCompData(null)
      return
    }

    setIsLoading(true)
    setErrorMsg(null)

    fetchCompetitionIntelligence(activeDataset.dataset_id)
      .then((res) => {
        setCompData(res)
        setIsLoading(false)
      })
      .catch((err) => {
        setErrorMsg(err?.message || "Failed to load competition intelligence.")
        setIsLoading(false)
      })
  }

  useEffect(() => {
    loadData()
  }, [activeDataset?.dataset_id])

  const intelErrorMsg = intelState.status === "error" ? intelState.message : ""
  const isSessionExpired =
    errorMsg?.toLowerCase().includes("not found") ||
    errorMsg?.toLowerCase().includes("expired") ||
    intelErrorMsg.toLowerCase().includes("not found") ||
    intelErrorMsg.toLowerCase().includes("expired")

  return (
    <div className="space-y-6">
      <PageHeader
        title="Competition & Benchmarking"
        description="Universal, domain-aware cohort comparisons, segment rankings, performance spreads, and competitive gap analysis calculated strictly from verified dataset evidence."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={Target}
            title="No dataset loaded"
            description="Upload a dataset first to evaluate competitive rankings, performance spreads, and cohort gaps."
          />
          <div className="flex justify-center">
            <Button asChild size="sm">
              <Link to="/dataset">Upload a dataset</Link>
            </Button>
          </div>
        </div>
      ) : isSessionExpired ? (
        <div className="space-y-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-6 text-center">
          <h3 className="text-lg font-semibold text-foreground">
            Dataset Session Expired
          </h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            The backend server restarted or the active dataset in-memory session has expired. Please re-upload your dataset to continue.
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <Button
              variant="default"
              size="sm"
              onClick={() => {
                removeDataset()
              }}
              asChild
            >
              <Link to="/dataset">
                <Upload className="h-4 w-4 mr-2" />
                Re-upload Dataset
              </Link>
            </Button>
          </div>
        </div>
      ) : isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">
            Evaluating cohort distributions and ranking competitive segments...
          </p>
        </div>
      ) : errorMsg ? (
        <div className="space-y-4 rounded-xl border border-destructive/30 bg-destructive/10 p-6 text-center">
          <h3 className="text-lg font-semibold text-foreground">
            Unable to Load Competition Intelligence
          </h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            {errorMsg}
          </p>
          <div className="flex justify-center gap-3 pt-2">
            <Button variant="outline" size="sm" onClick={loadData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </div>
      ) : compData ? (
        <div className="space-y-6">
          {intelState.status === "success" && (
            <DomainHeader domain={intelState.data.domain} />
          )}

          <CompetitionViewer
            data={compData}
            datasetId={activeDataset.dataset_id}
            onBenchmarkUpdated={(updated) => setCompData(updated)}
          />
        </div>
      ) : null}
    </div>
  )
}
