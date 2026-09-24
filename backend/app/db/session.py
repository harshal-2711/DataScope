"""Database Session and Connection Management for DataScope Platform.

Supports PostgreSQL (production Supabase) and SQLite (isolated tests/local dev).
Provides dependency injection helper `get_db()` for FastAPI route endpoints.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger("datascope.db")

is_postgres = settings.DATABASE_URL.startswith("postgresql") or settings.DATABASE_URL.startswith("postgres")

# Configure database engine arguments
if is_postgres:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300,
        pool_pre_ping=True,
        echo=False,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_diagnostics() -> Dict[str, Any]:
    """Return safe diagnostics about the active database engine without exposing secrets."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        return {
            "engine": "SQLite",
            "is_postgres": False,
            "target": "local_file",
            "is_production": False,
        }
    
    # Safe parse of PostgreSQL host / project
    match = re.search(r"@([^:/]+)", url)
    host = match.group(1) if match else "remote_postgres"
    
    return {
        "engine": "PostgreSQL",
        "is_postgres": True,
        "target": host,
        "is_production": True,
        "ssl": "sslmode=require" in url or "supabase" in host.lower(),
    }


def init_db() -> None:
    """Initialize all database tables and perform lightweight schema migrations."""
    from app.models import (  # noqa: F401
        user,
        company,
        membership,
        dataset,
        dataset_version,
        data_record,
        audit_log,
        data_source,
        data_sync_job,
    )
    Base.metadata.create_all(bind=engine)

    diag = get_database_diagnostics()
    logger.info(f"Database initialized: engine={diag['engine']}, target={diag['target']}")

    with engine.connect() as conn:
        if diag["is_postgres"]:
            # PostgreSQL non-destructive additive column checks
            try:
                conn.execute(text("""
                    ALTER TABLE IF EXISTS public.profiles
                        ADD COLUMN IF NOT EXISTS hashed_password TEXT,
                        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true,
                        ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT false,
                        ADD COLUMN IF NOT EXISTS auth_provider TEXT NOT NULL DEFAULT 'local',
                        ADD COLUMN IF NOT EXISTS google_id TEXT,
                        ADD COLUMN IF NOT EXISTS reset_password_token TEXT,
                        ADD COLUMN IF NOT EXISTS reset_password_expires_at TIMESTAMPTZ;
                """))
                conn.execute(text("""
                    ALTER TABLE IF EXISTS public.companies
                        ADD COLUMN IF NOT EXISTS owner_id UUID,
                        ADD COLUMN IF NOT EXISTS domain_type TEXT NOT NULL DEFAULT 'General Business',
                        ADD COLUMN IF NOT EXISTS logo_url TEXT;
                """))
                conn.execute(text("""
                    ALTER TABLE IF EXISTS public.company_memberships
                        ADD COLUMN IF NOT EXISTS invited_email TEXT,
                        ADD COLUMN IF NOT EXISTS invitation_token TEXT,
                        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
                """))
                conn.execute(text("""
                    ALTER TABLE IF EXISTS public.datasets
                        ADD COLUMN IF NOT EXISTS name TEXT,
                        ADD COLUMN IF NOT EXISTS file_type TEXT NOT NULL DEFAULT 'csv',
                        ADD COLUMN IF NOT EXISTS active_version_number INT NOT NULL DEFAULT 1,
                        ADD COLUMN IF NOT EXISTS current_row_count INT NOT NULL DEFAULT 0,
                        ADD COLUMN IF NOT EXISTS current_col_count INT NOT NULL DEFAULT 0,
                        ADD COLUMN IF NOT EXISTS currency_symbol TEXT NOT NULL DEFAULT 'Rs. ',
                        ADD COLUMN IF NOT EXISTS domain_id TEXT NOT NULL DEFAULT 'general_business',
                        ADD COLUMN IF NOT EXISTS domain_name TEXT NOT NULL DEFAULT 'General Business',
                        ADD COLUMN IF NOT EXISTS created_by_id UUID;
                """))
                conn.execute(text("""
                    ALTER TABLE IF EXISTS public.dataset_versions
                        ADD COLUMN IF NOT EXISTS col_count INT NOT NULL DEFAULT 0,
                        ADD COLUMN IF NOT EXISTS column_schema TEXT,
                        ADD COLUMN IF NOT EXISTS created_by_id UUID;
                """))
                conn.execute(text("""
                    ALTER TABLE IF EXISTS public.data_sources
                        ADD COLUMN IF NOT EXISTS dataset_id UUID,
                        ADD COLUMN IF NOT EXISTS config_json TEXT NOT NULL DEFAULT '{}',
                        ADD COLUMN IF NOT EXISTS is_paused BOOLEAN NOT NULL DEFAULT false,
                        ADD COLUMN IF NOT EXISTS next_sync_at TIMESTAMPTZ,
                        ADD COLUMN IF NOT EXISTS last_error_message TEXT,
                        ADD COLUMN IF NOT EXISTS total_records_synced INT NOT NULL DEFAULT 0;
                """))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS public.data_records (
                        id VARCHAR(36) PRIMARY KEY,
                        dataset_id VARCHAR(36) NOT NULL,
                        version_id VARCHAR(36),
                        row_index INT NOT NULL,
                        record_json TEXT NOT NULL,
                        is_deleted INT NOT NULL DEFAULT 0,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                    CREATE INDEX IF NOT EXISTS idx_data_records_dataset_id ON public.data_records(dataset_id);
                    CREATE INDEX IF NOT EXISTS idx_data_records_version_id ON public.data_records(version_id);
                    CREATE INDEX IF NOT EXISTS idx_data_records_row_index ON public.data_records(dataset_id, row_index);
                """))
                conn.commit()
            except Exception as e:
                logger.warning(f"PostgreSQL additive column sync skipped: {e}")
        else:
            # Lightweight SQLite schema auto-migration for newly added columns
            try:
                res = conn.execute(text("PRAGMA table_info(users)"))
                user_cols = {row[1] for row in res.fetchall()}
                if "reset_password_token" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(255)"))
                if "reset_password_expires_at" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_password_expires_at DATETIME"))
            except Exception:
                pass

            try:
                res = conn.execute(text("PRAGMA table_info(companies)"))
                company_cols = {row[1] for row in res.fetchall()}
                if "industry" not in company_cols:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN industry VARCHAR(100)"))
                if "company_size" not in company_cols:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN company_size VARCHAR(50)"))
                if "country" not in company_cols:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN country VARCHAR(100)"))
                if "primary_objective" not in company_cols:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN primary_objective VARCHAR(255)"))
                if "settings" not in company_cols:
                    conn.execute(text("ALTER TABLE companies ADD COLUMN settings VARCHAR(4000) DEFAULT '{}'"))
            except Exception:
                pass



