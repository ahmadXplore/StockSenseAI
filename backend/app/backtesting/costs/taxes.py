"""
StockSense AI — Statutory Taxes & Exchange Levies
Applies market-specific statutory taxes, capital value taxes (CVT), and regulatory fees.

Market Tax Schedules:
    PK (PSX):  SECP levy (~0.002%), CDC custodial (~0.005%), NCCPL levy (~0.005%), CVT (0.02% on buys)
               Total transaction levy: approx 0.035% on buys, 0.015% on sells
    US (SEC):  SEC Section 31 fee on SALES only (~$27.80/million = 0.00278%), FINRA TAF ($0.000145/share capped $7.27)
    UK/GB (SDRT): Stamp Duty Reserve Tax 0.50% on PURCHASES only
    IN (NSE/BSE): STT 0.1% on delivery equity buy+sell, Stamp Duty 0.015% on purchases
"""

from app.backtesting.schemas import OrderSide


def calculate_taxes_and_statutory_fees(
    trade_value: float,
    market_code: str,
    side: OrderSide,
    custom_tax_rate: float = 0.0,
    shares: float = 0.0,
    enable_local_taxation: bool = True,
) -> float:
    """
    Computes statutory taxes and government duties for a transaction.
    Returns total tax amount in the market's base currency.

    Args:
        trade_value: Total executed trade value (executed_price × shares)
        market_code: Market identifier — PK, US, UK, GB, IN, JP, HK
        side: OrderSide.BUY or OrderSide.SELL
        custom_tax_rate: Override rate (0.0 = use market defaults)
        shares: Number of shares traded (needed for US FINRA TAF)
        enable_local_taxation: If False, no taxes applied
    """
    if trade_value <= 0 or not enable_local_taxation:
        return 0.0

    if custom_tax_rate > 0:
        return round(trade_value * (custom_tax_rate / 100.0), 4)

    market = market_code.upper()
    # GB and UK are synonymous — both map to LSE/GBP rules
    if market == "GB":
        market = "UK"

    is_sell = side in (OrderSide.SELL, OrderSide.SELL_SHORT)
    is_buy = side in (OrderSide.BUY, OrderSide.BUY_TO_COVER)

    # ── PSX Pakistan ──────────────────────────────────────
    # CVT (Capital Value Tax): 0.02% on PURCHASES
    # SECP turnover levy: 0.002%
    # CDC custodial: 0.005%
    # NCCPL settlement: 0.005%
    if market == "PK":
        base_levy = trade_value * 0.00012   # SECP + CDC + NCCPL ≈ 0.012%
        cvt = trade_value * 0.0002 if is_buy else 0.0   # CVT 0.02% on purchases only
        total = base_levy + cvt
        return round(total, 4)

    # ── US Markets ────────────────────────────────────────
    # SEC Section 31 fee: 0.00278% on SELL side only
    # FINRA TAF: $0.000145/share (capped at $7.27/trade) on SELL side
    elif market == "US":
        if is_sell:
            sec_fee = trade_value * 0.0000278            # SEC Section 31 (~$27.80/million)
            finra_taf = min(7.27, shares * 0.000145) if shares > 0 else 0.0
            return round(sec_fee + finra_taf, 4)
        return 0.0  # No tax on US purchases

    # ── UK / GB Markets (LSE) ─────────────────────────────
    # Stamp Duty Reserve Tax (SDRT): 0.50% on PURCHASES
    # No tax on sales for UK equities
    elif market == "UK":
        if is_buy:
            return round(trade_value * 0.005, 4)  # 0.50% SDRT
        return 0.0

    # ── India (NSE / BSE) ─────────────────────────────────
    # STT: 0.1% on delivery equity buy AND sell
    # Stamp Duty: 0.015% on purchases
    elif market == "IN":
        stt = trade_value * 0.001
        stamp = trade_value * 0.00015 if is_buy else 0.0
        return round(stt + stamp, 4)

    # ── Japan (TSE) ───────────────────────────────────────
    # No transaction tax on TSE equity trades (withholding at income level)
    elif market == "JP":
        return 0.0

    # ── Hong Kong (HKEX) ─────────────────────────────────
    # Stamp Duty: 0.13% on both buy and sell sides
    elif market == "HK":
        return round(trade_value * 0.0013, 4)

    # Unknown market — no tax
    return 0.0
