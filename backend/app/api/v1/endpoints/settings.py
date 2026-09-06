"""
StockSense AI — User Settings Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.settings import UserSettingsRequest, UserSettingsResponse

router = APIRouter()


@router.get("", response_model=UserSettingsResponse, summary="Get user preferences")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """
    Returns current user settings and analysis quota status.
    """
    return UserSettingsResponse(
        user_id="usr_default",
        email="guest@stocksense.ai",
        default_investment_amount=10000.0,
        default_risk_tolerance="moderate",
        preferred_horizons=["all"],
        dark_mode=True,
        currency="USD",
        plan_type="free",
        analyses_today=0,
        max_analyses_per_day=100,
    )


@router.put("", response_model=UserSettingsResponse, summary="Update user preferences")
async def update_settings(
    payload: UserSettingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Updates user settings and preferences.
    """
    return UserSettingsResponse(
        user_id="usr_default",
        email="guest@stocksense.ai",
        default_investment_amount=payload.default_investment_amount or 10000.0,
        default_risk_tolerance=payload.default_risk_tolerance or "moderate",
        preferred_horizons=payload.preferred_horizons or ["all"],
        dark_mode=payload.dark_mode if payload.dark_mode is not None else True,
        currency=payload.currency or "USD",
        plan_type="free",
        analyses_today=0,
        max_analyses_per_day=100,
    )
