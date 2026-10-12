"""
StockSense AI — Analysis Endpoints
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisRequest, BatchAnalysisRequest, JobStatusResponse, FullReportResponse
)

from app.models.analysis import AnalysisJob, AnalysisReport
from app.core import db_cache
from app.core.logging import get_logger

logger = get_logger("api.analyze")
router = APIRouter()


@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, summary="Trigger async stock analysis")
async def trigger_analysis(
    payload: AnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an async stock analysis job to the worker queue.
    Persists the analysis job record in SQLite/PostgreSQL and returns a job_id.
    """
    job_uuid = uuid.uuid4()
    job_id = f"job_{job_uuid.hex[:12]}"
    clean_ticker = payload.ticker.strip().upper()

    try:
        # Ensure company exists in database
        await db_cache.ensure_company_and_security(session=db, ticker=clean_ticker)

        job_model = AnalysisJob(
            id=job_uuid,
            ticker=clean_ticker,
            status="PENDING",
            current_step=1,
            total_steps=14,
            current_step_name="Job queued for processing",
            progress_pct=5,
            celery_task_id=job_id,
            configuration_json=payload.dict() if hasattr(payload, "dict") else {},
        )
        db.add(job_model)
        await db.commit()
    except Exception as exc:
        logger.warning(f"[ANALYZE] Failed to persist job {job_id}: {exc}")

    return JobStatusResponse(
        job_id=job_id,
        ticker=clean_ticker,
        status="PENDING",
        step=1,
        total_steps=14,
        current_step_name="Job queued for processing",
        progress_pct=5,
    )


@router.get("/{ticker}", response_model=FullReportResponse, summary="Get latest or cached analysis report")
async def get_latest_report(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Fetches the latest completed analysis report for a ticker from SQLite/PostgreSQL.
    """
    ticker_clean = ticker.strip().upper()
    try:
        stmt = (
            select(AnalysisReport)
            .where(AnalysisReport.ticker == ticker_clean)
            .order_by(AnalysisReport.generated_at.desc())
        )
        res = await db.execute(stmt)
        rep = res.scalars().first()
        if rep and rep.report_snapshot_jsonb:
            return rep.report_snapshot_jsonb
    except Exception as exc:
        logger.warning(f"[ANALYZE] Failed to query report for {ticker_clean}: {exc}")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Report generation service for {ticker_clean} is scheduled in Phase 2/3."
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse, summary="Poll analysis job progress")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """
    Polls real-time step progress for an asynchronous analysis task from SQLite/PostgreSQL.
    """
    try:
        stmt = select(AnalysisJob).where(AnalysisJob.celery_task_id == job_id)
        res = await db.execute(stmt)
        job = res.scalars().first()
        if job:
            return JobStatusResponse(
                job_id=job_id,
                ticker=job.ticker,
                status=job.status,
                step=job.current_step,
                total_steps=job.total_steps,
                current_step_name=job.current_step_name,
                progress_pct=job.progress_pct,
            )
    except Exception:
        pass

    return JobStatusResponse(
        job_id=job_id,
        ticker="UNKNOWN",
        status="PENDING",
        step=1,
        total_steps=14,
        current_step_name="Awaiting worker execution",
        progress_pct=5,
    )
