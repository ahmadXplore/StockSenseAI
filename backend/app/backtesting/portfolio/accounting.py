"""
StockSense AI — Double-Entry Portfolio Accounting & Audit Ledger
Maintains transaction histories, cash inflows/outflows, dividends, fees, and realized gains.
"""

from typing import List, Dict, Any, Optional
from app.backtesting.schemas import TradeRecord, PortfolioAccountingSnapshot


class AccountingLedger:
    def __init__(self, base_currency: str = "USD"):
        self.base_currency = base_currency
        self.ledger_entries: List[Dict[str, Any]] = []
        self.total_dividends: float = 0.0
        self.total_friction: float = 0.0
        self.total_realized_pnl: float = 0.0

    def record_entry(
        self,
        entry_date: str,
        entry_type: str, # "TRADE_BUY", "TRADE_SELL", "DIVIDEND", "FEE", "SPLIT", "INTEREST"
        amount: float,
        description: str,
        security_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.ledger_entries.append({
            "date": entry_date,
            "type": entry_type,
            "amount": round(amount, 4),
            "description": description,
            "security_id": security_id,
            "metadata": metadata or {},
        })

    def record_dividend(self, entry_date: str, security_id: str, amount: float) -> None:
        self.total_dividends += amount
        self.record_entry(entry_date, "DIVIDEND", amount, f"Dividend received for {security_id}", security_id)

    def record_friction(self, entry_date: str, security_id: str, amount: float) -> None:
        self.total_friction += amount
        self.record_entry(entry_date, "FEE", -amount, f"Transaction friction on {security_id}", security_id)

    def record_realized_pnl(self, entry_date: str, security_id: str, pnl: float) -> None:
        self.total_realized_pnl += pnl
        self.record_entry(entry_date, "REALIZED_PNL", pnl, f"Realized P&L on {security_id}: ${pnl:+.2f}", security_id)
