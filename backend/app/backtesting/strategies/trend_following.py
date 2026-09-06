"""
StockSense AI — Trend Following Strategy
Executes based on MACD line crosses, SuperTrend direction, and 200-day long-term trend regimes.
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.schemas import OrderSide


class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("TREND_FOLLOWING_STRATEGY", params)
        self.atr_mult = float(self.params.get("atr_stop_multiplier", 2.0))

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
            atr = sec_price.get("atr", close_price * 0.02)

            if close_price <= 0:
                continue

            macd_line = float(sec_feat.get("macd_line", sec_feat.get("macd", 0.0)))
            macd_signal = float(sec_feat.get("macd_signal", 0.0))
            sma_200 = float(sec_feat.get("sma_200", close_price * 0.95))

            has_pos = sec_id in current_positions and current_positions[sec_id].shares > 0

            # Trend Confirmation: Price > SMA 200 and MACD Line > MACD Signal
            if close_price > sma_200 and macd_line > macd_signal and not has_pos:
                stop_price = close_price - (self.atr_mult * atr) if atr > 0 else close_price * 0.95
                take_profit = close_price + (self.atr_mult * 2.5 * atr) if atr > 0 else close_price * 1.20

                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.BUY,
                    confidence=0.75,
                    stop_loss_price=round(stop_price, 4),
                    take_profit_price=round(take_profit, 4),
                    reason=f"Trend following entry: Price (${close_price:.2f}) > SMA200 (${sma_200:.2f}) and MACD ({macd_line:.3f} > {macd_signal:.3f})",
                ))

            # Trend Breakdown: Price falls below SMA 200 or MACD bearish cross
            elif (close_price < sma_200 or macd_line < macd_signal) and has_pos:
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    reason=f"Trend following exit: MACD or SMA200 trend breakdown",
                ))

        return signals
