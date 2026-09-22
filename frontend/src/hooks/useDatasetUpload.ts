import { useActiveDataset } from "@/context/DatasetContext"

export function useDatasetUpload() {
  const {
    uploadState,
    selectFile,
    rejectFile,
    clearFile,
    analyzeFile,
    retryUpload,
  } = useActiveDataset()

  return {
    state: uploadState,
    selectFile,
    reject: rejectFile,
    clearFile,
    analyze: analyzeFile,
    retry: retryUpload,
  }
}
