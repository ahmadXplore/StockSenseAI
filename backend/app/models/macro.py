"""
StockSense AI — Macroeconomic ORM Models (Schema: macro)
Point-in-Time Macro Indicators & Historical Market Regimes.
"""

from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, UniqueConstraint, Index
)
from app.db.base import Base


class MacroIndicator(Base):
    """
    Point-in-time macroeconomic indicators with strict release_date / data_available_date.
    """
    __tablename__ = "indicators"
    __table_args__ = (
        UniqueConstraint("indicator_name", "observation_date", name="uq_indicator_name_obs_date"),
        Index("idx_macro_indicator_available", "indicator_name", "data_available_date"),
        {"schema": "macro"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_name = Column(String(100), nullable=False) # 'vix', 'fed_funds_rate', 'dgs10', 'cpi_yoy', 'hy_spread'
    observation_date = Column(Date, nullable=False)
    release_date = Column(Date, nullable=False)
    data_available_date = Column(Date, nullable=False)   # release_date + lag buffer
    value = Column(Numeric(12, 6), nullable=False)
    
    change_1d = Column(Numeric(12, 6))
    change_7d = Column(Numeric(12, 6))
    change_30d = Column(Numeric(12, 6))
    change_90d = Column(Numeric(12, 6))
    
    source = Column(String(50), default="fred")         # 'fred', 'cboe', 'census'
    series_id = Column(String(50))                      # e.g. 'DGS10', 'FEDFUNDS', 'VIXCLS'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MarketRegime(Base):
    """
    Timestamped historical market regimes queryable as-of any historical date T.
    """
    __tablename__ = "market_regimes"
    __table_args__ = (
        Index("idx_regime_date", "regime_date"),
        {"schema": "macro"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    regime_date = Column(Date, nullable=False, unique=True)
    regime = Column(String(30), nullable=False) # 'bull', 'bear', 'high_vol', 'low_vol', 'rate_shock', 'recession', 'mixed'
    
    spy_above_200sma = Column(Boolean)
    vix_level = Column(Numeric(8, 4))
    yield_curve_inverted = Column(Boolean)
    hy_spread_level = Column(Numeric(8, 4))
    spy_30d_return = Column(Numeric(8, 4))
    
    regime_confidence = Column(Numeric(5, 2), default=70.0) # 0 to 100
    model_confidence_modifier = Column(Numeric(5, 2), default=1.0) # e.g. 0.85 during high-vol regimes
    interval_width_modifier = Column(Numeric(5, 2), default=1.0)   # e.g. 1.25 during regime transitions
    methodology_version = Column(String(20), default="v1.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
