"""
StockSense AI — Ensemble Strategy
Combines AI predictions, momentum signals, and fundamental filters into a robust multi-factor consensus signal.
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.strategies.ai_prediction import AIPredictionStrategy
from app.backtesting.strategies.momentum import MomentumStrategy
from app.backtesting.strategies.fundamental import FundamentalStrategy
from app.backtesting.schemas import OrderSide


class EnsembleStrategy(BaseStrategy):
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("ENSEMBLE_STRATEGY", params)
        self.ai_sub = AIPredictionStrategy(params)
        self.mom_sub = MomentumStrategy(params)
        self.fund_sub = FundamentalStrategy(params)
        self.ai_weight = float(self.params.get("ai_weight", 0.50))
        self.mom_weight = float(self.params.get("momentum_weight", 0.30))
        self.fund_weight = float(self.params.get("fundamental_weight", 0.20))

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
        ai_sigs = {s.security_id: s for s in self.ai_sub.generate_signals(date_str, available_securities, prices, features, predictions, current_positions, portfolio_equity)}
        mom_sigs = {s.security_id: s for s in self.mom_sub.generate_signals(date_str, available_securities, prices, features, predictions, current_positions, portfolio_equity)}
        fund_sigs = {s.security_id: s for s in self.fund_sub.generate_signals(date_str, available_securities, prices, features, predictions, current_positions, portfolio_equity)}

        all_sec_ids = set(ai_sigs.keys()).union(mom_sigs.keys()).union(fund_sigs.keys())
        consensus_signals: List[StrategySignal] = []

        for sec_id in all_sec_ids:
            buy_score = 0.0
            sell_score = 0.0

            if sec_id in ai_sigs:
                if ai_sigs[sec_id].side == OrderSide.BUY:
                    buy_score += self.ai_weight * ai_sigs[sec_id].confidence
                else:
                    sell_score += self.ai_weight

            if sec_id in mom_sigs:
                if mom_sigs[sec_id].side == OrderSide.BUY:
                    buy_score += self.mom_weight * mom_sigs[sec_id].confidence
                else:
                    sell_score += self.mom_weight

            if sec_id in fund_sigs:
                if fund_sigs[sec_id].side == OrderSide.BUY:
                    buy_score += self.fund_weight * fund_sigs[sec_id].confidence
                else:
                    sell_score += self.fund_weight

            # Representative signal picking
            rep_sig = ai_sigs.get(sec_id) or mom_sigs.get(sec_id) or fund_sigs.get(sec_id)
            if not rep_sig:
                continue

            if buy_score >= 0.50:
                rep_sig.confidence = round(buy_score, 4)
                rep_sig.side = OrderSide.BUY
                rep_sig.reason = f"Ensemble consensus BUY score = {buy_score:.2f} (AI={self.ai_weight}, Mom={self.mom_weight}, Fund={self.fund_weight})"
                consensus_signals.append(rep_sig)
            elif sell_score >= 0.50:
                rep_sig.side = OrderSide.SELL
                rep_sig.reason = f"Ensemble consensus SELL score = {sell_score:.2f}"
                consensus_signals.append(rep_sig)

        return consensus_signals
