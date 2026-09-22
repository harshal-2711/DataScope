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

const apiCache = new Map<string, any>()

export function clearClientApiCache(datasetId?: string) {
  if (datasetId) {
    for (const key of Array.from(apiCache.keys())) {
      if (key.startsWith(datasetId)) {
        apiCache.delete(key)
      }
    }
  } else {
    apiCache.clear()
  }
}

export async function fetchDomainIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").DomainIntelligenceResponse> {
  const cacheKey = `${datasetId}_intelligence`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/intelligence`,
    undefined,
    "domain intelligence"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").DomainIntelligenceResponse>(
    res,
    "Domain intelligence could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}

export async function fetchDecisionDashboard(
  datasetId: string
): Promise<import("@/types/intelligence").DecisionDashboardResponse> {
  const cacheKey = `${datasetId}_decision_dashboard`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/decision_dashboard`,
    undefined,
    "decision dashboard"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").DecisionDashboardResponse>(
    res,
    "Decision dashboard could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}

export async function fetchTrendsIntelligence(
  datasetId: string,
  granularity: string = "auto",
  metric?: string,
  categoryCol?: string
): Promise<import("@/types/intelligence").TrendsIntelligenceResponse> {
  const cacheKey = `${datasetId}_trends_${granularity}_${metric || ""}_${categoryCol || ""}`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const params = new URLSearchParams({ granularity })
  if (metric) params.append("metric", metric)
  if (categoryCol) params.append("category_col", categoryCol)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/trends?${params.toString()}`,
    undefined,
    "trends intelligence"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").TrendsIntelligenceResponse>(
    res,
    "Trends intelligence could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}

export async function fetchForecast(
  datasetId: string,
  horizon: number = 7,
  metric?: string,
  granularity?: string,
  method?: string
): Promise<import("@/types/intelligence").ForecastResponse> {
  const cacheKey = `${datasetId}_forecast_${horizon}_${metric || ""}_${granularity || ""}_${method || ""}`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const params = new URLSearchParams({ horizon: String(horizon) })
  if (metric) params.append("metric", metric)
  if (granularity) params.append("granularity", granularity)
  if (method) params.append("method", method)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/forecast?${params.toString()}`,
    undefined,
    "time-series forecast"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").ForecastResponse>(
    res,
    "Forecast could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}

export async function fetchDataQualityReport(
  datasetId: string
): Promise<import("@/types/intelligence").DataQualityReportResponse> {
  const cacheKey = `${datasetId}_data_quality`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/data_quality`,
    undefined,
    "data quality validation"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").DataQualityReportResponse>(
    res,
    "Data quality report could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}

export async function fetchRiskIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").RiskIntelligenceResponse> {
  const cacheKey = `${datasetId}_risk`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/risk`,
    undefined,
    "risk intelligence"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").RiskIntelligenceResponse>(
    res,
    "Risk intelligence could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}

export async function fetchCompetitionIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").CompetitionIntelligenceResponse> {
  const cacheKey = `${datasetId}_competition`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/competition`,
    undefined,
    "competition intelligence"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").CompetitionIntelligenceResponse>(
    res,
    "Competition intelligence could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}

export async function previewMarketBenchmark(
  datasetId: string,
  file: File
): Promise<import("@/types/intelligence").MarketBenchmarkPreview> {
  const formData = new FormData()
  formData.append("file", file)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/benchmark/preview`,
    {
      method: "POST",
      body: formData,
    },
    "market benchmark preview"
  )

  return unwrapOrThrow<import("@/types/intelligence").MarketBenchmarkPreview>(
    res,
    "Could not validate the benchmark file."
  )
}

export async function applyMarketBenchmark(
  datasetId: string,
  file: File
): Promise<import("@/types/intelligence").CompetitionIntelligenceResponse> {
  const formData = new FormData()
  formData.append("file", file)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/benchmark/apply`,
    {
      method: "POST",
      body: formData,
    },
    "market benchmark apply"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").CompetitionIntelligenceResponse>(
    res,
    "Could not apply the benchmark file."
  )
  clearClientApiCache(datasetId)
  return data
}

export async function removeMarketBenchmark(
  datasetId: string
): Promise<import("@/types/intelligence").CompetitionIntelligenceResponse> {
  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/benchmark`,
    {
      method: "DELETE",
    },
    "market benchmark remove"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").CompetitionIntelligenceResponse>(
    res,
    "Could not remove the benchmark."
  )
  clearClientApiCache(datasetId)
  return data
}

export async function fetchRecommendationsIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").RecommendationsIntelligenceResponse> {
  const cacheKey = `${datasetId}_recommendations_intelligence`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/recommendations_intelligence`,
    undefined,
    "recommendations intelligence"
  )

  const data = await unwrapOrThrow<import("@/types/intelligence").RecommendationsIntelligenceResponse>(
    res,
    "Evidence-based recommendations could not be generated for this dataset."
  )
  apiCache.set(cacheKey, data)
  return data
}




