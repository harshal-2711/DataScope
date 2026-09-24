"""Data Sync Job Model for DataScope Data Pipelines."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class DataSyncJob(Base):
    __tablename__ = "data_sync_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data_source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(String(50), default="pending", nullable=False)  # "pending", "running", "success", "failed"
    sync_type = Column(String(50), default="manual", nullable=False)  # "manual", "scheduled", "webhook", "full_refresh"
    
    records_added = Column(Integer, default=0, nullable=False)
    records_updated = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    
    error_message = Column(Text, nullable=True)
    log_output = Column(Text, nullable=True)
    
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    data_source = relationship("DataSource", back_populates="sync_jobs")
