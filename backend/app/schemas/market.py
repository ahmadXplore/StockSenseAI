"""
StockSense AI — Market & Regime Schemas
"""

from typing import Optional, List, Dict
from datetime import date, datetime
from pydantic import BaseModel, Field


class RegimeResponse(BaseModel):
    regime_date: date
    regime: str  # 'bull', 'bear', 'high_vol', 'low_vol', 'rate_shock', 'recession', 'mixed'
    confidence: float
    spy_above_200sma: Optional[bool] = None
    vix_level: Optional[float] = None
    yield_curve_inverted: Optional[bool] = None
    spy_30d_return: Optional[float] = None
    confidence_modifier: float = 1.0
    interval_width_modifier: float = 1.0
    description: str


class MarketOverviewResponse(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    regime: RegimeResponse
    spy_price: Optional[float] = None
    spy_change_pct: Optional[float] = None
    qqq_price: Optional[float] = None
    qqq_change_pct: Optional[float] = None
    vix_value: Optional[float] = None
    vix_change: Optional[float] = None
    macro_score: Optional[float] = None


class TickerSearchResult(BaseModel):
    ticker: str
    name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[int] = None
    current_price: Optional[float] = None
