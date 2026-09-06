"""
StockSense AI — News & Sentiment Repository
"""

from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.models.news import NewsItem, SentimentAggregate


class NewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_veto_news(self, ticker: str) -> List[NewsItem]:
        """Fetch news items for ticker that triggered the Hard Veto rule."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(NewsItem)
            .where(
                and_(
                    NewsItem.ticker == ticker_clean,
                    NewsItem.triggers_veto == True
                )
            )
            .order_by(desc(NewsItem.published_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_sentiment_as_of(
        self, ticker: str, as_of_date: date
    ) -> Optional[SentimentAggregate]:
        """Fetch news sentiment aggregate available on or before as_of_date."""
        ticker_clean = ticker.strip().upper()
        stmt = (
            select(SentimentAggregate)
            .where(
                and_(
                    SentimentAggregate.ticker == ticker_clean,
                    SentimentAggregate.data_available_date <= as_of_date
                )
            )
            .order_by(desc(SentimentAggregate.aggregate_date))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
