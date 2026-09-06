"""
StockSense AI — Macro & Regime Repository
Point-in-Time Macro Lookups & Timestamped Market Regimes.
"""

from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models.macro import MacroIndicator, MarketRegime


class MacroRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_indicator_as_of(
        self, indicator_name: str, as_of_date: date
    ) -> Optional[MacroIndicator]:
        """
        Fetch macro indicator value available strictly on or before as_of_date.
        Prevents look-ahead macro leakage in backtests.
        """
        stmt = (
            select(MacroIndicator)
            .where(
                and_(
                    MacroIndicator.indicator_name == indicator_name.lower(),
                    MacroIndicator.data_available_date <= as_of_date
                )
            )
            .order_by(desc(MacroIndicator.observation_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_regime_as_of(self, as_of_date: date) -> Optional[MarketRegime]:
        """Fetch market regime known as of historical date T."""
        stmt = (
            select(MarketRegime)
            .where(MarketRegime.regime_date <= as_of_date)
            .order_by(desc(MarketRegime.regime_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
