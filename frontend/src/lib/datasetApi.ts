import type { DatasetSummary, DrilldownResponse, RecommendationsResponse } from "@/types/dataset"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

async function unwrapOrThrow<T>(res: Response, fallbackMessage: string): Promise<T> {
  if (!res.ok) {
    let detail = fallbackMessage
    try {
      const body = await res.json()
      if (typeof body?.detail === "string") detail = body.detail
    } catch {
      // response wasn't JSON — fall back to the default message
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function uploadDataset(file: File): Promise<DatasetSummary> {
  const formData = new FormData()
  formData.append("file", file)

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}/api/dataset/upload`, {
      method: "POST",
      body: formData,
    })
  } catch {
    throw new Error(
      "Could not reach the backend. Make sure the server is running on " +
        API_BASE_URL
    )
  }

  return unwrapOrThrow<DatasetSummary>(res, "The dataset could not be processed.")
}

export async function fetchRecommendations(
  datasetId: string
): Promise<RecommendationsResponse> {
  let res: Response
  try {
    res = await fetch(
      `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/recommendations`
    )
  } catch {
    throw new Error(
      "Could not reach the backend. Make sure the server is running on " +
        API_BASE_URL
    )
  }

  return unwrapOrThrow<RecommendationsResponse>(
    res,
    "Recommendations could not be generated for this dataset."
  )
}

export interface DrilldownFilter {
  dimension: string
  value: string
}

export async function fetchDrilldown(
  datasetId: string,
  filters: DrilldownFilter[]
): Promise<DrilldownResponse> {
  if (filters.length === 0) {
    throw new Error("At least one filter is required for a drill-down.")
  }
  let res: Response
  const params = new URLSearchParams({ filters: JSON.stringify(filters) })
  try {
    res = await fetch(
      `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/drilldown?${params}`
    )
  } catch {
    throw new Error(
      "Could not reach the backend. Make sure the server is running on " +
        API_BASE_URL
    )
  }

  return unwrapOrThrow<DrilldownResponse>(
    res,
    "Could not load a detailed breakdown for that selection."
  )
}

export async function fetchDomainIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").DomainIntelligenceResponse> {
  let res: Response
  try {
    res = await fetch(
      `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/intelligence`
    )
  } catch {
    throw new Error(
      "Could not reach the backend. Make sure the server is running on " +
        API_BASE_URL
    )
  }

  return unwrapOrThrow<import("@/types/intelligence").DomainIntelligenceResponse>(
    res,
    "Domain intelligence could not be generated for this dataset."
  )
}

export async function fetchDecisionDashboard(
  datasetId: string
): Promise<import("@/types/intelligence").DecisionDashboardResponse> {
  let res: Response
  try {
    res = await fetch(
      `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/decision_dashboard`
    )
  } catch {
    throw new Error(
      "Could not reach the backend. Make sure the server is running on " +
        API_BASE_URL
    )
  }

  return unwrapOrThrow<import("@/types/intelligence").DecisionDashboardResponse>(
    res,
    "Decision dashboard could not be generated for this dataset."
  )
}
