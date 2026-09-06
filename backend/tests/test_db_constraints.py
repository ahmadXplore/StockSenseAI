"""
StockSense AI — Database Constraints & Alert Deduplication Unit Tests
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base
from app.models.market_data import Company
from app.models.portfolio import Alert, User
from app.db.repositories.alert_repo import AlertRepository
from app.models.enums import AlertType, SeverityLevel


@pytest.mark.asyncio
async def test_alert_deduplication():
    """
    Test alert deduplication key:
    Creating two alerts with the same deduplication_key must suppress the second alert.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Seed company
        company = Company(ticker="MSFT", name="Microsoft Corp.", is_active=True)
        session.add(company)
        await session.commit()

        repo = AlertRepository(session)
        dedup_key = "MSFT:EARNINGS:2025-10-25"

        # First alert creation -> SUCCEEDS
        alert1 = await repo.create_deduplicated_alert(
            ticker="MSFT",
            alert_type=AlertType.EARNINGS.value,
            title="Earnings Tomorrow",
            message="MSFT reports Q1 earnings tomorrow after market close.",
            deduplication_key=dedup_key,
            severity=SeverityLevel.HIGH.value
        )
        await session.commit()
        assert alert1 is not None
        assert alert1.deduplication_key == dedup_key

        # Second alert creation with identical key -> SUPPRESSED (returns None)
        alert2 = await repo.create_deduplicated_alert(
            ticker="MSFT",
            alert_type=AlertType.EARNINGS.value,
            title="Duplicate Earnings Alert",
            message="Duplicate message.",
            deduplication_key=dedup_key,
            severity=SeverityLevel.HIGH.value
        )
        assert alert2 is None

    await engine.dispose()
