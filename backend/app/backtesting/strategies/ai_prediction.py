"""
StockSense AI — AI Machine Learning Prediction Strategy
Consumes Prompt 4 multi-horizon predictions, direction probability P(up), expected returns, and regime filters.
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.schemas import OrderSide, OrderType


class AIPredictionStrategy(BaseStrategy):
    """
    Executes trades based on point-in-time ML direction forecasts, probability thresholds,
    expected returns, and volatility calibration.
    """
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("AI_PREDICTION_STRATEGY", params)
        self.min_probability = float(self.params.get("min_probability", 0.52))
        self.min_expected_return = float(self.params.get("min_expected_return", 0.005)) # 0.5%
        self.max_predicted_volatility = float(self.params.get("max_predicted_volatility", 0.65))
        self.atr_stop_multiplier = float(self.params.get("atr_stop_multiplier", 2.0))
        self.atr_profit_multiplier = float(self.params.get("atr_profit_multiplier", 3.5))

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
            sec_pred = predictions.get(sec_id, {})
            sec_price = prices.get(sec_id, {})
            close_price = sec_price.get("close", 0.0)
            atr = sec_price.get("atr", close_price * 0.02)
            ticker = sec_price.get("ticker", sec_id.split("::")[-1])

            if close_price <= 0:
                continue

            prob_up = float(sec_pred.get("probability_up", 0.5))
            exp_ret = float(sec_pred.get("expected_return", sec_pred.get("expected_return_pct", 0.0)))
            pred_vol = float(sec_pred.get("predicted_volatility", 0.25))
            confidence = float(sec_pred.get("confidence_score", prob_up))
            market_regime = sec_pred.get("regime", "bull")

            has_pos = sec_id in current_positions and current_positions[sec_id].shares > 0

            # Buy Signal Criteria:
            # 1. P(up) >= min_probability
            # 2. Expected return >= min_expected_return
            # 3. Volatility <= max_predicted_volatility
            is_bullish = (
                prob_up >= self.min_probability and
                exp_ret >= self.min_expected_return and
                pred_vol <= self.max_predicted_volatility
            )

            if is_bullish and not has_pos:
                stop_price = close_price - (self.atr_stop_multiplier * atr) if atr > 0 else close_price * 0.95
                take_profit = close_price + (self.atr_profit_multiplier * atr) if atr > 0 else close_price * 1.15
                
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.BUY,
                    confidence=confidence,
                    expected_return=exp_ret,
                    predicted_volatility=pred_vol,
                    stop_loss_price=round(stop_price, 4),
                    take_profit_price=round(take_profit, 4),
                    reason=f"AI model bullish signal: P(up)={prob_up:.1%}, ExpRet={exp_ret:.2%}, Regime={market_regime}",
                    signal_metadata={
                        "probability_up": prob_up,
                        "expected_return": exp_ret,
                        "predicted_volatility": pred_vol,
                        "confidence": confidence,
                        "market_regime": market_regime,
                    }
                ))

            # Sell / Exit Signal Criteria:
            # P(up) drops significantly below threshold
            elif has_pos and prob_up < 0.45:
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    confidence=1.0 - prob_up,
                    reason=f"AI model signal reversal: P(up) dropped to {prob_up:.1%}",
                    signal_metadata={"probability_up": prob_up}
                ))

        return signals
