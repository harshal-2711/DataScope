import { RotateCcw } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { Button } from "@/components/ui/button"
import { FileDropzone } from "@/components/dataset/FileDropzone"
import { FileDetails } from "@/components/dataset/FileDetails"
import { UploadError } from "@/components/dataset/UploadError"
import { DatasetSummaryCards } from "@/components/dataset/DatasetSummaryCards"
import { DatasetPreviewTable } from "@/components/dataset/DatasetPreviewTable"
import { useDatasetUpload } from "@/hooks/useDatasetUpload"

export default function Dataset() {
  const { state, selectFile, reject, clearFile, analyze, retry } = useDatasetUpload()

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
          <div className="flex items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Dataset loaded successfully.
            </p>
            <Button variant="outline" size="sm" onClick={clearFile}>
              <RotateCcw className="h-4 w-4" />
              Upload a different dataset
            </Button>
          </div>
          <DatasetSummaryCards summary={state.summary} />
          <DatasetPreviewTable summary={state.summary} />
        </div>
      )}
    </div>
  )
}
