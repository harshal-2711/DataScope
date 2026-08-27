import { useEffect, useState } from "react"
import { fetchRecommendations } from "@/lib/datasetApi"
import type { RecommendationsResponse } from "@/types/dataset"

type RecommendationsState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: RecommendationsResponse }
  | { status: "error"; message: string }

export function useDatasetRecommendations(datasetId: string | null) {
  const [state, setState] = useState<RecommendationsState>({ status: "idle" })

  useEffect(() => {
    if (!datasetId) {
      setState({ status: "idle" })
      return
    }

    let cancelled = false
    setState({ status: "loading" })

    fetchRecommendations(datasetId)
      .then((data) => {
        if (!cancelled) setState({ status: "success", data })
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Something went wrong.",
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [datasetId])

  return state
}
