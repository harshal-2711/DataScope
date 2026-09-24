"""Company Membership & Role-Based Access Control Model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class Role:
    OWNER = "owner"
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class CompanyMembership(Base):
    __tablename__ = "company_memberships"


    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="analyst", nullable=False)  # "owner", "admin", "analyst", "viewer"
    invited_email = Column(String(255), nullable=True)
    invitation_token = Column(String(100), unique=True, nullable=True)
    status = Column(String(50), default="active", nullable=False)  # "active", "pending", "revoked"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="memberships")
    company = relationship("Company", back_populates="memberships")
