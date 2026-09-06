"""
StockSense AI — Complete Multi-Market Backtesting, Portfolio & Risk Management Platform
"""

from app.backtesting.schemas import (
    BacktestConfig, BacktestResponse, Order, Fill, TradeRecord,
    PositionSnapshot, EquityCurvePoint, PerformanceMetrics, RiskMetricsReport,
    PerformanceAttribution, HistoricalStressResult, MonteCarloSimulationResult,
    OptimizationRequest, OptimizationResponse, StrategyType, OrderSide, OrderType,
    OrderStatus, PositionSide, ExitReason, AllocationMethod, PositionSizingMethod,
    SlippageModelType, RebalanceFrequency, UniverseType
)
from app.backtesting.engine.backtest_engine import BacktestEngine
from app.backtesting.engine.event_loop import EventLoop, MarketTimelineBar
from app.backtesting.engine.execution_engine import ExecutionEngine
from app.backtesting.engine.order_engine import OrderEngine
from app.backtesting.engine.settlement import SettlementEngine
from app.backtesting.portfolio.portfolio_engine import PortfolioEngine
from app.backtesting.risk.risk_engine import RiskEngine
from app.backtesting.optimization import (
    optimize_mean_variance, optimize_risk_parity, optimize_minimum_variance, run_portfolio_optimization
)
from app.backtesting.stress.historical import evaluate_historical_stress_scenarios
from app.backtesting.stress.monte_carlo import run_monte_carlo_simulation

__all__ = [
    "BacktestConfig",
    "BacktestResponse",
    "BacktestEngine",
    "EventLoop",
    "MarketTimelineBar",
    "ExecutionEngine",
    "OrderEngine",
    "SettlementEngine",
    "PortfolioEngine",
    "RiskEngine",
    "optimize_mean_variance",
    "optimize_risk_parity",
    "optimize_minimum_variance",
    "run_portfolio_optimization",
    "evaluate_historical_stress_scenarios",
    "run_monte_carlo_simulation",
    "StrategyType",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "PositionSide",
    "ExitReason",
    "AllocationMethod",
    "PositionSizingMethod",
    "SlippageModelType",
    "RebalanceFrequency",
    "UniverseType",
]
