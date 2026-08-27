import { createContext, useContext, useMemo, useState, type ReactNode } from "react"
import type { DatasetSummary } from "@/types/dataset"

interface DatasetContextValue {
  activeDataset: DatasetSummary | null
  setActiveDataset: (summary: DatasetSummary | null) => void
}

const DatasetContext = createContext<DatasetContextValue | null>(null)

/**
 * Tracks "the dataset this workspace is currently analyzing" across pages.
 *
 * The Dataset page sets this once a file finishes uploading; the Explore
 * page (and anything else downstream) reads it to know what to visualize,
 * without re-uploading or re-fetching the summary. There's no backend
 * session concept (Phase 3 explicitly avoids auth/db), so "active dataset"
 * is simply client-side state scoped to this browser tab.
 */
export function DatasetProvider({ children }: { children: ReactNode }) {
  const [activeDataset, setActiveDataset] = useState<DatasetSummary | null>(null)

  const value = useMemo(
    () => ({ activeDataset, setActiveDataset }),
    [activeDataset]
  )

  return (
    <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>
  )
}

export function useActiveDataset() {
  const ctx = useContext(DatasetContext)
  if (!ctx) {
    throw new Error("useActiveDataset must be used within a DatasetProvider")
  }
  return ctx
}
