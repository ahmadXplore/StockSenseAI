"""
StockSense AI — Audit & Data Quality Repository
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.repositories.base import BaseRepository
from app.models.audit import AnalysisRequest, DataQualityLog, ReportExport


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_data_quality_check(
        self,
        data_source: str,
        data_type: str,
        quality_check: str,
        status: str,
        ticker: Optional[str] = None,
        severity: str = "LOW",
        missing_count: int = 0,
        stale_days: int = 0,
        detail: Optional[str] = None,
    ) -> DataQualityLog:
        """Log data quality validation check result."""
        log = DataQualityLog(
            logged_at=datetime.now(timezone.utc),
            data_source=data_source,
            ticker=ticker.strip().upper() if ticker else None,
            data_type=data_type,
            quality_check=quality_check,
            status=status,
            severity=severity,
            missing_count=missing_count,
            stale_days=stale_days,
            detail=detail,
        )
        self.session.add(log)
        await self.session.flush()
        return log
