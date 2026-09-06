"""
StockSense AI — Corporate Actions Module
"""

from app.backtesting.corporate_actions.splits import apply_stock_split
from app.backtesting.corporate_actions.dividends import apply_cash_dividend
from app.backtesting.corporate_actions.mergers import apply_merger_acquisition
from app.backtesting.corporate_actions.adjustments import (
    process_corporate_action,
    CorporateActionAdjustmentResult
)

__all__ = [
    "apply_stock_split",
    "apply_cash_dividend",
    "apply_merger_acquisition",
    "process_corporate_action",
    "CorporateActionAdjustmentResult",
]
