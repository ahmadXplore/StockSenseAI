"""
StockSense AI — Company Repository
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.db.repositories.base import BaseRepository
from app.models.market_data import Company


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession):
        super().__init__(Company, session)

    async def get_by_ticker(self, ticker: str) -> Optional[Company]:
        """Fetch active or inactive company by ticker symbol."""
        ticker_clean = ticker.strip().upper()
        result = await self.session.execute(
            select(Company).where(Company.ticker == ticker_clean)
        )
        return result.scalars().first()

    async def search_by_query(self, query_str: str, limit: int = 10) -> List[Company]:
        """Search companies by ticker prefix or company name substring."""
        pattern = f"%{query_str.strip()}%"
        ticker_pattern = f"{query_str.strip().upper()}%"
        stmt = select(Company).where(
            or_(
                Company.ticker.ilike(ticker_pattern),
                Company.name.ilike(pattern)
            ),
            Company.is_active == True
        ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_sector(self, sector: str, limit: int = 50) -> List[Company]:
        """Fetch companies by sector."""
        stmt = select(Company).where(
            Company.sector.ilike(sector),
            Company.is_active == True
        ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
