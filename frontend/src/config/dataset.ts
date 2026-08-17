// Mirrors backend/app/core/config.py Settings — keep these two in sync
// if the limit or supported formats ever change.
export const MAX_UPLOAD_SIZE_MB = 10
export const ACCEPTED_EXTENSIONS = [".csv", ".xlsx", ".xls"]
export const ACCEPTED_INPUT_ACCEPT = ACCEPTED_EXTENSIONS.join(",")
