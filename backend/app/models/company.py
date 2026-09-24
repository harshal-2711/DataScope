"""Company (Tenant Workspace) Model for DataScope SaaS Platform."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    domain_type = Column(String(100), default="General Business", nullable=False)
    logo_url = Column(String(500), nullable=True)
    owner_id = Column(String(36), nullable=False)
    industry = Column(String(100), default="SaaS / Technology", nullable=True)
    company_size = Column(String(50), default="11-50 Employees", nullable=True)
    country = Column(String(100), default="United States", nullable=True)
    primary_objective = Column(String(255), default="Revenue Growth & Margin Protection", nullable=True)
    settings = Column(String(4000), default="{}", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    memberships = relationship("CompanyMembership", back_populates="company", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="company", cascade="all, delete-orphan")
    data_sources = relationship("DataSource", back_populates="company", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="company", cascade="all, delete-orphan")

