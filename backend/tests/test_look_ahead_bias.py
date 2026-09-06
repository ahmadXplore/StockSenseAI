"""
StockSense AI — Look-Ahead Bias Regression Test
Proves that fundamental metrics with data_available_date > T cannot be accessed when querying as-of date T.
"""

import pytest
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.base import Base
from app.models.market_data import Company
from app.models.fundamentals import IncomeStatement
from app.db.repositories.fundamental_repo import FundamentalRepository


@pytest.mark.asyncio
async def test_look_ahead_bias_prevention():
    """
    Financial Correctness Test:
    Insert Q1 income statement for AAPL with:
      period_end_date = 2024-03-31
      filing_date = 2024-04-25
      data_available_date = 2024-04-25
    
    Assertion 1: Querying as of 2024-04-15 MUST return None (Q1 data unavailable).
    Assertion 2: Querying as of 2024-04-26 MUST return Q1 income statement.
    """
    # Create SQLite in-memory async engine for unit testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Seed test company
        company = Company(
            ticker="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            is_active=True
        )
        session.add(company)

        # Seed Q1 2024 Income Statement filed on April 25, 2024
        q1_statement = IncomeStatement(
            ticker="AAPL",
            fiscal_year=2024,
            fiscal_quarter=1,
            period_end_date=date(2024, 3, 31),
            report_type="quarterly",
            filing_date=date(2024, 4, 25),
            announcement_date=date(2024, 4, 25),
            data_available_date=date(2024, 4, 25),
            revenue=90750000000,
            eps_reported=1.53,
            currency="USD"
        )
        session.add(q1_statement)
        await session.commit()

        repo = FundamentalRepository(session)

        # Query As-Of April 15, 2024 (Before Filing Date) -> MUST BE NONE
        result_before_filing = await repo.get_income_statement_as_of(
            ticker="AAPL",
            as_of_date=date(2024, 4, 15),
            report_type="quarterly"
        )
        assert result_before_filing is None, (
            "CRITICAL LOOK-AHEAD LEAK: Fundamental data was retrieved before its data_available_date!"
        )

        # Query As-Of April 26, 2024 (After Filing Date) -> MUST BE PRESENT
        result_after_filing = await repo.get_income_statement_as_of(
            ticker="AAPL",
            as_of_date=date(2024, 4, 26),
            report_type="quarterly"
        )
        assert result_after_filing is not None
        assert result_after_filing.eps_reported == 1.53
        assert result_after_filing.period_end_date == date(2024, 3, 31)

    await engine.dispose()
