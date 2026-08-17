"""Domain exceptions for dataset processing.

These are intentionally decoupled from FastAPI/HTTP — the API layer
(app/api/dataset.py) is responsible for translating them into HTTP
responses. This keeps the processing logic reusable and testable on
its own.
"""


class DatasetError(Exception):
    """Base exception for all dataset processing failures."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class UnsupportedFileTypeError(DatasetError):
    """Raised when the file extension isn't one DataScope supports."""


class EmptyFileError(DatasetError):
    """Raised when the uploaded file has zero bytes."""


class FileTooLargeError(DatasetError):
    """Raised when the uploaded file exceeds the configured size limit."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=413)


class UnreadableFileError(DatasetError):
    """Raised when pandas cannot parse the file (corrupted/invalid)."""


class EmptyDatasetError(DatasetError):
    """Raised when the parsed dataset has no rows or no columns."""
