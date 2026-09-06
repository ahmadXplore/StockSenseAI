"""
StockSense AI — Ingestion Job Scheduler & Async Execution Manager
Executes large ETL and sync operations asynchronously in the background.
"""

from __future__ import annotations
import asyncio
from datetime import date
from typing import Optional, Dict, Any, Callable
from app.core.logging import get_logger
from app.data.ingestion.historical import ingest_historical
from app.data.ingestion.incremental import ingest_incremental
from app.db.session import AsyncSessionLocal

logger = get_logger("data.ingestion.scheduler")


class IngestionScheduler:
    """
    Manages non-blocking asynchronous backfills and background provider sync jobs.
    """

    def __init__(self):
        self._running_jobs: Dict[str, asyncio.Task] = {}

    def schedule_historical_backfill(
        self,
        job_id: str,
        market: str,
        exchange: str,
        symbol: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> str:
        """Schedules historical ingestion as an async task."""
        async def _task_wrapper():
            logger.info(f"Background task {job_id} started for {market}/{exchange}/{symbol}")
            try:
                async with AsyncSessionLocal() as db:
                    result = await ingest_historical(
                        market=market,
                        exchange=exchange,
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        db=db
                    )
                    logger.info(f"Background task {job_id} finished: status={result.status}")
            except Exception as e:
                logger.error(f"Background task {job_id} failed: {e}", exc_info=True)
            finally:
                self._running_jobs.pop(job_id, None)

        task = asyncio.create_task(_task_wrapper())
        self._running_jobs[job_id] = task
        return job_id

    def get_running_job_count(self) -> int:
        return len(self._running_jobs)


ingestion_scheduler = IngestionScheduler()
