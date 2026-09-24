"""Data Sources & Live Data Connection API Endpoints for DataScope SaaS."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import TenantContext, get_current_company, require_role
from app.db.session import get_db
from app.models.data_source import DataSource
from app.models.data_sync_job import DataSyncJob
from app.models.membership import Role
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceResponse,
    DataSourceUpdate,
    DataSyncJobResponse,
    DiscoverTablesRequest,
    DiscoverTablesResponse,
    ImportToDatasetRequest,
    ImportToDatasetResponse,
    PreviewDataRequest,
    PreviewDataResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.services.data_connector_service import data_connector_service

router = APIRouter(prefix="/api/data-sources", tags=["Data Sources"])


def _sanitize_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive secrets like passwords, tokens, or secret keys in JSON response."""
    sanitized = {}
    for k, v in config_dict.items():
        if any(secret_kw in k.lower() for secret_kw in ("password", "secret", "token", "key")):
            sanitized[k] = "••••••••" if v else ""
        else:
            sanitized[k] = v
    return sanitized


def _to_response(source: DataSource) -> DataSourceResponse:
    cfg = {}
    if source.config_json:
        try:
            cfg = json.loads(source.config_json) if isinstance(source.config_json, str) else source.config_json
        except Exception:
            cfg = {}
    return DataSourceResponse(
        id=str(source.id),
        company_id=str(source.company_id),
        dataset_id=str(source.dataset_id) if source.dataset_id else None,
        name=source.name,
        source_type=source.source_type,
        status=source.status,
        sync_frequency=source.sync_frequency,
        is_paused=source.is_paused,
        last_sync_at=source.last_sync_at,
        next_sync_at=source.next_sync_at,
        last_error_message=source.last_error_message,
        total_records_synced=source.total_records_synced,
        created_at=source.created_at,
        config_sanitized=_sanitize_config(cfg),
    )


@router.get("", response_model=List[DataSourceResponse])
def list_data_sources(
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """List all saved data sources configured for the current company workspace."""
    sources = db.query(DataSource).filter(DataSource.company_id == tenant.company_id).order_by(DataSource.created_at.desc()).all()
    return [_to_response(s) for s in sources]


@router.post("", response_model=DataSourceResponse, status_code=status.HTTP_201_CREATED)
def create_data_source(
    payload: DataSourceCreate,
    tenant: TenantContext = Depends(require_role(Role.ANALYST)),
    db: Session = Depends(get_db),
):
    """Create and save a new data source connection for the current workspace."""
    now = datetime.now(timezone.utc)
    source = DataSource(
        company_id=tenant.company_id,
        dataset_id=payload.dataset_id,
        name=payload.name,
        source_type=payload.source_type,
        status="active",
        sync_frequency=payload.sync_frequency,
        config_json=json.dumps(payload.config or {}),
        is_paused=False,
        created_at=now,
        updated_at=now,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return _to_response(source)


@router.post("/test", response_model=TestConnectionResponse)
def test_connection_endpoint(
    payload: TestConnectionRequest,
    tenant: TenantContext = Depends(get_current_company),
):
    """Test connectivity for credentials or URL prior to creating a data source."""
    result = data_connector_service.test_connection(payload.source_type, payload.config)
    return TestConnectionResponse(
        success=result["success"],
        message=result["message"],
        details=result.get("details"),
    )


@router.post("/tables", response_model=DiscoverTablesResponse)
def discover_tables_endpoint(
    payload: DiscoverTablesRequest,
    tenant: TenantContext = Depends(get_current_company),
):
    """Inspect tables, views, and schemas for a database or source connection."""
    result = data_connector_service.fetch_tables_and_metadata(payload.source_type, payload.config)
    return DiscoverTablesResponse(
        success=result["success"],
        tables=result.get("tables", []),
        error=result.get("error"),
    )


@router.post("/preview", response_model=PreviewDataResponse)
def preview_data_endpoint(
    payload: PreviewDataRequest,
    tenant: TenantContext = Depends(get_current_company),
):
    """Fetch live sample rows and column schemas from the selected table or query."""
    result = data_connector_service.preview_data(payload.source_type, payload.config, limit=payload.limit or 20)
    return PreviewDataResponse(
        success=result["success"],
        row_count_sample=result.get("row_count_sample", 0),
        column_count=result.get("column_count", 0),
        columns=result.get("columns", []),
        dtypes=result.get("dtypes", {}),
        preview=result.get("preview", []),
        error=result.get("error"),
    )


@router.post("/import", response_model=ImportToDatasetResponse)
def import_to_dataset_endpoint(
    payload: ImportToDatasetRequest,
    tenant: TenantContext = Depends(require_role(Role.ANALYST)),
    db: Session = Depends(get_db),
):
    """Extract data from connection and register directly into an active DataScope analytics dataset."""
    try:
        result = data_connector_service.import_to_dataset(
            db=db,
            company_id=tenant.company_id,
            source_type=payload.source_type,
            config=payload.config,
            connection_name=payload.connection_name,
            user_id=tenant.user_id,
        )
        return ImportToDatasetResponse(
            dataset_id=result["dataset_id"],
            filename=result["filename"],
            name=result["name"],
            file_type=result["file_type"],
            row_count=result["row_count"],
            column_count=result["column_count"],
            columns=result["columns"],
            dtypes=result["dtypes"],
            inferred_columns=result.get("inferred_columns"),
            diagnostics=result.get("diagnostics"),
            detected_currency=result.get("detected_currency"),
            preview=result["preview"],
            message=result["message"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{data_source_id}", response_model=DataSourceResponse)
def get_data_source(
    data_source_id: str,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Get single data source configuration and sync health."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.company_id == tenant.company_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")
    return _to_response(source)


@router.put("/{data_source_id}", response_model=DataSourceResponse)
def update_data_source(
    data_source_id: str,
    payload: DataSourceUpdate,
    tenant: TenantContext = Depends(require_role(Role.ANALYST)),
    db: Session = Depends(get_db),
):
    """Update data source properties."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.company_id == tenant.company_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    if payload.name is not None:
        source.name = payload.name
    if payload.sync_frequency is not None:
        source.sync_frequency = payload.sync_frequency
    if payload.config is not None:
        # If user passed masked password, retain original password
        existing_cfg = json.loads(source.config_json) if isinstance(source.config_json, str) else (source.config_json or {})
        for k, v in payload.config.items():
            if v == "••••••••" and k in existing_cfg:
                payload.config[k] = existing_cfg[k]
        source.config_json = json.dumps(payload.config)
    if payload.is_paused is not None:
        source.is_paused = payload.is_paused
        source.status = "paused" if payload.is_paused else "active"

    source.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(source)
    return _to_response(source)


@router.post("/{data_source_id}/test", response_model=TestConnectionResponse)
def test_existing_data_source(
    data_source_id: str,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Test connectivity for an existing saved data source."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.company_id == tenant.company_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    cfg = json.loads(source.config_json) if isinstance(source.config_json, str) else (source.config_json or {})
    result = data_connector_service.test_connection(source.source_type, cfg)
    return TestConnectionResponse(
        success=result["success"],
        message=result["message"],
        details=result.get("details"),
    )


@router.post("/{data_source_id}/sync")
def trigger_manual_sync(
    data_source_id: str,
    tenant: TenantContext = Depends(require_role(Role.ANALYST)),
    db: Session = Depends(get_db),
):
    """Trigger an immediate data synchronization."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.company_id == tenant.company_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    result = data_connector_service.sync_source(
        db=db,
        data_source_id=source.id,
        company_id=tenant.company_id,
        sync_type="manual",
    )
    return result


@router.post("/{data_source_id}/pause", response_model=DataSourceResponse)
def pause_data_source(
    data_source_id: str,
    tenant: TenantContext = Depends(require_role(Role.ANALYST)),
    db: Session = Depends(get_db),
):
    """Pause scheduled data synchronization for a data source."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.company_id == tenant.company_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    source.is_paused = True
    source.status = "paused"
    source.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(source)
    return _to_response(source)


@router.post("/{data_source_id}/resume", response_model=DataSourceResponse)
def resume_data_source(
    data_source_id: str,
    tenant: TenantContext = Depends(require_role(Role.ANALYST)),
    db: Session = Depends(get_db),
):
    """Resume scheduled data synchronization for a data source."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.company_id == tenant.company_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    source.is_paused = False
    source.status = "active"
    source.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(source)
    return _to_response(source)


@router.delete("/{data_source_id}")
def delete_data_source(
    data_source_id: str,
    tenant: TenantContext = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    """Delete a data source connection."""
    source = db.query(DataSource).filter(
        DataSource.id == data_source_id,
        DataSource.company_id == tenant.company_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found.")

    db.delete(source)
    db.commit()
    return {"message": f"Data source '{source.name}' deleted successfully."}


@router.get("/{data_source_id}/jobs", response_model=List[DataSyncJobResponse])
def get_data_source_sync_jobs(
    data_source_id: str,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """List execution history and logs for a data source."""
    jobs = db.query(DataSyncJob).filter(
        DataSyncJob.data_source_id == data_source_id,
        DataSyncJob.company_id == tenant.company_id,
    ).order_by(DataSyncJob.started_at.desc()).limit(50).all()
    return jobs
