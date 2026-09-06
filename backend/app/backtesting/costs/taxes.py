"""
StockSense AI — Statutory Taxes & Exchange Levies
Applies market-specific statutory taxes, capital value taxes (CVT), and regulatory fees.
"""

from app.backtesting.schemas import OrderSide


def calculate_taxes_and_statutory_fees(
    trade_value: float,
    market_code: str,
    side: OrderSide,
    custom_tax_rate: float = 0.0
) -> float:
    """
    Computes statutory taxes and government duties for a transaction.
    - PSX (Pakistan): Capital Value Tax (CVT), SECP turnover levy, CDC custodial charges
    - US: SEC transaction fee (on sales), FINRA TAF
    - UK: Stamp Duty Reserve Tax (SDRT 0.5% on purchases)
    - India: Securities Transaction Tax (STT), Stamp Duty, GST
    """
    if trade_value <= 0:
        return 0.0

    if custom_tax_rate > 0:
        return trade_value * (custom_tax_rate / 100.0)

    market = market_code.upper()
    is_sell = side in (OrderSide.SELL, OrderSide.SELL_SHORT)
    is_buy = side in (OrderSide.BUY, OrderSide.BUY_TO_COVER)

    if market == "PK":
        # PSX fees: SECP levy (~0.002%), CDC (~0.005%), NCCPL (~0.005%)
        # Total transaction levy approx 0.015%
        return trade_value * 0.00015

    elif market == "US":
        # US SEC Section 31 fee (applies only to sales, currently ~$27.80 per million)
        if is_sell:
            return trade_value * 0.0000278
        return 0.0

    elif market == "UK":
        # UK Stamp Duty: 0.5% on stock purchases
        if is_buy:
            return trade_value * 0.005
        return 0.0

    elif market == "IN":
        # Indian STT: 0.1% on delivery equity buy/sell
        return trade_value * 0.001

    return 0.0
