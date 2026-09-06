"""
StockSense AI — Master Risk Engine
Coordinates pre-trade validation, dynamic stop evaluations, portfolio-level risk metrics, and breach handling.
"""

from typing import List, Dict, Optional, Any
from app.backtesting.schemas import BacktestConfig, OrderSide, RiskMetricsReport
from app.backtesting.portfolio.position_manager import Position
from app.backtesting.risk.position_risk import evaluate_position_exits, PositionExitSignal
from app.backtesting.risk.limits import validate_pre_trade_limits, RiskCheckResult
from app.backtesting.risk.portfolio_risk import calculate_portfolio_risk_report


class RiskEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.risk_events: List[Dict[str, Any]] = []

    def check_pre_trade(
        self,
        security_id: str,
        requested_shares: float,
        current_price: float,
        side: OrderSide,
        portfolio_equity: float,
        cash_balance: float,
        existing_shares: float = 0.0,
        current_sector: Optional[str] = None,
        sector_exposures: Optional[Dict[str, float]] = None,
        current_drawdown_pct: float = 0.0,
        daily_pnl_pct: float = 0.0,
    ) -> RiskCheckResult:
        """Evaluates pre-trade hard risk constraints."""
        res = validate_pre_trade_limits(
            security_id=security_id,
            requested_shares=requested_shares,
            current_price=current_price,
            side=side,
            current_portfolio_equity=portfolio_equity,
            current_cash=cash_balance,
            existing_position_shares=existing_shares,
            current_sector=current_sector,
            sector_exposures=sector_exposures,
            config=self.config,
            current_drawdown_pct=current_drawdown_pct,
            daily_pnl_pct=daily_pnl_pct,
        )
        if not res.is_allowed:
            self.risk_events.append({
                "type": "TRADE_BLOCKED",
                "security_id": security_id,
                "reason": res.reason,
            })
        return res

    def check_position_exits(
        self,
        position: Position,
        high: float,
        low: float,
        close: float,
        atr: Optional[float] = None,
        volatility: Optional[float] = None,
        ai_prob_up: Optional[float] = None,
        fundamental_score: Optional[float] = None,
    ) -> PositionExitSignal:
        """Evaluates all dynamic stop-loss, trailing stops, and exit rules for an open position."""
        return evaluate_position_exits(
            position=position,
            current_high=high,
            current_low=low,
            current_close=close,
            current_atr=atr,
            current_volatility=volatility,
            current_ai_probability_up=ai_prob_up,
            fundamental_health_score=fundamental_score,
            trailing_stop_atr_mult=self.config.trailing_stop_atr_mult,
            volatility_stop_threshold=self.config.volatility_stop_threshold,
            time_stop_bars=self.config.time_stop_bars,
            check_thesis=self.config.fundamental_thesis_exit,
            check_prediction_reversal=self.config.prediction_reversal_exit,
        )

    def generate_risk_report(
        self,
        daily_returns: List[float],
        benchmark_returns: Optional[List[float]] = None,
        portfolio_value: float = 100000.0,
    ) -> RiskMetricsReport:
        """Generates comprehensive risk report."""
        return calculate_portfolio_risk_report(
            daily_returns=daily_returns,
            benchmark_returns=benchmark_returns,
            risk_free_rate=self.config.cash_interest_rate_pct / 100.0 if self.config.cash_interest_rate_pct > 0 else 0.045,
            portfolio_value=portfolio_value,
        )
