"""
StockSense AI — Master Portfolio Engine
Encapsulates complete multi-security, multi-market, multi-currency portfolio state, positions, cash, and valuations.
"""

from typing import Dict, List, Optional, Any, Tuple
from app.backtesting.schemas import (
    PositionSide, PositionSnapshot, EquityCurvePoint, PortfolioAccountingSnapshot
)
from app.backtesting.portfolio.position_manager import Position
from app.backtesting.portfolio.cash_manager import CashManager
from app.backtesting.portfolio.accounting import AccountingLedger


class PortfolioEngine:
    def __init__(
        self,
        initial_capital: float = 100000.0,
        base_currency: str = "USD",
        cash_interest_rate_pct: float = 0.0,
    ):
        self.base_currency = base_currency
        self.cash = CashManager(initial_capital, base_currency, cash_interest_rate_pct)
        self.positions: Dict[str, Position] = {} # Key: security_id
        self.ledger = AccountingLedger(base_currency)
        self.peak_equity = initial_capital
        self.initial_capital = initial_capital

    def get_position(self, security_id: str) -> Optional[Position]:
        return self.positions.get(security_id)

    def has_position(self, security_id: str) -> bool:
        pos = self.positions.get(security_id)
        return pos is not None and pos.shares > 0

    def open_or_add_position(
        self,
        security_id: str,
        ticker: str,
        market_code: str,
        shares: float,
        fill_price: float,
        entry_date: str,
        side: PositionSide = PositionSide.LONG,
        native_currency: str = "USD",
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        trailing_stop_price: Optional[float] = None,
    ) -> Position:
        """Opens a new position or adds to an existing one."""
        pos = self.positions.get(security_id)
        if pos is None:
            pos = Position(
                security_id=security_id,
                ticker=ticker,
                market_code=market_code,
                side=side,
                shares=shares,
                average_entry_price=fill_price,
                entry_date=entry_date,
                native_currency=native_currency,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                trailing_stop_price=trailing_stop_price,
            )
            self.positions[security_id] = pos
        else:
            pos.add_shares(shares, fill_price)
            if stop_loss_price:
                pos.stop_loss_price = stop_loss_price
            if take_profit_price:
                pos.take_profit_price = take_profit_price
            if trailing_stop_price:
                pos.trailing_stop_price = trailing_stop_price

        return pos

    def close_or_reduce_position(
        self,
        security_id: str,
        shares_to_close: float,
        exit_price: float,
        exit_date: str,
    ) -> Tuple[float, float]:
        """
        Reduces/closes a position and records realized P&L.
        Returns: (actual_shares_closed, realized_pnl)
        """
        pos = self.positions.get(security_id)
        if pos is None or pos.shares <= 0:
            return 0.0, 0.0

        closed = min(pos.shares, shares_to_close)
        pnl = pos.reduce_shares(closed, exit_price)
        self.ledger.record_realized_pnl(exit_date, security_id, pnl)

        if pos.shares <= 0.000001:
            del self.positions[security_id]

        return closed, pnl

    def get_positions_market_value(self, current_prices: Dict[str, float]) -> float:
        total = 0.0
        for sec_id, pos in self.positions.items():
            price = current_prices.get(sec_id, current_prices.get(pos.ticker, pos.average_entry_price))
            fx = self.cash.get_fx_rate(pos.native_currency)
            total += pos.get_market_value(price) * fx
        return total

    def get_total_equity(self, current_prices: Dict[str, float]) -> float:
        cash_val = self.cash.get_total_cash_in_base_currency()
        positions_val = self.get_positions_market_value(current_prices)
        return cash_val + positions_val

    def get_current_weights(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        total_equity = self.get_total_equity(current_prices)
        if total_equity <= 0:
            return {}
        weights: Dict[str, float] = {}
        for sec_id, pos in self.positions.items():
            price = current_prices.get(sec_id, current_prices.get(pos.ticker, pos.average_entry_price))
            fx = self.cash.get_fx_rate(pos.native_currency)
            val = pos.get_market_value(price) * fx
            weights[sec_id] = round(val / total_equity, 4)
        return weights

    def generate_snapshot(self, current_date: str, current_prices: Dict[str, float]) -> EquityCurvePoint:
        cash_val = self.cash.get_total_cash_in_base_currency()
        pos_val = self.get_positions_market_value(current_prices)
        total_val = cash_val + pos_val
        
        if total_val > self.peak_equity:
            self.peak_equity = total_val
        
        dd_pct = ((self.peak_equity - total_val) / self.peak_equity) * 100.0 if self.peak_equity > 0 else 0.0
        cum_ret = ((total_val - self.initial_capital) / self.initial_capital) * 100.0 if self.initial_capital > 0 else 0.0
        
        return EquityCurvePoint(
            date=current_date,
            cash=round(cash_val, 2),
            positions_value=round(pos_val, 2),
            portfolio_value=round(total_val, 2),
            daily_return=0.0, # Computed by event loop
            cumulative_return=round(cum_ret, 4),
            drawdown_pct=round(dd_pct, 4),
            number_of_positions=len(self.positions),
        )
