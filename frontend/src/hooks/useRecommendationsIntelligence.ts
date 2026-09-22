import { useEffect, useState } from "react"
import { fetchRecommendationsIntelligence } from "@/lib/datasetApi"
import type { RecommendationsIntelligenceResponse } from "@/types/intelligence"

export type RecommendationsState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: RecommendationsIntelligenceResponse }
  | { status: "error"; message: string }

const recommendationsCache = new Map<string, RecommendationsIntelligenceResponse>()

export function useRecommendationsIntelligence(datasetId: string | null) {
  const [state, setState] = useState<RecommendationsState>(() => {
    if (datasetId && recommendationsCache.has(datasetId)) {
      return { status: "success", data: recommendationsCache.get(datasetId)! }
    }
    return { status: datasetId ? "loading" : "idle" }
  })

  useEffect(() => {
    if (!datasetId) {
      setState({ status: "idle" })
      return
    }

    if (recommendationsCache.has(datasetId)) {
      setState({ status: "success", data: recommendationsCache.get(datasetId)! })
      return
    }

    let cancelled = false
    setState({ status: "loading" })

    fetchRecommendationsIntelligence(datasetId)
      .then((data) => {
        recommendationsCache.set(datasetId, data)
        if (!cancelled) setState({ status: "success", data })
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Failed to load recommendations intelligence.",
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [datasetId])

  return state
}
