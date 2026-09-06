"""
StockSense AI — Price Data Repository
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.db.repositories.base import BaseRepository
from app.models.market_data import PriceData


class PriceRepository(BaseRepository[PriceData]):
    def __init__(self, session: AsyncSession):
        super().__init__(PriceData, session)

    async def get_latest_price(self, ticker: str) -> Optional[PriceData]:
        """Fetch latest OHLCV bar for ticker."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(PriceData)
            .where(PriceData.ticker == ticker_clean)
            .order_by(desc(PriceData.time))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_price_history(
        self, ticker: str, start_time: datetime, end_time: datetime
    ) -> List[PriceData]:
        """Fetch OHLCV price series in date range."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(PriceData)
            .where(
                and_(
                    PriceData.ticker == ticker_clean,
                    PriceData.time >= start_time,
                    PriceData.time <= end_time
                )
            )
            .order_by(PriceData.time.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
