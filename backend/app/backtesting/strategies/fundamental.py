"""
StockSense AI — Fundamental Factor Strategy
Constructs positions in fundamentally sound companies with low P/E, high ROE, healthy debt ratios, and positive margins.
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.schemas import OrderSide


class FundamentalStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("FUNDAMENTAL_STRATEGY", params)
        self.min_roe = float(self.params.get("min_roe", 0.12)) # 12% ROE
        self.max_pe = float(self.params.get("max_pe", 35.0))
        self.max_debt_to_equity = float(self.params.get("max_debt_to_equity", 1.8))

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

            if close_price <= 0:
                continue

            pe_ratio = float(sec_feat.get("pe_ratio", 20.0))
            roe = float(sec_feat.get("roe", sec_feat.get("return_on_equity", 0.15)))
            debt_to_equity = float(sec_feat.get("debt_to_equity", 0.8))
            f_score = float(sec_feat.get("piotroski_f_score", 7.0))

            has_pos = sec_id in current_positions and current_positions[sec_id].shares > 0

            # Quality + Value Fundamental Criteria
            is_fundamental_winner = (
                0 < pe_ratio <= self.max_pe and
                roe >= self.min_roe and
                debt_to_equity <= self.max_debt_to_equity and
                f_score >= 5.0
            )

            if is_fundamental_winner and not has_pos:
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.BUY,
                    confidence=min(1.0, f_score / 9.0),
                    stop_loss_price=round(close_price * 0.90, 4), # 10% fundamental stop
                    take_profit_price=round(close_price * 1.30, 4), # 30% fundamental target
                    reason=f"Fundamental quality entry: P/E={pe_ratio:.1f}, ROE={roe:.1%}, F-Score={f_score:.0f}",
                ))

            elif not is_fundamental_winner and has_pos and (pe_ratio > self.max_pe * 1.5 or f_score < 4.0):
                signals.append(StrategySignal(
                    security_id=sec_id,
                    ticker=ticker,
                    side=OrderSide.SELL,
                    reason="Fundamental thesis exit: Valuation stretched or quality deteriorated",
                ))

        return signals
