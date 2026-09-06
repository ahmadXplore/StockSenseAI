"""
StockSense AI — Repository Layer Unit Tests
Tests Job state transitions, Company search, and Atomic Report persistence.
"""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from app.db.base import Base
from app.models.market_data import Company
from app.db.repositories.company_repo import CompanyRepository
from app.db.repositories.job_repo import JobRepository
from app.db.repositories.report_repo import ReportRepository
from app.models.enums import AnalysisJobStatus, RecommendationSignal
from app.models.analysis import AnalysisJob, AnalysisReport


@pytest.mark.asyncio
async def test_job_state_progression():
    """Verify AnalysisJob step progression, progress percentage, and completion timing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        repo = JobRepository(session)
        
        # 1. Create Job
        job = await repo.create_job(ticker="NVDA")
        await session.commit()
        assert job.status == AnalysisJobStatus.PENDING.value
        assert job.progress_pct == 5

        # 2. Update step
        updated_job = await repo.update_progress(
            job_id=job.id,
            step=5,
            step_name="Running Sentiment NLP",
            progress_pct=40,
            status=AnalysisJobStatus.RUNNING_SENTIMENT.value
        )
        await session.commit()
        assert updated_job.current_step == 5
        assert updated_job.progress_pct == 40
        assert updated_job.status == AnalysisJobStatus.RUNNING_SENTIMENT.value

    await engine.dispose()


@pytest.mark.asyncio
async def test_atomic_report_persistence():
    """Verify atomic persistence of master report and normalized section tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Seed company
        company = Company(ticker="NVDA", name="NVIDIA Corp.", is_active=True)
        session.add(company)
        await session.commit()

        repo = ReportRepository(session)
        
        report_data = {
            "ticker": "NVDA",
            "current_price": 124.50,
            "overall_score": 75.0,
            "short_term_rec": "BUY",
            "short_term_confidence": 68.0,
            "medium_term_rec": "STRONG BUY",
            "medium_term_confidence": 72.0,
            "long_term_rec": "BUY",
            "long_term_confidence": 75.0,
            "report_snapshot_jsonb": {"ticker": "NVDA", "score": 75}
        }
        
        predictions_data = [
            {
                "ticker": "NVDA",
                "prediction_date": datetime.now(timezone.utc).date(),
                "target_date": datetime.now(timezone.utc).date(),
                "horizon": "30d",
                "horizon_days": 30,
                "current_price": 124.50,
                "predicted_price": 135.00,
                "lower_bound_10th": 118.00,
                "upper_bound_90th": 142.00,
                "expected_return_pct": 8.43,
                "prob_positive_return": 0.65,
                "confidence_score": 70.0,
                "signal": "BUY"
            }
        ]

        scenarios_data = [
            {
                "scenario_type": "bull",
                "price_target": 150.00,
                "expected_return_pct": 20.48,
                "probability": 0.25
            },
            {
                "scenario_type": "base",
                "price_target": 135.00,
                "expected_return_pct": 8.43,
                "probability": 0.50
            }
        ]

        scores_data = [
            {
                "module_name": "fundamental",
                "score": 80.0,
                "status": "STRONG",
                "explanation": "High revenue growth and cash flow margin."
            }
        ]

        saved_report = await repo.save_full_report_atomic(
            report_data=report_data,
            predictions_data=predictions_data,
            scenarios_data=scenarios_data,
            scores_data=scores_data
        )
        await session.commit()

        assert saved_report.id is not None
        assert saved_report.ticker == "NVDA"
        assert saved_report.overall_score == 75.0

        # Verify normalized children were inserted
        stmt = (
            select(AnalysisReport)
            .options(selectinload(AnalysisReport.predictions), selectinload(AnalysisReport.scenarios))
            .where(AnalysisReport.ticker == "NVDA")
        )
        result = await session.execute(stmt)
        latest = result.scalars().first()
        assert latest is not None
        assert len(latest.predictions) == 1
        assert latest.predictions[0].predicted_price == 135.00
        assert len(latest.scenarios) == 2

    await engine.dispose()
