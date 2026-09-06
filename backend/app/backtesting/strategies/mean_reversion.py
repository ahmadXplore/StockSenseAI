"""
StockSense AI — Mean Reversion & Oscillators Strategy
Exploits oversold/overbought statistical extremes using RSI (e.g. RSI < 30) and Bollinger Band lower-band tests.
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.schemas import OrderSide


class MeanReversionStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("MEAN_REVERSION_STRATEGY", params)
        self.rsi_entry_threshold = float(self.params.get("rsi_entry", 32.0))
        self.rsi_exit_threshold = float(self.params.get("rsi_exit", 68.0))

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

            rsi = float(sec_feat.get("rsi_14", sec_feat.get("rsi", 50.0)))
            bb_lower = float(sec_feat.get("bb_lower", close_price * 0.96))
            bb_upper = float(sec_feat.get("bb_upper", close_price * 1.04))

            has_pos = sec_id in current_positions and current_positions[sec_id].shares > 0

            # Oversold Entry Condition
            if (rsi <= self.rsi_entry_threshold or close_price <= bb_lower) and not has_pos:
                stop_price = close_price - (2.0 * atr) if atr > 0 else close_price * 0.94
                take_profit = bb_upper

                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.BUY,
                    confidence=max(0.5, (100.0 - rsi) / 100.0),
                    stop_loss_price=round(stop_price, 4),
                    take_profit_price=round(take_profit, 4),
                    reason=f"Mean reversion oversold bounce: RSI={rsi:.1f}, BB Lower=${bb_lower:.2f}",
                ))

            # Overbought Mean-Reverted Exit Condition
            elif (rsi >= self.rsi_exit_threshold or close_price >= bb_upper) and has_pos:
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    reason=f"Mean reversion target reached: RSI={rsi:.1f} >= {self.rsi_exit_threshold}",
                ))

        return signals
