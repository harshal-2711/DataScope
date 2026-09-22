import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { ShieldAlert, Loader2, RefreshCw, Upload } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { EmptyState } from "@/components/shared/EmptyState"
import { Button } from "@/components/ui/button"
import { RiskViewer } from "@/components/intelligence/RiskViewer"
import { DomainHeader } from "@/components/intelligence/DomainHeader"
import { useActiveDataset } from "@/context/DatasetContext"
import { useDomainIntelligence } from "@/hooks/useDomainIntelligence"
import { fetchRiskIntelligence } from "@/lib/datasetApi"
import type { RiskIntelligenceResponse } from "@/types/intelligence"

export default function Risks() {
  const { activeDataset } = useActiveDataset()
  const intelState = useDomainIntelligence(activeDataset?.dataset_id ?? null)

  const [riskData, setRiskData] = useState<RiskIntelligenceResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (!activeDataset?.dataset_id) {
      setRiskData(null)
      return
    }

    let isMounted = true
    setIsLoading(true)
    setErrorMsg(null)

    fetchRiskIntelligence(activeDataset.dataset_id)
      .then((res) => {
        if (isMounted) {
          setRiskData(res)
          setIsLoading(false)
        }
      })
      .catch((err) => {
        if (isMounted) {
          setErrorMsg(err?.message || "Failed to load risk intelligence.")
          setIsLoading(false)
        }
      })

    return () => {
      isMounted = false
    }
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
        title="Risk & Anomaly Intelligence"
        description="Universal, domain-aware anomaly detection, severe concentration imbalances, and performance contraction signals surfaced using verified mathematical evidence."
      />

      {!activeDataset ? (
        <div className="space-y-4">
          <EmptyState
            icon={ShieldAlert}
            title="No dataset loaded"
            description="Upload a dataset to evaluate statistical anomalies and operational risk signals."
          />
          <div className="flex justify-center">
            <Button asChild size="sm">
              <Link to="/dataset">Upload a dataset</Link>
            </Button>
          </div>
        </div>
      ) : isSessionExpired ? (
        <div className="space-y-4">
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-6 text-center space-y-3">
            <h4 className="text-sm font-semibold text-amber-500">Dataset Session Expired</h4>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              The dataset in memory has expired or the server was restarted. Please re-upload your file to generate updated risk intelligence.
            </p>
            <Button asChild size="sm" className="gap-2">
              <Link to="/dataset">
                <Upload className="h-4 w-4" />
                Re-upload Dataset
              </Link>
            </Button>
          </div>
        </div>
      ) : isLoading || intelState.status === "loading" ? (
        <div className="flex h-64 items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            Evaluating statistical distributions, outlier fences, and domain risk thresholds...
          </div>
        </div>
      ) : errorMsg && !riskData ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-6 text-center text-sm text-rose-600 space-y-3">
          <div>{errorMsg}</div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              if (activeDataset?.dataset_id) {
                setIsLoading(true)
                setErrorMsg(null)
                fetchRiskIntelligence(activeDataset.dataset_id)
                  .then((res) => {
                    setRiskData(res)
                    setIsLoading(false)
                  })
                  .catch((err) => {
                    setErrorMsg(err?.message || "Failed to load risk intelligence.")
                    setIsLoading(false)
                  })
              }
            }}
            className="gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Retry
          </Button>
        </div>
      ) : (
        <div className="space-y-6">
          {intelState.status === "success" && intelState.data?.domain && (
            <DomainHeader domain={intelState.data.domain} />
          )}
          <RiskViewer data={riskData} risks={riskData?.risks ?? (intelState.status === "success" ? intelState.data.risks : [])} />
        </div>
      )}
    </div>
  )
}

