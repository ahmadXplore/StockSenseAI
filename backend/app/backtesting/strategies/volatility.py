"""
StockSense AI — Volatility Breakout Strategy
Enters on volatility expansions (Donchian channel / ATR surges) and manages trailing ATR stops.
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.schemas import OrderSide


class VolatilityBreakoutStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("VOLATILITY_BREAKOUT_STRATEGY", params)
        self.channel_period = int(self.params.get("channel_period", 20))
        self.atr_multiplier = float(self.params.get("atr_multiplier", 1.8))

    def generate_signals(
        self,
        date_str: str,
        available_securities: List[str],
        prices: Dict[str, Dict[str, float]],
        features: Dict[str, Dict[str, Any]],
        predictions: Dict[str, Dict[str, Any]],
        current_positions: Dict[str, Any],
        portfolio_equity: float,
    ) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        for sec_id in available_securities:
            sec_price = prices.get(sec_id, {})
            sec_feat = features.get(sec_id, {})
            close_price = sec_price.get("close", 0.0)
            ticker = sec_price.get("ticker", sec_id.split("::")[-1])
            atr = sec_price.get("atr", close_price * 0.025)

            if close_price <= 0:
                continue

            highest_high_20 = float(sec_feat.get("donchian_high_20", close_price * 1.02))
            lowest_low_20 = float(sec_feat.get("donchian_low_20", close_price * 0.98))

            has_pos = sec_id in current_positions and current_positions[sec_id].shares > 0

            # Breakout entry: price closes at or above the 20-bar high
            if close_price >= highest_high_20 and not has_pos:
                stop_price = close_price - (self.atr_multiplier * atr) if atr > 0 else close_price * 0.95
                trailing_stop = self.atr_multiplier

                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.BUY,
                    confidence=0.80,
                    stop_loss_price=round(stop_price, 4),
                    trailing_stop_atr_mult=trailing_stop,
                    reason=f"Volatility expansion entry: Price (${close_price:.2f}) >= 20-day high (${highest_high_20:.2f})",
                ))

            # Breakdown exit
            elif close_price <= lowest_low_20 and has_pos:
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    reason=f"Volatility breakdown: Price fell below 20-day low (${lowest_low_20:.2f})",
                ))

        return signals
