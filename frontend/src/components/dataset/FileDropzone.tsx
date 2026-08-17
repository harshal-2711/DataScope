import { useRef, useState } from "react"
import { UploadCloud } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  ACCEPTED_EXTENSIONS,
  ACCEPTED_INPUT_ACCEPT,
  MAX_UPLOAD_SIZE_MB,
} from "@/config/dataset"

interface FileDropzoneProps {
  onFileSelected: (file: File) => void
  onRejected: (message: string) => void
}

function isAcceptedFile(file: File): boolean {
  const name = file.name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
}

export function FileDropzone({ onFileSelected, onRejected }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0]
    if (!file) return

    if (!isAcceptedFile(file)) {
      onRejected(
        `Unsupported file type. Supported formats: ${ACCEPTED_EXTENSIONS.join(", ")}`
      )
      return
    }

    if (file.size === 0) {
      onRejected("The selected file is empty.")
      return
    }

    if (file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024) {
      onRejected(`File exceeds the ${MAX_UPLOAD_SIZE_MB}MB upload limit.`)
      return
    }

    onFileSelected(file)
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
      }}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click()
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-16 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border hover:bg-muted/50"
      )}
    >
      <div className="rounded-full bg-muted p-3">
        <UploadCloud className="h-6 w-6 text-muted-foreground" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium">
          Drag and drop your dataset here, or click to browse
        </p>
        <p className="text-xs text-muted-foreground">
          Supported formats: CSV, XLSX, XLS — up to {MAX_UPLOAD_SIZE_MB}MB
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_INPUT_ACCEPT}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  )
}
