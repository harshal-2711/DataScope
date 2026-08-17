from typing import Any

from pydantic import BaseModel, Field


class DatasetSummary(BaseModel):
    filename: str
    file_type: str
    row_count: int
    column_count: int
    columns: list[str]
    dtypes: dict[str, str]
    preview: list[dict[str, Any]] = Field(
        description="First N rows of the dataset (N = settings.PREVIEW_ROW_COUNT)."
    )
