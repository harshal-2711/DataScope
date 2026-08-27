import { useEffect } from "react"
import { Link } from "react-router-dom"
import { LineChart, RotateCcw } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { Button } from "@/components/ui/button"
import { FileDropzone } from "@/components/dataset/FileDropzone"
import { FileDetails } from "@/components/dataset/FileDetails"
import { UploadError } from "@/components/dataset/UploadError"
import { DatasetSummaryCards } from "@/components/dataset/DatasetSummaryCards"
import { DatasetPreviewTable } from "@/components/dataset/DatasetPreviewTable"
import { useDatasetUpload } from "@/hooks/useDatasetUpload"
import { useActiveDataset } from "@/context/DatasetContext"

export default function Dataset() {
  const { state, selectFile, reject, clearFile, analyze, retry } = useDatasetUpload()
  const { setActiveDataset } = useActiveDataset()

  // The dataset this workspace analyzes is shared across pages (Explore
  // reads it to know what to visualize) — sync it into context whenever a
  // new upload succeeds here.
  useEffect(() => {
    if (state.status === "success") {
      setActiveDataset(state.summary)
    }
  }, [state, setActiveDataset])

  const startOver = () => {
    setActiveDataset(null)
    clearFile()
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dataset"
        description="Upload and manage the dataset this workspace analyzes."
      />

      {state.status === "idle" && (
        <FileDropzone onFileSelected={selectFile} onRejected={reject} />
      )}

      {(state.status === "selected" || state.status === "processing") && (
        <FileDetails
          file={state.file}
          isProcessing={state.status === "processing"}
          onRemove={clearFile}
          onAnalyze={() => analyze(state.file)}
        />
      )}

      {state.status === "error" && (
        <UploadError
          message={state.message}
          canRetry={state.file !== null}
          onRetry={retry}
          onStartOver={clearFile}
        />
      )}

      {state.status === "success" && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Dataset loaded successfully. It's now the active dataset for
              this workspace.
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={startOver}>
                <RotateCcw className="h-4 w-4" />
                Upload a different dataset
              </Button>
              <Button asChild size="sm">
                <Link to="/explore">
                  <LineChart className="h-4 w-4" />
                  View visualizations
                </Link>
              </Button>
            </div>
          </div>
          <DatasetSummaryCards summary={state.summary} />
          <DatasetPreviewTable summary={state.summary} />
        </div>
      )}
    </div>
  )
}
