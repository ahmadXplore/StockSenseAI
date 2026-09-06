"""
StockSense AI — Unified Corporate Action Adjustments Manager
Orchestrates splits, dividends, rights issues, and mergers across active portfolio positions.
"""

from typing import Dict, Any, List, Tuple
from app.backtesting.corporate_actions.splits import apply_stock_split
from app.backtesting.corporate_actions.dividends import apply_cash_dividend
from app.backtesting.corporate_actions.mergers import apply_merger_acquisition


class CorporateActionAdjustmentResult:
    def __init__(
        self,
        security_id: str,
        action_type: str,
        ex_date: str,
        shares_delta: float,
        cash_delta: float,
        new_average_entry_price: float,
        description: str,
    ):
        self.security_id = security_id
        self.action_type = action_type
        self.ex_date = ex_date
        self.shares_delta = shares_delta
        self.cash_delta = cash_delta
        self.new_average_entry_price = new_average_entry_price
        self.description = description


def process_corporate_action(
    action: Dict[str, Any],
    current_shares: float,
    current_avg_price: float,
    current_market_price: float,
    reinvest_dividends: bool = True,
) -> CorporateActionAdjustmentResult:
    """
    Processes a canonical corporate action record against an open portfolio position.
    """
    action_type = action.get("action_type", "").upper()
    security_id = action.get("security_id", "")
    ex_date = action.get("ex_date", "")

    if "SPLIT" in action_type:
        ratio = float(action.get("split_ratio", action.get("ratio", 1.0)))
        new_shares, new_avg_price = apply_stock_split(current_shares, current_avg_price, ratio)
        shares_delta = new_shares - current_shares
        desc = f"Stock split {ratio}:1 applied. Shares changed by {shares_delta:+.2f}."
        return CorporateActionAdjustmentResult(
            security_id=security_id,
            action_type="SPLIT",
            ex_date=ex_date,
            shares_delta=shares_delta,
            cash_delta=0.0,
            new_average_entry_price=new_avg_price,
            description=desc,
        )

    elif "DIVIDEND" in action_type:
        div_amount = float(action.get("dividend_amount", action.get("amount", 0.0)))
        tax = float(action.get("withholding_tax_pct", 0.0))
        net_div, new_shares, cash_change = apply_cash_dividend(
            shares=current_shares,
            dividend_per_share=div_amount,
            current_market_price=current_market_price,
            reinvest=reinvest_dividends,
            withholding_tax_pct=tax,
        )
        desc = f"Dividend of ${div_amount:.2f}/share processed. Net payout: ${net_div:.2f}."
        return CorporateActionAdjustmentResult(
            security_id=security_id,
            action_type="DIVIDEND",
            ex_date=ex_date,
            shares_delta=new_shares,
            cash_delta=cash_change,
            new_average_entry_price=current_avg_price,
            description=desc,
        )

    elif "MERGER" in action_type or "ACQUISITION" in action_type:
        cash_per_share = float(action.get("cash_per_share", 0.0))
        swap_ratio = float(action.get("swap_ratio", 0.0))
        cash_proceeds, new_shares = apply_merger_acquisition(
            current_shares=current_shares,
            cash_per_share=cash_per_share,
            swap_ratio=swap_ratio,
        )
        desc = f"M&A corporate action processed. Cash: ${cash_proceeds:.2f}, Swapped shares: {new_shares:.2f}."
        return CorporateActionAdjustmentResult(
            security_id=security_id,
            action_type="MERGER",
            ex_date=ex_date,
            shares_delta=new_shares - current_shares,
            cash_delta=cash_proceeds,
            new_average_entry_price=current_avg_price,
            description=desc,
        )

    return CorporateActionAdjustmentResult(
        security_id=security_id,
        action_type=action_type,
        ex_date=ex_date,
        shares_delta=0.0,
        cash_delta=0.0,
        new_average_entry_price=current_avg_price,
        description="Unrecognized or non-adjusting corporate action ignored.",
    )
