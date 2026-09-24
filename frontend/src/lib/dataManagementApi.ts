import { safeFetch } from "@/lib/datasetApi"

const API_BASE = "/api/data-management"

export interface ColumnSchema {
  name: string
  dtype: string
  semantic_role: string
  is_numeric: boolean
  is_datetime: boolean
  is_categorical: boolean
}

export interface RecordItem {
  record_id: string
  row_index: number
  data: Record<string, any>
  updated_at: string
}


export interface PaginatedRecordsResponse {
  dataset_id: string
  dataset_name: string
  total_records: number
  page: number
  page_size: number
  total_pages: number
  current_version: number
  columns: ColumnSchema[]
  records: RecordItem[]
}

export interface VersionHistoryItem {
  id: string
  version_number: number
  change_summary: string
  row_count: number
  col_count: number
  created_at: string
  created_by?: string | null
  is_active: boolean
}

export async function fetchPaginatedRecords(
  datasetId: string,
  page = 1,
  pageSize = 25,
  search?: string
): Promise<PaginatedRecordsResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (search?.trim()) {
    params.set("search", search.trim())
  }

  const res = await safeFetch(`${API_BASE}/datasets/${datasetId}/records?${params.toString()}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to load records.")
  }
  return res.json()
}

export async function addRecord(datasetId: string, data: Record<string, any>): Promise<RecordItem> {
  const res = await safeFetch(`${API_BASE}/datasets/${datasetId}/records`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to add record.")
  }
  return res.json()
}

export async function updateRecord(datasetId: string, recordId: string, data: Record<string, any>): Promise<RecordItem> {
  const res = await safeFetch(`${API_BASE}/datasets/${datasetId}/records/${recordId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to update record.")
  }
  return res.json()
}

export async function deleteRecord(datasetId: string, recordId: string): Promise<void> {
  const res = await safeFetch(`${API_BASE}/datasets/${datasetId}/records/${recordId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to delete record.")
  }
}

export async function bulkImportRecords(
  datasetId: string,
  records: Array<Record<string, any>>,
  changeSummary?: string
): Promise<{ imported_count: number; total_records: number; new_version_number: number; message: string }> {
  const res = await safeFetch(`${API_BASE}/datasets/${datasetId}/bulk-import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ records, change_summary: changeSummary }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to bulk import records.")
  }
  return res.json()
}

export async function fetchVersionHistory(datasetId: string): Promise<VersionHistoryItem[]> {
  const res = await safeFetch(`${API_BASE}/datasets/${datasetId}/versions`)
  if (!res.ok) {
    throw new Error("Failed to load version history.")
  }
  return res.json()
}

export async function rollbackDatasetVersion(datasetId: string, versionNumber: number): Promise<void> {
  const res = await safeFetch(`${API_BASE}/datasets/${datasetId}/rollback/${versionNumber}`, {
    method: "POST",
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || "Failed to rollback dataset version.")
  }
}
