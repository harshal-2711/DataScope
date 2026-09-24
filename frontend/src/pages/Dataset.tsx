import { useRef } from "react"
import { Link } from "react-router-dom"
import { LineChart, Trash2, UploadCloud, FileSpreadsheet, Database, TableProperties, X } from "lucide-react"
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

  const csvInputRef = useRef<HTMLInputElement>(null)
  const excelInputRef = useRef<HTMLInputElement>(null)

  const handleManualFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size === 0) {
      rejectFile("The selected file is empty.")
      return
    }
    if (file.size > 100 * 1024 * 1024) {
      rejectFile("File exceeds the 100MB upload limit.")
      return
    }
    selectFile(file)
    e.target.value = ""
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <PageHeader
          title="Dataset Management"
          description="Upload, inspect, and manage datasets analyzed across your workspace modules."
        />
        
        {/* Visible Direct Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <input
            ref={csvInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={handleManualFileInput}
          />
          <input
            ref={excelInputRef}
            type="file"
            accept=".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
            className="hidden"
            onChange={handleManualFileInput}
          />
          
          <Button
            variant="default"
            size="sm"
            onClick={() => csvInputRef.current?.click()}
            className="gap-1.5 text-xs bg-white text-black hover:bg-neutral-200 font-medium cursor-pointer"
          >
            <UploadCloud className="h-4 w-4" />
            Upload CSV
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => excelInputRef.current?.click()}
            className="gap-1.5 text-xs border-neutral-800 bg-neutral-900 text-neutral-200 hover:bg-neutral-800 cursor-pointer"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Upload Excel
          </Button>

          <Button asChild variant="outline" size="sm" className="gap-1.5 text-xs border-neutral-800 bg-neutral-900 text-neutral-200 hover:bg-neutral-800">
            <Link to="/connect-data">
              <Database className="h-4 w-4 text-blue-400" />
              Connect Data Source
            </Link>
          </Button>

          <Button asChild variant="outline" size="sm" className="gap-1.5 text-xs border-neutral-800 bg-neutral-900 text-neutral-200 hover:bg-neutral-800">
            <Link to="/data-management">
              <TableProperties className="h-4 w-4 text-emerald-400" />
              View Stored Datasets
            </Link>
          </Button>
        </div>
      </div>

      {/* When the user explicitly wants to replace the active dataset */}
      {isReplacing && (
        <div className="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Replace Active Dataset</h3>
              <p className="text-xs text-neutral-400">
                Select a new CSV or Excel file to analyze. Current dataset ({activeDataset?.filename}) remains active until confirmed.
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={cancelReplace} className="gap-1 text-xs text-neutral-400 hover:text-white">
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
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-neutral-800 bg-[#141414] p-4 shadow-sm">
            <div>
              <p className="text-sm font-medium text-white">
                Active Dataset: <span className="font-semibold text-blue-400">{activeDataset.filename}</span>
              </p>
              <p className="text-xs text-neutral-400 mt-0.5">
                {activeDataset.row_count.toLocaleString()} rows · {activeDataset.column_count.toLocaleString()} columns · Synchronized across all analytics, risk, and report engines.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={startReplace}
                className="gap-1.5 text-xs border-neutral-800 bg-neutral-900 text-neutral-200 hover:bg-neutral-800"
              >
                <UploadCloud className="h-4 w-4" />
                Replace Dataset
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={removeDataset}
                className="gap-1.5 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 border-neutral-800"
              >
                <Trash2 className="h-4 w-4" />
                Remove Dataset
              </Button>
              <Button asChild size="sm" className="gap-1.5 text-xs bg-white text-black hover:bg-neutral-200 font-medium">
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
