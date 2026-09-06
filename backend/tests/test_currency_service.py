"""
StockSense AI — Currency Service Tests
Verifies non-destructive currency conversion and FX rate calculations.
"""

import pytest
from decimal import Decimal
from app.data.currency.converter import CurrencyService


def test_currency_conversion():
    service = CurrencyService({
        "USD": Decimal("1.0"),
        "PKR": Decimal("0.00357"), # 1 PKR = 0.00357 USD (~280 PKR/USD)
        "GBP": Decimal("1.25"),    # 1 GBP = 1.25 USD
        "EUR": Decimal("1.10"),    # 1 EUR = 1.10 USD
    })

    # Same currency conversion (identity)
    assert service.convert(Decimal("100.0"), "USD", "USD") == Decimal("100.0")
    assert service.convert(Decimal("500.0"), "PKR", "PKR") == Decimal("500.0")

    # PKR to USD
    pkr_amount = Decimal("28000.0")
    usd_val = service.convert(pkr_amount, "PKR", "USD")
    assert round(usd_val, 2) == Decimal("99.96") # ~ 100 USD

    # GBP to USD
    gbp_amount = Decimal("100.0")
    usd_from_gbp = service.convert(gbp_amount, "GBP", "USD")
    assert usd_from_gbp == Decimal("125.0")

    # GBP to PKR
    pkr_from_gbp = service.convert(gbp_amount, "GBP", "PKR")
    assert pkr_from_gbp > Decimal("30000.0")
