"""
StockSense AI — Backtesting, Portfolio & Risk Management Schemas
Comprehensive Pydantic models for configuration, trade lifecycle, portfolio accounting,
performance metrics, risk analytics, stress testing, Monte Carlo, and optimization.
"""

from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    VWAP = "VWAP"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SELL_SHORT = "SELL_SHORT"
    BUY_TO_COVER = "BUY_TO_COVER"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ExecutionTiming(str, Enum):
    NEXT_OPEN = "NEXT_OPEN"
    SAME_CLOSE = "SAME_CLOSE"
    VWAP = "VWAP"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class ExitReason(str, Enum):
    STOP_LOSS = "STOP_LOSS"
    TRAILING_STOP = "TRAILING_STOP"
    TAKE_PROFIT = "TAKE_PROFIT"
    TIME_STOP = "TIME_STOP"
    VOLATILITY_STOP = "VOLATILITY_STOP"
    THESIS_EXIT = "THESIS_EXIT"
    PREDICTION_REVERSAL = "PREDICTION_REVERSAL"
    REBALANCE = "REBALANCE"
    RISK_LIMIT_BREACH = "RISK_LIMIT_BREACH"
    END_OF_BACKTEST = "END_OF_BACKTEST"


class StrategyType(str, Enum):
    AI_PREDICTION = "AI_PREDICTION"
    MOMENTUM = "MOMENTUM"
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MEAN_REVERSION = "MEAN_REVERSION"
    FUNDAMENTAL = "FUNDAMENTAL"
    VOLATILITY_BREAKOUT = "VOLATILITY_BREAKOUT"
    ENSEMBLE = "ENSEMBLE"
    CUSTOM = "CUSTOM"


class AllocationMethod(str, Enum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    MARKET_CAP_WEIGHT = "MARKET_CAP_WEIGHT"
    VOLATILITY_WEIGHT = "VOLATILITY_WEIGHT"
    INVERSE_VOLATILITY = "INVERSE_VOLATILITY"
    RISK_PARITY = "RISK_PARITY"
    MAX_SHARPE = "MAX_SHARPE"
    MIN_VARIANCE = "MIN_VARIANCE"
    AI_CONFIDENCE = "AI_CONFIDENCE"
    AI_EXPECTED_RETURN = "AI_EXPECTED_RETURN"


class PositionSizingMethod(str, Enum):
    FIXED_AMOUNT = "FIXED_AMOUNT"
    FIXED_PERCENTAGE = "FIXED_PERCENTAGE"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"
    ATR_RISK = "ATR_RISK"
    KELLY_CRITERION = "KELLY_CRITERION"
    FRACTIONAL_KELLY = "FRACTIONAL_KELLY"
    CONFIDENCE_WEIGHTED = "CONFIDENCE_WEIGHTED"
    AI_CONFIDENCE_SIZING = "AI_CONFIDENCE_SIZING"  # Alias: AI confidence-weighted with monthly volatility recalibration


class SlippageModelType(str, Enum):
    FIXED_BPS = "FIXED_BPS"
    FIXED_PCT = "FIXED_PCT"
    VOLATILITY_BASED = "VOLATILITY_BASED"
    VOLUME_BASED = "VOLUME_BASED"
    SPREAD_BASED = "SPREAD_BASED"


class RebalanceFrequency(str, Enum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    THRESHOLD_DRIFT = "THRESHOLD_DRIFT"


class UniverseType(str, Enum):
    POINT_IN_TIME = "POINT_IN_TIME"
    STATIC = "STATIC"
    SURVIVORSHIP_FREE = "SURVIVORSHIP_FREE"


# ─────────────────────────────────────────────────────────
# Configuration Schemas
# ─────────────────────────────────────────────────────────

class BacktestConfig(BaseModel):
    # Strategy & Identification
    name: str = Field("Default Strategy Backtest", description="Human-readable name")
    strategy_type: StrategyType = Field(StrategyType.AI_PREDICTION)
    strategy_params: Dict[str, Any] = Field(default_factory=dict)
    
    # Universe & Market
    market_code: str = Field("US", description="Target market (US, PK, UK, JP, HK, IN)")
    exchange_code: Optional[str] = Field("NASDAQ", description="Target exchange (e.g. PSX, NASDAQ, NYSE, LSE)")
    securities: List[str] = Field(default_factory=lambda: ["AAPL"], description="List of ticker symbols or security IDs")
    universe_type: UniverseType = Field(UniverseType.SURVIVORSHIP_FREE)
    benchmark_symbol: Optional[str] = Field("SPY", description="Market benchmark ticker (e.g. SPY, QQQ, KSE100)")
    
    # Time Horizon
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    
    # Capital & Currency
    initial_capital: float = Field(100000.0, gt=0, description="Starting cash capital")
    base_currency: str = Field("USD", description="Portfolio base currency (USD, PKR, GBP, JPY, INR)")
    cash_interest_rate_pct: float = Field(0.0, ge=0, description="Annualized cash interest rate")
    
    # Execution & Sizing
    execution_timing: ExecutionTiming = Field(ExecutionTiming.NEXT_OPEN)
    allow_fractional_shares: bool = Field(False)
    short_selling_enabled: bool = Field(False)
    leverage_limit: float = Field(1.0, ge=1.0, le=4.0)
    
    position_sizing: PositionSizingMethod = Field(PositionSizingMethod.ATR_RISK)
    risk_per_trade_pct: float = Field(0.02, ge=0.001, le=0.20, description="Max capital fraction at risk per trade")
    max_position_weight: float = Field(0.20, ge=0.01, le=1.0, description="Max portfolio weight per security")
    min_position_weight: float = Field(0.01, ge=0.0, le=0.20)
    max_positions: int = Field(10, ge=1, le=200)
    
    # Risk Management & Exits
    stop_loss_pct: Optional[float] = Field(0.10, description="Hard stop-loss percentage (0.10 = 10%). Overrides all other exits with priority.")
    stop_loss_atr_mult: Optional[float] = Field(2.0, description="ATR multiplier for dynamic stop-loss")
    take_profit_pct: Optional[float] = Field(0.30, description="Take-profit target percentage (0.30 = 30%)")
    risk_reward_ratio: Optional[float] = Field(3.0, description="Risk/Reward ratio target (e.g. 3.0 = 1:3)")
    take_profit_levels: Optional[List[float]] = Field(None, description="Multi-stage profit targets (e.g. [0.15, 0.25, 0.30])")
    trailing_stop_atr_mult: Optional[float] = Field(1.5, description="Trailing stop ATR multiplier")
    time_stop_bars: Optional[int] = Field(None, description="Max holding period in bars")
    volatility_stop_threshold: Optional[float] = Field(None, description="Max annualized volatility before exit")
    fundamental_thesis_exit: bool = Field(True, description="Exit when fundamental rating deteriorates")
    prediction_reversal_exit: bool = Field(True, description="Exit when AI probability reverses")

    # Monthly Volatility Recalibration (AI Confidence Sizing)
    monthly_volatility_recalibration: bool = Field(True, description="Re-evaluate AI Confidence Sizing monthly based on localized 30d realized volatility")
    volatility_target_pct: float = Field(0.20, description="Target annualized volatility for position scaling (0.20 = 20%)")

    # Macro Conditioning Labels
    macro_conditioning: Optional[List[str]] = Field(None, description="Macro regimes to annotate results (e.g. ['Post-Pandemic', 'Rate-Hike Cycle'])")

    # Portfolio Allocation & Rebalancing
    allocation_method: AllocationMethod = Field(AllocationMethod.EQUAL_WEIGHT)
    rebalance_frequency: RebalanceFrequency = Field(RebalanceFrequency.MONTHLY)
    rebalance_drift_threshold_pct: float = Field(0.05, description="Threshold drift triggering rebalancing")
    
    # Hard Risk Limits
    max_portfolio_risk_pct: float = Field(0.15, description="Max portfolio-wide open risk fraction")
    max_sector_weight: float = Field(0.35, description="Max exposure to a single sector")
    max_drawdown_limit_pct: float = Field(0.25, description="Max drawdown breach threshold")
    max_daily_loss_pct: float = Field(0.05, description="Max daily portfolio loss threshold")
    
    # Cost & Friction Models
    slippage_model: SlippageModelType = Field(SlippageModelType.FIXED_BPS)
    slippage_bps: float = Field(5.0, ge=0, description="Slippage in basis points (5 bps = 0.05%)")
    commission_per_share: float = Field(0.0, ge=0)
    commission_pct: float = Field(0.001, ge=0, description="Broker commission percentage (e.g. 0.1%)")
    min_commission: float = Field(1.0, ge=0)
    exchange_fee_pct: float = Field(0.0002, ge=0)
    tax_rate_pct: float = Field(0.0, ge=0, description="Transaction tax or withholding tax rate")
    enable_broker_commissions: bool = Field(True, description="Enable market-specific broker commissions")
    enable_local_taxation: bool = Field(True, description="Enable local statutory taxes (SEC fee, CVT, Stamp Duty)")

    # Corporate Actions & Adjustments
    dividend_handling: str = Field("REINVEST", description="'REINVEST' or 'CASH'")
    apply_splits: bool = Field(True)
    apply_dividends: bool = Field(True)
    
    # Reproducibility
    random_seed: int = Field(42)


# ─────────────────────────────────────────────────────────
# Trade & Execution Schemas
# ─────────────────────────────────────────────────────────

class Order(BaseModel):
    order_id: str
    security_id: str
    ticker: str
    market_code: str
    exchange_code: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    created_at: str
    status: OrderStatus = OrderStatus.PENDING
    reason: Optional[str] = None
    strategy_signal: Optional[Dict[str, Any]] = None


class Fill(BaseModel):
    fill_id: str
    order_id: str
    security_id: str
    ticker: str
    market_code: str
    side: OrderSide
    quantity: float
    fill_price: float
    reference_price: float
    slippage_cost: float
    commission: float
    exchange_fee: float
    taxes: float
    total_friction: float
    filled_at: str


class TradeRecord(BaseModel):
    trade_id: str
    security_id: str
    ticker: str
    market_code: str
    exchange_code: str
    side: PositionSide
    
    # Entry
    entry_date: str
    entry_price: float
    shares: float
    entry_cost_basis: float
    entry_friction: float
    
    # Exit
    exit_date: str
    exit_price: float
    exit_proceeds: float
    exit_friction: float
    exit_reason: ExitReason
    
    # Performance
    holding_period_days: int
    gross_pnl: float
    net_pnl: float
    return_pct: float
    
    # Strategy & Context Provenance
    signal_name: Optional[str] = None
    prediction_probability: Optional[float] = None
    expected_return: Optional[float] = None
    predicted_volatility: Optional[float] = None
    risk_score: Optional[float] = None
    market_regime: Optional[str] = None
    
    # Currency
    native_currency: str = "USD"
    base_currency: str = "USD"
    fx_rate: float = 1.0


# ─────────────────────────────────────────────────────────
# Portfolio State & Accounting Schemas
# ─────────────────────────────────────────────────────────

class PositionSnapshot(BaseModel):
    security_id: str
    ticker: str
    market_code: str
    side: PositionSide
    shares: float
    average_entry_price: float
    current_price: float
    cost_basis: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    portfolio_weight: float
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    trailing_stop_price: Optional[float] = None
    native_currency: str = "USD"
    base_currency_value: float


class EquityCurvePoint(BaseModel):
    date: str
    cash: float
    positions_value: float
    portfolio_value: float
    daily_return: float
    cumulative_return: float
    drawdown_pct: float
    benchmark_value: Optional[float] = None
    benchmark_daily_return: Optional[float] = None
    benchmark_cumulative_return: Optional[float] = None
    leverage: float = 1.0
    number_of_positions: int = 0


class PortfolioAccountingSnapshot(BaseModel):
    date: str
    base_currency: str
    total_equity: float
    cash_balance: float
    positions_market_value: float
    total_cost_basis: float
    total_unrealized_pnl: float
    total_realized_pnl: float
    total_dividends_received: float
    total_friction_paid: float
    gross_exposure: float
    net_exposure: float
    leverage: float


# ─────────────────────────────────────────────────────────
# Performance & Risk Analytics Schemas
# ─────────────────────────────────────────────────────────

class PerformanceMetrics(BaseModel):
    # Returns
    initial_capital: float
    ending_capital: float
    total_return_pct: float
    cagr_pct: float
    annualized_return_pct: float
    annualized_volatility_pct: float
    
    # Risk-Adjusted Returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    information_ratio: Optional[float] = None
    
    # Drawdown
    max_drawdown_pct: float
    max_drawdown_duration_days: int
    average_drawdown_pct: float
    current_drawdown_pct: float
    
    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    loss_rate_pct: float
    profit_factor: float
    expectancy_per_trade: float
    average_win_amount: float
    average_loss_amount: float
    win_loss_ratio: float
    largest_winning_trade: float
    largest_losing_trade: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    average_holding_period_days: float
    
    # Efficiency & Turnover
    annual_turnover_pct: float
    exposure_time_pct: float
    total_friction_cost: float


class RiskMetricsReport(BaseModel):
    portfolio_volatility: float
    downside_deviation: float
    beta_to_benchmark: Optional[float] = None
    alpha_annualized: Optional[float] = None
    correlation_to_benchmark: Optional[float] = None
    tracking_error: Optional[float] = None
    
    # Value at Risk (Historical & Parametric)
    var_95_daily: float
    var_99_daily: float
    cvar_95_daily: float
    cvar_99_daily: float
    
    var_95_annualized: float
    cvar_95_annualized: float
    
    # Tail Risk
    skewness: float
    kurtosis: float
    tail_ratio: float


class PerformanceAttribution(BaseModel):
    by_security: Dict[str, Dict[str, float]]
    by_market: Dict[str, float]
    by_sector: Dict[str, float]
    by_regime: Dict[str, Dict[str, float]]
    by_strategy: Dict[str, float]
    top_contributors: List[Dict[str, Any]]
    top_detractors: List[Dict[str, Any]]


# ─────────────────────────────────────────────────────────
# Stress Testing & Monte Carlo Schemas
# ─────────────────────────────────────────────────────────

class HistoricalStressResult(BaseModel):
    scenario_name: str
    period_start: str
    period_end: str
    scenario_description: str
    portfolio_drawdown_pct: float
    benchmark_drawdown_pct: float
    portfolio_loss_amount: float
    recovery_time_days: Optional[int] = None
    worst_day_loss_pct: float


class MonteCarloSimulationResult(BaseModel):
    iterations: int
    simulated_horizon_days: int
    confidence_level_pct: float = 95.0
    
    # Return Distribution
    mean_terminal_wealth: float
    median_terminal_wealth: float
    p5_terminal_wealth: float
    p25_terminal_wealth: float
    p75_terminal_wealth: float
    p95_terminal_wealth: float
    
    # Risk Distribution
    mean_max_drawdown_pct: float
    worst_case_max_drawdown_pct: float
    p95_max_drawdown_pct: float
    probability_of_profit_pct: float
    probability_of_loss_pct: float
    probability_of_ruin_pct: float
    
    # Sample trajectories (for plotting, e.g. 20 representative curves)
    sample_trajectories: List[List[float]] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────
# Portfolio Optimization Schemas
# ─────────────────────────────────────────────────────────

class OptimizationRequest(BaseModel):
    securities: List[str]
    method: AllocationMethod = AllocationMethod.MAX_SHARPE
    historical_start_date: Optional[str] = None
    historical_end_date: Optional[str] = None
    risk_free_rate: float = 0.045
    min_weight: float = 0.0
    max_weight: float = 0.40
    target_return: Optional[float] = None
    target_volatility: Optional[float] = None
    market_code: str = "US"


class OptimizationResponse(BaseModel):
    method: AllocationMethod
    weights: Dict[str, float]
    expected_annual_return: float
    expected_annual_volatility: float
    sharpe_ratio: float
    diversification_ratio: float
    efficient_frontier: Optional[List[Dict[str, float]]] = None


# ─────────────────────────────────────────────────────────
# Complete Backtest Result Schema (Master)
# ─────────────────────────────────────────────────────────

class BacktestResponse(BaseModel):
    run_id: str
    configuration_hash: str
    created_at: str
    status: str = "COMPLETED"
    
    # Configuration
    config: BacktestConfig
    
    # Performance & Risk Summaries
    performance: PerformanceMetrics
    risk: RiskMetricsReport
    attribution: PerformanceAttribution
    
    # Timeseries & Detailed Data
    equity_curve: List[EquityCurvePoint]
    trades: List[TradeRecord]
    monthly_returns_heatmap: Dict[str, Dict[str, float]] # e.g. {"2024": {"01": 2.5, "02": -1.2}}
    yearly_returns: Dict[str, float]
    
    # Diagnostics & Integrity
    data_quality_score: float = 100.0
    lookahead_audit_passed: bool = True
    survivorship_audit_passed: bool = True
    reproducibility_seed: int = 42
    execution_duration_seconds: float = 0.0
    warnings: List[str] = Field(default_factory=list)
