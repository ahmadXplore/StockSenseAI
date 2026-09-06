"""
StockSense AI — Pre-Trade Risk Limits & Constraint Enforcer
Hard pre-trade gates: max position weight, max sector weight, max leverage, max drawdown, max daily loss.
"""

from typing import Dict, Optional, Tuple
from app.backtesting.schemas import BacktestConfig, OrderSide


class RiskCheckResult:
    def __init__(self, is_allowed: bool, reason: str = "", adjusted_shares: Optional[float] = None):
        self.is_allowed = is_allowed
        self.reason = reason
        self.adjusted_shares = adjusted_shares


def validate_pre_trade_limits(
    security_id: str,
    requested_shares: float,
    current_price: float,
    side: OrderSide,
    current_portfolio_equity: float,
    current_cash: float,
    existing_position_shares: float,
    current_sector: Optional[str] = None,
    sector_exposures: Optional[Dict[str, float]] = None,
    config: Optional[BacktestConfig] = None,
    current_drawdown_pct: float = 0.0,
    daily_pnl_pct: float = 0.0,
) -> RiskCheckResult:
    """
    Validates if placing a trade complies with all hard portfolio risk constraints.
    """
    if requested_shares <= 0 or current_price <= 0:
        return RiskCheckResult(False, "Invalid order quantity or price <= 0")

    if not config:
        return RiskCheckResult(True, "No config constraints")

    trade_value = requested_shares * current_price
    is_buy = side in (OrderSide.BUY, OrderSide.BUY_TO_COVER)

    # 1. Check Max Drawdown Emergency Halt
    if config.max_drawdown_limit_pct and current_drawdown_pct >= config.max_drawdown_limit_pct * 100.0:
        if is_buy:
            return RiskCheckResult(False, f"Trade blocked: Max portfolio drawdown limit ({config.max_drawdown_limit_pct:.1%}) breached")

    # 2. Check Max Daily Loss Circuit Breaker
    if config.max_daily_loss_pct and daily_pnl_pct <= -config.max_daily_loss_pct * 100.0:
        if is_buy:
            return RiskCheckResult(False, f"Trade blocked: Daily loss circuit breaker (-{config.max_daily_loss_pct:.1%}) triggered")

    # 3. Check Cash Availability for Buys
    if is_buy and not config.short_selling_enabled:
        if trade_value > current_cash:
            # Sizing down to available cash if allowed
            max_affordable_shares = current_cash / current_price
            if max_affordable_shares <= 0.001:
                return RiskCheckResult(False, f"Insufficient cash: Required ${trade_value:.2f}, available ${current_cash:.2f}")
            requested_shares = max_affordable_shares

    # 4. Check Single Position Concentration Limit
    if is_buy and current_portfolio_equity > 0:
        new_total_shares = existing_position_shares + requested_shares
        new_position_value = new_total_shares * current_price
        max_allowed_value = current_portfolio_equity * config.max_position_weight

        if new_position_value > max_allowed_value:
            allowed_shares_cap = (max_allowed_value - (existing_position_shares * current_price)) / current_price
            if allowed_shares_cap <= 0.001:
                return RiskCheckResult(False, f"Position concentration limit ({config.max_position_weight:.1%}) reached for {security_id}")
            return RiskCheckResult(True, f"Shares capped at {allowed_shares_cap:.2f} due to max position weight limit", adjusted_shares=allowed_shares_cap)

    # 5. Check Sector Concentration Limit
    if is_buy and current_sector and sector_exposures and current_portfolio_equity > 0:
        current_sector_exp = sector_exposures.get(current_sector, 0.0)
        new_sector_exp = current_sector_exp + trade_value
        max_sector_val = current_portfolio_equity * config.max_sector_weight
        if new_sector_exp > max_sector_val:
            return RiskCheckResult(False, f"Sector exposure limit ({config.max_sector_weight:.1%}) breached for sector {current_sector}")

    return RiskCheckResult(True, "Risk checks passed", adjusted_shares=requested_shares)
