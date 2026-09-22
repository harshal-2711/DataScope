"""In-memory storage for uploaded datasets.

Phase 2 processed each upload statelessly (validate -> read -> summarize ->
respond, nothing retained). Phase 3 needs the full DataFrame to still be
around after the initial response so the recommendation engine can
aggregate it on demand, without re-uploading the file each time.

Deliberately NOT a database: this is a process-local, in-memory dict keyed
by a generated dataset_id, capped at `settings.MAX_STORED_DATASETS` with
oldest-first eviction. Restarting the backend clears it. This matches the
project's "no database, no persistence beyond memory" constraint while
still letting the frontend refer back to "the dataset it just uploaded" by
id across separate API calls.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

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


class DatasetStore:
    """Thread-safe, in-memory, capacity-bounded dataset store."""

    def __init__(self, max_entries: int) -> None:
        self._max_entries = max_entries
        self._lock = threading.Lock()
        # Insertion order == recency; dicts preserve insertion order.
        self._entries: dict[str, StoredDataset] = {}

    def put(self, filename: str, file_type: str, df: pd.DataFrame) -> str:
        dataset_id = uuid.uuid4().hex
        entry = StoredDataset(
            dataset_id=dataset_id, filename=filename, file_type=file_type, df=df
        )
        with self._lock:
            self._entries[dataset_id] = entry
            while len(self._entries) > self._max_entries:
                oldest_id = next(iter(self._entries))
                del self._entries[oldest_id]
        return dataset_id

    def get(self, dataset_id: str) -> StoredDataset | None:
        with self._lock:
            return self._entries.get(dataset_id)

    def __len__(self) -> int:  # pragma: no cover - convenience only
        return len(self._entries)


_store = DatasetStore(max_entries=settings.MAX_STORED_DATASETS)


def save_dataset(filename: str, file_type: str, df: pd.DataFrame) -> str:
    """Store a parsed dataset and return its generated dataset_id."""
    return _store.put(filename, file_type, df)


def get_dataset(dataset_id: str) -> StoredDataset | None:
    """Look up a previously stored dataset by id, or None if absent/evicted."""
    return _store.get(dataset_id)


def get_dataset_or_raise(dataset_id: str) -> StoredDataset:
    from app.services.dataset_exceptions import DatasetNotFoundError

    entry = _store.get(dataset_id)
    if entry is None:
        raise DatasetNotFoundError(
            f"Dataset '{dataset_id}' was not found. It may have expired "
            "from memory or the backend may have restarted — try "
            "uploading the file again."
        )
    return entry


def _debug_snapshot() -> dict[str, Any]:  # pragma: no cover - debugging aid
    with _store._lock:  # noqa: SLF001
        return {k: v.filename for k, v in _store._entries.items()}
