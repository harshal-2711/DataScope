export type FileType = "csv" | "xlsx" | "xls"

export interface DatasetPreviewRow {
  [column: string]: string | number | boolean | null
}

export interface DatasetSummary {
  filename: string
  file_type: FileType
  row_count: number
  column_count: number
  columns: string[]
  dtypes: Record<string, string>
  preview: DatasetPreviewRow[]
}

export type UploadState =
  | { status: "idle" }
  | { status: "selected"; file: File }
  | { status: "processing"; file: File }
  | { status: "success"; file: File; summary: DatasetSummary }
  | { status: "error"; file: File | null; message: string }
