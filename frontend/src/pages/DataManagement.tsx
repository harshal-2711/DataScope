import { useState, useEffect, useCallback } from "react"
import {
  Database,
  Plus,
  Edit2,
  Trash2,
  UploadCloud,
  History,
  Search,
  RefreshCw,
  RotateCcw,
  X,
  AlertCircle,
  Sparkles,
  Wifi,
  WifiOff,
} from "lucide-react"
import { useActiveDataset } from "@/context/DatasetContext"
import { useAuth } from "@/context/AuthContext"
import {
  addRecord,
  bulkImportRecords,
  deleteRecord,
  fetchPaginatedRecords,
  fetchVersionHistory,
  rollbackDatasetVersion,
  updateRecord,
  type PaginatedRecordsResponse,
  type RecordItem,
  type VersionHistoryItem,
} from "@/lib/dataManagementApi"

export default function DataManagement() {
  const { activeDataset } = useActiveDataset()
  const { isWsConnected, lastRealtimeEvent } = useAuth()

  const [paginatedData, setPaginatedData] = useState<PaginatedRecordsResponse | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(25)
  const [searchQuery, setSearchQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)


  // Modals
  const [showAddModal, setShowAddModal] = useState(false)
  const [showBulkModal, setShowBulkModal] = useState(false)
  const [showHistoryModal, setShowHistoryModal] = useState(false)
  const [editingRecord, setEditingRecord] = useState<RecordItem | null>(null)
  const [newRowData, setNewRowData] = useState<Record<string, any>>({})
  const [bulkJsonText, setBulkJsonText] = useState("")
  const [versionHistory, setVersionHistory] = useState<VersionHistoryItem[]>([])

  const datasetId = activeDataset?.dataset_id

  const loadRecords = useCallback(async () => {
    if (!datasetId) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await fetchPaginatedRecords(datasetId, currentPage, pageSize, searchQuery)
      setPaginatedData(data)
    } catch (err: any) {
      setError(err.message || "Failed to load dataset records.")
    } finally {
      setIsLoading(false)
    }
  }, [datasetId, currentPage, pageSize, searchQuery])

  useEffect(() => {
    loadRecords()
  }, [loadRecords])

  // Listen for real-time WebSocket dataset changes
  useEffect(() => {
    if (lastRealtimeEvent?.type === "DATASET_UPDATED" && lastRealtimeEvent.data?.dataset_id === datasetId) {
      loadRecords()
    }
  }, [lastRealtimeEvent, datasetId, loadRecords])

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!datasetId) return
    try {
      await addRecord(datasetId, newRowData)
      setNewRowData({})
      setShowAddModal(false)
      await loadRecords()
    } catch (err: any) {
      alert(err.message || "Failed to add record.")
    }
  }

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!datasetId || !editingRecord) return
    try {
      await updateRecord(datasetId, editingRecord.record_id, editingRecord.data)
      setEditingRecord(null)
      await loadRecords()
    } catch (err: any) {
      alert(err.message || "Failed to update record.")
    }
  }

  const handleDelete = async (recordId: string) => {
    if (!datasetId) return
    if (!confirm("Are you sure you want to delete this record? A new version snapshot will be created.")) return
    try {
      await deleteRecord(datasetId, recordId)
      await loadRecords()
    } catch (err: any) {
      alert(err.message || "Failed to delete record.")
    }
  }

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!datasetId || !bulkJsonText.trim()) return
    try {
      const parsed = JSON.parse(bulkJsonText.trim())
      const recordsArray = Array.isArray(parsed) ? parsed : [parsed]
      await bulkImportRecords(datasetId, recordsArray, "Bulk JSON Import")
      setBulkJsonText("")
      setShowBulkModal(false)
      await loadRecords()
    } catch (err: any) {
      alert("Invalid JSON format: " + err.message)
    }
  }

  const handleOpenHistory = async () => {
    if (!datasetId) return
    setShowHistoryModal(true)
    try {
      const history = await fetchVersionHistory(datasetId)
      setVersionHistory(history)
    } catch (err: any) {
      alert(err.message || "Failed to load version history.")
    }
  }

  const handleRollback = async (versionNumber: number) => {
    if (!datasetId) return
    if (!confirm(`Are you sure you want to rollback to version ${versionNumber}?`)) return
    try {
      await rollbackDatasetVersion(datasetId, versionNumber)
      setShowHistoryModal(false)
      await loadRecords()
    } catch (err: any) {
      alert(err.message || "Failed to rollback.")
    }
  }

  if (!activeDataset) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-8 text-center text-slate-400">
        <Database className="w-12 h-12 text-slate-600 mb-4 animate-pulse" />
        <h2 className="text-xl font-bold text-white mb-2">No Active Dataset Selected</h2>
        <p className="text-sm max-w-md mb-6">
          Upload or select a dataset in the Overview tab to view, edit, search, and manage live business records.
        </p>
      </div>
    )
  }

  const columns = paginatedData?.columns || []
  const records = paginatedData?.records || []

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-md shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
              <Sparkles className="w-3 h-3" />
              <span>Version {paginatedData?.current_version || 1}</span>
            </span>
            <div className="flex items-center gap-1 text-[11px] text-slate-400">
              {isWsConnected ? (
                <span className="flex items-center gap-1 text-emerald-400 font-medium">
                  <Wifi className="w-3 h-3" /> Live Sync
                </span>
              ) : (
                <span className="flex items-center gap-1 text-slate-500">
                  <WifiOff className="w-3 h-3" /> Reconnecting...
                </span>
              )}
            </div>
          </div>
          <h1 className="text-xl font-extrabold text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-500" />
            <span>Live Data Management: {activeDataset.filename}</span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Total {paginatedData?.total_records.toLocaleString() || 0} business records stored in private workspace
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleOpenHistory}
            className="px-3 py-1.5 rounded-md bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer border border-border"
          >
            <History className="w-3.5 h-3.5" />
            <span>Version History</span>
          </button>

          <button
            type="button"
            onClick={() => setShowBulkModal(true)}
            className="px-3 py-1.5 rounded-md bg-secondary hover:bg-secondary/80 text-secondary-foreground text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer border border-border"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Bulk Import</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setNewRowData({})
              setShowAddModal(true)
            }}
            className="px-3 py-1.5 rounded-md bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-medium flex items-center gap-1.5 transition-colors shadow-xs cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Single Record</span>
          </button>
        </div>
      </div>

      {/* Search and Table Container */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-xs space-y-4">
        {/* Search Bar */}
        <div className="flex items-center justify-between gap-4">
          <div className="relative max-w-sm w-full">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search across all records..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setCurrentPage(1)
              }}
              className="w-full pl-9 pr-4 py-2 bg-background border border-input rounded-md text-xs text-foreground placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <button
              type="button"
              onClick={loadRecords}
              className="p-2 rounded-md bg-secondary hover:bg-secondary/80 text-foreground transition-colors cursor-pointer border border-border"
              title="Refresh records"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-primary" : ""}`} />
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Data Table */}
        <div className="border border-slate-800/80 rounded-xl overflow-x-auto max-h-[500px]">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-950/80 text-slate-300 font-semibold sticky top-0 z-10 backdrop-blur-md">
              <tr>
                <th className="p-3 border-b border-slate-800 w-16 text-center">#</th>
                {columns.map((col) => (
                  <th key={col.name} className="p-3 border-b border-slate-800 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <span>{col.name}</span>
                      <span className="text-[10px] font-mono text-slate-500 font-normal">({col.dtype})</span>
                    </div>
                  </th>
                ))}
                <th className="p-3 border-b border-slate-800 text-right w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {isLoading ? (
                <tr>
                  <td colSpan={columns.length + 2} className="p-8 text-center text-slate-500">
                    Loading records...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={columns.length + 2} className="p-8 text-center text-slate-500">
                    No records found matching search criteria.
                  </td>
                </tr>
              ) : (
                records.map((rec) => (
                  <tr key={rec.record_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 text-slate-500 font-mono text-center">{rec.row_index}</td>
                    {columns.map((col) => (
                      <td key={col.name} className="p-3 text-slate-300 font-mono whitespace-nowrap max-w-[200px] truncate">
                        {String(rec.data[col.name] ?? "—")}
                      </td>
                    ))}
                    <td className="p-3 text-right">
                      <div className="inline-flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => setEditingRecord(rec)}
                          className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors cursor-pointer"
                          title="Edit record"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(rec.record_id)}
                          className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors cursor-pointer"
                          title="Delete record"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {paginatedData && paginatedData.total_pages > 1 && (
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
            <div>
              Showing Page {paginatedData.page} of {paginatedData.total_pages} ({paginatedData.total_records} records)
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={currentPage >= paginatedData.total_pages}
                onClick={() => setCurrentPage((p) => p + 1)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ADD RECORD MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-blue-400" />
                <span>Add Single Record</span>
              </h3>
              <button type="button" onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              {columns.map((col) => (
                <div key={col.name}>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    {col.name} <span className="text-slate-500 font-normal">({col.dtype})</span>
                  </label>
                  <input
                    type="text"
                    value={newRowData[col.name] ?? ""}
                    onChange={(e) =>
                      setNewRowData({
                        ...newRowData,
                        [col.name]: col.is_numeric ? (e.target.value === "" ? "" : Number(e.target.value)) : e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
                  />
                </div>
              ))}

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl"
                >
                  Save Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT RECORD MODAL */}
      {editingRecord && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Edit2 className="w-4 h-4 text-blue-400" />
                <span>Edit Record (Row {editingRecord.row_index})</span>
              </h3>
              <button type="button" onClick={() => setEditingRecord(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
              {columns.map((col) => (
                <div key={col.name}>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    {col.name} <span className="text-slate-500 font-normal">({col.dtype})</span>
                  </label>
                  <input
                    type="text"
                    value={editingRecord.data[col.name] ?? ""}
                    onChange={(e) =>
                      setEditingRecord({
                        ...editingRecord,
                        data: {
                          ...editingRecord.data,
                          [col.name]: col.is_numeric ? (e.target.value === "" ? "" : Number(e.target.value)) : e.target.value,
                        },
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500"
                  />
                </div>
              ))}

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setEditingRecord(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl"
                >
                  Update Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* BULK IMPORT MODAL */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-emerald-400" />
                <span>Bulk Import / Append Records (JSON)</span>
              </h3>
              <button type="button" onClick={() => setShowBulkModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-3">
              Paste a JSON array of record objects matching your dataset schema:
            </p>

            <form onSubmit={handleBulkSubmit} className="space-y-4">
              <textarea
                rows={8}
                required
                placeholder='[&#10;  {"Sales": 1200, "Profit": 300, "Category": "Technology"},&#10;  {"Sales": 450, "Profit": -20, "Category": "Furniture"}&#10;]'
                value={bulkJsonText}
                onChange={(e) => setBulkJsonText(e.target.value)}
                className="w-full p-3 bg-slate-950 font-mono text-xs text-slate-200 border border-slate-800 rounded-xl focus:outline-none focus:border-blue-500"
              />

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowBulkModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl"
                >
                  Import Records
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* VERSION HISTORY DRAWER / MODAL */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                <History className="w-4 h-4 text-primary" />
                <span>Dataset Version History & Rollback</span>
              </h3>
              <button type="button" onClick={() => setShowHistoryModal(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2.5 max-h-[55vh] overflow-y-auto pr-1">
              {versionHistory.map((v) => (
                <div
                  key={v.id}
                  className={`p-3.5 rounded-lg border transition-colors flex items-center justify-between ${
                    v.is_active
                      ? "bg-secondary border-primary/40 text-foreground"
                      : "bg-card/40 border-border text-muted-foreground hover:border-border"
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
                      <span>Version {v.version_number}</span>
                      {v.is_active && (
                        <span className="px-1.5 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-bold border border-primary/20">
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-0.5">{v.change_summary}</div>
                    <div className="text-[10px] text-muted-foreground mt-1">
                      {v.row_count} rows · By {v.created_by || "System"} · {new Date(v.created_at).toLocaleString()}
                    </div>
                  </div>

                  {!v.is_active && (
                    <button
                      type="button"
                      onClick={() => handleRollback(v.version_number)}
                      className="px-2.5 py-1.5 rounded-md bg-secondary hover:bg-secondary/80 text-foreground text-xs font-medium flex items-center gap-1 transition-colors cursor-pointer border border-border"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Rollback</span>
                    </button>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-end mt-5">
              <button
                type="button"
                onClick={() => setShowHistoryModal(false)}
                className="px-4 py-2 bg-secondary hover:bg-secondary/80 text-foreground text-xs font-medium rounded-md border border-border cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
