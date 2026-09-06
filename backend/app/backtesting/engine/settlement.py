"""
StockSense AI — Settlement Engine
Models clearing cycles and settlement cash delays (e.g. US T+1 as of May 2024, PSX T+2, UK T+2).
"""

from typing import Dict, List
from datetime import datetime, timedelta


class SettlementEngine:
    def __init__(self, default_delay_days: int = 1):
        self.default_delay_days = default_delay_days
        # List of unsettled cash credits: [{"available_date": "2024-05-15", "amount": 5000.0, "currency": "USD"}]
        self.pending_settlements: List[Dict[str, Any]] = []

    def get_market_settlement_days(self, market_code: str) -> int:
        m = market_code.upper()
        if m == "US":
            return 1 # US T+1
        elif m in ("PK", "UK", "IN", "JP", "HK"):
            return 2 # T+2
        return self.default_delay_days

    def schedule_settlement(self, trade_date: str, amount: float, market_code: str, currency: str = "USD") -> str:
        days = self.get_market_settlement_days(market_code)
        dt = datetime.strptime(trade_date, "%Y-%m-%d") + timedelta(days=days)
        avail_date = dt.strftime("%Y-%m-%d")
        
        self.pending_settlements.append({
            "available_date": avail_date,
            "amount": amount,
            "currency": currency,
        })
        return avail_date

    def process_available_settlements(self, current_date: str) -> float:
        """Returns total cash ready to clear into portfolio."""
        cleared_total = 0.0
        remaining = []
        for s in self.pending_settlements:
            if s["available_date"] <= current_date:
                cleared_total += s["amount"]
            else:
                remaining.append(s)
        self.pending_settlements = remaining
        return cleared_total
