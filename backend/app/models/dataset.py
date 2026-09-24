"""Dataset Model for Multi-Tenant Data Storage."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), default="dataset.csv", nullable=True)
    file_type = Column(String(50), default="csv", nullable=False)
    active_version_number = Column(Integer, default=1, nullable=False)
    current_row_count = Column(Integer, default=0, nullable=False)
    current_col_count = Column(Integer, default=0, nullable=False)
    currency_symbol = Column(String(10), default="Rs. ", nullable=False)
    domain_id = Column(String(100), default="general_business", nullable=False)
    domain_name = Column(String(255), default="General Business", nullable=False)
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company = relationship("Company", back_populates="datasets")
    creator = relationship("User", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan", order_by="desc(DatasetVersion.version_number)")
    records = relationship("DataRecord", back_populates="dataset", cascade="all, delete-orphan")
