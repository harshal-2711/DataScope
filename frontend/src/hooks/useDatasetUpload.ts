import { useCallback, useState } from "react"
import { uploadDataset } from "@/lib/datasetApi"
import type { UploadState } from "@/types/dataset"

export function useDatasetUpload() {
  const [state, setState] = useState<UploadState>({ status: "idle" })

  const selectFile = useCallback((file: File) => {
    setState({ status: "selected", file })
  }, [])

  const reject = useCallback((message: string) => {
    setState({ status: "error", file: null, message })
  }, [])

  const clearFile = useCallback(() => {
    setState({ status: "idle" })
  }, [])

  const analyze = useCallback(async (file: File) => {
    setState({ status: "processing", file })
    try {
      const summary = await uploadDataset(file)
      setState({ status: "success", file, summary })
    } catch (err) {
      setState({
        status: "error",
        file,
        message: err instanceof Error ? err.message : "Something went wrong.",
      })
    }
  }, [])

  const retry = useCallback(() => {
    setState((prev) => {
      if (prev.status === "error" && prev.file) {
        return { status: "selected", file: prev.file }
      }
      return { status: "idle" }
    })
  }, [])

  return { state, selectFile, reject, clearFile, analyze, retry }
}
