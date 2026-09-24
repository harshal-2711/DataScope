import React, { useEffect, useState, useRef } from "react"
import { useNavigate } from "react-router-dom"
import {
  Database,
  RefreshCw,
  Plus,
  Play,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Server,
  Globe,
  Layers,
  X,
  FileSpreadsheet,
  ArrowRight,
  ShieldCheck,
  Eye,
  Sparkles,
  UploadCloud,
  ArrowLeft,
} from "lucide-react"
import {
  dataSourcesApi,
  type DataSource,
  type DataSyncJob,
  type TableItem,
  type TestConnectionResult,
  type PreviewDataResult,
} from "@/lib/dataSourcesApi"
import { useAuth } from "@/context/AuthContext"
import { useActiveDataset } from "@/context/DatasetContext"
import { PageHeader } from "@/components/shared/PageHeader"
import { Button } from "@/components/ui/button"

export type SourceType = "csv" | "excel" | "postgres" | "mysql" | "rest_api" | "google_sheets"

interface ConnectorCard {
  type: SourceType
  title: string
  subtitle: string
  icon: React.ComponentType<{ className?: string }>
  badge: string
}

const CONNECTOR_CARDS: ConnectorCard[] = [
  {
    type: "csv",
    title: "CSV Upload",
    subtitle: "Direct CSV file ingestion with automatic delimiter and schema detection",
    icon: FileText,
    badge: "Fast Ingest",
  },
  {
    type: "excel",
    title: "Excel / XLSX",
    subtitle: "Multi-sheet workbook ingestion with sheet selection and header validation",
    icon: FileSpreadsheet,
    badge: "Spreadsheet",
  },
  {
    type: "postgres",
    title: "PostgreSQL",
    subtitle: "Enterprise relational database with schema introspection and SSL support",
    icon: Server,
    badge: "Direct SQL",
  },
  {
    type: "mysql",
    title: "MySQL",
    subtitle: "High-performance transactional database connector with table inspection",
    icon: Database,
    badge: "Direct SQL",
  },
  {
    type: "rest_api",
    title: "REST API Endpoint",
    subtitle: "Ingest live JSON and CSV HTTP streams with custom headers and auth",
    icon: Globe,
    badge: "Live API",
  },
  {
    type: "google_sheets",
    title: "Google Sheets",
    subtitle: "Connect shareable Google Spreadsheets with real-time sync capabilities",
    icon: Layers,
    badge: "Cloud Sheet",
  },
]

export default function ConnectDataSource() {
  const { activeCompany } = useAuth()
  const { setActiveDataset, analyzeFile } = useActiveDataset()
  const navigate = useNavigate()

  const [sources, setSources] = useState<DataSource[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // Selected connector & wizard
  const [selectedType, setSelectedType] = useState<SourceType>("postgres")
  const [isWizardOpen, setIsWizardOpen] = useState(false)

  // Form states
  const [connectionName, setConnectionName] = useState("")
  const [syncFrequency, setSyncFrequency] = useState<"manual" | "hourly" | "daily" | "weekly">("manual")

  // File Upload State (CSV & Excel)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [isAnalyzingFile, setIsAnalyzingFile] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  // Postgres & MySQL fields
  const [host, setHost] = useState("")
  const [port, setPort] = useState("5432")
  const [database, setDatabase] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [sslmode, setSslmode] = useState("prefer")
  const [selectedTable, setSelectedTable] = useState("")
  const [customQuery, setCustomQuery] = useState("")
  const [useCustomQuery, setUseCustomQuery] = useState(false)

  // REST API fields
  const [apiUrl, setApiUrl] = useState("")
  const [apiMethod, setApiMethod] = useState<"GET" | "POST">("GET")
  const [authType, setAuthType] = useState<"none" | "bearer" | "api_key">("none")
  const [authToken, setAuthToken] = useState("")
  const [apiKeyHeader, setApiKeyHeader] = useState("X-API-Key")
  const [apiKeyValue, setApiKeyValue] = useState("")
  const [apiHeaders, setApiHeaders] = useState("")
  const [apiBody, setApiBody] = useState("")

  // Google Sheets fields
  const [sheetUrl, setSheetUrl] = useState("")
  const [sheetGid, setSheetGid] = useState("")

  // Tables discovery & preview states
  const [discoveredTables, setDiscoveredTables] = useState<TableItem[]>([])
  const [loadingTables, setLoadingTables] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestConnectionResult | null>(null)
  const [previewing, setPreviewing] = useState(false)
  const [previewData, setPreviewData] = useState<PreviewDataResult | null>(null)
  const [saving, setSaving] = useState(false)
  const [importing, setImporting] = useState(false)
  const [actionNotice, setActionNotice] = useState<{ text: string; type: "success" | "error" } | null>(null)

  // Sync jobs logs modal
  const [selectedLogsSource, setSelectedLogsSource] = useState<DataSource | null>(null)
  const [jobs, setJobs] = useState<DataSyncJob[]>([])
  const [loadingJobs, setLoadingJobs] = useState(false)

  const loadSources = async () => {
    try {
      setRefreshing(true)
      const data = await dataSourcesApi.list()
      setSources(Array.isArray(data) ? data : [])
    } catch (err: any) {
      console.warn("Failed to load data sources:", err)
      setSources([])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadSources()
  }, [activeCompany?.company_id])

  const resetForm = (type: SourceType) => {
    setSelectedType(type)
    setConnectionName("")
    setSelectedFile(null)
    setFileError(null)
    setHost("")
    setPort(type === "postgres" ? "5432" : type === "mysql" ? "3306" : "")
    setDatabase("")
    setUsername("")
    setPassword("")
    setSelectedTable("")
    setCustomQuery("")
    setUseCustomQuery(false)
    setApiUrl("")
    setApiMethod("GET")
    setAuthType("none")
    setAuthToken("")
    setApiHeaders("")
    setApiBody("")
    setSheetUrl("")
    setSheetGid("")
    setDiscoveredTables([])
    setTestResult(null)
    setPreviewData(null)
  }

  const handleSelectConnector = (type: SourceType) => {
    resetForm(type)
    setIsWizardOpen(true)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setFileError(null)

    // Validation
    const ext = file.name.split(".").pop()?.toLowerCase() || ""
    if (selectedType === "csv" && ext !== "csv") {
      setFileError("Please select a valid .csv file.")
      return
    }
    if (selectedType === "excel" && !["xlsx", "xls"].includes(ext)) {
      setFileError("Please select a valid Excel (.xlsx or .xls) file.")
      return
    }
    if (file.size > 50 * 1024 * 1024) {
      setFileError("File size exceeds 50 MB limit.")
      return
    }
    if (file.size === 0) {
      setFileError("File is empty (0 bytes).")
      return
    }

    setSelectedFile(file)
    if (!connectionName) {
      setConnectionName(file.name.replace(/\.[^/.]+$/, ""))
    }
  }

  const handleFileAnalyze = async () => {
    if (!selectedFile) return
    setIsAnalyzingFile(true)
    try {
      await analyzeFile(selectedFile)
      setActionNotice({
        text: `Successfully uploaded and analyzed ${selectedFile.name}!`,
        type: "success",
      })
      setIsWizardOpen(false)
      navigate("/overview")
    } catch (err: any) {
      setFileError(err?.message || "Failed to analyze dataset.")
    } finally {
      setIsAnalyzingFile(false)
    }
  }

  const buildConfigObject = () => {
    const cfg: Record<string, any> = {}

    if (selectedType === "postgres" || selectedType === "mysql") {
      cfg.host = host.trim()
      cfg.port = parseInt(port) || (selectedType === "postgres" ? 5432 : 3306)
      cfg.database = database.trim()
      cfg.username = username.trim()
      cfg.password = password
      if (selectedType === "postgres") cfg.sslmode = sslmode
      if (useCustomQuery && customQuery.trim()) {
        cfg.custom_query = customQuery.trim()
      } else if (selectedTable) {
        cfg.table_name = selectedTable
      }
    } else if (selectedType === "rest_api") {
      cfg.url = apiUrl.trim()
      cfg.method = apiMethod
      cfg.auth_type = authType
      if (authType === "bearer" && authToken.trim()) cfg.token = authToken.trim()
      if (authType === "api_key" && apiKeyValue.trim()) {
        cfg.api_key_header = apiKeyHeader.trim() || "X-API-Key"
        cfg.api_key = apiKeyValue.trim()
      }
      if (apiHeaders.trim()) {
        try {
          cfg.headers = JSON.parse(apiHeaders)
        } catch {
          // ignore parsing error
        }
      }
      if (apiMethod === "POST" && apiBody.trim()) {
        try {
          cfg.body = JSON.parse(apiBody)
        } catch {
          cfg.body = apiBody.trim()
        }
      }
    } else if (selectedType === "google_sheets") {
      cfg.sheet_url = sheetUrl.trim()
      if (sheetGid.trim()) cfg.sheet_gid = sheetGid.trim()
      if (selectedTable.trim()) cfg.table_name = selectedTable.trim()
    }

    return cfg
  }

  const handleTestConnection = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const config = buildConfigObject()
      const res = await dataSourcesApi.testConnection({
        source_type: selectedType,
        config,
      })
      setTestResult(res)

      if (res.success) {
        if (res.details?.title && !connectionName.trim()) {
          setConnectionName(res.details.title)
        }
        if (selectedType === "postgres" || selectedType === "mysql" || selectedType === "google_sheets") {
          handleDiscoverTables()
        }
      }
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.message || "Failed to test connection.",
      })
    } finally {
      setTesting(false)
    }
  }

  const handleDiscoverTables = async () => {
    setLoadingTables(true)
    try {
      const config = buildConfigObject()
      const res = await dataSourcesApi.discoverTables({
        source_type: selectedType,
        config,
      })
      if (res.success && res.tables) {
        setDiscoveredTables(res.tables)
        if (res.tables.length > 0 && !selectedTable) {
          setSelectedTable(res.tables[0].full_name)
          if ((res.tables[0] as any).gid) {
            setSheetGid((res.tables[0] as any).gid)
          }
        }
      }
    } catch (err) {
      console.warn("Could not list tables:", err)
    } finally {
      setLoadingTables(false)
    }
  }

  const handlePreviewData = async () => {
    setPreviewing(true)
    setPreviewData(null)
    try {
      const config = buildConfigObject()
      const res = await dataSourcesApi.previewData({
        source_type: selectedType,
        config,
        limit: 15,
      })
      setPreviewData(res)
    } catch (err: any) {
      setPreviewData({
        success: false,
        error: err.message || "Failed to fetch sample data.",
      })
    } finally {
      setPreviewing(false)
    }
  }

  const handleSaveConnection = async () => {
    if (!connectionName.trim()) {
      setActionNotice({ text: "Please enter a connection name.", type: "error" })
      return
    }
    setSaving(true)
    try {
      const config = buildConfigObject()
      await dataSourcesApi.create({
        name: connectionName.trim(),
        source_type: selectedType,
        sync_frequency: syncFrequency,
        config,
      })
      setActionNotice({ text: `Connection '${connectionName}' saved successfully!`, type: "success" })
      setIsWizardOpen(false)
      loadSources()
    } catch (err: any) {
      setActionNotice({ text: err.message || "Failed to save connection.", type: "error" })
    } finally {
      setSaving(false)
    }
  }

  const handleImportAndAnalyze = async () => {
    const name = connectionName.trim() || `${selectedType.toUpperCase()} Dataset`
    setImporting(true)
    try {
      const config = buildConfigObject()
      const res = await dataSourcesApi.importToDataset({
        connection_name: name,
        source_type: selectedType,
        config,
      })
      if (res.dataset_id) {
        setActiveDataset({
          dataset_id: res.dataset_id,
          filename: res.filename,
          file_type: (res.file_type === "xlsx" || res.file_type === "xls") ? res.file_type : "csv",
          row_count: res.row_count,
          column_count: res.column_count,
          columns: res.columns,
          dtypes: res.dtypes,
          inferred_columns: res.inferred_columns,
          diagnostics: res.diagnostics,
          detected_currency: res.detected_currency,
          preview: res.preview,
        })
        setActionNotice({ text: `Ingested ${res.row_count.toLocaleString()} records. Launching analytics!`, type: "success" })
        setIsWizardOpen(false)
        navigate("/overview")
      }
    } catch (err: any) {
      setActionNotice({ text: err.message || "Import failed.", type: "error" })
    } finally {
      setImporting(false)
    }
  }

  const handleManualSync = async (sourceId: string) => {
    try {
      setActionNotice({ text: "Triggering data sync...", type: "success" })
      const res = await dataSourcesApi.syncNow(sourceId)
      if (res.status === "success") {
        setActionNotice({ text: `Successfully synced ${res.records_synced.toLocaleString()} records!`, type: "success" })
        loadSources()
      } else {
        setActionNotice({ text: res.error || "Sync failed.", type: "error" })
      }
    } catch (err: any) {
      setActionNotice({ text: err.message || "Sync execution error.", type: "error" })
    }
  }

  const handleDeleteSource = async (sourceId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete data connection '${name}'?`)) return
    try {
      await dataSourcesApi.delete(sourceId)
      setActionNotice({ text: `Data source '${name}' removed.`, type: "success" })
      loadSources()
    } catch (err: any) {
      setActionNotice({ text: err.message || "Failed to delete connection.", type: "error" })
    }
  }

  const handleViewLogs = async (source: DataSource) => {
    setSelectedLogsSource(source)
    setLoadingJobs(true)
    try {
      const data = await dataSourcesApi.getJobs(source.id)
      setJobs(Array.isArray(data) ? data : [])
    } catch (err) {
      console.warn(err)
      setJobs([])
    } finally {
      setLoadingJobs(false)
    }
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      <PageHeader
        title="Connect Data Sources"
        description="Connect PostgreSQL, MySQL, REST APIs, Google Sheets, or CSV/Excel files with live schema introspection and automated synchronization."
      />

      {actionNotice && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between text-xs transition-all ${
            actionNotice.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-rose-500/10 border-rose-500/30 text-rose-300"
          }`}
        >
          <div className="flex items-center gap-2">
            {actionNotice.type === "success" ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
            <span>{actionNotice.text}</span>
          </div>
          <button onClick={() => setActionNotice(null)} className="text-neutral-400 hover:text-white p-1">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Source Selection Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-white uppercase tracking-wider">Choose Connection Type</h2>
            <p className="text-xs text-neutral-400 mt-0.5">Select a database driver, API stream, or file format to configure</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {CONNECTOR_CARDS.map((card) => {
            const Icon = card.icon
            return (
              <button
                key={card.type}
                type="button"
                onClick={() => handleSelectConnector(card.type)}
                className="p-5 rounded-xl border border-border bg-card text-card-foreground text-left flex flex-col justify-between hover:border-primary/50 transition-colors group cursor-pointer shadow-xs"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="p-2.5 rounded-lg bg-secondary text-foreground border border-border">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md bg-secondary border border-border text-muted-foreground">
                      {card.badge}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-foreground mb-1 group-hover:text-primary transition-colors">
                    {card.title}
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{card.subtitle}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-border/60 flex items-center justify-between text-xs font-medium text-muted-foreground group-hover:text-foreground">
                  <span>Connect & Configure</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Saved Connections Table */}
      <div className="rounded-2xl border border-neutral-800 bg-neutral-950/70 p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">Active Connected Data Sources</h2>
            <p className="text-xs text-neutral-400 mt-0.5">
              Saved database connections and sync schedules in {activeCompany?.company_name || "your workspace"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadSources}
              disabled={refreshing}
              className="px-3 py-1.5 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 rounded-xl text-xs font-medium text-neutral-300 transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-neutral-400 text-xs flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin text-primary" />
            <span>Loading workspace data connections...</span>
          </div>
        ) : !sources || sources.length === 0 ? (
          <div className="py-12 px-4 rounded-xl border border-dashed border-neutral-800 text-center bg-neutral-900/30">
            <Database className="w-8 h-8 text-neutral-600 mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-white mb-1">No Active Data Connections</h4>
            <p className="text-xs text-neutral-400 max-w-md mx-auto mb-4">
              Select one of the connectors above (CSV, Excel, PostgreSQL, MySQL, REST API, or Google Sheets) to establish your first data connection.
            </p>
            <button
              onClick={() => handleSelectConnector("postgres")}
              className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-xl text-xs font-semibold shadow-md transition inline-flex items-center gap-2 cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              Add First Connection
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Connection Name</th>
                  <th className="py-3 px-4">Source Type</th>
                  <th className="py-3 px-4">Health Status</th>
                  <th className="py-3 px-4">Sync Frequency</th>
                  <th className="py-3 px-4">Records Synced</th>
                  <th className="py-3 px-4">Last Sync</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-800/60">
                {sources.map((source) => {
                  const isError = source.status === "error"
                  const isSyncing = source.status === "syncing"
                  const isPaused = source.status === "paused"
                  return (
                    <tr key={source.id} className="hover:bg-neutral-900/40 transition">
                      <td className="py-3.5 px-4 font-semibold text-white flex items-center gap-2">
                        <Server className="w-4 h-4 text-primary shrink-0" />
                        <div>
                          <div>{source.name}</div>
                          {source.last_error_message && (
                            <div className="text-[11px] text-rose-400 font-normal truncate max-w-xs">
                              {source.last_error_message}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 uppercase font-mono text-[11px] text-neutral-300">
                        {source.source_type}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                            isSyncing
                              ? "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                              : isError
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                              : isPaused
                              ? "bg-neutral-800 text-neutral-400 border border-neutral-700"
                              : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isSyncing ? "bg-amber-400 animate-ping" : isError ? "bg-rose-400" : isPaused ? "bg-neutral-400" : "bg-emerald-400"
                            }`}
                          />
                          {source.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-neutral-300 capitalize">{source.sync_frequency}</td>
                      <td className="py-3.5 px-4 font-mono text-neutral-200">
                        {source.total_records_synced.toLocaleString()} rows
                      </td>
                      <td className="py-3.5 px-4 text-neutral-400">
                        {source.last_sync_at ? new Date(source.last_sync_at).toLocaleString() : "Never"}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            title="Sync Now"
                            onClick={() => handleManualSync(source.id)}
                            className="p-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 transition cursor-pointer"
                          >
                            <Play className="w-3.5 h-3.5" />
                          </button>
                          <button
                            title="View Sync History"
                            onClick={() => handleViewLogs(source)}
                            className="p-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 transition cursor-pointer"
                          >
                            <FileText className="w-3.5 h-3.5" />
                          </button>
                          <button
                            title="Delete Connection"
                            onClick={() => handleDeleteSource(source.id, source.name)}
                            className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 transition cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Interactive Connection Modal / Wizard */}
      {isWizardOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-card border border-border rounded-xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-lg overflow-hidden my-auto">
            {/* Modal Header */}
            <div className="p-6 border-b border-border flex items-center justify-between bg-card">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-secondary border border-border text-foreground">
                  {selectedType === "csv" && <FileText className="w-5 h-5 text-foreground" />}
                  {selectedType === "excel" && <FileSpreadsheet className="w-5 h-5 text-foreground" />}
                  {selectedType === "postgres" && <Server className="w-5 h-5 text-foreground" />}
                  {selectedType === "mysql" && <Database className="w-5 h-5 text-foreground" />}
                  {selectedType === "rest_api" && <Globe className="w-5 h-5 text-foreground" />}
                  {selectedType === "google_sheets" && <Layers className="w-5 h-5 text-foreground" />}
                </div>
                <div>
                  <h3 className="text-base font-bold text-foreground">
                    Connect {selectedType === "csv" ? "CSV File" : selectedType === "excel" ? "Excel Workbook (XLSX)" : selectedType === "postgres" ? "PostgreSQL" : selectedType === "mysql" ? "MySQL" : selectedType === "rest_api" ? "REST API" : "Google Sheets"}
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Step-by-step connection configuration, live test, and instant dataset ingestion
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsWizardOpen(false)}
                className="p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              {/* CSV & Excel File Upload Mode */}
              {(selectedType === "csv" || selectedType === "excel") && (
                <div className="space-y-5">
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-neutral-800 hover:border-neutral-600 rounded-2xl p-8 text-center bg-neutral-900/20 cursor-pointer transition flex flex-col items-center justify-center gap-3"
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept={selectedType === "csv" ? ".csv" : ".xlsx,.xls"}
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <div className="p-4 rounded-full bg-neutral-900 border border-neutral-800">
                      <UploadCloud className="w-8 h-8 text-neutral-300" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">
                        {selectedFile ? selectedFile.name : `Click to select ${selectedType.toUpperCase()} file`}
                      </p>
                      <p className="text-xs text-neutral-400 mt-1">
                        {selectedFile
                          ? `${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Ready to analyze`
                          : `Supported format: ${selectedType === "csv" ? ".csv" : ".xlsx, .xls"} (up to 50MB)`}
                      </p>
                    </div>
                  </div>

                  {fileError && (
                    <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                      <span>{fileError}</span>
                    </div>
                  )}

                  {selectedFile && (
                    <div className="p-4 rounded-xl bg-neutral-900/40 border border-neutral-800 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                        <div>
                          <p className="font-semibold text-white">{selectedFile.name}</p>
                          <p className="text-[11px] text-neutral-400">
                            {(selectedFile.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      <Button
                        onClick={handleFileAnalyze}
                        disabled={isAnalyzingFile}
                        className="gap-2"
                      >
                        {isAnalyzingFile ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span>Ingesting & Analyzing...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" />
                            <span>Analyze in DataScope</span>
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {/* Database & API Connectors Mode */}
              {selectedType !== "csv" && selectedType !== "excel" && (
                <>
                  {/* Common Name & Frequency */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="sm:col-span-2">
                      <label className="block font-medium text-neutral-300 mb-1.5">Connection Name *</label>
                      <input
                        type="text"
                        required
                        placeholder={`e.g. Production ${selectedType.toUpperCase()}`}
                        value={connectionName}
                        onChange={(e) => setConnectionName(e.target.value)}
                        className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                      />
                    </div>
                    <div>
                      <label className="block font-medium text-neutral-300 mb-1.5">Sync Schedule</label>
                      <select
                        value={syncFrequency}
                        onChange={(e: any) => setSyncFrequency(e.target.value)}
                        className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                      >
                        <option value="manual">Manual on Demand</option>
                        <option value="hourly">Hourly Automated</option>
                        <option value="daily">Daily Automated</option>
                        <option value="weekly">Weekly Automated</option>
                      </select>
                    </div>
                  </div>

                  {/* PostgreSQL & MySQL Form */}
                  {(selectedType === "postgres" || selectedType === "mysql") && (
                    <div className="space-y-4 pt-2 border-t border-neutral-800">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="sm:col-span-2">
                          <label className="block font-medium text-neutral-300 mb-1.5">Database Host *</label>
                          <input
                            type="text"
                            required
                            placeholder="db.example.com or localhost"
                            value={host}
                            onChange={(e) => setHost(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                          />
                        </div>
                        <div>
                          <label className="block font-medium text-neutral-300 mb-1.5">Port *</label>
                          <input
                            type="text"
                            required
                            value={port}
                            onChange={(e) => setPort(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div>
                          <label className="block font-medium text-neutral-300 mb-1.5">Database Name *</label>
                          <input
                            type="text"
                            required
                            placeholder="analytics_db"
                            value={database}
                            onChange={(e) => setDatabase(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                          />
                        </div>
                        <div>
                          <label className="block font-medium text-neutral-300 mb-1.5">Username *</label>
                          <input
                            type="text"
                            required
                            placeholder="readonly_user"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                          />
                        </div>
                        <div>
                          <label className="block font-medium text-neutral-300 mb-1.5">Password</label>
                          <input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                          />
                        </div>
                      </div>

                      {selectedType === "postgres" && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <div>
                            <label className="block font-medium text-neutral-300 mb-1.5">SSL Mode</label>
                            <select
                              value={sslmode}
                              onChange={(e) => setSslmode(e.target.value)}
                              className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                            >
                              <option value="prefer">Prefer SSL (Default)</option>
                              <option value="require">Require SSL</option>
                              <option value="disable">Disable SSL</option>
                            </select>
                          </div>
                        </div>
                      )}

                      {/* Table Selection or Custom Query */}
                      <div className="pt-3 border-t border-neutral-800 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white">Table or Query Selection</span>
                          <button
                            type="button"
                            onClick={() => setUseCustomQuery(!useCustomQuery)}
                            className="text-neutral-300 hover:text-white text-xs font-medium cursor-pointer underline"
                          >
                            {useCustomQuery ? "← Switch to Table Picker" : "Use Custom SELECT Query →"}
                          </button>
                        </div>

                        {!useCustomQuery ? (
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <select
                                value={selectedTable}
                                onChange={(e) => setSelectedTable(e.target.value)}
                                className="flex-1 px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                              >
                                {discoveredTables.length === 0 ? (
                                  <option value="">No tables loaded. Click 'Test Connection' or enter name below.</option>
                                ) : (
                                  discoveredTables.map((t) => (
                                    <option key={t.full_name} value={t.full_name}>
                                      {t.full_name} ({t.type})
                                    </option>
                                  ))
                                )}
                              </select>
                              <button
                                type="button"
                                onClick={handleDiscoverTables}
                                disabled={loadingTables || !host || !database}
                                className="px-3 py-2 bg-neutral-900 hover:bg-neutral-800 border border-neutral-700 text-white rounded-xl transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                              >
                                <RefreshCw className={`w-3.5 h-3.5 ${loadingTables ? "animate-spin" : ""}`} />
                                Fetch Tables
                              </button>
                            </div>
                            <input
                              type="text"
                              placeholder="Or type table name manually (e.g. public.orders)"
                              value={selectedTable}
                              onChange={(e) => setSelectedTable(e.target.value)}
                              className="w-full px-3.5 py-1.5 bg-black border border-neutral-800 rounded-xl text-neutral-300 placeholder-neutral-600 focus:outline-none focus:border-neutral-500 text-[11px]"
                            />
                          </div>
                        ) : (
                          <div>
                            <textarea
                              rows={3}
                              placeholder="SELECT id, created_at, total_amount, status FROM orders WHERE created_at >= NOW() - INTERVAL '30 days'"
                              value={customQuery}
                              onChange={(e) => setCustomQuery(e.target.value)}
                              className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white font-mono text-xs placeholder-neutral-600 focus:outline-none focus:border-neutral-500"
                            />
                            <p className="text-[11px] text-neutral-500 mt-1">
                              🔒 For safety, only SELECT statements are allowed.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* REST API Form */}
                  {selectedType === "rest_api" && (
                    <div className="space-y-4 pt-2 border-t border-neutral-800">
                      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                        <div className="sm:col-span-3">
                          <label className="block font-medium text-neutral-300 mb-1.5">API Endpoint URL *</label>
                          <input
                            type="url"
                            required
                            placeholder="https://api.example.com/v1/analytics/orders"
                            value={apiUrl}
                            onChange={(e) => setApiUrl(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                          />
                        </div>
                        <div>
                          <label className="block font-medium text-neutral-300 mb-1.5">HTTP Method</label>
                          <select
                            value={apiMethod}
                            onChange={(e: any) => setApiMethod(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                          >
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div>
                          <label className="block font-medium text-neutral-300 mb-1.5">Authentication Type</label>
                          <select
                            value={authType}
                            onChange={(e: any) => setAuthType(e.target.value)}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                          >
                            <option value="none">No Auth (Public)</option>
                            <option value="bearer">Bearer Token</option>
                            <option value="api_key">API Key Header</option>
                          </select>
                        </div>

                        {authType === "bearer" && (
                          <div className="sm:col-span-2">
                            <label className="block font-medium text-neutral-300 mb-1.5">Bearer Token</label>
                            <input
                              type="password"
                              placeholder="eyJhbGciOi..."
                              value={authToken}
                              onChange={(e) => setAuthToken(e.target.value)}
                              className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                            />
                          </div>
                        )}

                        {authType === "api_key" && (
                          <>
                            <div>
                              <label className="block font-medium text-neutral-300 mb-1.5">Header Name</label>
                              <input
                                type="text"
                                placeholder="X-API-Key"
                                value={apiKeyHeader}
                                onChange={(e) => setApiKeyHeader(e.target.value)}
                                className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                              />
                            </div>
                            <div>
                              <label className="block font-medium text-neutral-300 mb-1.5">API Key Value</label>
                              <input
                                type="password"
                                placeholder="key_live_..."
                                value={apiKeyValue}
                                onChange={(e) => setApiKeyValue(e.target.value)}
                                className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                              />
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Google Sheets Form */}
                  {selectedType === "google_sheets" && (
                    <div className="space-y-4 pt-2 border-t border-neutral-800">
                      <div>
                        <label className="block font-medium text-neutral-300 mb-1.5">Google Sheet Shareable URL *</label>
                        <input
                          type="url"
                          required
                          placeholder="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
                          value={sheetUrl}
                          onChange={(e) => {
                            setSheetUrl(e.target.value)
                            setTestResult(null)
                            setPreviewData(null)
                          }}
                          className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                        />
                      </div>

                      {/* Worksheet / Tab Picker if discovered */}
                      {discoveredTables.length > 0 && (
                        <div>
                          <label className="block font-medium text-neutral-300 mb-1.5">Selected Worksheet / Tab</label>
                          <select
                            value={selectedTable}
                            onChange={(e) => {
                              setSelectedTable(e.target.value)
                              const matched = discoveredTables.find((t) => t.full_name === e.target.value)
                              if (matched && (matched as any).gid) {
                                setSheetGid((matched as any).gid)
                              }
                            }}
                            className="w-full px-3.5 py-2 bg-black border border-neutral-800 rounded-xl text-white focus:outline-none focus:border-neutral-500"
                          >
                            {discoveredTables.map((t) => (
                              <option key={t.full_name} value={t.full_name}>
                                📄 {t.name} (Worksheet)
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      <div className="p-3.5 rounded-xl bg-neutral-900/60 border border-neutral-800 text-neutral-400 space-y-1.5">
                        <p className="font-semibold text-white flex items-center gap-1.5">
                          <Layers className="w-3.5 h-3.5 text-green-400" />
                          <span>Quick Sharing Guide:</span>
                        </p>
                        <ol className="list-decimal list-inside space-y-0.5 text-[11px]">
                          <li>In your Google Sheet, click the top-right <strong>Share</strong> button.</li>
                          <li>Under General Access, select <strong>"Anyone with the link can view"</strong>.</li>
                          <li>Paste the shareable URL above, then click <strong>Test Connection</strong>.</li>
                        </ol>
                      </div>
                    </div>
                  )}

                  {/* Test Connection & Preview Actions */}
                  <div className="p-4 rounded-xl bg-neutral-900/60 border border-neutral-800 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleTestConnection}
                        disabled={testing}
                        className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-xl font-semibold transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
                      >
                        <ShieldCheck className={`w-4 h-4 ${testing ? "animate-spin text-amber-400" : "text-emerald-400"}`} />
                        {testing ? "Testing Connectivity..." : "Test Connection"}
                      </button>

                      <button
                        type="button"
                        onClick={handlePreviewData}
                        disabled={previewing}
                        className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-xl font-semibold transition flex items-center gap-2 cursor-pointer disabled:opacity-50"
                      >
                        <Eye className="w-4 h-4 text-neutral-300" />
                        {previewing ? "Fetching Sample..." : "Preview Data"}
                      </button>
                    </div>

                    {testResult && (
                      <div
                        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold ${
                          testResult.success
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        {testResult.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                        <span>{testResult.message}</span>
                      </div>
                    )}
                  </div>

                  {/* Live Data Preview Table */}
                  {previewData && (
                    <div className="p-4 rounded-xl bg-neutral-950 border border-neutral-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white">Live Data Preview</span>
                        <span className="text-neutral-400 text-[11px]">
                          {previewData.columns?.length || 0} columns detected · {previewData.row_count_sample || 0} sample rows
                        </span>
                      </div>

                      {previewData.success && previewData.preview && previewData.preview.length > 0 ? (
                        <div className="overflow-x-auto max-h-56 border border-neutral-800 rounded-lg">
                          <table className="w-full text-left text-[11px] border-collapse font-mono">
                            <thead className="bg-neutral-900 sticky top-0 border-b border-neutral-800">
                              <tr>
                                {previewData.columns?.map((col) => (
                                  <th key={col} className="py-2 px-3 text-neutral-300 uppercase font-semibold">
                                    {col}
                                    <span className="block text-[9px] text-neutral-500 font-normal">
                                      {previewData.dtypes?.[col] || "text"}
                                    </span>
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-neutral-900">
                              {previewData.preview.map((row, idx) => (
                                <tr key={idx} className="hover:bg-neutral-900/40">
                                  {previewData.columns?.map((col) => (
                                    <td key={col} className="py-1.5 px-3 text-neutral-300 truncate max-w-xs">
                                      {row[col] !== null && row[col] !== undefined ? String(row[col]) : <em className="text-neutral-600">null</em>}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-rose-400 text-xs">{previewData.error || "No sample data returned."}</p>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Actions */}
            <div className="p-5 border-t border-border bg-card flex flex-wrap items-center justify-between gap-3">
              <button
                type="button"
                onClick={() => setIsWizardOpen(false)}
                className="px-4 py-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors flex items-center gap-1.5 text-xs font-medium cursor-pointer"
              >
                <ArrowLeft className="w-4 h-4" />
                Cancel / Back
              </button>

              {selectedType !== "csv" && selectedType !== "excel" && (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleSaveConnection}
                    disabled={saving || !connectionName.trim() || !testResult?.success}
                    className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-secondary-foreground border border-border font-medium rounded-md transition-colors cursor-pointer disabled:opacity-50 text-xs"
                  >
                    {saving ? "Saving..." : "Save Connection"}
                  </button>

                  <Button
                    onClick={handleImportAndAnalyze}
                    disabled={importing || !testResult?.success}
                    className="gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    {importing ? "Ingesting Data..." : "Analyze in DataScope"}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Sync Execution Logs Modal */}
      {selectedLogsSource && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-lg overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-foreground">Sync History: {selectedLogsSource.name}</h3>
                <p className="text-[11px] text-muted-foreground">Execution logs and record ingestion history</p>
              </div>
              <button onClick={() => setSelectedLogsSource(null)} className="p-1 text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-3 flex-1 text-xs">
              {loadingJobs ? (
                <div className="py-8 text-center text-muted-foreground">Loading sync history...</div>
              ) : !jobs || jobs.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground">No sync jobs recorded yet.</div>
              ) : (
                jobs.map((job) => (
                  <div key={job.id} className="p-3.5 rounded-lg bg-secondary/40 border border-border space-y-2">
                    <div className="flex items-center justify-between">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-md border ${
                          job.status === "success"
                            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                            : "bg-rose-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400"
                        }`}
                      >
                        {job.status.toUpperCase()}
                      </span>
                      <span className="text-muted-foreground text-[10px]">
                        {new Date(job.started_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-foreground">
                      <strong>{job.records_added.toLocaleString()}</strong> records synced via {job.sync_type} execution
                    </div>
                    {job.log_output && (
                      <pre className="p-2.5 rounded-md bg-muted text-[10px] font-mono text-muted-foreground overflow-x-auto whitespace-pre-wrap">
                        {job.log_output}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
