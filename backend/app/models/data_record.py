"""Data Record Model for Dynamic Row-Level Multi-Tenant Storage."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class DataRecord(Base):
    __tablename__ = "data_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    row_index = Column(Integer, nullable=False, index=True)
    record_json = Column(Text, nullable=False)  # JSON-serialized row dict
    is_deleted = Column(Integer, default=0, nullable=False)  # Soft-delete support
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    dataset = relationship("Dataset", back_populates="records")

    def to_dict(self) -> Dict[str, Any]:
        """Parse the stored JSON string into a Python dict with row ID."""
        try:
            d = json.loads(self.record_json)
            d["__record_id"] = self.id
            d["__row_index"] = self.row_index
            return d
        except Exception:
            return {"__record_id": self.id, "__row_index": self.row_index}
