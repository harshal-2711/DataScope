"""Live Data Management API Router for Row-Level CRUD, Search, Pagination & Versioning."""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import TenantContext, get_current_company, require_role
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.data_record import DataRecord
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.user import User
from app.schemas.data_management import (
    BulkImportRequest,
    BulkImportResponse,
    ColumnSchemaItem,
    DatasetListItem,
    PaginatedRecordsResponse,
    RecordCreateRequest,
    RecordItemResponse,
    RecordUpdateRequest,
    RollbackResponse,
    VersionHistoryItem,
)
from app.services import dataset_store
from app.services.column_profiler import profile_dataset
from app.services.realtime_manager import realtime_manager

router = APIRouter(prefix="/data-management", tags=["Live Data Management"])


def _rebuild_dataset_dataframe(db: Session, dataset_id: str) -> pd.DataFrame:
    """Rebuild in-memory DataFrame from active database records and update cache."""
    records = (
        db.query(DataRecord)
        .filter(DataRecord.dataset_id == dataset_id, DataRecord.is_deleted == 0)
        .order_by(DataRecord.row_index.asc())
        .all()
    )
    rows = []
    for r in records:
        try:
            d = json.loads(r.record_json)
            rows.append(d)
        except Exception:
            pass

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    return df


@router.get("/datasets", response_model=List[DatasetListItem])
def list_company_datasets(
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """List all persisted datasets belonging to the authenticated tenant company."""
    datasets = (
        db.query(Dataset)
        .filter(Dataset.company_id == tenant.company_id)
        .order_by(Dataset.updated_at.desc())
        .all()
    )
    result = []
    from app.models.data_source import DataSource
    for d in datasets:
        ds = db.query(DataSource).filter(DataSource.dataset_id == d.id).first()
        source_type = ds.source_type if ds else "file_upload"
        data_source_id = ds.id if ds else None

        result.append(
            DatasetListItem(
                id=str(d.id),
                company_id=str(d.company_id),
                name=d.name,
                file_type=d.file_type or "csv",
                row_count=getattr(d, "current_row_count", 0) or 0,
                column_count=getattr(d, "current_col_count", 0) or 0,
                currency_symbol=d.currency_symbol,
                domain_id=d.domain_id,
                domain_name=d.domain_name,
                active_version_number=d.active_version_number or 1,
                created_at=d.created_at,
                updated_at=d.updated_at,
                data_source_id=str(data_source_id) if data_source_id else None,
                source_type=source_type,
                is_active=True,
            )
        )
    return result


@router.get("/active-dataset")
def get_active_company_dataset(
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Return the most recent active dataset for the authenticated company workspace."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.company_id == tenant.company_id)
        .order_by(Dataset.updated_at.desc())
        .first()
    )
    if not dataset:
        return {"active": False, "dataset": None}

    # Ensure cached in dataset_store
    stored = dataset_store.get_dataset(str(dataset.id))
    if not stored:
        df = _rebuild_dataset_dataframe(db, str(dataset.id))
        row_cnt = getattr(dataset, "current_row_count", 0) or 0
        if not df.empty or row_cnt == 0:
            dataset_store.save_dataset(dataset.name, dataset.file_type or "csv", df, dataset_id=str(dataset.id))
            stored = dataset_store.get_dataset(str(dataset.id))

    from app.models.data_source import DataSource
    ds = db.query(DataSource).filter(DataSource.dataset_id == dataset.id).first()
    source_type = ds.source_type if ds else "file_upload"
    data_source_id = ds.id if ds else None

    # Retrieve columns from active DatasetVersion or DataFrame
    cols = []
    version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset.id)
        .order_by(DatasetVersion.version_number.desc())
        .first()
    )
    if version and version.column_schema:
        try:
            cols = json.loads(version.column_schema)
        except Exception:
            pass
    elif stored and stored.df is not None:
        cols = [{"name": str(c), "data_type": "string", "semantic_type": "text"} for c in stored.df.columns]

    return {
        "active": True,
        "dataset": {
            "id": str(dataset.id),
            "name": dataset.name,
            "file_type": dataset.file_type,
            "row_count": getattr(dataset, "current_row_count", 0) or 0,
            "column_count": getattr(dataset, "current_col_count", 0) or 0,
            "currency_symbol": dataset.currency_symbol,
            "domain_id": dataset.domain_id,
            "domain_name": dataset.domain_name,
            "active_version_number": dataset.active_version_number or 1,
            "columns": cols,
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
            "data_source_id": str(data_source_id) if data_source_id else None,
            "source_type": source_type,
        },
    }


@router.post("/datasets/{dataset_id}/activate")
def activate_company_dataset(
    dataset_id: str,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Set a specific dataset as active for the workspace and ensure it is hydrated in memory."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found in this company workspace.")

    # Update updated_at so it stays most recent
    dataset.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Hydrate in memory
    stored = dataset_store.get_dataset(str(dataset.id))
    if not stored:
        df = _rebuild_dataset_dataframe(db, str(dataset.id))
        dataset_store.save_dataset(dataset.name, dataset.file_type or "csv", df, dataset_id=str(dataset.id))

    return {
        "status": "success",
        "dataset_id": str(dataset.id),
        "name": dataset.name,
        "row_count": getattr(dataset, "current_row_count", 0) or 0,
        "column_count": getattr(dataset, "current_col_count", 0) or 0,
    }


@router.get("/datasets/{dataset_id}/records", response_model=PaginatedRecordsResponse)
def get_dataset_records(
    dataset_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=5, le=200),
    search: Optional[str] = Query(None),
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Fetch paginated, searchable records for the active dataset."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    cached_entry = dataset_store.get_dataset(dataset_id)

    if not dataset and cached_entry is not None:
        # Auto-provision Dataset record for active cached dataset
        now = datetime.now(timezone.utc)
        dataset = Dataset(
            id=dataset_id,
            company_id=tenant.company_id,
            name=cached_entry.filename,
            file_type=cached_entry.file_type or "csv",
            active_version_number=1,
            current_row_count=int(cached_entry.df.shape[0]),
            current_col_count=int(cached_entry.df.shape[1]),
            created_at=now,
            updated_at=now,
        )
        db.add(dataset)
        try:
            db.commit()
        except Exception:
            db.rollback()
            dataset = (
                db.query(Dataset)
                .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
                .first()
            )

    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found in this company workspace.")

    query = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_id, DataRecord.is_deleted == 0)

    if search:
        search_clean = search.strip().lower()
        query = query.filter(DataRecord.record_json.ilike(f"%{search_clean}%"))

    db_records_count = query.count()

    if db_records_count == 0 and cached_entry is not None and not cached_entry.df.empty:
        df = cached_entry.df
        if search:
            search_clean = search.strip().lower()
            mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(search_clean).any(), axis=1)
            df = df[mask]

        total_records = len(df)
        total_pages = max(1, math.ceil(total_records / page_size))
        offset = (page - 1) * page_size
        sliced_df = df.iloc[offset : offset + page_size]

        col_schemas: List[ColumnSchemaItem] = []
        profiles = profile_dataset(cached_entry.df)
        for p in profiles:
            col_schemas.append(
                ColumnSchemaItem(
                    name=p.name,
                    dtype=str(p.dtype),
                    semantic_role=str(p.role),
                    is_numeric=(p.role == "numeric"),
                    is_datetime=(p.role == "datetime"),
                    is_categorical=(p.role in ("categorical", "boolean")),
                )
            )

        formatted_records = []
        for idx, row in sliced_df.iterrows():
            formatted_records.append(
                RecordItemResponse(
                    record_id=f"row-{idx}",
                    row_index=int(idx) + 1,
                    data=row.to_dict(),
                    updated_at=datetime.now(timezone.utc),
                )
            )

        return PaginatedRecordsResponse(
            dataset_id=dataset.id,
            dataset_name=dataset.name,
            total_records=total_records,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            current_version=dataset.active_version_number,
            columns=col_schemas,
            records=formatted_records,
        )

    total_records = db_records_count
    total_pages = max(1, math.ceil(total_records / page_size))
    offset = (page - 1) * page_size

    records_page = query.order_by(DataRecord.row_index.asc()).offset(offset).limit(page_size).all()

    # Column schema detection
    col_schemas: List[ColumnSchemaItem] = []
    if cached_entry is not None and not cached_entry.df.empty:
        profiles = profile_dataset(cached_entry.df)
        for p in profiles:
            col_schemas.append(
                ColumnSchemaItem(
                    name=p.name,
                    dtype=str(p.dtype),
                    semantic_role=str(p.role),
                    is_numeric=(p.role == "numeric"),
                    is_datetime=(p.role == "datetime"),
                    is_categorical=(p.role in ("categorical", "boolean")),
                )
            )
    elif records_page:
        first_row = records_page[0].to_dict()
        for k in first_row.keys():
            if not k.startswith("__"):
                col_schemas.append(ColumnSchemaItem(name=k, dtype="string"))

    formatted_records = [
        RecordItemResponse(
            record_id=str(r.id),
            row_index=r.row_index,
            data=r.to_dict(),
            updated_at=r.updated_at,
        )
        for r in records_page
    ]

    return PaginatedRecordsResponse(
        dataset_id=str(dataset.id),
        dataset_name=dataset.name,
        total_records=total_records,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        current_version=dataset.active_version_number,
        columns=col_schemas,
        records=formatted_records,
    )


@router.post("/datasets/{dataset_id}/records", response_model=RecordItemResponse, status_code=status.HTTP_201_CREATED)
async def add_dataset_record(
    dataset_id: str,
    payload: RecordCreateRequest,
    tenant: TenantContext = Depends(require_role("analyst")),
    db: Session = Depends(get_db),
):
    """Add a single new business record, advance version number, and trigger real-time recalculation."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found in this company workspace.")

    # 1. Compute next row index
    current_count = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_id, DataRecord.is_deleted == 0).count()
    new_row_index = current_count + 1

    # 2. Advance version number
    new_version_num = dataset.active_version_number + 1
    dataset.active_version_number = new_version_num
    dataset.current_row_count = new_row_index
    dataset.updated_at = datetime.now(timezone.utc)

    # Clean payload data (strip internal keys)
    cleaned_data = {k: v for k, v in payload.data.items() if not k.startswith("__")}

    new_version = DatasetVersion(
        id=str(uuid.uuid4()),
        dataset_id=dataset.id,
        version_number=new_version_num,
        change_summary=f"Added 1 record (Row {new_row_index})",
        row_count=new_row_index,
        col_count=len(cleaned_data),
        created_by_id=tenant.user.id,
    )
    db.add(new_version)
    db.flush()

    new_record = DataRecord(
        id=str(uuid.uuid4()),
        dataset_id=dataset.id,
        version_id=new_version.id,
        row_index=new_row_index,
        record_json=json.dumps(cleaned_data),
        is_deleted=0,
    )
    db.add(new_record)

    # 3. Audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        company_id=tenant.company_id,
        user_id=tenant.user.id,
        user_email=tenant.user.email,
        action="RECORD_ADD",
        target_type="record",
        target_id=new_record.id,
        details_json=json.dumps({"version": new_version_num, "row_index": new_row_index}),
    )
    db.add(audit)
    db.commit()
    db.refresh(new_record)

    # 4. Rebuild in-memory DataFrame & broadcast WebSocket event
    df = _rebuild_dataset_dataframe(db, dataset.id)
    dataset_store.save_dataset(dataset.name, dataset.file_type, df, dataset_id=dataset.id)

    await realtime_manager.broadcast_to_company(
        tenant.company_id,
        "DATASET_UPDATED",
        {
            "dataset_id": dataset.id,
            "version": new_version_num,
            "action": "RECORD_ADD",
            "total_rows": new_row_index,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return RecordItemResponse(
        record_id=new_record.id,
        row_index=new_record.row_index,
        data=new_record.to_dict(),
        updated_at=new_record.updated_at,
    )


@router.put("/datasets/{dataset_id}/records/{record_id}", response_model=RecordItemResponse)
async def update_dataset_record(
    dataset_id: str,
    record_id: str,
    payload: RecordUpdateRequest,
    tenant: TenantContext = Depends(require_role("analyst")),
    db: Session = Depends(get_db),
):
    """Update a specific record inline, create a new version snapshot, and trigger real-time recalculation."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    record = (
        db.query(DataRecord)
        .filter(DataRecord.id == record_id, DataRecord.dataset_id == dataset_id, DataRecord.is_deleted == 0)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")

    cleaned_data = {k: v for k, v in payload.data.items() if not k.startswith("__")}
    record.record_json = json.dumps(cleaned_data)
    record.updated_at = datetime.now(timezone.utc)

    # Advance version
    new_version_num = dataset.active_version_number + 1
    dataset.active_version_number = new_version_num
    dataset.updated_at = datetime.now(timezone.utc)

    new_version = DatasetVersion(
        id=str(uuid.uuid4()),
        dataset_id=dataset.id,
        version_number=new_version_num,
        change_summary=f"Updated record (Row {record.row_index})",
        row_count=dataset.current_row_count,
        col_count=len(cleaned_data),
        created_by_id=tenant.user.id,
    )
    db.add(new_version)
    db.commit()
    db.refresh(record)

    # Rebuild in-memory DataFrame
    df = _rebuild_dataset_dataframe(db, dataset.id)
    dataset_store.save_dataset(dataset.name, dataset.file_type, df, dataset_id=dataset.id)

    await realtime_manager.broadcast_to_company(
        tenant.company_id,
        "DATASET_UPDATED",
        {
            "dataset_id": dataset.id,
            "version": new_version_num,
            "action": "RECORD_UPDATE",
            "total_rows": dataset.current_row_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return RecordItemResponse(
        record_id=record.id,
        row_index=record.row_index,
        data=record.to_dict(),
        updated_at=record.updated_at,
    )


@router.delete("/datasets/{dataset_id}/records/{record_id}")
async def delete_dataset_record(
    dataset_id: str,
    record_id: str,
    tenant: TenantContext = Depends(require_role("analyst")),
    db: Session = Depends(get_db),
):
    """Delete a record from the dataset and trigger real-time recalculation."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    record = (
        db.query(DataRecord)
        .filter(DataRecord.id == record_id, DataRecord.dataset_id == dataset_id, DataRecord.is_deleted == 0)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")

    record.is_deleted = 1
    new_count = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_id, DataRecord.is_deleted == 0).count()
    new_version_num = dataset.active_version_number + 1
    dataset.active_version_number = new_version_num
    dataset.current_row_count = new_count
    dataset.updated_at = datetime.now(timezone.utc)

    new_version = DatasetVersion(
        id=str(uuid.uuid4()),
        dataset_id=dataset.id,
        version_number=new_version_num,
        change_summary=f"Deleted record (Row {record.row_index})",
        row_count=new_count,
        col_count=dataset.current_col_count,
        created_by_id=tenant.user.id,
    )
    db.add(new_version)
    db.commit()

    df = _rebuild_dataset_dataframe(db, dataset.id)
    dataset_store.save_dataset(dataset.name, dataset.file_type, df, dataset_id=dataset.id)

    await realtime_manager.broadcast_to_company(
        tenant.company_id,
        "DATASET_UPDATED",
        {
            "dataset_id": dataset.id,
            "version": new_version_num,
            "action": "RECORD_DELETE",
            "total_rows": new_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {"status": "success", "message": "Record successfully deleted.", "new_version": new_version_num}


@router.post("/datasets/{dataset_id}/bulk-import", response_model=BulkImportResponse)
async def bulk_import_records(
    dataset_id: str,
    payload: BulkImportRequest,
    tenant: TenantContext = Depends(require_role("analyst")),
    db: Session = Depends(get_db),
):
    """Bulk import / append multiple records into the dataset."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    if not payload.records:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No records provided for bulk import.")

    current_count = db.query(DataRecord).filter(DataRecord.dataset_id == dataset_id, DataRecord.is_deleted == 0).count()
    new_version_num = dataset.active_version_number + 1
    new_total_count = current_count + len(payload.records)

    new_version = DatasetVersion(
        id=str(uuid.uuid4()),
        dataset_id=dataset.id,
        version_number=new_version_num,
        change_summary=payload.change_summary or f"Bulk imported {len(payload.records)} records",
        row_count=new_total_count,
        col_count=len(payload.records[0]) if payload.records else dataset.current_col_count,
        created_by_id=tenant.user.id,
    )
    db.add(new_version)
    db.flush()

    for idx, row in enumerate(payload.records, start=current_count + 1):
        cleaned = {k: v for k, v in row.items() if not k.startswith("__")}
        record = DataRecord(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            version_id=new_version.id,
            row_index=idx,
            record_json=json.dumps(cleaned),
            is_deleted=0,
        )
        db.add(record)

    dataset.active_version_number = new_version_num
    dataset.current_row_count = new_total_count
    dataset.updated_at = datetime.now(timezone.utc)
    db.commit()

    df = _rebuild_dataset_dataframe(db, dataset.id)
    dataset_store.save_dataset(dataset.name, dataset.file_type, df, dataset_id=dataset.id)

    await realtime_manager.broadcast_to_company(
        tenant.company_id,
        "DATASET_UPDATED",
        {
            "dataset_id": dataset.id,
            "version": new_version_num,
            "action": "BULK_IMPORT",
            "imported_count": len(payload.records),
            "total_rows": new_total_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return BulkImportResponse(
        imported_count=len(payload.records),
        total_records=new_total_count,
        new_version_number=new_version_num,
        message=f"Successfully imported {len(payload.records)} records into version {new_version_num}.",
    )


@router.get("/datasets/{dataset_id}/versions", response_model=List[VersionHistoryItem])
def get_dataset_version_history(
    dataset_id: str,
    tenant: TenantContext = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """List all version snapshots and audit history for the dataset."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    from sqlalchemy import cast, String
    versions = (
        db.query(DatasetVersion, User)
        .outerjoin(User, cast(User.id, String) == cast(DatasetVersion.created_by_id, String))
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
        .all()
    )

    return [
        VersionHistoryItem(
            id=str(v.id),
            version_number=v.version_number,
            change_summary=v.change_summary,
            row_count=v.row_count,
            col_count=v.col_count,
            created_at=v.created_at,
            created_by=u.email if u else "System",
            is_active=(v.version_number == dataset.active_version_number),
        )
        for v, u in versions
    ]


@router.post("/datasets/{dataset_id}/rollback/{version_number}", response_model=RollbackResponse)
async def rollback_dataset_version(
    dataset_id: str,
    version_number: int,
    tenant: TenantContext = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Rollback dataset state to a specific historical version number."""
    dataset = (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id, Dataset.company_id == tenant.company_id)
        .first()
    )
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    target_version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.version_number == version_number)
        .first()
    )
    if not target_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Version {version_number} not found.")

    dataset.active_version_number = version_number
    dataset.current_row_count = target_version.row_count
    dataset.updated_at = datetime.now(timezone.utc)
    db.commit()

    df = _rebuild_dataset_dataframe(db, dataset.id)
    dataset_store.save_dataset(dataset.name, dataset.file_type, df, dataset_id=dataset.id)

    await realtime_manager.broadcast_to_company(
        tenant.company_id,
        "DATASET_UPDATED",
        {
            "dataset_id": dataset.id,
            "version": version_number,
            "action": "ROLLBACK",
            "total_rows": target_version.row_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return RollbackResponse(
        dataset_id=dataset.id,
        restored_version_number=version_number,
        active_row_count=target_version.row_count,
        message=f"Dataset successfully restored to version {version_number}.",
    )
