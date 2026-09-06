"""
StockSense AI — User, Portfolio, Watchlist & Alerts ORM Models (Schema: portfolio)
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Index, ARRAY, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import ThesisStatus, AlertType, SeverityLevel, PositionStatus


class User(Base):
    """
    User account with authentication credentials separated from analysis records.
    Never stores plaintext passwords.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        {"schema": "portfolio"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=True)
    full_name = Column(String(150), nullable=True)
    password_hash = Column(String(255), nullable=True) # bcrypt hash, nullable for anonymous/guest sessions
    email_verified = Column(Boolean, default=False, nullable=False)

    # Biometric Face Authentication
    face_descriptor = Column(JSON, nullable=True) # 128-dimensional float array
    face_enrolled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Financial Analysis Preferences
    default_risk_tolerance = Column(String(20), default="moderate", nullable=False)
    default_investment_amount = Column(Numeric(15, 2), default=10000.0, nullable=False)
    preferred_horizons = Column(ARRAY(String(20)).with_variant(JSON, "sqlite"), default=["all"], nullable=False)
    
    # UI Preferences
    dark_mode = Column(Boolean, default=True, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    
    # Subscription & Quotas
    plan_type = Column(String(20), default="free", nullable=False)
    plan_started_at = Column(DateTime(timezone=True), nullable=True)
    plan_expires_at = Column(DateTime(timezone=True), nullable=True)
    analyses_today = Column(Integer, default=0, nullable=False)
    analyses_this_month = Column(Integer, default=0, nullable=False)
    last_analysis_at = Column(DateTime(timezone=True), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    role = Column(String(20), default="user", nullable=False) # 'admin', 'user', 'analyst'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")


class Watchlist(Base):
    """
    Named watchlists container.
    """
    __tablename__ = "watchlists"
    __table_args__ = (
        Index("idx_watchlists_user", "user_id"),
        {"schema": "portfolio"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portfolio.users.id"), nullable=False)
    name = Column(String(100), default="Default Watchlist", nullable=False)
    is_default = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "ticker", name="uq_watchlist_ticker"),
        {"schema": "portfolio"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(Integer, ForeignKey("portfolio.watchlists.id"), nullable=False)
    ticker = Column(String(20), nullable=False)  # Plain VARCHAR — no FK to companies
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    user_notes = Column(Text, nullable=True)
    
    # Alert Preferences
    alert_earnings = Column(Boolean, default=True, nullable=False)
    alert_anomaly = Column(Boolean, default=True, nullable=False)
    alert_score_change = Column(Boolean, default=True, nullable=False)
    alert_stop_loss = Column(Boolean, default=True, nullable=False)

    watchlist = relationship("Watchlist", back_populates="items")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("idx_positions_user_status", "user_id", "status"),
        {"schema": "portfolio"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portfolio.users.id"), nullable=False)
    ticker = Column(String(20), nullable=False)  # Plain VARCHAR — no FK to companies
    
    # Entry
    entry_date = Column(Date, nullable=False)
    entry_price = Column(Numeric(12, 4), nullable=False)
    shares = Column(Numeric(12, 4), nullable=False)
    investment_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    
    # Entry Context
    entry_report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=True)
    entry_thesis = Column(Text, nullable=True)
    entry_stop_loss_price = Column(Numeric(12, 4), nullable=True)
    entry_profit_target_1 = Column(Numeric(12, 4), nullable=True)
    entry_profit_target_2 = Column(Numeric(12, 4), nullable=True)
    entry_time_horizon = Column(String(20), default="1y")
    
    # Exit
    exit_date = Column(Date, nullable=True)
    exit_price = Column(Numeric(12, 4), nullable=True)
    exit_reason = Column(String(100), nullable=True)
    
    # Status & Realized P&L
    status = Column(String(20), default=PositionStatus.OPEN.value, nullable=False)
    realized_pnl = Column(Numeric(15, 2), nullable=True)
    realized_return_pct = Column(Numeric(8, 4), nullable=True)
    
    # Soft deletion
    is_active = Column(Boolean, default=True, nullable=False)
    broker = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="positions")
    thesis_validations = relationship("ThesisValidation", back_populates="position", cascade="all, delete-orphan")


class ThesisValidation(Base):
    """
    Periodic thesis health check audits for tracked positions.
    """
    __tablename__ = "thesis_validations"
    __table_args__ = (
        Index("idx_thesis_position_date", "position_id", "checked_at"),
        {"schema": "portfolio"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(UUID(as_uuid=True), ForeignKey("portfolio.positions.id"), nullable=False)
    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    original_thesis = Column(Text, nullable=False)
    current_thesis_state = Column(Text, nullable=False)
    status = Column(String(20), default=ThesisStatus.VALID.value, nullable=False) # 'valid', 'review', 'invalidated'
    
    supporting_factors = Column(JSONB, nullable=True)
    invalidating_factors = Column(JSONB, nullable=True)
    recommendation = Column(String(50), nullable=True)
    evaluator_notes = Column(Text, nullable=True)

    position = relationship("Position", back_populates="thesis_validations")


class Alert(Base):
    """
    System alerts with deduplication key to prevent repeated alerts for the same event.
    """
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_user_unread", "user_id", "is_read", "triggered_at"),
        UniqueConstraint("deduplication_key", name="uq_alert_dedup_key"),
        {"schema": "portfolio"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portfolio.users.id"), nullable=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    position_id = Column(UUID(as_uuid=True), ForeignKey("portfolio.positions.id"), nullable=True)
    
    alert_type = Column(String(30), nullable=False) # 'EARNINGS', 'STOP_LOSS', 'THESIS', 'ANOMALY', etc.
    severity = Column(String(20), default=SeverityLevel.MEDIUM.value, nullable=False) # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Deduplication key e.g. 'AAPL:EARNINGS:2025-09-01' or 'MSFT:STOP_LOSS:2025-09-02'
    deduplication_key = Column(String(255), nullable=False)
    
    triggered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(JSONB, nullable=True)

    user = relationship("User", back_populates="alerts")
