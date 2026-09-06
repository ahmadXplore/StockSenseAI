"""
StockSense AI — Technical Indicator Repository
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.db.repositories.base import BaseRepository
from app.models.market_data import TechnicalIndicator


class TechnicalRepository(BaseRepository[TechnicalIndicator]):
    def __init__(self, session: AsyncSession):
        super().__init__(TechnicalIndicator, session)

    async def get_latest_indicators(self, ticker: str) -> Optional[TechnicalIndicator]:
        """Fetch latest calculated technical indicators for ticker."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(TechnicalIndicator)
            .where(TechnicalIndicator.ticker == ticker_clean)
            .order_by(desc(TechnicalIndicator.time))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_indicator_history(
        self, ticker: str, start_time: datetime, end_time: datetime
    ) -> List[TechnicalIndicator]:
        """Fetch historical technical indicators time-series."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(TechnicalIndicator)
            .where(
                and_(
                    TechnicalIndicator.ticker == ticker_clean,
                    TechnicalIndicator.time >= start_time,
                    TechnicalIndicator.time <= end_time
                )
            )
            .order_by(TechnicalIndicator.time.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
