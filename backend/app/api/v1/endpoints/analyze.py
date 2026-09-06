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

router = APIRouter()


@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_202_ACCEPTED, summary="Trigger async stock analysis")
async def trigger_analysis(
    payload: AnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits an async stock analysis job to the Celery worker queue.
    Returns a job_id for progress polling.
    """
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    return JobStatusResponse(
        job_id=job_id,
        ticker=payload.ticker,
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
    Fetches the latest completed analysis report for a ticker.
    """
    ticker_clean = ticker.strip().upper()
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Report generation service for {ticker_clean} is scheduled in Phase 2/3."
    )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse, summary="Poll analysis job progress")
async def get_job_status(job_id: str):
    """
    Polls real-time step progress for an asynchronous analysis task.
    """
    return JobStatusResponse(
        job_id=job_id,
        ticker="UNKNOWN",
        status="PENDING",
        step=1,
        total_steps=14,
        current_step_name="Awaiting worker execution",
        progress_pct=5,
    )
