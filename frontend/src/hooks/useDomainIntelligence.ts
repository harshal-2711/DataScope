import { useEffect, useState } from "react"
import { fetchDomainIntelligence } from "@/lib/datasetApi"
import type { DomainIntelligenceResponse } from "@/types/intelligence"

export type DomainIntelligenceState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: DomainIntelligenceResponse }
  | { status: "error"; message: string }

const domainIntelligenceCache = new Map<string, DomainIntelligenceResponse>()

export function useDomainIntelligence(datasetId: string | null) {
  const [state, setState] = useState<DomainIntelligenceState>(() => {
    if (datasetId && domainIntelligenceCache.has(datasetId)) {
      return { status: "success", data: domainIntelligenceCache.get(datasetId)! }
    }
    return { status: datasetId ? "loading" : "idle" }
  })

  useEffect(() => {
    if (!datasetId) {
      setState({ status: "idle" })
      return
    }

    if (domainIntelligenceCache.has(datasetId)) {
      setState({ status: "success", data: domainIntelligenceCache.get(datasetId)! })
      return
    }

    let cancelled = false
    setState({ status: "loading" })

    fetchDomainIntelligence(datasetId)
      .then((data) => {
        domainIntelligenceCache.set(datasetId, data)
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
