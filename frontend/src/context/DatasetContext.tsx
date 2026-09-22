import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { uploadDataset, clearClientApiCache } from "@/lib/datasetApi"
import type { DatasetSummary, UploadState } from "@/types/dataset"

const SESSION_STORAGE_KEY = "datascope_active_dataset_summary"

function loadInitialDataset(): DatasetSummary | null {
  try {
    const raw = typeof window !== "undefined" ? sessionStorage.getItem(SESSION_STORAGE_KEY) : null
    if (raw) {
      const parsed = JSON.parse(raw) as DatasetSummary
      if (parsed && typeof parsed.dataset_id === "string") {
        return parsed
      }
    }
  } catch (err) {
    console.warn("Failed to load active dataset from sessionStorage:", err)
  }
  return null
}

function saveDatasetToSession(dataset: DatasetSummary | null) {
  try {
    if (typeof window !== "undefined") {
      if (dataset) {
        sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(dataset))
      } else {
        sessionStorage.removeItem(SESSION_STORAGE_KEY)
      }
    }
  } catch (err) {
    console.warn("Failed to save active dataset to sessionStorage:", err)
  }
}

export interface DatasetContextValue {
  activeDataset: DatasetSummary | null
  uploadState: UploadState
  isReplacing: boolean
  setActiveDataset: (summary: DatasetSummary | null) => void
  selectFile: (file: File) => void
  rejectFile: (message: string) => void
  clearFile: () => void
  analyzeFile: (file: File) => Promise<void>
  retryUpload: () => void
  startReplace: () => void
  cancelReplace: () => void
  removeDataset: () => void
}

const DatasetContext = createContext<DatasetContextValue | null>(null)

/**
 * Tracks the globally active dataset and upload lifecycle across all pages in the workspace.
 *
 * Persists in React state during internal route navigation and across tab refreshes
 * via client-side sessionStorage, avoiding repeated parsing, loss of state, or redundant uploads.
 */
export function DatasetProvider({ children }: { children: ReactNode }) {
  const [activeDataset, setActiveDatasetState] = useState<DatasetSummary | null>(() => loadInitialDataset())
  const [uploadState, setUploadState] = useState<UploadState>(() => {
    const initial = loadInitialDataset()
    return initial ? { status: "success", file: null as any, summary: initial } : { status: "idle" }
  })
  const [isReplacing, setIsReplacing] = useState(false)

  const setActiveDataset = useCallback((summary: DatasetSummary | null) => {
    setActiveDatasetState(summary)
    saveDatasetToSession(summary)
    if (summary) {
      setUploadState({ status: "success", file: null as any, summary })
      setIsReplacing(false)
    } else {
      setUploadState({ status: "idle" })
      setIsReplacing(false)
    }
  }, [])

  const selectFile = useCallback((file: File) => {
    setUploadState({ status: "selected", file })
  }, [])

  const rejectFile = useCallback((message: string) => {
    setUploadState({ status: "error", file: null, message })
  }, [])

  const clearFile = useCallback(() => {
    if (activeDataset) {
      setUploadState({ status: "success", file: null as any, summary: activeDataset })
      setIsReplacing(false)
    } else {
      setUploadState({ status: "idle" })
    }
  }, [activeDataset])

  const startReplace = useCallback(() => {
    setIsReplacing(true)
    setUploadState({ status: "idle" })
  }, [])

  const cancelReplace = useCallback(() => {
    setIsReplacing(false)
    if (activeDataset) {
      setUploadState({ status: "success", file: null as any, summary: activeDataset })
    } else {
      setUploadState({ status: "idle" })
    }
  }, [activeDataset])

  const analyzeFile = useCallback(async (file: File) => {
    setUploadState({ status: "processing", file })
    try {
      const summary = await uploadDataset(file)
      setActiveDatasetState(summary)
      saveDatasetToSession(summary)
      setUploadState({ status: "success", file, summary })
      setIsReplacing(false)
    } catch (err) {
      setUploadState({
        status: "error",
        file,
        message: err instanceof Error ? err.message : "Something went wrong during dataset analysis.",
      })
    }
  }, [])

  const retryUpload = useCallback(() => {
    setUploadState((prev) => {
      if (prev.status === "error" && prev.file) {
        return { status: "selected", file: prev.file }
      }
      if (activeDataset) {
        return { status: "success", file: null as any, summary: activeDataset }
      }
      return { status: "idle" }
    })
  }, [activeDataset])

  const removeDataset = useCallback(() => {
    if (activeDataset?.dataset_id) {
      clearClientApiCache(activeDataset.dataset_id)
    } else {
      clearClientApiCache()
    }
    setActiveDatasetState(null)
    saveDatasetToSession(null)
    setUploadState({ status: "idle" })
    setIsReplacing(false)
  }, [activeDataset])

  const value = useMemo<DatasetContextValue>(
    () => ({
      activeDataset,
      uploadState,
      isReplacing,
      setActiveDataset,
      selectFile,
      rejectFile,
      clearFile,
      analyzeFile,
      retryUpload,
      startReplace,
      cancelReplace,
      removeDataset,
    }),
    [
      activeDataset,
      uploadState,
      isReplacing,
      setActiveDataset,
      selectFile,
      rejectFile,
      clearFile,
      analyzeFile,
      retryUpload,
      startReplace,
      cancelReplace,
      removeDataset,
    ]
  )

  return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>
}

export function useActiveDataset() {
  const ctx = useContext(DatasetContext)
  if (!ctx) {
    throw new Error("useActiveDataset must be used within a DatasetProvider")
  }
  return ctx
}
