"""
StockSense AI — Alert Repository
Handles alert creation with deduplication key protection.
"""

import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.db.repositories.base import BaseRepository
from app.models.portfolio import Alert
from app.models.enums import AlertType, SeverityLevel


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, session: AsyncSession):
        super().__init__(Alert, session)

    async def create_deduplicated_alert(
        self,
        ticker: str,
        alert_type: str,
        title: str,
        message: str,
        deduplication_key: str,
        user_id: Optional[uuid.UUID] = None,
        position_id: Optional[uuid.UUID] = None,
        severity: str = SeverityLevel.MEDIUM.value,
        metadata_json: dict = None,
    ) -> Optional[Alert]:
        """
        Creates alert unless duplicate deduplication_key already exists.
        Prevents repeating alerts for the same event.
        """
        ticker_clean = ticker.strip().upper()
        stmt = select(Alert).where(Alert.deduplication_key == deduplication_key)
        existing = await self.session.execute(stmt)
        if existing.scalars().first():
            return None  # Suppress duplicate alert

        alert = Alert(
            id=uuid.uuid4(),
            user_id=user_id,
            ticker=ticker_clean,
            position_id=position_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            deduplication_key=deduplication_key,
            triggered_at=datetime.now(timezone.utc),
            is_read=False,
            metadata_json=metadata_json or {},
        )
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def list_unread(self, user_id: uuid.UUID) -> List[Alert]:
        """List unread alerts for user."""
        stmt = (
            select(Alert)
            .where(and_(Alert.user_id == user_id, Alert.is_read == False))
            .order_by(Alert.triggered_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
