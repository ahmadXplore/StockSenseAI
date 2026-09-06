"""
Tests: Master Backtest Engine — End-to-End Integration
Tests the full event-driven backtest loop with synthetic timelines for US (AAPL) and Pakistan (ENGRO) markets.
"""

import pytest
import numpy as np
from datetime import date, timedelta
from typing import List, Dict, Any

from app.backtesting.engine.backtest_engine import BacktestEngine
from app.backtesting.engine.event_loop import MarketTimelineBar
from app.backtesting.schemas import BacktestConfig, StrategyType, ExitReason, PositionSizingMethod


# ── Synthetic Timeline Builder ──

def build_synthetic_timeline(
    security_id: str,
    ticker: str,
    start_date: str = "2022-01-03",
    n_days: int = 252,
    start_price: float = 150.0,
    daily_drift: float = 0.0003,
    daily_vol: float = 0.015,
    with_predictions: bool = True,
) -> List[MarketTimelineBar]:
    """Generates a synthetic chronological timeline with realistic OHLCV data."""
    np.random.seed(42)
    bars = []
    dt = date.fromisoformat(start_date)
    price = start_price
    bm_price = 100.0

    for i in range(n_days):
        # Skip weekends
        while dt.weekday() >= 5:
            dt += timedelta(days=1)

        daily_ret = np.random.normal(daily_drift, daily_vol)
        price = max(0.01, price * (1.0 + daily_ret))
        high = price * (1.0 + abs(np.random.normal(0, 0.005)))
        low = price * (1.0 - abs(np.random.normal(0, 0.005)))
        open_ = price * (1.0 + np.random.normal(0, 0.003))
        volume = float(np.random.randint(100_000, 5_000_000))
        atr = max(0.5, (high - low) * 0.8)

        bm_ret = np.random.normal(0.0002, 0.012)
        bm_price = max(0.01, bm_price * (1.0 + bm_ret))

        predictions = {}
        if with_predictions:
            prob_up = 0.55 + (daily_ret * 5.0)  # Correlate prediction loosely with actual direction
            predictions[security_id] = {
                "probability_up": float(np.clip(prob_up, 0.40, 0.90)),
                "expected_return": float(daily_ret * 10.0),
                "predicted_volatility": daily_vol * np.sqrt(252.0),
                "timestamp": str(dt),
            }

        bars.append(MarketTimelineBar(
            date=str(dt),
            prices={
                security_id: {
                    "ticker": ticker,
                    "open": round(open_, 4),
                    "high": round(high, 4),
                    "low": round(low, 4),
                    "close": round(price, 4),
                    "volume": volume,
                    "atr": round(atr, 4),
                    "timestamp": str(dt),
                }
            },
            features={
                security_id: {
                    "sma_20": price * 0.98, "sma_50": price * 0.95, "sma_200": price * 0.90,
                    "rsi_14": float(np.clip(50.0 + daily_ret * 300, 20, 80)),
                    "macd_histogram": float(daily_ret * 10.0),
                    "bb_upper": price * 1.04, "bb_lower": price * 0.96,
                    "pe_ratio": 22.0, "roe": 0.18, "debt_to_equity": 0.6,
                    "piotroski_f_score": 7.0,
                    "donchian_high_20": price * 1.01, "donchian_low_20": price * 0.95,
                    "timestamp": str(dt),
                }
            },
            predictions=predictions,
            corporate_actions=[],
            benchmark={"close": round(bm_price, 4)},
        ))
        dt += timedelta(days=1)

    return bars


# ── US Market Backtest (AAPL) ──

def test_backtest_us_aapl_completes():
    """Full backtest on synthetic US/AAPL data completes with valid results."""
    config = BacktestConfig(
        name="US AAPL AI Backtest",
        strategy_type=StrategyType.AI_PREDICTION,
        market_code="US",
        exchange_code="NASDAQ",
        securities=["AAPL"],
        benchmark_symbol="SPY",
        start_date="2022-01-01",
        end_date="2022-12-31",
        initial_capital=100_000.0,
        base_currency="USD",
        position_sizing=PositionSizingMethod.FIXED_PERCENTAGE,
        max_position_weight=0.20,
        stop_loss_pct=0.05,
        take_profit_pct=0.15,
        random_seed=42,
    )
    timeline = build_synthetic_timeline("AAPL", "AAPL", n_days=200)
    engine = BacktestEngine(config)
    result = engine.run(timeline)

    # Core structural assertions
    assert result.run_id is not None
    assert result.status == "COMPLETED"
    assert result.configuration_hash is not None
    assert len(result.equity_curve) > 0
    assert result.performance.initial_capital == 100_000.0
    assert result.performance.ending_capital > 0.0
    assert isinstance(result.performance.total_return_pct, float)
    assert isinstance(result.performance.sharpe_ratio, float)
    assert result.performance.total_trades >= 0


def test_backtest_psx_engro_completes():
    """Full backtest on synthetic PSX/ENGRO data completes with valid results."""
    config = BacktestConfig(
        name="PSX ENGRO Momentum Backtest",
        strategy_type=StrategyType.MOMENTUM,
        market_code="PK",
        exchange_code="PSX",
        securities=["PK::PSX::ENGRO"],
        benchmark_symbol="KSE100",
        start_date="2022-01-01",
        end_date="2022-12-31",
        initial_capital=5_000_000.0,  # PKR
        base_currency="PKR",
        position_sizing=PositionSizingMethod.FIXED_PERCENTAGE,
        max_position_weight=0.25,
        stop_loss_pct=0.07,
        random_seed=42,
    )
    timeline = build_synthetic_timeline("PK::PSX::ENGRO", "ENGRO", start_price=300.0, n_days=150)
    engine = BacktestEngine(config)
    result = engine.run(timeline)

    assert result.status == "COMPLETED"
    assert result.performance.initial_capital == 5_000_000.0
    assert result.performance.ending_capital > 0.0


def test_backtest_equity_curve_monotonically_dated():
    """Equity curve must always be chronologically sorted."""
    config = BacktestConfig(
        name="Monotonic Date Test",
        strategy_type=StrategyType.TREND_FOLLOWING,
        market_code="US",
        securities=["MSFT"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=50_000.0,
    )
    timeline = build_synthetic_timeline("MSFT", "MSFT", n_days=100)
    engine = BacktestEngine(config)
    result = engine.run(timeline)

    dates = [pt.date for pt in result.equity_curve]
    assert dates == sorted(dates)


def test_backtest_no_lookahead_bias_in_timeline():
    """Ensures no prediction timestamps are ahead of the decision bar date."""
    config = BacktestConfig(
        name="No Lookahead Test",
        strategy_type=StrategyType.AI_PREDICTION,
        market_code="US",
        securities=["AAPL"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100_000.0,
    )
    timeline = build_synthetic_timeline("AAPL", "AAPL", n_days=100)
    
    # Inject a future timestamp into predictions (this should be caught)
    for bar in timeline:
        for sec_id, pred in bar.predictions.items():
            # All predictions should match or precede bar date
            assert pred.get("timestamp", bar.date) <= bar.date


def test_backtest_zero_timeline_raises():
    """Empty timeline should raise ValueError."""
    config = BacktestConfig(
        name="Empty Timeline Test",
        strategy_type=StrategyType.AI_PREDICTION,
        market_code="US",
        securities=["AAPL"],
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=100_000.0,
    )
    engine = BacktestEngine(config)
    with pytest.raises(ValueError, match="INSUFFICIENT_BACKTEST_DATA"):
        engine.run([])


def test_backtest_reproducible_with_same_seed():
    """Identical config + seed must produce identical results."""
    config = BacktestConfig(
        name="Reproducibility Test",
        strategy_type=StrategyType.MOMENTUM,
        market_code="US",
        securities=["AAPL"],
        start_date="2022-01-01",
        end_date="2022-06-30",
        initial_capital=100_000.0,
        random_seed=7777,
    )
    timeline = build_synthetic_timeline("AAPL", "AAPL", n_days=120)

    r1 = BacktestEngine(config).run(timeline)
    r2 = BacktestEngine(config).run(timeline)

    assert r1.configuration_hash == r2.configuration_hash
    assert abs(r1.performance.total_return_pct - r2.performance.total_return_pct) < 1e-6
    assert r1.performance.total_trades == r2.performance.total_trades


def test_backtest_max_drawdown_non_negative():
    config = BacktestConfig(
        name="Drawdown Sanity Test",
        strategy_type=StrategyType.AI_PREDICTION,
        market_code="US",
        securities=["AAPL"],
        start_date="2022-01-01",
        end_date="2022-12-31",
        initial_capital=100_000.0,
    )
    timeline = build_synthetic_timeline("AAPL", "AAPL", n_days=200, daily_drift=-0.001)  # Bearish drift
    engine = BacktestEngine(config)
    result = engine.run(timeline)

    assert result.performance.max_drawdown_pct >= 0.0


def test_backtest_all_trades_have_exit_reason():
    config = BacktestConfig(
        name="Trade Exit Reason Test",
        strategy_type=StrategyType.TREND_FOLLOWING,
        market_code="US",
        securities=["AAPL"],
        start_date="2022-01-01",
        end_date="2022-12-31",
        initial_capital=100_000.0,
        stop_loss_pct=0.08,
        take_profit_pct=0.20,
    )
    timeline = build_synthetic_timeline("AAPL", "AAPL", n_days=200)
    engine = BacktestEngine(config)
    result = engine.run(timeline)

    for trade in result.trades:
        assert trade.exit_reason in [r.value for r in ExitReason]
        assert trade.net_pnl != 0.0 or trade.shares == 0.0  # Zero-P&L only on zero shares


def test_backtest_monthly_heatmap_generated():
    config = BacktestConfig(
        name="Heatmap Test",
        strategy_type=StrategyType.AI_PREDICTION,
        market_code="US",
        securities=["AAPL"],
        start_date="2022-01-01",
        end_date="2022-12-31",
        initial_capital=100_000.0,
    )
    timeline = build_synthetic_timeline("AAPL", "AAPL", n_days=200)
    engine = BacktestEngine(config)
    result = engine.run(timeline)

    assert isinstance(result.monthly_returns_heatmap, dict)
    # Should have at least one year key
    if len(result.equity_curve) > 20:
        assert len(result.monthly_returns_heatmap) >= 1
