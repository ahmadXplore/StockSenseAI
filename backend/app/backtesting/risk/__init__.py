"""
StockSense AI — Risk Management Module
"""

from app.backtesting.risk.var import compute_var
from app.backtesting.risk.cvar import compute_cvar
from app.backtesting.risk.position_risk import evaluate_position_exits, PositionExitSignal
from app.backtesting.risk.limits import validate_pre_trade_limits, RiskCheckResult
from app.backtesting.risk.portfolio_risk import calculate_portfolio_risk_report
from app.backtesting.risk.risk_engine import RiskEngine

__all__ = [
    "compute_var",
    "compute_cvar",
    "evaluate_position_exits",
    "PositionExitSignal",
    "validate_pre_trade_limits",
    "RiskCheckResult",
    "calculate_portfolio_risk_report",
    "RiskEngine",
]
