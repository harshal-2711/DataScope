import { AlertCircle } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

interface UploadErrorProps {
  message: string
  canRetry: boolean
  onRetry: () => void
  onStartOver: () => void
}

export function UploadError({
  message,
  canRetry,
  onRetry,
  onStartOver,
}: UploadErrorProps) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Upload failed</AlertTitle>
      <AlertDescription className="w-full space-y-3">
        <p>{message}</p>
        <div className="flex gap-2">
          {canRetry && (
            <Button size="sm" variant="outline" onClick={onRetry}>
              Try again
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={onStartOver}>
            Choose a different file
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  )
}
