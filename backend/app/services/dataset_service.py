"""Dataset processing logic.

Deliberately separate from the API layer (app/api/dataset.py) and from
any UI concerns. Everything here operates on raw bytes and pandas
DataFrames in memory only — nothing is written to disk, and the
original uploaded bytes are never mutated.
"""

import io
import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.core.config import settings
from app.services.dataset_exceptions import (
    EmptyDatasetError,
    EmptyFileError,
    FileTooLargeError,
    UnreadableFileError,
    UnsupportedFileTypeError,
)


def get_file_type(filename: str) -> str:
    """Resolve and validate the file extension. Returns a normalized type key."""
    extension = Path(filename).suffix.lower()
    if extension not in settings.ALLOWED_EXTENSIONS:
        supported = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension or 'unknown'}'. "
            f"Supported formats: {supported}"
        )
    return settings.ALLOWED_EXTENSIONS[extension]


def validate_content_type(content_type: Optional[str], file_type: str) -> None:
    """Best-effort MIME sniff check.

    Browsers/OSes report inconsistent MIME types for CSV/Excel files
    (text/csv, application/vnd.ms-excel, application/octet-stream, or
    nothing at all are all common and valid). Rather than maintain an
    exact allow-list that will false-positive-reject legitimate files,
    we only reject content types that are obviously wrong for a
    dataset file. The real validation is: can pandas parse it?
    """
    if not content_type:
        return

    obviously_wrong_prefixes = ("image/", "video/", "audio/")
    obviously_wrong_types = {"application/pdf", "text/html", "application/zip"}

    # .xlsx files are zip-based and sometimes reported as application/zip —
    # don't reject that combination.
    if content_type in obviously_wrong_types and not (
        file_type == "xlsx" and content_type == "application/zip"
    ):
        raise UnsupportedFileTypeError(
            f"The file's content type ('{content_type}') does not match a "
            "supported dataset format."
        )

    if content_type.startswith(obviously_wrong_prefixes):
        raise UnsupportedFileTypeError(
            f"The file's content type ('{content_type}') does not match a "
            "supported dataset format."
        )


def validate_size(contents: bytes) -> None:
    """Reject empty files and files over the configured size limit."""
    if len(contents) == 0:
        raise EmptyFileError("The uploaded file is empty.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise FileTooLargeError(
            f"File is {size_mb:.1f}MB, which exceeds the "
            f"{settings.MAX_UPLOAD_SIZE_MB}MB upload limit."
        )


def read_dataframe(contents: bytes, file_type: str) -> pd.DataFrame:
    """Parse the uploaded bytes into a DataFrame. Original bytes are untouched."""
    buffer = io.BytesIO(contents)

    try:
        if file_type == "csv":
            df = pd.read_csv(buffer)
        elif file_type == "xlsx":
            df = pd.read_excel(buffer, engine="openpyxl")
        elif file_type == "xls":
            df = pd.read_excel(buffer, engine="xlrd")
        else:  # pragma: no cover - guarded by get_file_type earlier
            raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}")
    except UnsupportedFileTypeError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise EmptyDatasetError("The file contains no data.") from exc
    except Exception as exc:
        raise UnreadableFileError(
            "The file could not be read. It may be corrupted, malformed, "
            f"or not a valid {file_type.upper()} file. "
            f"(details: {type(exc).__name__})"
        ) from exc

    if df.shape[1] == 0:
        raise EmptyDatasetError("The dataset contains no columns.")
    if df.shape[0] == 0:
        raise EmptyDatasetError("The dataset contains no rows.")

    return df


def build_summary(df: pd.DataFrame, filename: str, file_type: str) -> dict[str, Any]:
    """Build the metadata + preview payload returned to the frontend.

    Uses pandas' own JSON serialization (via to_json) to safely handle
    NaN -> null and numpy scalar types -> native Python types, rather
    than hand-rolling type coercion.
    """
    dtypes = {str(col): str(df[col].dtype) for col in df.columns}

    preview_df = df.head(settings.PREVIEW_ROW_COUNT)
    preview: list[dict[str, Any]] = json.loads(
        preview_df.to_json(orient="records", date_format="iso")
    )

    return {
        "filename": filename,
        "file_type": file_type,
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "columns": [str(col) for col in df.columns],
        "dtypes": dtypes,
        "preview": preview,
    }


def process_upload(
   filename: str, contents: bytes, content_type: Optional[str]
) -> dict[str, Any]:
    """Full validate -> read -> summarize pipeline for one uploaded file."""
    file_type = get_file_type(filename)
    validate_content_type(content_type, file_type)
    validate_size(contents)
    df = read_dataframe(contents, file_type)
    return build_summary(df, filename, file_type)
