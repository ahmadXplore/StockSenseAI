"""
StockSense AI — Centralized Transaction Costs & Friction Engine
Aggregates slippage, commissions, exchange fees, and statutory taxes into a complete friction summary.
"""

from typing import Dict, Any, Optional
from app.backtesting.schemas import BacktestConfig, OrderSide, SlippageModelType
from app.backtesting.costs.slippage import calculate_slippage
from app.backtesting.costs.commissions import calculate_commission
from app.backtesting.costs.taxes import calculate_taxes_and_statutory_fees
from app.backtesting.costs.spread import estimate_bid_ask_spread


class FrictionBreakdown:
    def __init__(
        self,
        executed_price: float,
        reference_price: float,
        shares: float,
        slippage_cost: float,
        commission: float,
        exchange_fee: float,
        taxes: float,
        total_friction: float,
    ):
        self.executed_price = executed_price
        self.reference_price = reference_price
        self.shares = shares
        self.slippage_cost = slippage_cost
        self.commission = commission
        self.exchange_fee = exchange_fee
        self.taxes = taxes
        self.total_friction = total_friction

    def to_dict(self) -> Dict[str, float]:
        return {
            "executed_price": self.executed_price,
            "reference_price": self.reference_price,
            "shares": self.shares,
            "slippage_cost": self.slippage_cost,
            "commission": self.commission,
            "exchange_fee": self.exchange_fee,
            "taxes": self.taxes,
            "total_friction": self.total_friction,
        }


def compute_transaction_friction(
    reference_price: float,
    shares: float,
    side: OrderSide,
    market_code: str,
    exchange_code: str = "US",
    config: Optional[BacktestConfig] = None,
    daily_volume: Optional[float] = None,
    atr_volatility: Optional[float] = None,
) -> FrictionBreakdown:
    """
    Computes all frictional costs for an order:
    1. Slippage on price execution
    2. Brokerage commissions
    3. Exchange fees
    4. Statutory taxes / levies
    """
    if reference_price <= 0 or shares <= 0:
        return FrictionBreakdown(reference_price, reference_price, shares, 0, 0, 0, 0, 0)

    # 1. Slippage
    slippage_model = config.slippage_model if config else SlippageModelType.FIXED_BPS
    slippage_bps = config.slippage_bps if config else 5.0
    spread = estimate_bid_ask_spread(reference_price, market_code, exchange_code, daily_volume)

    executed_price = calculate_slippage(
        reference_price=reference_price,
        shares=shares,
        side=side,
        model_type=slippage_model,
        slippage_bps=slippage_bps,
        daily_volume=daily_volume,
        atr_volatility=atr_volatility,
        bid_ask_spread=spread,
    )

    trade_value = executed_price * shares
    slippage_cost = abs(executed_price - reference_price) * shares

    # 2. Commission
    comm_pct = config.commission_pct if config else 0.001
    comm_per_share = config.commission_per_share if config else 0.0
    min_comm = config.min_commission if config else 0.0

    commission = calculate_commission(
        trade_value=trade_value,
        shares=shares,
        market_code=market_code,
        commission_pct=comm_pct,
        commission_per_share=comm_per_share,
        min_commission=min_comm,
    )

    # 3. Exchange Fee
    exchange_fee_pct = config.exchange_fee_pct if config else 0.0002
    exchange_fee = round(trade_value * exchange_fee_pct, 4)

    # 4. Taxes & Levies
    tax_rate = config.tax_rate_pct if config else 0.0
    taxes = calculate_taxes_and_statutory_fees(
        trade_value=trade_value,
        market_code=market_code,
        side=side,
        custom_tax_rate=tax_rate,
    )

    total_friction = round(slippage_cost + commission + exchange_fee + taxes, 4)

    return FrictionBreakdown(
        executed_price=executed_price,
        reference_price=reference_price,
        shares=shares,
        slippage_cost=round(slippage_cost, 4),
        commission=round(commission, 4),
        exchange_fee=round(exchange_fee, 4),
        taxes=round(taxes, 4),
        total_friction=total_friction,
    )
