"""
StockSense AI — Transaction Costs & Friction Module
"""

from app.backtesting.costs.slippage import calculate_slippage
from app.backtesting.costs.spread import estimate_bid_ask_spread
from app.backtesting.costs.taxes import calculate_taxes_and_statutory_fees
from app.backtesting.costs.commissions import calculate_commission
from app.backtesting.costs.transaction_costs import compute_transaction_friction, FrictionBreakdown

__all__ = [
    "calculate_slippage",
    "estimate_bid_ask_spread",
    "calculate_taxes_and_statutory_fees",
    "calculate_commission",
    "compute_transaction_friction",
    "FrictionBreakdown",
]
