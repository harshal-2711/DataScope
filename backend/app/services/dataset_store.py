"""Hybrid In-Memory + Persistent Storage Bridge for DataScope Datasets.

Maintains in-memory DataFrame cache for lightning-fast sub-millisecond calculation responses,
while hydrating from and syncing with the persistent database whenever needed.
"""
from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd

from app.core.config import settings


@dataclass
class StoredDataset:
    dataset_id: str
    filename: str
    file_type: str
    df: pd.DataFrame
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cache: dict[str, Any] = field(default_factory=dict)
    benchmark_df: Optional[pd.DataFrame] = None
    benchmark_filename: Optional[str] = None
    benchmark_created_at: Optional[datetime] = None


class DatasetStore:
    """Thread-safe dataset cache bounded with LRU eviction."""

    def __init__(self, max_entries: int) -> None:
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._entries: dict[str, StoredDataset] = {}

    def put(self, filename: str, file_type: str, df: pd.DataFrame, dataset_id: Optional[str] = None) -> str:
        d_id = str(dataset_id) if dataset_id else uuid.uuid4().hex
        entry = StoredDataset(
            dataset_id=d_id, filename=filename, file_type=file_type, df=df
        )
        with self._lock:
            self._entries[d_id] = entry
            while len(self._entries) > self._max_entries:
                oldest_id = next(iter(self._entries))
                del self._entries[oldest_id]
        return d_id

    def get(self, dataset_id: str) -> StoredDataset | None:
        key = str(dataset_id)
        with self._lock:
            return self._entries.get(key)

    def attach_benchmark(self, dataset_id: str, benchmark_filename: str, benchmark_df: pd.DataFrame) -> bool:
        """Attach a verified external market benchmark DataFrame to an existing dataset entry."""
        key = str(dataset_id)
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return False
            entry.benchmark_df = benchmark_df
            entry.benchmark_filename = benchmark_filename
            entry.benchmark_created_at = datetime.now(timezone.utc)
            entry.cache.pop("competition_intelligence", None)
            return True

    def remove_benchmark(self, dataset_id: str) -> bool:
        """Detach external benchmark DataFrame from dataset entry."""
        key = str(dataset_id)
        with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return False
            entry.benchmark_df = None
            entry.benchmark_filename = None
            entry.benchmark_created_at = None
            entry.cache.pop("competition_intelligence", None)
            return True

    def __len__(self) -> int:
        return len(self._entries)


_store = DatasetStore(max_entries=settings.MAX_STORED_DATASETS)
dataset_store = _store



def save_dataset(filename: str, file_type: str, df: pd.DataFrame, dataset_id: Optional[str] = None) -> str:
    """Store a parsed dataset into the cache and return its dataset_id."""
    return _store.put(filename, file_type, df, dataset_id=str(dataset_id) if dataset_id else None)


def get_dataset(dataset_id: str) -> StoredDataset | None:
    """Look up dataset from memory, or hydrate from persistent DB / Supabase Storage."""
    key = str(dataset_id)
    entry = _store.get(key)
    if entry is not None:
        return entry

    # Try hydrating from database
    try:
        import io
        from app.db.session import SessionLocal
        from app.models.dataset import Dataset
        from app.models.data_record import DataRecord
        from app.core.supabase_client import SupabaseStorageService

        db = SessionLocal()
        try:
            ds = db.query(Dataset).filter(Dataset.id == key).first()
            if ds:
                records = (
                    db.query(DataRecord)
                    .filter(DataRecord.dataset_id == key, DataRecord.is_deleted == 0)
                    .order_by(DataRecord.row_index.asc())
                    .all()
                )
                df = pd.DataFrame()
                if records:
                    rows = [json.loads(r.record_json) for r in records if r.record_json]
                    if rows:
                        df = pd.DataFrame(rows)

                # Fallback to Supabase Storage if no DataRecord rows stored yet
                if df.empty:
                    storage_paths = [
                        f"{ds.company_id}/{ds.id}.csv",
                        f"{ds.id}.csv"
                    ]
                    for sp in storage_paths:
                        csv_bytes = SupabaseStorageService.download_file("datasets", sp)
                        if csv_bytes:
                            df = pd.read_csv(io.BytesIO(csv_bytes))
                            break

                row_cnt = getattr(ds, "current_row_count", 0) or 0
                if not df.empty or row_cnt == 0:
                    save_dataset(ds.name, ds.file_type or "csv", df, dataset_id=str(ds.id))
                    return _store.get(key)
        finally:
            db.close()
    except Exception:
        pass

    return None


def get_dataset_or_raise(dataset_id: str) -> StoredDataset:
    from app.services.dataset_exceptions import DatasetNotFoundError

    entry = get_dataset(dataset_id)
    if entry is None:
        raise DatasetNotFoundError(
            f"Dataset '{dataset_id}' was not found. It may have expired "
            "from memory or the backend may have restarted — try "
            "uploading the file again."
        )
    return entry


def attach_benchmark(dataset_id: str, filename: str, df: pd.DataFrame) -> bool:
    """Attach benchmark DataFrame to the stored dataset entry."""
    return _store.attach_benchmark(dataset_id, filename, df)


def remove_benchmark(dataset_id: str) -> bool:
    """Remove attached benchmark DataFrame from the stored dataset entry."""
    return _store.remove_benchmark(dataset_id)


def clear_store() -> None:
    """Clear all entries from in-memory dataset store (testing helper)."""
    with _store._lock:
        _store._entries.clear()


def _debug_snapshot() -> dict[str, Any]:
    with _store._lock:
        return {k: v.filename for k, v in _store._entries.items()}
