"""
StockSense AI — Backtesting & Quantitative Risk ORM Models (Schema: analysis)
Stores backtest runs, trade logs, equity curves, stress test outputs, and optimization records.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class BacktestRunRecord(Base):
    __tablename__ = "backtest_run_records"
    __table_args__ = (
        Index("idx_bt_run_hash", "configuration_hash"),
        Index("idx_bt_run_market", "market_code"),
        Index("idx_bt_run_created", "created_at"),
        {"schema": "analysis"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    configuration_hash = Column(String(64), nullable=False)
    market_code = Column(String(10), default="US", nullable=False)
    exchange_code = Column(String(20), default="NASDAQ")
    strategy_type = Column(String(50), nullable=False)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Numeric(15, 2), default=100000.0, nullable=False)
    ending_capital = Column(Numeric(15, 2), nullable=False)
    
    # Core Performance Metrics
    total_return_pct = Column(Numeric(10, 4), nullable=False)
    cagr_pct = Column(Numeric(10, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    sortino_ratio = Column(Numeric(8, 4))
    calmar_ratio = Column(Numeric(8, 4))
    max_drawdown_pct = Column(Numeric(8, 4))
    win_rate_pct = Column(Numeric(6, 2))
    profit_factor = Column(Numeric(8, 4))
    total_trades = Column(Integer, default=0)
    
    # Risk Metrics
    portfolio_volatility = Column(Numeric(8, 4))
    var_95_daily = Column(Numeric(8, 4))
    cvar_95_daily = Column(Numeric(8, 4))
    beta_to_benchmark = Column(Numeric(8, 4))
    alpha_annualized = Column(Numeric(8, 4))
    
    # Serialized Payloads
    configuration_json = Column(JSONB, nullable=False)
    performance_json = Column(JSONB, nullable=True)
    risk_json = Column(JSONB, nullable=True)
    attribution_json = Column(JSONB, nullable=True)
    monthly_returns_json = Column(JSONB, nullable=True)
    
    reproducibility_seed = Column(Integer, default=42)
    execution_duration_seconds = Column(Numeric(8, 3))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    trades = relationship("BacktestTradeRecord", back_populates="backtest_run", cascade="all, delete-orphan")


class BacktestTradeRecord(Base):
    __tablename__ = "backtest_trade_records"
    __table_args__ = (
        Index("idx_bt_trade_sec", "security_id"),
        Index("idx_bt_trade_date", "entry_date"),
        {"schema": "analysis"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backtest_run_id = Column(UUID(as_uuid=True), ForeignKey("analysis.backtest_run_records.id"), nullable=False)
    trade_id = Column(String(50), nullable=False)
    security_id = Column(String(100), nullable=False)
    ticker = Column(String(20), nullable=False)
    market_code = Column(String(10), default="US")
    side = Column(String(10), default="LONG")
    
    entry_date = Column(Date, nullable=False)
    entry_price = Column(Numeric(12, 4), nullable=False)
    exit_date = Column(Date, nullable=False)
    exit_price = Column(Numeric(12, 4), nullable=False)
    shares = Column(Numeric(14, 4), nullable=False)
    
    gross_pnl = Column(Numeric(15, 2), nullable=False)
    net_pnl = Column(Numeric(15, 2), nullable=False)
    return_pct = Column(Numeric(10, 4), nullable=False)
    holding_period_days = Column(Integer, default=1)
    exit_reason = Column(String(50), default="STOP_LOSS")
    
    total_friction = Column(Numeric(12, 4), default=0.0)
    prediction_probability = Column(Numeric(6, 4))
    market_regime = Column(String(30))

    backtest_run = relationship("BacktestRunRecord", back_populates="trades")


class RiskLimitRecord(Base):
    __tablename__ = "risk_limit_records"
    __table_args__ = (
        Index("idx_risk_limit_user", "user_id"),
        {"schema": "portfolio"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("portfolio.users.id"), nullable=True)
    market_code = Column(String(10), default="GLOBAL")
    
    max_position_weight = Column(Numeric(6, 4), default=0.20)
    max_sector_weight = Column(Numeric(6, 4), default=0.35)
    max_portfolio_risk = Column(Numeric(6, 4), default=0.15)
    max_drawdown_limit = Column(Numeric(6, 4), default=0.25)
    max_daily_loss = Column(Numeric(6, 4), default=0.05)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RiskEventRecord(Base):
    __tablename__ = "risk_event_records"
    __table_args__ = (
        Index("idx_risk_event_date", "occurred_at"),
        {"schema": "portfolio"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False) # 'TRADE_BLOCKED', 'DRAWDOWN_HALT', 'CIRCUIT_BREAKER'
    security_id = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    context_json = Column(JSONB, nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PortfolioOptimizationRecord(Base):
    __tablename__ = "portfolio_optimization_records"
    __table_args__ = (
        Index("idx_optim_created", "created_at"),
        {"schema": "analysis"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    method = Column(String(50), nullable=False)
    securities_json = Column(JSONB, nullable=False)
    optimal_weights_json = Column(JSONB, nullable=False)
    expected_annual_return = Column(Numeric(8, 4))
    expected_annual_volatility = Column(Numeric(8, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    diversification_ratio = Column(Numeric(8, 4))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
