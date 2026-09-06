"""
StockSense AI — Portfolio & Watchlist Repository
"""

import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.db.repositories.base import BaseRepository
from app.models.portfolio import User, Watchlist, WatchlistItem, Position, ThesisValidation
from app.models.enums import ThesisStatus, PositionStatus


class PortfolioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_default_watchlist(self, user_id: uuid.UUID) -> Watchlist:
        """Fetch user's default watchlist or create one if missing."""
        stmt = select(Watchlist).where(
            and_(Watchlist.user_id == user_id, Watchlist.is_default == True)
        )
        result = await self.session.execute(stmt)
        watchlist = result.scalars().first()

        if not watchlist:
            watchlist = Watchlist(
                user_id=user_id,
                name="Default Watchlist",
                is_default=True
            )
            self.session.add(watchlist)
            await self.session.flush()

        return watchlist

    async def add_watchlist_item(
        self, user_id: uuid.UUID, ticker: str, notes: Optional[str] = None
    ) -> WatchlistItem:
        """Add ticker to user's default watchlist."""
        ticker_clean = ticker.strip().upper()
        watchlist = await self.get_or_create_default_watchlist(user_id)

        item = WatchlistItem(
            watchlist_id=watchlist.id,
            ticker=ticker_clean,
            user_notes=notes
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_open_positions(self, user_id: uuid.UUID) -> List[Position]:
        """Fetch all open portfolio positions for user."""
        stmt = select(Position).where(
            and_(
                Position.user_id == user_id,
                Position.status == PositionStatus.OPEN.value,
                Position.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def log_thesis_validation(
        self,
        position_id: uuid.UUID,
        original_thesis: str,
        current_state: str,
        status: str = ThesisStatus.VALID.value,
        supporting: list = None,
        invalidating: list = None,
        recommendation: str = "HOLD"
    ) -> ThesisValidation:
        """Log thesis audit check for position."""
        audit = ThesisValidation(
            position_id=position_id,
            checked_at=datetime.now(timezone.utc),
            original_thesis=original_thesis,
            current_thesis_state=current_state,
            status=status,
            supporting_factors=supporting or [],
            invalidating_factors=invalidating or [],
            recommendation=recommendation
        )
        self.session.add(audit)
        await self.session.flush()
        return audit
