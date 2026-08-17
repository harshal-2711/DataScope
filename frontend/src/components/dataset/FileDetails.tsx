import { FileSpreadsheet, Loader2, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

interface FileDetailsProps {
  file: File
  isProcessing: boolean
  onRemove: () => void
  onAnalyze: () => void
}

export function FileDetails({
  file,
  isProcessing,
  onRemove,
  onAnalyze,
}: FileDetailsProps) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-4 py-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="shrink-0 rounded-full bg-muted p-2">
            <FileSpreadsheet className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium">{file.name}</p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(file.size)}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={onRemove}
            disabled={isProcessing}
            aria-label="Remove file"
          >
            <X className="h-4 w-4" />
          </Button>
          <Button onClick={onAnalyze} disabled={isProcessing}>
            {isProcessing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing…
              </>
            ) : (
              "Analyze Dataset"
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
