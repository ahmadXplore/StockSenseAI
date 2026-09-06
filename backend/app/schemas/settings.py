"""
StockSense AI — User Settings Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class UserSettingsRequest(BaseModel):
    default_investment_amount: Optional[float] = Field(10000.0, ge=0.0)
    default_risk_tolerance: Optional[str] = Field("moderate")
    preferred_horizons: Optional[List[str]] = Field(default_factory=lambda: ["all"])
    dark_mode: Optional[bool] = True
    currency: Optional[str] = "USD"
    alert_earnings: Optional[bool] = True
    alert_stop_loss: Optional[bool] = True
    alert_anomaly: Optional[bool] = True
    alert_score_change: Optional[bool] = True


class UserSettingsResponse(BaseModel):
    user_id: str
    email: str
    default_investment_amount: float
    default_risk_tolerance: str
    preferred_horizons: List[str]
    dark_mode: bool
    currency: str
    plan_type: str = "free"
    analyses_today: int = 0
    max_analyses_per_day: int = 100
