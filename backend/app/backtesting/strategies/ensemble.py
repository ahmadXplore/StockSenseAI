"""
StockSense AI — Multi-Factor Ensemble Strategy
Quantitative Archetype: AI Prediction (50%), Technical Momentum (30%), Fundamental Factor (20%).
Execution Semantics: NEXT_OPEN — signals generated EOD, fills execute on next bar open.
Risk/Reward: 1:3 default (10% Stop Loss / 30% Take Profit).
"""

from typing import Dict, List, Any, Optional
from app.backtesting.strategies.base import BaseStrategy, StrategySignal
from app.backtesting.strategies.ai_prediction import AIPredictionStrategy
from app.backtesting.strategies.momentum import MomentumStrategy
from app.backtesting.strategies.fundamental import FundamentalStrategy
from app.backtesting.schemas import OrderSide


class EnsembleStrategy(BaseStrategy):
    """
    Multi-Factor Ensemble Strategy: consensus-weighted signal aggregation across AI prediction,
    technical momentum, and fundamental quality sub-strategies.

    Weight configuration (default matches quantitative spec):
        ai_weight        = 0.50  (AI model direction probability & expected return)
        momentum_weight  = 0.30  (MA crossover, RSI, momentum score)
        fundamental_weight = 0.20  (P/E, ROE, F-Score quality filter)

    Stop Loss / Take Profit:
        Enforced via config.stop_loss_pct (default 10%) and config.take_profit_pct (default 30%).
        If not provided via config, falls back to strategy-level params.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__("ENSEMBLE_STRATEGY", params)
        self.ai_weight = float(self.params.get("ai_weight", 0.50))
        self.mom_weight = float(self.params.get("momentum_weight", 0.30))
        self.fund_weight = float(self.params.get("fundamental_weight", 0.20))

        # Normalize weights to always sum to 1.0
        total_weight = self.ai_weight + self.mom_weight + self.fund_weight
        if total_weight > 0:
            self.ai_weight /= total_weight
            self.mom_weight /= total_weight
            self.fund_weight /= total_weight

        # Stop Loss / Take Profit defaults (override via BacktestConfig)
        self.default_stop_loss_pct = float(self.params.get("stop_loss_pct", 0.10))  # 10%
        self.default_take_profit_pct = float(self.params.get("take_profit_pct", 0.30))  # 30%

        # Minimum consensus buy score threshold (sum of weighted sub-strategy confidence)
        self.buy_score_threshold = float(self.params.get("buy_score_threshold", 0.30))
        self.sell_score_threshold = float(self.params.get("sell_score_threshold", 0.30))

        # Sub-strategies
        self.ai_sub = AIPredictionStrategy(params)
        self.mom_sub = MomentumStrategy(params)
        self.fund_sub = FundamentalStrategy(params)

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
        """
        Generates ensemble consensus signals via weighted scoring across all three sub-strategies.
        NEXT_OPEN execution semantics: signals are based strictly on close-of-bar data.
        """
        # Collect sub-strategy signals indexed by security_id
        ai_sigs = {
            s.security_id: s for s in self.ai_sub.generate_signals(
                date_str, available_securities, prices, features, predictions,
                current_positions, portfolio_equity
            )
        }
        mom_sigs = {
            s.security_id: s for s in self.mom_sub.generate_signals(
                date_str, available_securities, prices, features, predictions,
                current_positions, portfolio_equity
            )
        }
        fund_sigs = {
            s.security_id: s for s in self.fund_sub.generate_signals(
                date_str, available_securities, prices, features, predictions,
                current_positions, portfolio_equity
            )
        }

        all_sec_ids = set(ai_sigs.keys()) | set(mom_sigs.keys()) | set(fund_sigs.keys())
        consensus_signals: List[StrategySignal] = []

        for sec_id in all_sec_ids:
            buy_score = 0.0
            sell_score = 0.0
            component_reasons = []

            # ── AI Model Component (0.50 weight) ──
            if sec_id in ai_sigs:
                ai_sig = ai_sigs[sec_id]
                ai_conf = max(0.0, min(1.0, ai_sig.confidence))
                if ai_sig.side == OrderSide.BUY:
                    contrib = self.ai_weight * ai_conf
                    buy_score += contrib
                    component_reasons.append(f"AI={contrib:.2f}({ai_conf:.0%}↑)")
                else:
                    contrib = self.ai_weight * ai_conf
                    sell_score += contrib
                    component_reasons.append(f"AI={contrib:.2f}({ai_conf:.0%}↓)")

            # ── Momentum Component (0.30 weight) ──
            if sec_id in mom_sigs:
                mom_sig = mom_sigs[sec_id]
                mom_conf = max(0.0, min(1.0, mom_sig.confidence))
                if mom_sig.side == OrderSide.BUY:
                    contrib = self.mom_weight * mom_conf
                    buy_score += contrib
                    component_reasons.append(f"Mom={contrib:.2f}({mom_conf:.0%}↑)")
                else:
                    contrib = self.mom_weight * mom_conf
                    sell_score += contrib
                    component_reasons.append(f"Mom={contrib:.2f}({mom_conf:.0%}↓)")

            # ── Fundamental Component (0.20 weight) ──
            if sec_id in fund_sigs:
                fund_sig = fund_sigs[sec_id]
                fund_conf = max(0.0, min(1.0, fund_sig.confidence))
                if fund_sig.side == OrderSide.BUY:
                    contrib = self.fund_weight * fund_conf
                    buy_score += contrib
                    component_reasons.append(f"Fund={contrib:.2f}({fund_conf:.0%}↑)")
                else:
                    contrib = self.fund_weight * fund_conf
                    sell_score += contrib
                    component_reasons.append(f"Fund={contrib:.2f}({fund_conf:.0%}↓)")

            # Use the representative signal for metadata (AI > Momentum > Fundamental)
            rep_sig = ai_sigs.get(sec_id) or mom_sigs.get(sec_id) or fund_sigs.get(sec_id)
            if not rep_sig:
                continue

            close_price = prices.get(sec_id, {}).get("close", 0.0)
            if close_price <= 0:
                continue

            component_str = ", ".join(component_reasons)

            # ── BUY Consensus ──
            if buy_score >= self.buy_score_threshold and buy_score > sell_score:
                # Compute stop_loss / take_profit from percentage config
                sl_pct = self.default_stop_loss_pct
                tp_pct = self.default_take_profit_pct

                # Respect sub-strategy overrides if more conservative
                if rep_sig.stop_loss_price and rep_sig.stop_loss_price > 0:
                    implied_sl_pct = (close_price - rep_sig.stop_loss_price) / close_price
                    sl_pct = max(sl_pct, implied_sl_pct)  # use whichever is tighter protection

                stop_price = round(close_price * (1.0 - sl_pct), 4)
                take_profit = round(close_price * (1.0 + tp_pct), 4)

                rep_sig.side = OrderSide.BUY
                rep_sig.confidence = round(min(1.0, buy_score), 4)
                rep_sig.stop_loss_price = stop_price
                rep_sig.take_profit_price = take_profit
                rep_sig.reason = (
                    f"[ENSEMBLE BUY] Consensus score={buy_score:.3f} "
                    f"(AI×{self.ai_weight:.0%} | Mom×{self.mom_weight:.0%} | Fund×{self.fund_weight:.0%}) — "
                    f"Components: {component_str} | "
                    f"SL=${stop_price:.2f}(-{sl_pct:.0%}) TP=${take_profit:.2f}(+{tp_pct:.0%})"
                )
                consensus_signals.append(rep_sig)

            # ── SELL Consensus ──
            elif sell_score >= self.sell_score_threshold and sell_score > buy_score:
                rep_sig.side = OrderSide.SELL
                rep_sig.confidence = round(min(1.0, sell_score), 4)
                rep_sig.reason = (
                    f"[ENSEMBLE SELL] Consensus score={sell_score:.3f} "
                    f"(AI×{self.ai_weight:.0%} | Mom×{self.mom_weight:.0%} | Fund×{self.fund_weight:.0%}) — "
                    f"Components: {component_str}"
                )
                consensus_signals.append(rep_sig)

        return consensus_signals
