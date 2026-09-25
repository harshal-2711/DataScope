"""Supabase Cloud PostgREST & Storage Synchronization Service.

Ensures all DataScope workspace resources (Profiles, Companies, Memberships,
Data Sources, Datasets, Dataset Versions, Data Records, Audit Logs) are synchronized
with the Supabase Cloud project configured via SUPABASE_URL.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.core.supabase_client import get_clean_supabase_url, is_supabase_configured

logger = logging.getLogger("datascope.supabase_sync")


class SupabaseSyncService:
    """Service to push application entities directly to Supabase Cloud PostgREST tables."""

    @staticmethod
    def _get_headers(user_token: Optional[str] = None) -> Dict[str, str]:
        auth_header = f"Bearer {user_token}" if user_token else f"Bearer {settings.SUPABASE_ANON_KEY}"
        return {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        }

    @staticmethod
    def sync_data_source(
        source_id: str,
        company_id: str,
        name: str,
        source_type: str,
        dataset_id: Optional[str] = None,
        sync_frequency: str = "manual",
        config_dict: Optional[Dict[str, Any]] = None,
        total_records: int = 0,
        user_token: Optional[str] = None,
    ) -> bool:
        """Upsert a DataSource record in Supabase Cloud public.data_sources table."""
        if not is_supabase_configured():
            return False

        clean_url = get_clean_supabase_url()
        url = f"{clean_url}/rest/v1/data_sources"
        payload = {
            "id": source_id,
            "company_id": company_id,
            "name": name,
            "source_type": source_type,
            "sync_frequency": sync_frequency,
            "config": config_dict or {},
            "status": "active",
            "total_records_synced": total_records,
        }
        if dataset_id:
            payload["dataset_id"] = dataset_id

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.post(url, headers=SupabaseSyncService._get_headers(user_token), json=payload)
                if res.status_code in (200, 201):
                    logger.info(f"Synchronized data source {source_id} to Supabase Cloud")
                    return True
                else:
                    logger.debug(f"Supabase data_source sync status {res.status_code}: {res.text}")
                    return False
        except Exception as e:
            logger.debug(f"Supabase data_source sync exception: {e}")
            return False

    @staticmethod
    def sync_dataset(
        dataset_id: str,
        company_id: str,
        name: str,
        file_type: str,
        row_count: int,
        col_count: int,
        user_id: Optional[str] = None,
        user_token: Optional[str] = None,
    ) -> bool:
        """Upsert a Dataset record in Supabase Cloud public.datasets table."""
        if not is_supabase_configured():
            return False

        clean_url = get_clean_supabase_url()
        url = f"{clean_url}/rest/v1/datasets"
        payload = {
            "id": dataset_id,
            "company_id": company_id,
            "filename": f"{name}.csv" if not name.endswith(".csv") else name,
            "name": name,
            "file_format": file_type,
            "row_count": row_count,
            "column_count": col_count,
            "storage_path": f"{company_id}/{dataset_id}.csv",
            "is_active": True,
        }
        if user_id:
            payload["user_id"] = user_id
            payload["created_by_id"] = user_id

        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.post(url, headers=SupabaseSyncService._get_headers(user_token), json=payload)
                if res.status_code in (200, 201):
                    logger.info(f"Synchronized dataset {dataset_id} to Supabase Cloud")
                    return True
                else:
                    logger.debug(f"Supabase dataset sync status {res.status_code}: {res.text}")
                    return False
        except Exception as e:
            logger.debug(f"Supabase dataset sync exception: {e}")
            return False
