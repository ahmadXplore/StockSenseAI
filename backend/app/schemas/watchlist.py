"""
StockSense AI — Watchlist Schemas
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class WatchlistAddRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    user_notes: Optional[str] = None
    alert_earnings: bool = True
    alert_anomaly: bool = True
    alert_score_change: bool = True
    alert_stop_loss: bool = True


class WatchlistItemResponse(BaseModel):
    id: int
    ticker: str
    company_name: str
    current_price: Optional[float] = None
    change_today_pct: Optional[float] = None
    overall_score: Optional[float] = None
    recommendation: Optional[str] = None
    forecast_7d_pct: Optional[float] = None
    forecast_1y_pct: Optional[float] = None
    thesis_status: Optional[str] = "valid"  # valid, review, broken
    earnings_in_days: Optional[int] = None
    added_at: datetime
    user_notes: Optional[str] = None


class WatchlistResponse(BaseModel):
    items: List[WatchlistItemResponse]
    total_count: int
