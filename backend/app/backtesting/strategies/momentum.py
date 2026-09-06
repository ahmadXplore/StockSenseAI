"""
StockSense AI — Momentum & Moving Average Breakout Strategy
Trades based on momentum scores, EMA/SMA crossovers, and price velocity above moving averages.
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.schemas import OrderSide


class MomentumStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("MOMENTUM_STRATEGY", params)
        self.fast_window = int(self.params.get("fast_window", 20))
        self.slow_window = int(self.params.get("slow_window", 50))
        self.min_momentum_score = float(self.params.get("min_momentum_score", 0.01))

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

            ma_fast = float(sec_feat.get("ema_20", sec_feat.get("sma_20", sec_feat.get(f"ema_{self.fast_window}", close_price))))
            ma_slow = float(sec_feat.get("ema_50", sec_feat.get("sma_50", sec_feat.get(f"ema_{self.slow_window}", close_price * 0.98))))
            momentum_ret = float(sec_feat.get("return_20d", sec_feat.get("momentum_20d", 0.02)))

            has_pos = sec_id in current_positions and current_positions[sec_id].shares > 0

            # Bullish crossover + price above slow MA + positive return momentum
            if ma_fast > ma_slow and close_price >= ma_slow and momentum_ret >= self.min_momentum_score and not has_pos:
                stop_price = close_price - (2.0 * atr) if atr > 0 else close_price * 0.95
                take_profit = close_price + (4.0 * atr) if atr > 0 else close_price * 1.15

                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.BUY,
                    confidence=min(1.0, 0.5 + momentum_ret),
                    stop_loss_price=round(stop_price, 4),
                    take_profit_price=round(take_profit, 4),
                    reason=f"Momentum breakout: MA{self.fast_window} ({ma_fast:.2f}) > MA{self.slow_window} ({ma_slow:.2f}), Close={close_price:.2f}",
                ))

            # Bearish crossover exit
            elif ma_fast < ma_slow and has_pos:
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    reason=f"Momentum breakdown: MA{self.fast_window} crossed below MA{self.slow_window}",
                ))

        return signals
