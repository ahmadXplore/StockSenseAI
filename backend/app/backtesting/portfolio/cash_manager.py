"""
StockSense AI — Multi-Currency Cash Manager
Maintains multi-currency cash balances, handles foreign exchange conversions, interest accruals, and deposits/withdrawals.
"""

from typing import Dict, Optional


class CashManager:
    def __init__(self, initial_capital: float = 100000.0, base_currency: str = "USD", interest_rate_pct: float = 0.0):
        self.base_currency = base_currency.upper()
        self.interest_rate_pct = interest_rate_pct
        # Currency balances: e.g. {"USD": 100000.0, "PKR": 0.0, "GBP": 0.0}
        self.balances: Dict[str, float] = {self.base_currency: initial_capital}
        # FX Rates to Base Currency: e.g. {"USD": 1.0, "PKR": 0.0036, "GBP": 1.28}
        self.fx_rates: Dict[str, float] = {self.base_currency: 1.0}
        self.total_interest_earned: float = 0.0

    def set_fx_rate(self, currency: str, rate_to_base: float) -> None:
        self.fx_rates[currency.upper()] = rate_to_base

    def get_fx_rate(self, currency: str) -> float:
        return self.fx_rates.get(currency.upper(), 1.0)

    def get_balance(self, currency: Optional[str] = None) -> float:
        curr = (currency or self.base_currency).upper()
        return self.balances.get(curr, 0.0)

    def get_total_cash_in_base_currency(self) -> float:
        total = 0.0
        for curr, bal in self.balances.items():
            rate = self.fx_rates.get(curr, 1.0)
            total += bal * rate
        return total

    def debit_cash(self, amount: float, currency: Optional[str] = None) -> bool:
        curr = (currency or self.base_currency).upper()
        current_bal = self.balances.get(curr, 0.0)
        if current_bal >= amount:
            self.balances[curr] = current_bal - amount
            return True
        else:
            # Multi-currency auto-conversion if base currency has sufficient funds
            needed_in_base = amount * self.get_fx_rate(curr)
            base_bal = self.balances.get(self.base_currency, 0.0)
            if base_bal >= needed_in_base:
                self.balances[self.base_currency] = base_bal - needed_in_base
                return True
            return False

    def credit_cash(self, amount: float, currency: Optional[str] = None) -> None:
        if amount <= 0:
            return
        curr = (currency or self.base_currency).upper()
        self.balances[curr] = self.balances.get(curr, 0.0) + amount

    def accrue_daily_interest(self) -> float:
        if self.interest_rate_pct <= 0:
            return 0.0
        daily_rate = (self.interest_rate_pct / 100.0) / 252.0
        interest = self.get_total_cash_in_base_currency() * daily_rate
        if interest > 0:
            self.credit_cash(interest, self.base_currency)
            self.total_interest_earned += interest
        return interest
