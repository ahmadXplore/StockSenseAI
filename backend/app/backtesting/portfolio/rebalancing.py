"""
StockSense AI — Rebalancing Engine
Manages periodic (daily, weekly, monthly, quarterly) and drift-threshold portfolio rebalancing.
"""

from typing import Dict, List, Tuple
from datetime import datetime, date
from app.backtesting.schemas import RebalanceFrequency


class RebalancingEngine:
    def __init__(self, frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY, drift_threshold_pct: float = 0.05):
        self.frequency = frequency
        self.drift_threshold_pct = drift_threshold_pct
        self.last_rebalance_date: Optional[str] = None
        self.last_rebalance_month: Optional[int] = None
        self.last_rebalance_week: Optional[int] = None

    def should_rebalance(
        self,
        current_date: str,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float]
    ) -> bool:
        """Determines if a rebalancing event is triggered on the given date."""
        if self.frequency == RebalanceFrequency.NONE:
            return False

        if self.frequency == RebalanceFrequency.DAILY:
            return True

        dt = datetime.strptime(current_date, "%Y-%m-%d")

        if self.frequency == RebalanceFrequency.WEEKLY:
            week_num = dt.isocalendar()[1]
            if self.last_rebalance_week != week_num:
                self.last_rebalance_week = week_num
                return True

        elif self.frequency == RebalanceFrequency.MONTHLY:
            if self.last_rebalance_month != dt.month:
                self.last_rebalance_month = dt.month
                return True

        elif self.frequency == RebalanceFrequency.QUARTERLY:
            quarter = (dt.month - 1) // 3 + 1
            if self.last_rebalance_month is None or ((dt.month - 1) // 3 + 1) != quarter:
                self.last_rebalance_month = quarter
                return True

        elif self.frequency == RebalanceFrequency.THRESHOLD_DRIFT:
            # Check maximum drift between current weights and target weights
            all_keys = set(current_weights.keys()).union(set(target_weights.keys()))
            for k in all_keys:
                cw = current_weights.get(k, 0.0)
                tw = target_weights.get(k, 0.0)
                if abs(cw - tw) >= self.drift_threshold_pct:
                    return True

        return False
