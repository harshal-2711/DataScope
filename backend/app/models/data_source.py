"""Data Source Model for DataScope Multi-Tenant SaaS Platform."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # "postgres", "mysql", "rest_api", "google_sheets", "file_upload", "manual_entry"
    status = Column(String(50), default="active", nullable=False)  # "active", "paused", "syncing", "error", "configured"
    
    # Configuration stored securely (JSON serialized)
    config_json = Column(Text, nullable=False, default="{}")
    
    # Sync settings
    sync_frequency = Column(String(50), default="manual", nullable=False)  # "manual", "hourly", "daily", "weekly"
    is_paused = Column(Boolean, default=False, nullable=False)
    
    last_sync_at = Column(DateTime, nullable=True)
    next_sync_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    
    # Record metrics
    total_records_synced = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company = relationship("Company", back_populates="data_sources")
    dataset = relationship("Dataset", foreign_keys=[dataset_id])
    sync_jobs = relationship("DataSyncJob", back_populates="data_source", cascade="all, delete-orphan", order_by="desc(DataSyncJob.started_at)")
