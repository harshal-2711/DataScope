import type { DatasetSummary, DrilldownResponse, RecommendationsResponse } from "@/types/dataset"
import { getStoredActiveCompanyId, getStoredToken, refreshTokenApi } from "./authApi"

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ""

export function resolveApiUrl(path: string): string {
  if (!path) return ""
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path
  }
  const cleanPath = path.startsWith("/") ? path : `/${path}`
  const base = (API_BASE_URL || "").replace(/\/$/, "")
  return base ? `${base}${cleanPath}` : cleanPath
}

export async function safeFetch(
  url: string,
  init?: RequestInit,
  actionName = "request"
): Promise<Response> {
  const targetUrl = resolveApiUrl(url)
  try {
    const headers = new Headers(init?.headers || {})
    const token = getStoredToken()
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`)
    }
    const companyId = getStoredActiveCompanyId()
    if (companyId && !headers.has("X-Company-Id")) {
      headers.set("X-Company-Id", companyId)
    }

    let res = await fetch(targetUrl, { ...init, headers })

    // If 401 unauthorized, attempt transparent token refresh once
    if (res.status === 401 && token) {
      const refreshed = await refreshTokenApi()
      if (refreshed?.access_token) {
        const retryHeaders = new Headers(init?.headers || {})
        retryHeaders.set("Authorization", `Bearer ${refreshed.access_token}`)
        const activeComp = refreshed.active_company_id || getStoredActiveCompanyId()
        if (activeComp) {
          retryHeaders.set("X-Company-Id", activeComp)
        }
        res = await fetch(targetUrl, { ...init, headers: retryHeaders })
      }
    }

    return res
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

export async function uploadDataset(file: File, signal?: AbortSignal): Promise<DatasetSummary> {
  const formData = new FormData()
  formData.append("file", file)

  const res = await safeFetch(
    `${API_BASE_URL}/api/dataset/upload`,
    {
      method: "POST",
      body: formData,
      signal,
    },
    "dataset upload"
  )

  return unwrapOrThrow<DatasetSummary>(res, "The dataset could not be processed.")
}

export async function fetchRecommendations(
  datasetId: string
): Promise<RecommendationsResponse> {
  const cacheKey = `${datasetId}_recommendations`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
      const res = await safeFetch(
        `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/recommendations`,
        undefined,
        "recommendations"
      )
      const data = await unwrapOrThrow<RecommendationsResponse>(
        res,
        "Recommendations could not be generated for this dataset."
      )
      apiCache.set(cacheKey, data)
      return data
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
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
const inFlightRequests = new Map<string, Promise<any>>()

export function clearClientApiCache(datasetId?: string) {
  if (datasetId) {
    for (const key of Array.from(apiCache.keys())) {
      if (key.startsWith(datasetId)) {
        apiCache.delete(key)
      }
    }
    for (const key of Array.from(inFlightRequests.keys())) {
      if (key.startsWith(datasetId)) {
        inFlightRequests.delete(key)
      }
    }
  } else {
    apiCache.clear()
    inFlightRequests.clear()
  }
}

export async function fetchDomainIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").DomainIntelligenceResponse> {
  const cacheKey = `${datasetId}_intelligence`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
}

export async function fetchDecisionDashboard(
  datasetId: string
): Promise<import("@/types/intelligence").DecisionDashboardResponse> {
  const cacheKey = `${datasetId}_decision_dashboard`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
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
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
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
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
}

export async function fetchDataQualityReport(
  datasetId: string
): Promise<import("@/types/intelligence").DataQualityReportResponse> {
  const cacheKey = `${datasetId}_data_quality`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
}

export async function fetchRiskIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").RiskIntelligenceResponse> {
  const cacheKey = `${datasetId}_risk`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
}

export async function fetchCompetitionIntelligence(
  datasetId: string
): Promise<import("@/types/intelligence").CompetitionIntelligenceResponse> {
  const cacheKey = `${datasetId}_competition`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
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
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
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
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
}

export async function fetchComprehensiveReport(
  datasetId: string,
  sections?: string[]
): Promise<import("@/types/report").ComprehensiveReportResponse> {
  const params = sections && sections.length > 0 ? `?sections=${encodeURIComponent(sections.join(","))}` : ""
  const cacheKey = `${datasetId}_report_${sections?.join("_") || "all"}`
  if (apiCache.has(cacheKey)) {
    return apiCache.get(cacheKey)
  }
  if (inFlightRequests.has(cacheKey)) {
    return inFlightRequests.get(cacheKey)!
  }

  const promise = (async () => {
    try {
      const res = await safeFetch(
        `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/report${params}`,
        undefined,
        "executive comprehensive report"
      )

      const data = await unwrapOrThrow<import("@/types/report").ComprehensiveReportResponse>(
        res,
        "Executive report could not be synthesized for this dataset."
      )
      apiCache.set(cacheKey, data)
      return data
    } finally {
      inFlightRequests.delete(cacheKey)
    }
  })()

  inFlightRequests.set(cacheKey, promise)
  return promise
}

export async function downloadReportDocx(
  datasetId: string,
  sections?: string[],
  customFilename?: string
): Promise<void> {
  const params = sections && sections.length > 0 ? `?sections=${encodeURIComponent(sections.join(","))}` : ""
  const url = `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/report/docx${params}`
  const res = await safeFetch(url, undefined, "DOCX report export")

  if (!res.ok) {
    let errorDetail = "Failed to export Word document."
    try {
      const errJson = await res.json()
      if (errJson?.detail) errorDetail = errJson.detail
    } catch {}
    throw new Error(errorDetail)
  }

  const blob = await res.blob()
  let filename = customFilename
  if (!filename) {
    const disp = res.headers.get("Content-Disposition")
    if (disp && disp.includes("filename=")) {
      const match = disp.match(/filename="?([^"]+)"?/)
      if (match && match[1]) filename = match[1]
    }
  }
  filename = filename || `DataScope_Report_${datasetId.slice(0, 8)}.docx`

  const blobUrl = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(blobUrl)
}

export async function downloadReportPdf(
  datasetId: string,
  sections?: string[],
  customFilename?: string
): Promise<void> {
  const params = sections && sections.length > 0 ? `?sections=${encodeURIComponent(sections.join(","))}` : ""
  const url = `${API_BASE_URL}/api/dataset/${encodeURIComponent(datasetId)}/report/pdf${params}`
  const res = await safeFetch(url, undefined, "PDF report export")

  if (!res.ok) {
    let errorDetail = "Failed to export PDF document."
    try {
      const errJson = await res.json()
      if (errJson?.detail) errorDetail = errJson.detail
    } catch {}
    throw new Error(errorDetail)
  }

  const blob = await res.blob()
  let filename = customFilename
  if (!filename) {
    const disp = res.headers.get("Content-Disposition")
    if (disp && disp.includes("filename=")) {
      const match = disp.match(/filename="?([^"]+)"?/)
      if (match && match[1]) filename = match[1]
    }
  }
  filename = filename || `DataScope_Report_${datasetId.slice(0, 8)}.pdf`

  const blobUrl = window.URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(blobUrl)
}

export interface PersistedDatasetItem {
  id: string
  company_id: string
  name: string
  file_type: string
  row_count: number
  column_count: number
  currency_symbol?: string | null
  domain_id?: string | null
  domain_name?: string | null
  active_version_number: number
  created_at: string
  updated_at: string
  data_source_id?: string | null
  source_type?: string | null
  is_active: boolean
}

export async function fetchCompanyDatasets(): Promise<PersistedDatasetItem[]> {
  const res = await safeFetch(`${API_BASE_URL}/api/data-management/datasets`, undefined, "list datasets")
  return unwrapOrThrow<PersistedDatasetItem[]>(res, "Failed to load company datasets.")
}

export async function fetchActiveCompanyDataset(): Promise<{ active: boolean; dataset: any | null }> {
  const res = await safeFetch(`${API_BASE_URL}/api/data-management/active-dataset`, undefined, "active dataset")
  return unwrapOrThrow<{ active: boolean; dataset: any | null }>(res, "Failed to load active dataset.")
}

export async function activateCompanyDataset(datasetId: string): Promise<any> {
  const res = await safeFetch(
    `${API_BASE_URL}/api/data-management/datasets/${encodeURIComponent(datasetId)}/activate`,
    { method: "POST" },
    "activate dataset"
  )
  return unwrapOrThrow(res, "Failed to activate dataset.")
}






