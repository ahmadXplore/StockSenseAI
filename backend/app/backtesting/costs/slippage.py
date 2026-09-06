"""
StockSense AI — Slippage Models
Calculates realistic execution price degradation based on trade size, volatility, liquidity, or basis points.
"""

import math
from typing import Optional
from app.backtesting.schemas import SlippageModelType, OrderSide


def calculate_slippage(
    reference_price: float,
    shares: float,
    side: OrderSide,
    model_type: SlippageModelType = SlippageModelType.FIXED_BPS,
    slippage_bps: float = 5.0,
    daily_volume: Optional[float] = None,
    atr_volatility: Optional[float] = None,
    bid_ask_spread: Optional[float] = None,
) -> float:
    """
    Computes executed price including directional slippage penalty.
    For BUY: executed_price >= reference_price
    For SELL: executed_price <= reference_price
    """
    if reference_price <= 0:
        return reference_price

    slippage_fraction = 0.0

    if model_type == SlippageModelType.FIXED_BPS:
        slippage_fraction = slippage_bps / 10000.0

    elif model_type == SlippageModelType.FIXED_PCT:
        slippage_fraction = slippage_bps / 100.0

    elif model_type == SlippageModelType.VOLATILITY_BASED:
        # Slippage scales with current normalized ATR volatility
        if atr_volatility and reference_price > 0:
            vol_ratio = min(0.05, atr_volatility / reference_price)
            slippage_fraction = max(0.0005, vol_ratio * 0.1) # 10% of 1-day ATR
        else:
            slippage_fraction = slippage_bps / 10000.0

    elif model_type == SlippageModelType.VOLUME_BASED:
        # Market impact model: slippage = alpha * (shares / volume)^0.5
        if daily_volume and daily_volume > 0:
            participation_rate = min(0.5, shares / daily_volume)
            slippage_fraction = 0.1 * math.sqrt(participation_rate)
        else:
            slippage_fraction = slippage_bps / 10000.0

    elif model_type == SlippageModelType.SPREAD_BASED:
        if bid_ask_spread and bid_ask_spread > 0 and reference_price > 0:
            slippage_fraction = (bid_ask_spread / reference_price) * 0.5
        else:
            slippage_fraction = slippage_bps / 10000.0

    # Apply directional adjustment
    is_buying = side in (OrderSide.BUY, OrderSide.BUY_TO_COVER)
    if is_buying:
        executed_price = reference_price * (1.0 + slippage_fraction)
    else:
        executed_price = reference_price * max(0.01, (1.0 - slippage_fraction))

    return round(executed_price, 4)
