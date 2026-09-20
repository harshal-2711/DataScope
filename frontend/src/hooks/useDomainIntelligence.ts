import { useEffect, useState } from "react"
import { fetchDomainIntelligence } from "@/lib/datasetApi"
import type { DomainIntelligenceResponse } from "@/types/intelligence"

export type DomainIntelligenceState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: DomainIntelligenceResponse }
  | { status: "error"; message: string }

export function useDomainIntelligence(datasetId: string | null) {
  const [state, setState] = useState<DomainIntelligenceState>({ status: "idle" })

  useEffect(() => {
    if (!datasetId) {
      setState({ status: "idle" })
      return
    }

    let cancelled = false
    setState({ status: "loading" })

    fetchDomainIntelligence(datasetId)
      .then((data) => {
        if (!cancelled) setState({ status: "success", data })
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Failed to load domain intelligence.",
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [datasetId])

  return state
}
