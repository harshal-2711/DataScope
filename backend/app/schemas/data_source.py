"""Pydantic Schemas for Data Sources and Sync Jobs."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: str = Field(..., description="postgres, mysql, rest_api, google_sheets, file_upload, manual_entry")
    sync_frequency: str = Field("manual", description="manual, hourly, daily, weekly")
    config: Dict[str, Any] = Field(default_factory=dict)
    dataset_id: Optional[str] = None


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    sync_frequency: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_paused: Optional[bool] = None


class DataSourceResponse(BaseModel):
    id: str
    company_id: str
    dataset_id: Optional[str]
    name: str
    source_type: str
    status: str
    sync_frequency: str
    is_paused: bool
    last_sync_at: Optional[datetime]
    next_sync_at: Optional[datetime]
    last_error_message: Optional[str]
    total_records_synced: int
    created_at: datetime
    config_sanitized: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class DataSyncJobResponse(BaseModel):
    id: str
    data_source_id: str
    company_id: str
    status: str
    sync_type: str
    records_added: int
    records_updated: int
    records_rejected: int
    error_message: Optional[str]
    log_output: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    source_type: str
    config: Dict[str, Any]


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class DiscoverTablesRequest(BaseModel):
    source_type: str
    config: Dict[str, Any]


class TableMetadataItem(BaseModel):
    schema_name: Optional[str] = Field(None, alias="schema")
    name: str
    full_name: str
    type: Optional[str] = "BASE TABLE"


class DiscoverTablesResponse(BaseModel):
    success: bool
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class PreviewDataRequest(BaseModel):
    source_type: str
    config: Dict[str, Any]
    limit: Optional[int] = 20


class PreviewDataResponse(BaseModel):
    success: bool
    row_count_sample: Optional[int] = 0
    column_count: Optional[int] = 0
    columns: List[str] = Field(default_factory=list)
    dtypes: Dict[str, str] = Field(default_factory=dict)
    preview: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class ImportToDatasetRequest(BaseModel):
    connection_name: str
    source_type: str
    config: Dict[str, Any]


class ImportToDatasetResponse(BaseModel):
    dataset_id: str
    filename: str
    name: str
    file_type: str
    row_count: int
    column_count: int
    columns: List[str]
    dtypes: Dict[str, str]
    inferred_columns: Optional[List[Dict[str, Any]]] = None
    diagnostics: Optional[Dict[str, Any]] = None
    detected_currency: Optional[str] = None
    preview: List[Dict[str, Any]]
    message: str
