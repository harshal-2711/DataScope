"""Dataset Version Model for Immutable Audit Trail & Rollback Support."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    change_summary = Column(String(500), default="Initial upload", nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    col_count = Column(Integer, default=0, nullable=False)
    column_schema = Column(Text, nullable=True)  # JSON-encoded column schema & types
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    dataset = relationship("Dataset", back_populates="versions")
