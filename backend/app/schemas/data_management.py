"""Pydantic Schemas for Live Data Management, Search, Pagination & Versioning."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecordItemResponse(BaseModel):
    record_id: str
    row_index: int
    data: Dict[str, Any]
    updated_at: datetime


class ColumnSchemaItem(BaseModel):
    name: str
    dtype: str
    semantic_role: str = "general"
    is_numeric: bool = False
    is_datetime: bool = False
    is_categorical: bool = False


class PaginatedRecordsResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    total_records: int
    page: int
    page_size: int
    total_pages: int
    current_version: int
    columns: List[ColumnSchemaItem]
    records: List[RecordItemResponse]


class RecordCreateRequest(BaseModel):
    data: Dict[str, Any]


class RecordUpdateRequest(BaseModel):
    data: Dict[str, Any]


class BulkImportRequest(BaseModel):
    records: List[Dict[str, Any]]
    change_summary: Optional[str] = "Bulk record import"


class BulkImportResponse(BaseModel):
    imported_count: int
    total_records: int
    new_version_number: int
    message: str


class VersionHistoryItem(BaseModel):
    id: str
    version_number: int
    change_summary: str
    row_count: int
    col_count: int
    created_at: datetime
    created_by: Optional[str] = None
    is_active: bool = False


class RollbackResponse(BaseModel):
    dataset_id: str
    restored_version_number: int
    active_row_count: int
    message: str


class DatasetListItem(BaseModel):
    id: str
    company_id: str
    name: str
    file_type: str
    row_count: int
    column_count: int
    currency_symbol: Optional[str] = None
    domain_id: Optional[str] = None
    domain_name: Optional[str] = None
    active_version_number: int
    created_at: datetime
    updated_at: datetime
    data_source_id: Optional[str] = None
    source_type: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True

