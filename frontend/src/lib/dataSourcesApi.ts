/**
 * Data Sources & Live Data Connection API Client for DataScope SaaS
 */
import { safeFetch } from './datasetApi';

export interface DataSource {
  id: string;
  company_id: string;
  dataset_id?: string;
  name: string;
  source_type: 'postgres' | 'mysql' | 'rest_api' | 'google_sheets' | 'file_upload' | 'manual_entry';
  status: 'active' | 'paused' | 'syncing' | 'error' | 'configured';
  sync_frequency: 'manual' | 'hourly' | 'daily' | 'weekly';
  is_paused: boolean;
  last_sync_at?: string;
  next_sync_at?: string;
  last_error_message?: string;
  total_records_synced: number;
  created_at: string;
  config_sanitized: Record<string, any>;
}

export interface DataSyncJob {
  id: string;
  data_source_id: string;
  company_id: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  sync_type: string;
  records_added: number;
  records_updated: number;
  records_rejected: number;
  error_message?: string;
  log_output?: string;
  started_at: string;
  completed_at?: string;
}

export interface TestConnectionPayload {
  source_type: string;
  config: Record<string, any>;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  details?: Record<string, any>;
}

export interface TableItem {
  schema?: string;
  name: string;
  full_name: string;
  type?: string;
}

export interface DiscoverTablesResult {
  success: boolean;
  tables: TableItem[];
  error?: string;
}

export interface PreviewDataResult {
  success: boolean;
  row_count_sample?: number;
  column_count?: number;
  columns?: string[];
  dtypes?: Record<string, string>;
  preview?: Record<string, any>[];
  error?: string;
}

export interface ImportDatasetResult {
  dataset_id: string;
  filename: string;
  name: string;
  file_type: string;
  row_count: number;
  column_count: number;
  columns: string[];
  dtypes: Record<string, string>;
  inferred_columns?: any[];
  diagnostics?: any;
  detected_currency?: string | null;
  preview: Record<string, any>[];
  message: string;
}

async function unwrapJson<T>(res: Response, fallbackError: string): Promise<T> {
  if (!res.ok) {
    let detail = fallbackError
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') {
        detail = body.detail
      } else if (typeof body?.message === 'string') {
        detail = body.message
      }
    } catch {
      detail = `${fallbackError} (${res.status} ${res.statusText})`
    }
    if (res.status === 401 && (detail === "Invalid or expired access token." || detail.includes("Authentication required"))) {
      detail = "Your DataScope user session has expired. Please log in or refresh your session."
    }
    throw new Error(detail)
  }
  return res.json()
}

export const dataSourcesApi = {
  async list(): Promise<DataSource[]> {
    try {
      const res = await safeFetch('/api/data-sources')
      const data = await unwrapJson<DataSource[]>(res, 'Failed to fetch data sources.')
      return Array.isArray(data) ? data : []
    } catch (err: any) {
      console.warn('Could not list data sources:', err?.message || err)
      return []
    }
  },

  async get(id: string): Promise<DataSource> {
    const res = await safeFetch(`/api/data-sources/${id}`)
    return unwrapJson<DataSource>(res, 'Failed to fetch data source details.')
  },

  async create(payload: {
    name: string
    source_type: string
    sync_frequency: string
    config: Record<string, any>
    dataset_id?: string
  }): Promise<DataSource> {
    const res = await safeFetch('/api/data-sources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    return unwrapJson<DataSource>(res, 'Failed to create data source.')
  },

  async update(id: string, payload: {
    name?: string
    sync_frequency?: string
    config?: Record<string, any>
    is_paused?: boolean
  }): Promise<DataSource> {
    const res = await safeFetch(`/api/data-sources/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    return unwrapJson<DataSource>(res, 'Failed to update data source.')
  },

  async testConnection(payload: TestConnectionPayload): Promise<TestConnectionResult> {
    try {
      const res = await safeFetch('/api/data-sources/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      return unwrapJson<TestConnectionResult>(res, 'Failed to test connection.')
    } catch (err: any) {
      return {
        success: false,
        message: err?.message || 'Connection test failed.',
      }
    }
  },

  async discoverTables(payload: TestConnectionPayload): Promise<DiscoverTablesResult> {
    try {
      const res = await safeFetch('/api/data-sources/tables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      return unwrapJson<DiscoverTablesResult>(res, 'Failed to discover tables.')
    } catch (err: any) {
      return {
        success: false,
        tables: [],
        error: err?.message || 'Table discovery failed.',
      }
    }
  },

  async previewData(payload: {
    source_type: string
    config: Record<string, any>
    limit?: number
  }): Promise<PreviewDataResult> {
    try {
      const res = await safeFetch('/api/data-sources/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      return unwrapJson<PreviewDataResult>(res, 'Failed to preview data.')
    } catch (err: any) {
      return {
        success: false,
        error: err?.message || 'Data preview failed.',
      }
    }
  },

  async importToDataset(payload: {
    connection_name: string
    source_type: string
    config: Record<string, any>
  }): Promise<ImportDatasetResult> {
    const res = await safeFetch('/api/data-sources/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    return unwrapJson<ImportDatasetResult>(res, 'Failed to import data into dataset.')
  },

  async testExisting(id: string): Promise<TestConnectionResult> {
    try {
      const res = await safeFetch(`/api/data-sources/${id}/test`, {
        method: 'POST',
      })
      return unwrapJson<TestConnectionResult>(res, 'Failed to test existing data source.')
    } catch (err: any) {
      return {
        success: false,
        message: err?.message || 'Connection test failed.',
      }
    }
  },

  async syncNow(id: string): Promise<any> {
    const res = await safeFetch(`/api/data-sources/${id}/sync`, {
      method: 'POST',
    })
    return unwrapJson<any>(res, 'Failed to trigger sync.')
  },

  async pause(id: string): Promise<DataSource> {
    const res = await safeFetch(`/api/data-sources/${id}/pause`, {
      method: 'POST',
    })
    return unwrapJson<DataSource>(res, 'Failed to pause sync.')
  },

  async resume(id: string): Promise<DataSource> {
    const res = await safeFetch(`/api/data-sources/${id}/resume`, {
      method: 'POST',
    })
    return unwrapJson<DataSource>(res, 'Failed to resume sync.')
  },

  async delete(id: string): Promise<{ message: string }> {
    const res = await safeFetch(`/api/data-sources/${id}`, {
      method: 'DELETE',
    })
    return unwrapJson<{ message: string }>(res, 'Failed to delete data source.')
  },

  async getJobs(id: string): Promise<DataSyncJob[]> {
    try {
      const res = await safeFetch(`/api/data-sources/${id}/jobs`)
      const data = await unwrapJson<DataSyncJob[]>(res, 'Failed to fetch sync jobs.')
      return Array.isArray(data) ? data : []
    } catch (err: any) {
      console.warn('Could not list sync jobs:', err?.message || err)
      return []
    }
  },
}
