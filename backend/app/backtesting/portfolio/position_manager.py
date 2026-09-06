"""
StockSense AI — Position Manager
Tracks individual positions, cost basis, average entry prices, realized & unrealized P&L.
"""

from typing import Dict, Optional
from app.backtesting.schemas import PositionSide, PositionSnapshot


class Position:
    def __init__(
        self,
        security_id: str,
        ticker: str,
        market_code: str,
        side: PositionSide = PositionSide.LONG,
        shares: float = 0.0,
        average_entry_price: float = 0.0,
        entry_date: str = "",
        native_currency: str = "USD",
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        trailing_stop_price: Optional[float] = None,
        highest_price_seen: Optional[float] = None,
        lowest_price_seen: Optional[float] = None,
    ):
        self.security_id = security_id
        self.ticker = ticker
        self.market_code = market_code
        self.side = side
        self.shares = shares
        self.average_entry_price = average_entry_price
        self.entry_date = entry_date
        self.native_currency = native_currency
        self.stop_loss_price = stop_loss_price
        self.take_profit_price = take_profit_price
        self.trailing_stop_price = trailing_stop_price
        self.highest_price_seen = highest_price_seen or average_entry_price
        self.lowest_price_seen = lowest_price_seen or average_entry_price
        self.realized_pnl = 0.0
        self.bars_held = 0

    @property
    def cost_basis(self) -> float:
        return self.shares * self.average_entry_price

    def update_price_extremes(self, high: float, low: float) -> None:
        if self.highest_price_seen is None or high > self.highest_price_seen:
            self.highest_price_seen = high
        if self.lowest_price_seen is None or low < self.lowest_price_seen:
            self.lowest_price_seen = low

    def get_market_value(self, current_price: float) -> float:
        return self.shares * current_price

    def get_unrealized_pnl(self, current_price: float) -> float:
        if self.side == PositionSide.LONG:
            return (current_price - self.average_entry_price) * self.shares
        else: # SHORT
            return (self.average_entry_price - current_price) * self.shares

    def get_unrealized_pnl_pct(self, current_price: float) -> float:
        if self.average_entry_price <= 0:
            return 0.0
        if self.side == PositionSide.LONG:
            return ((current_price - self.average_entry_price) / self.average_entry_price) * 100.0
        else:
            return ((self.average_entry_price - current_price) / self.average_entry_price) * 100.0

    def add_shares(self, new_shares: float, fill_price: float) -> None:
        if new_shares <= 0:
            return
        total_cost = (self.shares * self.average_entry_price) + (new_shares * fill_price)
        self.shares += new_shares
        self.average_entry_price = total_cost / self.shares if self.shares > 0 else fill_price

    def reduce_shares(self, shares_to_close: float, exit_price: float) -> float:
        """Closes a portion of the position and computes realized P&L."""
        closed = min(self.shares, shares_to_close)
        if self.side == PositionSide.LONG:
            pnl = (exit_price - self.average_entry_price) * closed
        else:
            pnl = (self.average_entry_price - exit_price) * closed
        
        self.shares -= closed
        self.realized_pnl += pnl
        return pnl

    def to_snapshot(self, current_price: float, total_portfolio_equity: float, fx_rate: float = 1.0) -> PositionSnapshot:
        mkt_val = self.get_market_value(current_price)
        base_val = mkt_val * fx_rate
        weight = (base_val / total_portfolio_equity) if total_portfolio_equity > 0 else 0.0
        
        return PositionSnapshot(
            security_id=self.security_id,
            ticker=self.ticker,
            market_code=self.market_code,
            side=self.side,
            shares=round(self.shares, 4),
            average_entry_price=round(self.average_entry_price, 4),
            current_price=round(current_price, 4),
            cost_basis=round(self.cost_basis, 2),
            market_value=round(mkt_val, 2),
            unrealized_pnl=round(self.get_unrealized_pnl(current_price), 2),
            unrealized_pnl_pct=round(self.get_unrealized_pnl_pct(current_price), 2),
            portfolio_weight=round(weight, 4),
            stop_loss_price=self.stop_loss_price,
            take_profit_price=self.take_profit_price,
            trailing_stop_price=self.trailing_stop_price,
            native_currency=self.native_currency,
            base_currency_value=round(base_val, 2),
        )
