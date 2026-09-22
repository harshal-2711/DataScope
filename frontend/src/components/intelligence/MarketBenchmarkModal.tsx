import React, { useState, useRef } from "react"
import {
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Building2,
  Layers,
  Calendar,
  Info,
  ArrowRight,
  RefreshCw,
  X,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { previewMarketBenchmark, applyMarketBenchmark } from "@/lib/datasetApi"
import type { MarketBenchmarkPreview, CompetitionIntelligenceResponse } from "@/types/intelligence"

interface MarketBenchmarkModalProps {
  isOpen: boolean
  onClose: () => void
  datasetId: string
  onBenchmarkApplied: (data: CompetitionIntelligenceResponse) => void
}

export function MarketBenchmarkModal({
  isOpen,
  onClose,
  datasetId,
  onBenchmarkApplied,
}: MarketBenchmarkModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<MarketBenchmarkPreview | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  const [isApplying, setIsApplying] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const handleFileChange = async (selectedFile: File) => {
    setFile(selectedFile)
    setErrorMessage(null)
    setPreview(null)
    setIsValidating(true)

    try {
      const result = await previewMarketBenchmark(datasetId, selectedFile)
      setPreview(result)
    } catch (err: any) {
      setErrorMessage(err.message || "Could not parse or validate the benchmark file.")
    } finally {
      setIsValidating(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0]
      handleFileChange(droppedFile)
    }
  }

  const handleApply = async () => {
    if (!file) return
    setIsApplying(true)
    setErrorMessage(null)

    try {
      const res = await applyMarketBenchmark(datasetId, file)
      onBenchmarkApplied(res)
      onClose()
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to apply benchmark dataset.")
    } finally {
      setIsApplying(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setPreview(null)
    setErrorMessage(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-xl border border-border bg-card shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4 bg-muted/30">
          <div className="flex items-center gap-3">
            <div className="rounded-lg p-2 bg-primary/10 text-primary">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-tight">Upload Market Benchmark Dataset</h2>
              <p className="text-xs text-muted-foreground">
                Compare your business against external competitors. Your internal sales data remains preserved.
              </p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="rounded-full">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Informational Alert */}
          <div className="flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-3.5 text-xs">
            <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
            <div className="space-y-1 text-muted-foreground">
              <p className="font-medium text-foreground">External Market Data Segregation</p>
              <p>
                A single internal transactions dataset cannot reliably determine external market shares or competitor revenues.
                Upload a market report or competitor benchmark table (CSV, XLSX, or JSON) containing competitor entities and comparable turnover/margins.
              </p>
            </div>
          </div>

          {/* File Upload Zone */}
          {!file && (
            <div
              onDragOver={(e) => {
                e.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors flex flex-col items-center justify-center gap-3 ${
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50 hover:bg-muted/30"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileChange(e.target.files[0])
                  }
                }}
              />
              <div className="rounded-full p-4 bg-muted text-muted-foreground">
                <Upload className="h-8 w-8" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Click to upload or drag & drop</p>
                <p className="text-xs text-muted-foreground">
                  Supports CSV, Excel (.xlsx, .xls), and JSON market datasets (up to 10MB)
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 pt-2">
                <Badge variant="outline" className="text-[10px]">
                  Required: competitor/company
                </Badge>
                <Badge variant="outline" className="text-[10px]">
                  Required: revenue/sales
                </Badge>
                <Badge variant="secondary" className="text-[10px]">
                  Optional: profit, margin, market_share, growth, price
                </Badge>
              </div>
            </div>
          )}

          {/* Validation Loading State */}
          {isValidating && (
            <div className="flex flex-col items-center justify-center p-8 space-y-3">
              <RefreshCw className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm font-medium">Validating market schema and competitor entities...</p>
              <p className="text-xs text-muted-foreground">Checking required metrics and calculating data hygiene...</p>
            </div>
          )}

          {/* Error State */}
          {errorMessage && (
            <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-xs text-destructive">
              <XCircle className="h-5 w-5 shrink-0 mt-0.5" />
              <div className="space-y-1 flex-1">
                <p className="font-semibold text-sm">Validation Error</p>
                <p>{errorMessage}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleReset}
                  className="mt-2 text-xs border-destructive/30 hover:bg-destructive/10"
                >
                  Choose Another File
                </Button>
              </div>
            </div>
          )}

          {/* Preview & Validation Dashboard */}
          {preview && (
            <div className="space-y-5">
              {/* File Info Bar */}
              <div className="flex items-center justify-between rounded-lg border border-border p-3 bg-card">
                <div className="flex items-center gap-2.5">
                  <FileSpreadsheet className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">{preview.filename}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={preview.is_valid ? "default" : "destructive"} className="text-xs">
                    {preview.is_valid ? (
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Ready to Apply
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" /> Validation Issues
                      </span>
                    )}
                  </Badge>
                  <Button variant="ghost" size="sm" onClick={handleReset} className="h-7 text-xs">
                    Change File
                  </Button>
                </div>
              </div>

              {/* Summary Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="rounded-lg border border-border p-3.5 bg-muted/20">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                    <Building2 className="h-3.5 w-3.5" />
                    <span>Companies Detected</span>
                  </div>
                  <p className="text-lg font-bold text-foreground">{preview.company_count}</p>
                  <p className="text-[11px] text-muted-foreground truncate">
                    {preview.companies_sample.slice(0, 3).join(", ")}
                    {preview.company_count > 3 && ` +${preview.company_count - 3} more`}
                  </p>
                </div>

                <div className="rounded-lg border border-border p-3.5 bg-muted/20">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                    <Layers className="h-3.5 w-3.5" />
                    <span>Industry / Sector</span>
                  </div>
                  <p className="text-lg font-bold text-foreground">
                    {preview.industry || "General Market"}
                  </p>
                  <p className="text-[11px] text-muted-foreground">Market segmentation domain</p>
                </div>

                <div className="rounded-lg border border-border p-3.5 bg-muted/20">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>Reporting Period</span>
                  </div>
                  <p className="text-lg font-bold text-foreground">
                    {preview.reporting_period || "Single Snapshot"}
                  </p>
                  <p className="text-[11px] text-muted-foreground">Timeline coverage</p>
                </div>
              </div>

              {/* Detected Metrics vs Missing Fields */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg border border-border p-4 space-y-2.5">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    Detected Market Fields ({preview.detected_fields.length})
                  </h4>
                  <div className="space-y-1">
                    {preview.detected_fields.map((f, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        <span className="font-mono text-[11px]">{f}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-lg border border-border p-4 space-y-2.5">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                    Missing / Optional Fields ({preview.missing_required_fields.length + preview.missing_optional_fields.length})
                  </h4>
                  <div className="space-y-1">
                    {preview.missing_required_fields.map((f, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs text-destructive font-medium">
                        <span className="h-1.5 w-1.5 rounded-full bg-destructive" />
                        <span>{f}</span>
                      </div>
                    ))}
                    {preview.missing_optional_fields.map((f, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40" />
                        <span>{f} (optional)</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Data Quality Warnings */}
              {preview.warnings.length > 0 && (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 space-y-2">
                  <h4 className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                    <AlertTriangle className="h-4 w-4" />
                    Data Quality Observations ({preview.warnings.length})
                  </h4>
                  <ul className="space-y-1 text-xs text-muted-foreground list-disc list-inside">
                    {preview.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Sample Records Table Preview */}
              {preview.sample_records.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Data Sample Preview (First 5 Rows)
                  </h4>
                  <div className="rounded-lg border border-border overflow-x-auto max-h-48">
                    <table className="w-full text-xs text-left border-collapse">
                      <thead>
                        <tr className="bg-muted/50 border-b border-border">
                          {Object.keys(preview.sample_records[0]).map((key) => (
                            <th key={key} className="p-2 font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.sample_records.map((row, rIdx) => (
                          <tr key={rIdx} className="border-b border-border/50 hover:bg-muted/20">
                            {Object.values(row).map((val: any, cIdx) => (
                              <td key={cIdx} className="p-2 whitespace-nowrap font-sans">
                                {val !== null && val !== undefined ? String(val) : "-"}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between border-t border-border px-6 py-4 bg-muted/20">
          <Button variant="ghost" onClick={onClose} disabled={isApplying}>
            Cancel
          </Button>
          <div className="flex items-center gap-3">
            {preview && preview.is_valid && (
              <Button
                onClick={handleApply}
                disabled={isApplying}
                className="gap-2 bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                {isApplying ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Applying Benchmark...
                  </>
                ) : (
                  <>
                    Apply Benchmark to Analysis
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
