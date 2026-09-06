"""
StockSense AI — Analysis Job Repository
"""

import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.repositories.base import BaseRepository
from app.models.analysis import AnalysisJob
from app.models.enums import AnalysisJobStatus


class JobRepository(BaseRepository[AnalysisJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(AnalysisJob, session)

    async def create_job(self, ticker: str, configuration_json: dict = None) -> AnalysisJob:
        """Create a new pending analysis job."""
        ticker_clean = ticker.strip().upper()
        job = AnalysisJob(
            id=uuid.uuid4(),
            ticker=ticker_clean,
            status=AnalysisJobStatus.PENDING.value,
            current_step=1,
            total_steps=14,
            current_step_name="Job queued for processing",
            progress_pct=5,
            requested_at=datetime.now(timezone.utc),
            configuration_json=configuration_json or {},
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def update_progress(
        self,
        job_id: uuid.UUID,
        step: int,
        step_name: str,
        progress_pct: int,
        status: Optional[str] = None
    ) -> Optional[AnalysisJob]:
        """Update current step, step description, and percentage complete."""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.current_step = step
        job.current_step_name = step_name
        job.progress_pct = progress_pct
        if status:
            job.status = status
            if status == AnalysisJobStatus.FETCHING_PRICE.value and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            elif status == AnalysisJobStatus.COMPLETED.value:
                job.completed_at = datetime.now(timezone.utc)
            elif status == AnalysisJobStatus.FAILED.value:
                job.failed_at = datetime.now(timezone.utc)

        await self.session.flush()
        return job

    async def mark_failed(self, job_id: uuid.UUID, error_code: str, safe_message: str) -> Optional[AnalysisJob]:
        """Mark job as failed with user-safe error message."""
        job = await self.get_by_id(job_id)
        if not job:
            return None

        job.status = AnalysisJobStatus.FAILED.value
        job.error_code = error_code
        job.safe_error_message = safe_message
        job.failed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return job
