"""
StockSense AI — Multi-Currency Conversion Service
Provides on-the-fly currency conversion for portfolio valuation, cross-market analytics,
and risk modeling WITHOUT mutating native canonical OHLCV records.
"""

from __future__ import annotations
from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, date, timezone


# Benchmark FX baseline rates against USD
# In production, this integrates with FRED/ECB or live FX feeds.
DEFAULT_FX_RATES_TO_USD: Dict[str, Decimal] = {
    "USD": Decimal("1.0"),
    "PKR": Decimal("0.0036"),    # 1 PKR ~ 0.0036 USD (~278 PKR/USD)
    "GBP": Decimal("1.27"),      # 1 GBP ~ 1.27 USD
    "EUR": Decimal("1.08"),      # 1 EUR ~ 1.08 USD
    "JPY": Decimal("0.0067"),    # 1 JPY ~ 0.0067 USD (~150 JPY/USD)
    "HKD": Decimal("0.128"),     # 1 HKD ~ 0.128 USD (~7.8 HKD/USD)
    "INR": Decimal("0.012"),     # 1 INR ~ 0.012 USD (~84 INR/USD)
    "CAD": Decimal("0.73"),      # 1 CAD ~ 0.73 USD
    "AUD": Decimal("0.65"),      # 1 AUD ~ 0.65 USD
}


class CurrencyService:
    """
    Currency conversion service. Keeps prices purely native in storage and DB,
    converting only on demand for cross-market comparisons or consolidated reporting.
    """

    def __init__(self, fx_rates: Optional[Dict[str, Decimal]] = None):
        self.fx_rates_to_usd = fx_rates or DEFAULT_FX_RATES_TO_USD.copy()

    def update_rate_to_usd(self, currency: str, rate_to_usd: Decimal):
        """Updates or registers a currency exchange rate against 1 USD."""
        self.fx_rates_to_usd[currency.upper()] = rate_to_usd

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Decimal:
        """
        Converts an amount from `from_currency` to `to_currency`.
        Formula: (Amount * (from_currency -> USD)) / (to_currency -> USD)
        """
        src = from_currency.strip().upper()
        dst = to_currency.strip().upper()

        if src == dst:
            return amount

        if src not in self.fx_rates_to_usd:
            raise ValueError(f"Unsupported source currency for conversion: {src}")
        if dst not in self.fx_rates_to_usd:
            raise ValueError(f"Unsupported destination currency for conversion: {dst}")

        rate_src_to_usd = self.fx_rates_to_usd[src]
        rate_dst_to_usd = self.fx_rates_to_usd[dst]

        # Convert to USD first, then to target currency
        amount_usd = amount * rate_src_to_usd
        converted = amount_usd / rate_dst_to_usd
        return converted

    def get_fx_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Returns direct exchange rate factor (1 unit of from_currency in to_currency)."""
        return self.convert(Decimal("1.0"), from_currency, to_currency)
