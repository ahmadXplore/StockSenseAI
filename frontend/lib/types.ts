/**
 * StockSense AI — Universal TypeScript Type Definitions
 * Strictly aligned 1:1 with backend schemas from Prompts 3, 4, and 5.
 */

export type MarketCode = "PK" | "US" | "UK" | string;
export type ExchangeCode = "PSX" | "NASDAQ" | "NYSE" | "LSE" | string;

export type DataFreshnessStatus = "LIVE" | "DELAYED" | "LATEST_AVAILABLE_EOD";

export interface DataFreshnessInfo {
  status: DataFreshnessStatus;
  asOfDate?: string;
  timestamp?: string;
  source: string;
  delayMinutes?: number;
}

// ─────────────────────────────────────────────────────────
// Market & Security Master
// ─────────────────────────────────────────────────────────

export interface SupportedMarket {
  id: string;
  code: MarketCode;
  name: string;
  country: string;
  default_currency: string;
  timezone: string;
  status: "ACTIVE" | "MAINTENANCE" | "CLOSED";
  metadata?: Record<string, unknown>;
}

export interface SupportedExchange {
  id: string;
  market_id: string;
  code: ExchangeCode;
  name: string;
  country: string;
  currency: string;
  timezone: string;
  mic_code?: string;
  website?: string;
  status: string;
  trading_calendar_id?: string;
}

export interface SecurityDTO {
  security_id: string; // e.g. "PK.PSX.ENGRO", "US.NASDAQ.AAPL"
  ticker: string;
  name: string;
  market_code: MarketCode;
  exchange_code: ExchangeCode;
  currency: string;
  sector?: string;
  industry?: string;
  is_active: boolean;
  listing_date?: string;
  delisting_date?: string;
}

export interface SecuritySearchResult {
  security_id: string;
  ticker: string;
  name: string;
  market_code: MarketCode;
  exchange_code: ExchangeCode;
  currency: string;
  sector?: string;
  is_active: boolean;
}

// ─────────────────────────────────────────────────────────
// Market Quotes & Context
// ─────────────────────────────────────────────────────────

export interface LiveQuote {
  ticker: string;
  security_id?: string;
  price?: number;
  open?: number;
  high?: number;
  low?: number;
  previous_close?: number;
  change?: number;
  change_pct?: number;
  volume?: number;
  market_cap?: number;
  pe_ratio?: number;
  eps?: number;
  dividend_yield?: number;
  week_52_high?: number;
  week_52_low?: number;
  beta?: number;
  company_name?: string;
  sector?: string;
  industry?: string;
  description?: string;
  currency?: string;
  exchange?: string;
  market_code?: string;
  source?: string;
  as_of_date?: string;
  is_delayed?: boolean;
}

export interface MarketRegime {
  regime_date: string;
  regime: "bull" | "bear" | "high_volatility" | "mixed" | string;
  confidence: number;
  vix_level: number;
  yield_curve_inverted: boolean;
  spy_above_200sma: boolean;
  description: string;
  confidence_modifier: number;
  interval_width_modifier: number;
}

export interface MarketOverview {
  timestamp: string;
  spy_price: number;
  spy_change_pct: number;
  qqq_price: number;
  qqq_change_pct: number;
  vix_value: number;
  vix_change: number;
  macro_score: number;
  regime: MarketRegime;
}

export interface MacroData {
  fed_funds_rate?: number;
  yield_curve_10y2y?: number;
  cpi_yoy?: number;
  unemployment_rate?: number;
  vix?: number;
  gdp_growth?: number;
  [key: string]: number | undefined;
}

export interface OHLCVPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close?: number;
  volume: number;
  atr?: number;
}

export interface PriceHistoryResponse {
  ticker?: string;
  security_id?: string;
  output_size?: string;
  data_points: number;
  history: OHLCVPoint[];
  source: string;
}

// ─────────────────────────────────────────────────────────
// ML & Predictions
// ─────────────────────────────────────────────────────────

export interface MLPrediction {
  security_id: string;
  horizon: string;
  direction: "UP" | "DOWN" | "NEUTRAL" | string;
  probability_up: number;
  probability_down: number;
  expected_return_pct: number;
  lower_bound_pct: number;
  upper_bound_pct: number;
  predicted_volatility: number;
  confidence_score: number;
  model_version: string;
  feature_version: string;
  prediction_timestamp: string;
  top_positive_features?: string[] | { feature: string; impact: number; description?: string }[];
  top_negative_features?: string[] | { feature: string; impact: number; description?: string }[];
  diagnostics?: Record<string, unknown>;
}

export interface ModelMetadata {
  model_id: string;
  model_type: string;
  model_name: string;
  market_code: string;
  exchange_code: string;
  horizon: string;
  status: "DEPLOYED" | "STAGED" | "TRAINING" | "RETIRED" | string;
  is_deployed: boolean;
  feature_version: string;
  metrics: {
    accuracy?: number;
    f1_score?: number;
    pr_auc?: number;
    roc_auc?: number;
    brier_score?: number;
    sharpe?: number;
    information_coefficient?: number;
    [key: string]: number | undefined;
  };
  artifact_hash?: string;
  created_at: string;
}

export interface DriftCheckResponse {
  model_id: string;
  drift_detected: boolean;
  drift_score: number;
  method: string;
  p_value?: number;
  feature_drifts?: Record<string, { ks_stat: number; p_value: number; is_drifted: boolean }>;
  checked_at: string;
}

// ─────────────────────────────────────────────────────────
// Fundamentals
// ─────────────────────────────────────────────────────────

export interface FundamentalsData {
  ticker: string;
  security_id?: string;
  ratios_ttm?: {
    peRatioTTM?: number;
    pbRatioTTM?: number;
    evToEbitdaTTM?: number;
    returnOnEquityTTM?: number;
    returnOnAssetsTTM?: number;
    debtToEquityTTM?: number;
    currentRatioTTM?: number;
    quickRatioTTM?: number;
    grossProfitMarginTTM?: number;
    netProfitMarginTTM?: number;
    operatingMarginTTM?: number;
    dividendYielTTM?: number;
    freeCashFlowYieldTTM?: number;
    interestCoverageTTM?: number;
    [key: string]: number | undefined;
  };
  income_statements?: Array<{
    date?: string;
    revenue?: number;
    grossProfit?: number;
    operatingIncome?: number;
    netIncome?: number;
    eps?: number;
    ebitda?: number;
  }>;
  balance_sheets?: Array<{
    date?: string;
    totalAssets?: number;
    totalLiabilities?: number;
    totalEquity?: number;
    cashAndCashEquivalents?: number;
    totalDebt?: number;
  }>;
  cash_flows?: Array<{
    date?: string;
    operatingCashFlow?: number;
    capitalExpenditure?: number;
    freeCashFlow?: number;
  }>;
  source?: string;
}

export interface NewsItem {
  headline?: string;
  summary?: string;
  url?: string;
  source?: string;
  datetime?: number;
  sentiment?: string;
}

// ─────────────────────────────────────────────────────────
// Backtesting & Risk Management (Prompt 5)
// ─────────────────────────────────────────────────────────

export type StrategyType =
  | "AI_PREDICTION"
  | "MOMENTUM"
  | "TREND_FOLLOWING"
  | "MEAN_REVERSION"
  | "FUNDAMENTAL"
  | "VOLATILITY_BREAKOUT"
  | "ENSEMBLE"
  | "CUSTOM";

export type PositionSizingMethod =
  | "FIXED_AMOUNT"
  | "FIXED_PERCENTAGE"
  | "VOLATILITY_ADJUSTED"
  | "ATR_RISK"
  | "CONFIDENCE_WEIGHTED";

export type SlippageModelType =
  | "FIXED_BPS"
  | "FIXED_PCT"
  | "VOLATILITY_BASED"
  | "VOLUME_BASED"
  | "SPREAD_BASED";

export type AllocationMethod =
  | "EQUAL_WEIGHT"
  | "MARKET_CAP_WEIGHT"
  | "VOLATILITY_WEIGHT"
  | "INVERSE_VOLATILITY"
  | "RISK_PARITY"
  | "MAX_SHARPE"
  | "MIN_VARIANCE"
  | "AI_CONFIDENCE"
  | "AI_EXPECTED_RETURN";

export interface BacktestConfig {
  name: string;
  strategy_type: StrategyType;
  strategy_params?: Record<string, unknown>;
  market_code: string;
  exchange_code?: string;
  securities: string[];
  universe_type?: "SURVIVORSHIP_FREE" | "POINT_IN_TIME" | "STATIC";
  benchmark_symbol?: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  base_currency: string;
  cash_interest_rate_pct?: number;
  execution_timing?: "NEXT_OPEN" | "SAME_CLOSE" | "VWAP";
  allow_fractional_shares?: boolean;
  short_selling_enabled?: boolean;
  position_sizing?: PositionSizingMethod;
  risk_per_trade_pct?: number;
  max_position_weight?: number;
  max_positions?: number;
  stop_loss_pct?: number;
  stop_loss_atr_mult?: number;
  take_profit_pct?: number;
  trailing_stop_atr_mult?: number;
  allocation_method?: AllocationMethod;
  rebalance_frequency?: "NONE" | "DAILY" | "WEEKLY" | "MONTHLY" | "QUARTERLY";
  max_drawdown_limit_pct?: number;
  max_daily_loss_pct?: number;
  slippage_model?: "FIXED_BPS" | "FIXED_PCT" | "VOLATILITY_BASED" | "VOLUME_BASED";
  slippage_bps?: number;
  commission_pct?: number;
  min_commission?: number;
  dividend_handling?: "REINVEST" | "CASH";
  apply_splits?: boolean;
  random_seed?: number;
}

export interface TradeRecord {
  trade_id: string;
  security_id: string;
  ticker: string;
  market_code: string;
  exchange_code: string;
  side: "BUY" | "SELL" | "SELL_SHORT" | "BUY_TO_COVER";
  entry_date: string;
  entry_price: number;
  shares: number;
  entry_cost_basis: number;
  entry_friction: number;
  exit_date: string;
  exit_price: number;
  exit_proceeds: number;
  exit_friction: number;
  exit_reason: string;
  holding_period_days: number;
  gross_pnl: number;
  net_pnl: number;
  return_pct: number;
  signal_name?: string;
  prediction_probability?: number;
  expected_return?: number;
  predicted_volatility?: number;
  risk_score?: number;
  market_regime?: string;
  native_currency: string;
  base_currency: string;
  fx_rate?: number;
}

export interface EquityCurvePoint {
  date: string;
  portfolio_value: number;
  cash_balance: number;
  positions_value: number;
  daily_return: number;
  cumulative_return_pct: number;
  drawdown_pct: number;
  peak_portfolio_value: number;
  number_of_positions: number;
  gross_exposure_pct: number;
  net_exposure_pct: number;
  benchmark_value?: number;
  benchmark_cumulative_return?: number;
}

export interface PerformanceMetrics {
  initial_capital: number;
  ending_capital: number;
  total_return_pct: number;
  cagr_pct: number;
  annualized_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  omega_ratio: number;
  max_drawdown_pct: number;
  max_drawdown_duration_days: number;
  average_drawdown_pct: number;
  current_drawdown_pct: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  loss_rate_pct: number;
  profit_factor: number;
  expectancy_per_trade: number;
  average_win_amount: number;
  average_loss_amount: number;
  win_loss_ratio: number;
  largest_winning_trade: number;
  largest_losing_trade: number;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  average_holding_period_days: number;
  annual_turnover_pct: number;
  exposure_time_pct: number;
  total_friction_cost: number;
}

export interface RiskMetricsReport {
  portfolio_volatility_pct: number;
  downside_deviation_pct: number;
  var_95_pct: number;
  var_99_pct: number;
  cvar_95_pct: number;
  cvar_99_pct: number;
  beta_to_benchmark: number;
  alpha_annualized: number;
  correlation_to_benchmark: number;
  tracking_error_pct: number;
  information_ratio: number;
  tail_ratio: number;
  skewness: number;
  kurtosis: number;
  worst_day_pct: number;
  best_day_pct: number;
  positive_days_pct: number;
}

export interface PerformanceAttribution {
  by_security: Record<string, { total_pnl: number; trades_count: number; win_rate_pct: number }>;
  by_market: Record<string, number>;
  by_sector: Record<string, number>;
  by_regime: Record<string, { total_pnl: number; trades: number }>;
  by_strategy: Record<string, number>;
  top_contributors: Array<{ security: string; net_pnl: number; trades: number }>;
  top_detractors: Array<{ security: string; net_pnl: number; trades: number }>;
}

export interface BacktestResponse {
  run_id: string;
  configuration_hash: string;
  created_at: string;
  status: "COMPLETED" | "RUNNING" | "FAILED";
  config: BacktestConfig;
  performance: PerformanceMetrics;
  risk: RiskMetricsReport;
  attribution?: PerformanceAttribution;
  equity_curve: EquityCurvePoint[];
  trades: TradeRecord[];
  monthly_returns_heatmap: Record<string, Record<string, number>>;
  yearly_returns: Record<string, number>;
  data_quality_score: number;
  lookahead_audit_passed: boolean;
  survivorship_audit_passed: boolean;
  reproducibility_seed: number;
  execution_duration_seconds: number;
  warnings: string[];
}

export interface BacktestRunSummary {
  run_id: string;
  name: string;
  market_code: string;
  strategy_type: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  ending_capital: number;
  total_return_pct: number;
  cagr_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  total_trades: number;
  created_at: string;
}

export interface OptimizationRequest {
  securities: string[];
  method: AllocationMethod;
  historical_start_date?: string;
  historical_end_date?: string;
  market_code?: string;
  risk_free_rate?: number;
  min_weight?: number;
  max_weight?: number;
}

export interface OptimizationResponse {
  method: AllocationMethod;
  weights: Record<string, number>;
  expected_annual_return: number;
  expected_annual_volatility: number;
  sharpe_ratio: number;
  diversification_ratio: number;
}

export interface HistoricalStressResult {
  scenario_name: string;
  period_start: string;
  period_end: string;
  scenario_description: string;
  portfolio_drawdown_pct: number;
  benchmark_drawdown_pct: number;
  portfolio_loss_amount: number;
  recovery_time_days: number;
  worst_day_loss_pct: number;
}

export interface MonteCarloSimulationResult {
  iterations: number;
  simulated_horizon_days: number;
  confidence_level_pct: number;
  mean_terminal_wealth: number;
  median_terminal_wealth: number;
  p5_terminal_wealth: number;
  p25_terminal_wealth: number;
  p75_terminal_wealth: number;
  p95_terminal_wealth: number;
  mean_max_drawdown_pct: number;
  worst_case_max_drawdown_pct: number;
  p95_max_drawdown_pct: number;
  probability_of_profit_pct: number;
  probability_of_loss_pct: number;
  probability_of_ruin_pct: number;
  sample_trajectories: number[][];
}

// ─────────────────────────────────────────────────────────
// Portfolio & Risk Limits
// ─────────────────────────────────────────────────────────

export interface PortfolioPosition {
  id?: string;
  security_id?: string;
  ticker: string;
  company_name?: string;
  market_code: string;
  exchange_code?: string;
  currency: string;
  shares: number;
  entry_price: number;
  current_price: number;
  investment_amount?: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_return_pct: number;
  entry_date?: string;
  entry_thesis?: string;
  thesis_valid?: boolean;
  thesis_status?: string;
  stop_loss_price?: number;
  status?: string;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost_basis: number;
  total_pnl: number;
  total_return_pct: number;
  base_currency: string;
  positions: PortfolioPosition[];
  cash_balances?: Record<string, number>;
  warning_positions?: Array<{ ticker: string; message: string; reason: string }>;
}

export interface RiskLimit {
  id?: string;
  user_id?: string;
  market_code: string;
  max_position_weight: number;
  max_sector_weight: number;
  max_portfolio_risk: number;
  max_drawdown_limit: number;
  max_daily_loss: number;
  is_active: boolean;
}

export interface RiskEvent {
  id: string;
  event_type: string;
  security_id?: string;
  message: string;
  context_json?: Record<string, unknown>;
  occurred_at: string;
}

// ─────────────────────────────────────────────────────────
// System & Data Health
// ─────────────────────────────────────────────────────────

export interface ProviderHealth {
  provider_name: string;
  status: "healthy" | "ok" | "degraded" | "down" | string;
  latency_ms?: number;
  last_checked?: string;
  error_count?: number;
  rate_limit_remaining?: number;
  message?: string;
}

// ─────────────────────────────────────────────────────────
// Biometric Authentication
// ─────────────────────────────────────────────────────────

export interface FaceUser {
  id: string;
  name: string;
  email: string;
  username?: string;
  role?: string;
  is_active?: boolean;
  is_admin?: boolean;
  face_enrolled_at?: string;
  last_login_at?: string;
  created_at: string;
}

export interface FaceAuthResponse {
  success: boolean;
  message: string;
  token?: string;
  distance?: number;
  confidence_pct?: number;
  user?: FaceUser;
}

// ─────────────────────────────────────────────────────────
// Admin Panel Management Types
// ─────────────────────────────────────────────────────────

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  username?: string;
  role: "admin" | "analyst" | "user" | string;
  is_active: boolean;
  is_admin: boolean;
  face_enrolled: boolean;
  face_enrolled_at?: string;
  last_login_at?: string;
  created_at: string;
  positions_count: number;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  blocked_users: number;
  admin_users: number;
  total_positions: number;
  total_watchlist_items: number;
  total_securities: number;
  total_price_records: number;
  database_status: string;
  environment: string;
}

export interface AdminAuditLog {
  id: string;
  action: string;
  target_type: string;
  target_id?: string;
  actor_email?: string;
  status: string;
  details?: string;
  timestamp: string;
}
