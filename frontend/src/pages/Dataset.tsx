import { Link } from "react-router-dom"
import { LineChart, Trash2, UploadCloud, X } from "lucide-react"
import { PageHeader } from "@/components/shared/PageHeader"
import { Button } from "@/components/ui/button"
import { FileDropzone } from "@/components/dataset/FileDropzone"
import { FileDetails } from "@/components/dataset/FileDetails"
import { UploadError } from "@/components/dataset/UploadError"
import { DatasetSummaryCards } from "@/components/dataset/DatasetSummaryCards"
import { DatasetPreviewTable } from "@/components/dataset/DatasetPreviewTable"
import { DataQualityCard } from "@/components/intelligence/DataQualityCard"
import { useActiveDataset } from "@/context/DatasetContext"

export default function Dataset() {
  const {
    activeDataset,
    uploadState,
    isReplacing,
    selectFile,
    rejectFile,
    clearFile,
    analyzeFile,
    retryUpload,
    startReplace,
    cancelReplace,
    removeDataset,
  } = useActiveDataset()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dataset"
        description="Upload, inspect, and manage the dataset this workspace analyzes."
      />

      {/* When the user explicitly wants to replace the active dataset */}
      {isReplacing && (
        <div className="space-y-4 rounded-xl border border-primary/20 bg-primary/5 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Replace Active Dataset</h3>
              <p className="text-xs text-muted-foreground">
                Select a new CSV or Excel file to analyze. The current dataset ({activeDataset?.filename}) will remain active until you confirm the new upload.
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={cancelReplace} className="gap-1 text-xs">
              <X className="h-4 w-4" />
              Cancel
            </Button>
          </div>

          {uploadState.status === "idle" && (
            <FileDropzone onFileSelected={selectFile} onRejected={rejectFile} />
          )}

          {(uploadState.status === "selected" || uploadState.status === "processing") && (
            <FileDetails
              file={uploadState.file}
              isProcessing={uploadState.status === "processing"}
              onRemove={cancelReplace}
              onAnalyze={() => analyzeFile(uploadState.file)}
            />
          )}

          {uploadState.status === "error" && (
            <UploadError
              message={uploadState.message}
              canRetry={uploadState.file !== null}
              onRetry={retryUpload}
              onStartOver={cancelReplace}
            />
          )}
        </div>
      )}

      {/* Initial state when no dataset is loaded and not replacing */}
      {!activeDataset && !isReplacing && (
        <>
          {uploadState.status === "idle" && (
            <FileDropzone onFileSelected={selectFile} onRejected={rejectFile} />
          )}

          {(uploadState.status === "selected" || uploadState.status === "processing") && (
            <FileDetails
              file={uploadState.file}
              isProcessing={uploadState.status === "processing"}
              onRemove={clearFile}
              onAnalyze={() => analyzeFile(uploadState.file)}
            />
          )}

          {uploadState.status === "error" && (
            <UploadError
              message={uploadState.message}
              canRetry={uploadState.file !== null}
              onRetry={retryUpload}
              onStartOver={clearFile}
            />
          )}
        </>
      )}

      {/* Active dataset view */}
      {activeDataset && !isReplacing && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-card p-4">
            <div>
              <p className="text-sm font-medium text-foreground">
                Active Dataset: <span className="font-semibold text-primary">{activeDataset.filename}</span>
              </p>
              <p className="text-xs text-muted-foreground">
                {activeDataset.row_count.toLocaleString()} rows · {activeDataset.column_count.toLocaleString()} columns · Persisted across all workspace modules.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" size="sm" onClick={startReplace} className="gap-1.5 text-xs">
                <UploadCloud className="h-4 w-4" />
                Replace Dataset
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={removeDataset}
                className="gap-1.5 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30 border-rose-200 dark:border-rose-900/40"
              >
                <Trash2 className="h-4 w-4" />
                Remove Dataset
              </Button>
              <Button asChild size="sm" className="gap-1.5 text-xs">
                <Link to="/explore">
                  <LineChart className="h-4 w-4" />
                  View Visualizations
                </Link>
              </Button>
            </div>
          </div>

          <DatasetSummaryCards summary={activeDataset} />
          <DataQualityCard datasetId={activeDataset.dataset_id} />
          <DatasetPreviewTable summary={activeDataset} />
        </div>
      )}
    </div>
  )
}
