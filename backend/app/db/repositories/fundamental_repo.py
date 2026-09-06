"""
StockSense AI — Fundamental Data Repository
Enforces Point-in-Time compliance: data_available_date <= as_of_date.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.db.repositories.base import BaseRepository
from app.models.fundamentals import (
    IncomeStatement, BalanceSheet, CashFlowStatement, FinancialRatio, AnalystEstimate
)


class FundamentalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_income_statement_as_of(
        self, ticker: str, as_of_date: date, report_type: str = "quarterly"
    ) -> Optional[IncomeStatement]:
        """
        Fetch latest income statement strictly available on or before as_of_date.
        Prevents look-ahead bias in backtests and live inference.
        """
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(IncomeStatement)
            .where(
                and_(
                    IncomeStatement.ticker == ticker_clean,
                    IncomeStatement.report_type == report_type,
                    IncomeStatement.data_available_date <= as_of_date
                )
            )
            .order_by(desc(IncomeStatement.period_end_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_balance_sheet_as_of(
        self, ticker: str, as_of_date: date, report_type: str = "quarterly"
    ) -> Optional[BalanceSheet]:
        """Fetch latest balance sheet available on or before as_of_date."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(BalanceSheet)
            .where(
                and_(
                    BalanceSheet.ticker == ticker_clean,
                    BalanceSheet.report_type == report_type,
                    BalanceSheet.data_available_date <= as_of_date
                )
            )
            .order_by(desc(BalanceSheet.period_end_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_cash_flow_as_of(
        self, ticker: str, as_of_date: date, report_type: str = "quarterly"
    ) -> Optional[CashFlowStatement]:
        """Fetch latest cash flow statement available on or before as_of_date."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(CashFlowStatement)
            .where(
                and_(
                    CashFlowStatement.ticker == ticker_clean,
                    CashFlowStatement.report_type == report_type,
                    CashFlowStatement.data_available_date <= as_of_date
                )
            )
            .order_by(desc(CashFlowStatement.period_end_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_financial_ratios_as_of(
        self, ticker: str, as_of_date: date
    ) -> Optional[FinancialRatio]:
        """Fetch financial ratios available on or before as_of_date."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(FinancialRatio)
            .where(
                and_(
                    FinancialRatio.ticker == ticker_clean,
                    FinancialRatio.data_available_date <= as_of_date
                )
            )
            .order_by(desc(FinancialRatio.as_of_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
