"""Background Sync Scheduler & Worker for DataScope."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from app.db.session import SessionLocal
from app.models.data_source import DataSource
from app.services.data_connector_service import data_connector_service

logger = logging.getLogger("datascope.sync_worker")


class SyncWorker:
    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background periodic sync polling worker."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"SyncWorker started (polling every {self.check_interval_seconds}s).")

    async def stop(self):
        """Gracefully stop the background worker."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SyncWorker stopped.")

    async def _run_loop(self):
        while self.is_running:
            try:
                await asyncio.sleep(self.check_interval_seconds)
                self.check_and_run_due_syncs()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in SyncWorker loop: {e}", exc_info=True)

    def check_and_run_due_syncs(self):
        """Check database for any active data sources due for scheduled synchronization."""
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            due_sources = db.query(DataSource).filter(
                DataSource.is_paused == False,
                DataSource.sync_frequency != "manual",
                DataSource.next_sync_at != None,
                DataSource.next_sync_at <= now,
            ).all()

            for source in due_sources:
                logger.info(f"Triggering scheduled sync for source '{source.name}' ({source.id})")
                try:
                    data_connector_service.sync_source(
                        db=db,
                        data_source_id=source.id,
                        company_id=source.company_id,
                        sync_type="scheduled",
                    )
                except Exception as sync_err:
                    logger.error(f"Scheduled sync failed for source {source.id}: {sync_err}")
        finally:
            db.close()


sync_worker = SyncWorker(check_interval_seconds=60)
