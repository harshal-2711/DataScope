import type { DatasetSummary, DrilldownResponse, RecommendationsResponse } from "@/types/dataset"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""

async function safeFetch(
  url: string,
  init?: RequestInit,
  actionName = "request"
): Promise<Response> {
  try {
    return await fetch(url, init)
  } catch (err: any) {
    const errorMsg = err?.message ? ` (${err.message})` : ""
    const target = API_BASE_URL || "http://localhost:8000"
    throw new Error(
      `Could not reach the backend API for ${actionName}${errorMsg}. Ensure the server is running on ${target}.`
    )
  }
}

async function unwrapOrThrow<T>(res: Response, fallbackMessage: string): Promise<T> {
  if (!res.ok) {
    let detail = fallbackMessage
    try {
      const body = await res.json()
      if (typeof body?.detail === "string") {
        detail = body.detail
      } else if (typeof body?.message === "string") {
        detail = body.message
      }
    } catch {
      if (res.status === 404) {
        detail = "The requested dataset was not found or has expired from server memory."
      } else if (res.status === 500) {
        detail = "A server processing error occurred while computing analytics."
      } else if (res.status === 504 || res.status === 408) {
        detail = "The analytics calculation request timed out on the server."
      } else if (res.statusText) {
        detail = `${fallbackMessage} (${res.status} ${res.statusText})`
      }
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function uploadDataset(file: File): Promise<DatasetSummary> {
  const formData = new FormData()
  formData.append("file", file)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/upload`,
    {
      method: "POST",
      body: formData,
    },
    "dataset upload"
  )

  return unwrapOrThrow<DatasetSummary>(res, "The dataset could not be processed.")
}

export async function fetchRecommendations(
  datasetId: string
): Promise<RecommendationsResponse> {
  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/recommendations`,
    undefined,
    "recommendations"
  )

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
  const params = new URLSearchParams({ filters: JSON.stringify(filters) })
  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/drilldown?${params}`,
    undefined,
    "drilldown breakdown"
  )

  return unwrapOrThrow<DrilldownResponse>(
    res,
    "Could not load a detailed breakdown for that selection."
  )
}

export async function fetchDomainIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").DomainIntelligenceResponse> {
  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/intelligence`,
    undefined,
    "domain intelligence"
  )

  return unwrapOrThrow<import("@/types/intelligence").DomainIntelligenceResponse>(
    res,
    "Domain intelligence could not be generated for this dataset."
  )
}

export async function fetchDecisionDashboard(
  datasetId: string
): Promise<import("@/types/intelligence").DecisionDashboardResponse> {
  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/decision_dashboard`,
    undefined,
    "decision dashboard"
  )

  return unwrapOrThrow<import("@/types/intelligence").DecisionDashboardResponse>(
    res,
    "Decision dashboard could not be generated for this dataset."
  )
}

export async function fetchTrendsIntelligence(
  datasetId: string,
  granularity: string = "auto",
  metric?: string,
  categoryCol?: string
): Promise<import("@/types/intelligence").TrendsIntelligenceResponse> {
  const params = new URLSearchParams({ granularity })
  if (metric) params.append("metric", metric)
  if (categoryCol) params.append("category_col", categoryCol)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/trends?${params.toString()}`,
    undefined,
    "trends intelligence"
  )

  return unwrapOrThrow<import("@/types/intelligence").TrendsIntelligenceResponse>(
    res,
    "Trends intelligence could not be generated for this dataset."
  )
}

export async function fetchForecast(
  datasetId: string,
  horizon: number = 6,
  metric?: string,
  granularity?: string
): Promise<import("@/types/intelligence").ForecastResponse> {
  const params = new URLSearchParams({ horizon: String(horizon) })
  if (metric) params.append("metric", metric)
  if (granularity) params.append("granularity", granularity)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/forecast?${params.toString()}`,
    undefined,
    "time-series forecast"
  )

  return unwrapOrThrow<import("@/types/intelligence").ForecastResponse>(
    res,
    "Forecast could not be generated for this dataset."
  )
}

export async function fetchDataQualityReport(
  datasetId: string
): Promise<import("@/types/intelligence").DataQualityReportResponse> {
  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/data_quality`,
    undefined,
    "data quality validation"
  )

  return unwrapOrThrow<import("@/types/intelligence").DataQualityReportResponse>(
    res,
    "Data quality report could not be generated for this dataset."
  )
}
