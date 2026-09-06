"""
StockSense AI — Portfolio Position Schemas
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field


class PositionCreateRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    entry_date: date
    entry_price: float = Field(..., gt=0.0)
    shares: float = Field(..., gt=0.0)
    entry_thesis: Optional[str] = None
    entry_stop_loss_price: Optional[float] = None
    entry_profit_target_1: Optional[float] = None
    entry_profit_target_2: Optional[float] = None
    entry_time_horizon: Optional[str] = None
    broker: Optional[str] = None
    notes: Optional[str] = None


class PositionResponse(BaseModel):
    id: str
    ticker: str
    company_name: str
    entry_date: date
    entry_price: float
    shares: float
    investment_amount: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_return_pct: Optional[float] = None
    entry_thesis: Optional[str] = None
    thesis_valid: Optional[bool] = True
    thesis_status: str = "valid"  # valid, review, broken
    thesis_notes: Optional[str] = None
    stop_loss_price: Optional[float] = None
    is_approaching_stop: bool = False
    status: str = "open"


class PortfolioSummaryResponse(BaseModel):
    total_value: float
    total_cost_basis: float
    total_pnl: float
    total_return_pct: float
    positions: List[PositionResponse]
    warning_positions: List[PositionResponse] = []
