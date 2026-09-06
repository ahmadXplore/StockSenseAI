"""
StockSense AI — Analysis & Report ORM Models (Schema: analysis)
Normalized support for all 14 report sections defined in APP_FLOW.md.
"""

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, Date, DateTime, Text, ForeignKey, Index, ARRAY, CheckConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.models.enums import AnalysisJobStatus, RecommendationSignal, AnomalyType, UniverseType


class AnalysisJob(Base):
    """
    Tracks asynchronous execution of multi-step analysis jobs.
    """
    __tablename__ = "analysis_jobs"
    __table_args__ = (
        Index("idx_jobs_ticker_status", "ticker", "status"),
        Index("idx_jobs_requested_at", "requested_at"),
        {"schema": "analysis"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(30), default=AnalysisJobStatus.PENDING.value, nullable=False)
    current_step = Column(Integer, default=1, nullable=False)
    total_steps = Column(Integer, default=14, nullable=False)
    current_step_name = Column(String(100), default="Initializing job")
    progress_pct = Column(Integer, default=0, nullable=False)
    
    # Execution timing
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Errors & Cancellation
    error_code = Column(String(50), nullable=True)
    safe_error_message = Column(Text, nullable=True)
    is_cancelled = Column(Boolean, default=False, nullable=False)
    
    # Task metadata
    celery_task_id = Column(String(100), nullable=True)
    report_id = Column(UUID(as_uuid=True), nullable=True)
    configuration_json = Column(JSONB, nullable=True)


class AnalysisReport(Base):
    """
    Master report entity referencing normalized component tables for all 14 report sections.
    """
    __tablename__ = "analysis_reports"
    __table_args__ = (
        Index("idx_reports_ticker_date", "ticker", "generated_at"),
        Index("idx_reports_user_date", "user_id", "generated_at"),
        {"schema": "analysis"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    analysis_job_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_jobs.id"), nullable=True)
    
    # Report Versioning & Provenance
    report_version = Column(String(20), default="1.0.0", nullable=False)
    schema_version = Column(String(20), default="1.0.0", nullable=False)
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    generation_duration_ms = Column(Integer)
    
    # Input parameters
    investment_amount = Column(Numeric(15, 2), default=10000.0)
    horizon = Column(String(20), default="all")
    risk_tolerance = Column(String(20), default="moderate")
    currency = Column(String(10), default="USD", nullable=False)
    current_price = Column(Numeric(12, 4), nullable=False)
    
    # Data freshness timestamps
    price_data_as_of = Column(DateTime(timezone=True))
    fundamentals_as_of = Column(Date)
    news_as_of = Column(DateTime(timezone=True))
    macro_as_of = Column(Date)
    stale_data_warning = Column(Boolean, default=False)
    model_available = Column(Boolean, default=True)
    
    # Veto status (Deterministic safety gate)
    veto_triggered = Column(Boolean, default=False, nullable=False)
    veto_reasons = Column(ARRAY(Text).with_variant(JSON, "sqlite"), nullable=True)
    
    # Macro / Regime
    market_regime = Column(String(50))
    regime_warning = Column(Boolean, default=False)
    
    # Score Summary
    overall_score = Column(Numeric(5, 2), nullable=False)
    
    # Horizon Recommendations
    short_term_rec = Column(String(20))
    short_term_confidence = Column(Numeric(5, 2))
    medium_term_rec = Column(String(20))
    medium_term_confidence = Column(Numeric(5, 2))
    long_term_rec = Column(String(20))
    long_term_confidence = Column(Numeric(5, 2))
    
    # Complete fast-render JSONB snapshot
    report_snapshot_jsonb = Column(JSONB, nullable=False)
    disclaimer_version = Column(String(20), default="v1.0", nullable=False)

    # Relationships to normalized section tables
    company = relationship("Company", back_populates="reports")
    predictions = relationship("Prediction", back_populates="report", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="report", cascade="all, delete-orphan")
    score_components = relationship("ScoreComponent", back_populates="report", cascade="all, delete-orphan")
    calculator_run = relationship("InvestmentCalculatorRun", back_populates="report", uselist=False, cascade="all, delete-orphan")
    fundamental_health = relationship("FundamentalHealthScore", back_populates="report", uselist=False, cascade="all, delete-orphan")
    valuation = relationship("ValuationAnalysis", back_populates="report", uselist=False, cascade="all, delete-orphan")
    risk_metrics = relationship("RiskMetrics", back_populates="report", uselist=False, cascade="all, delete-orphan")
    exit_strategy = relationship("ExitStrategy", back_populates="report", uselist=False, cascade="all, delete-orphan")
    anomaly_detection = relationship("AnomalyDetection", back_populates="report", uselist=False, cascade="all, delete-orphan")


class ScoreComponent(Base):
    """
    Normalized storage for all 8 score modules: Fundamental Health, Technical Health,
    Valuation, Risk, Opportunity, Macro, Sentiment, Overall.
    """
    __tablename__ = "score_components"
    __table_args__ = (
        Index("idx_score_comp_report", "report_id"),
        CheckConstraint("score >= 0 AND score <= 100", name="chk_score_range"),
        {"schema": "analysis"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    module_name = Column(String(50), nullable=False) # 'fundamental', 'technical', 'valuation', 'risk', 'opportunity', 'macro', 'sentiment', 'overall'
    score = Column(Numeric(5, 2), nullable=False)
    status = Column(String(50), nullable=False)      # e.g. 'STRONG', 'MODERATE', 'CONCERNING'
    explanation = Column(Text, nullable=True)
    subcomponents_json = Column(JSONB, nullable=True)

    report = relationship("AnalysisReport", back_populates="score_components")


class ScoreHistory(Base):
    """
    Daily score history for tracking trends over time.
    """
    __tablename__ = "score_history"
    __table_args__ = (
        Index("idx_score_hist_ticker_date", "ticker", "score_date"),
        {"schema": "analysis"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    score_date = Column(Date, nullable=False)
    overall_score = Column(Numeric(5, 2), nullable=False)
    fundamental_score = Column(Numeric(5, 2))
    technical_score = Column(Numeric(5, 2))
    valuation_score = Column(Numeric(5, 2))
    risk_score = Column(Numeric(5, 2))
    opportunity_score = Column(Numeric(5, 2))
    macro_score = Column(Numeric(5, 2))
    sentiment_score = Column(Numeric(5, 2))
    short_term_rec = Column(String(20))
    medium_term_rec = Column(String(20))
    long_term_rec = Column(String(20))
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=True)


class Prediction(Base):
    """
    Multi-horizon ML predictions with calibrated probability and interval bounds.
    """
    __tablename__ = "predictions"
    __table_args__ = (
        Index("idx_predictions_ticker_target", "ticker", "target_date"),
        CheckConstraint("prob_positive_return >= 0 AND prob_positive_return <= 1", name="chk_prob_positive_range"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 100", name="chk_pred_confidence_range"),
        {"schema": "analysis"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    prediction_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    horizon = Column(String(20), nullable=False)  # '7d', '30d', '3m', '6m', '1y', '3y'
    horizon_days = Column(Integer, nullable=False)
    
    current_price = Column(Numeric(12, 4), nullable=False)
    predicted_price = Column(Numeric(12, 4), nullable=False)
    lower_bound_10th = Column(Numeric(12, 4), nullable=False)
    upper_bound_90th = Column(Numeric(12, 4), nullable=False)
    expected_return_pct = Column(Numeric(8, 4), nullable=False)
    
    # Calibrated probability
    prob_positive_return = Column(Numeric(5, 4), nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    signal = Column(String(20), nullable=False)
    
    # Model provenance
    model_version = Column(String(50), default="ensemble_v1.0")
    feature_version = Column(String(50), default="ft_v1.0")
    dataset_version = Column(String(50), default="ds_v1.0")
    
    # Outcome tracking
    actual_price = Column(Numeric(12, 4), nullable=True)
    actual_return = Column(Numeric(8, 4), nullable=True)
    direction_correct = Column(Boolean, nullable=True)

    report = relationship("AnalysisReport", back_populates="predictions")


class Scenario(Base):
    """
    Bull, Base, Bear, and Tail Risk scenario projections.
    """
    __tablename__ = "scenarios"
    __table_args__ = (
        Index("idx_scenarios_report", "report_id"),
        CheckConstraint("probability >= 0 AND probability <= 1", name="chk_scenario_prob_range"),
        {"schema": "analysis"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    scenario_type = Column(String(20), nullable=False)  # 'bull', 'base', 'bear', 'tail_risk'
    price_target = Column(Numeric(12, 4), nullable=False)
    expected_return_pct = Column(Numeric(8, 4), nullable=False)
    probability = Column(Numeric(5, 4), nullable=False)
    investment_value = Column(Numeric(15, 2), nullable=True)
    gain_loss = Column(Numeric(15, 2), nullable=True)
    assumptions_json = Column(JSONB, nullable=True)

    report = relationship("AnalysisReport", back_populates="scenarios")


class InvestmentCalculatorRun(Base):
    """
    Persisted state of investment calculator runs to reproduce calculations accurately.
    """
    __tablename__ = "investment_calculator_runs"
    __table_args__ = ({"schema": "analysis"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    investment_amount = Column(Numeric(15, 2), nullable=False)
    current_price = Column(Numeric(12, 4), nullable=False)
    shares = Column(Numeric(12, 4), nullable=False)
    fractional_shares_allowed = Column(Boolean, default=True)
    horizon = Column(String(20), default="all")
    risk_tolerance = Column(String(20), default="moderate")
    currency = Column(String(10), default="USD", nullable=False)
    
    suggested_position_size = Column(Numeric(15, 2))
    position_sizing_pct = Column(Numeric(5, 2))
    bull_projection = Column(Numeric(15, 2))
    base_projection = Column(Numeric(15, 2))
    bear_projection = Column(Numeric(15, 2))
    tail_projection = Column(Numeric(15, 2))
    annualized_return_base = Column(Numeric(8, 4))

    report = relationship("AnalysisReport", back_populates="calculator_run")


class FundamentalHealthScore(Base):
    """
    Normalized sub-scores breakdown for Fundamental Analysis.
    """
    __tablename__ = "fundamental_health_scores"
    __table_args__ = ({"schema": "analysis"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    total_score = Column(Numeric(5, 2), nullable=False)
    
    revenue_growth_score = Column(Numeric(5, 2))
    revenue_growth_metric = Column(String(50))
    earnings_growth_score = Column(Numeric(5, 2))
    earnings_growth_metric = Column(String(50))
    profitability_score = Column(Numeric(5, 2))
    profitability_metric = Column(String(50))
    free_cash_flow_score = Column(Numeric(5, 2))
    free_cash_flow_metric = Column(String(50))
    debt_health_score = Column(Numeric(5, 2))
    debt_health_metric = Column(String(50))
    roe_roic_score = Column(Numeric(5, 2))
    roe_roic_metric = Column(String(50))
    cash_position_score = Column(Numeric(5, 2))
    cash_position_metric = Column(String(50))
    margin_stability_score = Column(Numeric(5, 2))
    margin_stability_metric = Column(String(50))
    competitive_score = Column(Numeric(5, 2))
    competitive_metric = Column(String(50))
    historical_stability_score = Column(Numeric(5, 2))
    historical_stability_metric = Column(String(50))
    
    data_period = Column(String(50))
    detail_json = Column(JSONB)

    report = relationship("AnalysisReport", back_populates="fundamental_health")


class ValuationAnalysis(Base):
    """
    Normalized valuation calculations: Multiples, DCF bull/base/bear, WACC, sensitivity matrix.
    """
    __tablename__ = "valuation_analysis"
    __table_args__ = ({"schema": "analysis"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    current_price = Column(Numeric(12, 4), nullable=False)
    
    fair_value_low = Column(Numeric(12, 4))
    fair_value_mid = Column(Numeric(12, 4))
    fair_value_high = Column(Numeric(12, 4))
    valuation_status = Column(String(30)) # 'significantly_undervalued', 'moderately_undervalued', 'fairly_valued', etc.
    premium_discount_pct = Column(Numeric(8, 4))
    
    # Relative multiples
    pe_current = Column(Numeric(10, 4))
    pe_5y_average = Column(Numeric(10, 4))
    pe_sector_median = Column(Numeric(10, 4))
    forward_pe_current = Column(Numeric(10, 4))
    peg_current = Column(Numeric(10, 4))
    ev_ebitda_current = Column(Numeric(10, 4))
    fcf_yield = Column(Numeric(8, 6))
    
    # Absolute DCF
    dcf_base_value = Column(Numeric(12, 4))
    dcf_bull_value = Column(Numeric(12, 4))
    dcf_bear_value = Column(Numeric(12, 4))
    dcf_growth_rate_y1_3 = Column(Numeric(6, 4))
    dcf_terminal_growth_rate = Column(Numeric(6, 4))
    dcf_wacc_discount_rate = Column(Numeric(6, 4))
    dcf_assumptions_json = Column(JSONB)
    dcf_sensitivity_matrix_json = Column(JSONB)

    report = relationship("AnalysisReport", back_populates="valuation")


class RiskMetrics(Base):
    """
    Normalized quantitative risk parameters and position sizing recommendations.
    """
    __tablename__ = "risk_metrics"
    __table_args__ = (
        CheckConstraint("risk_score_total >= 0 AND risk_score_total <= 100", name="chk_risk_score_range"),
        {"schema": "analysis"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    
    hist_vol_20d = Column(Numeric(8, 4))
    hist_vol_252d = Column(Numeric(8, 4))
    beta_1y = Column(Numeric(8, 4))
    max_drawdown_alltime = Column(Numeric(8, 4))
    max_drawdown_3y = Column(Numeric(8, 4))
    
    var_95_1m = Column(Numeric(8, 4))
    cvar_95_1m = Column(Numeric(8, 4))
    sharpe_1y = Column(Numeric(8, 4))
    sortino_1y = Column(Numeric(8, 4))
    
    risk_score_total = Column(Numeric(5, 2), nullable=False)
    risk_reward_ratio = Column(Numeric(8, 4))
    
    # Suggested position sizes by risk profile
    conservative_pos_pct = Column(Numeric(5, 2), default=1.5)
    moderate_pos_pct = Column(Numeric(5, 2), default=2.5)
    aggressive_pos_pct = Column(Numeric(5, 2), default=4.0)

    report = relationship("AnalysisReport", back_populates="risk_metrics")


class ExitStrategy(Base):
    """
    Generated exit plan and entry hypothesis tracking.
    """
    __tablename__ = "exit_strategies"
    __table_args__ = ({"schema": "analysis"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    
    entry_reference_price = Column(Numeric(12, 4), nullable=False)
    hard_stop_price = Column(Numeric(12, 4), nullable=False)
    hard_stop_pct = Column(Numeric(8, 4), nullable=False)
    trailing_stop_activation_price = Column(Numeric(12, 4))
    trailing_stop_distance = Column(Numeric(12, 4))
    time_stop_date = Column(Date)
    volatility_stop_threshold = Column(Numeric(8, 4))
    
    profit_target_partial = Column(Numeric(12, 4))
    profit_target_full = Column(Numeric(12, 4))
    earnings_exit_recommendation = Column(Text)
    fundamental_exit_triggers = Column(ARRAY(Text).with_variant(JSON, "sqlite"))
    entry_thesis_statement = Column(Text, nullable=False)

    report = relationship("AnalysisReport", back_populates="exit_strategy")


class AnomalyDetection(Base):
    """
    Statistical drop anomaly evaluation and Type A/B/C classification.
    """
    __tablename__ = "anomaly_detection"
    __table_args__ = ({"schema": "analysis"})

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("analysis.analysis_reports.id"), nullable=False)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=False)
    
    current_decline_pct = Column(Numeric(8, 4))
    historical_avg_decline_pct = Column(Numeric(8, 4))
    historical_std_decline_pct = Column(Numeric(8, 4))
    z_score = Column(Numeric(8, 4))
    is_statistically_unusual = Column(Boolean, default=False)
    
    similar_events_count = Column(Integer)
    recovery_rate_12m_pct = Column(Numeric(8, 4))
    avg_recovery_days = Column(Integer)
    
    anomaly_type = Column(String(20), default=AnomalyType.UNCLEAR.value)
    classification_confidence = Column(Numeric(5, 2))
    opportunity_score = Column(Numeric(5, 2))
    is_recovery_opportunity = Column(Boolean, default=False)
    conditions_met_json = Column(JSONB)
    failed_conditions_json = Column(JSONB)
    summary_text = Column(Text)

    report = relationship("AnalysisReport", back_populates="anomaly_detection")


class BacktestRun(Base):
    """
    Out-of-sample backtesting validation results.
    """
    __tablename__ = "backtest_runs"
    __table_args__ = (
        Index("idx_backtest_ticker", "ticker"),
        {"schema": "analysis"}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(10), ForeignKey("market_data.companies.ticker"), nullable=True)
    model_id = Column(UUID(as_uuid=True), nullable=True)
    
    backtest_start_date = Column(Date, nullable=False)
    backtest_end_date = Column(Date, nullable=False)
    initial_capital = Column(Numeric(15, 2), default=100000.0)
    
    total_return_pct = Column(Numeric(8, 4), nullable=False)
    cagr_pct = Column(Numeric(8, 4))
    sharpe_ratio = Column(Numeric(8, 4))
    sortino_ratio = Column(Numeric(8, 4))
    max_drawdown_pct = Column(Numeric(8, 4))
    win_rate_pct = Column(Numeric(6, 4))
    total_trades = Column(Integer)
    profit_factor = Column(Numeric(8, 4))
    
    # Benchmarks
    buy_and_hold_return_pct = Column(Numeric(8, 4))
    spy_return_pct = Column(Numeric(8, 4))
    alpha_vs_buy_hold = Column(Numeric(8, 4))
    alpha_vs_spy = Column(Numeric(8, 4))
    
    # Non-negotiable survivorship bias disclosure flag
    universe_type = Column(String(50), default=UniverseType.CURRENT_UNIVERSE_APPROXIMATE.value, nullable=False)
    excluded_delisted_tickers = Column(ARRAY(Text).with_variant(JSON, "sqlite"), nullable=True)
    trade_log_json = Column(JSONB, nullable=True)
    monthly_returns_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
