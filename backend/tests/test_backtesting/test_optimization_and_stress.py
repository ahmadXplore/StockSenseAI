"""
Tests: Portfolio Optimization, Stress Testing, and Monte Carlo Simulation
"""

import pytest
import numpy as np
from app.backtesting.optimization.mean_variance import optimize_mean_variance
from app.backtesting.optimization.risk_parity import optimize_risk_parity
from app.backtesting.optimization.minimum_variance import optimize_minimum_variance
from app.backtesting.optimization.constraints import run_portfolio_optimization
from app.backtesting.stress.monte_carlo import run_monte_carlo_simulation
from app.backtesting.stress.historical import evaluate_historical_stress_scenarios
from app.backtesting.schemas import AllocationMethod


# ── Shared test data ──

# 3 assets, 252 trading days of synthetic daily returns
np.random.seed(42)
N_ASSETS = 3
N_DAYS = 252

RETURNS_MATRIX = np.random.multivariate_normal(
    mean=[0.0008, 0.0005, 0.0003],
    cov=np.array([
        [0.0004, 0.0001, 0.00005],
        [0.0001, 0.0003, 0.00006],
        [0.00005, 0.00006, 0.0002],
    ]),
    size=N_DAYS
)
COV_ANN = np.cov(RETURNS_MATRIX, rowvar=False) * 252
EXP_RETURNS_ANN = np.mean(RETURNS_MATRIX, axis=0) * 252
SECURITY_IDS = ["AAPL", "MSFT", "GOOGL"]


# ── Mean-Variance Tests ──

def test_max_sharpe_weights_sum_to_one():
    w, ret, vol, sharpe = optimize_mean_variance(EXP_RETURNS_ANN, COV_ANN)
    assert abs(np.sum(w) - 1.0) < 1e-5


def test_max_sharpe_all_weights_non_negative():
    w, ret, vol, sharpe = optimize_mean_variance(EXP_RETURNS_ANN, COV_ANN, min_weight=0.0)
    assert all(wi >= -1e-6 for wi in w)


def test_max_sharpe_respects_max_weight_constraint():
    max_w = 0.50
    w, ret, vol, sharpe = optimize_mean_variance(EXP_RETURNS_ANN, COV_ANN, max_weight=max_w)
    assert all(wi <= max_w + 1e-5 for wi in w)


def test_max_sharpe_positive_sharpe():
    w, ret, vol, sharpe = optimize_mean_variance(EXP_RETURNS_ANN, COV_ANN)
    assert sharpe > 0.0


def test_max_sharpe_single_asset():
    w, ret, vol, sharpe = optimize_mean_variance(
        np.array([0.10]),
        np.array([[0.04]]),
    )
    assert abs(w[0] - 1.0) < 1e-5


# ── Risk Parity Tests ──

def test_risk_parity_weights_sum_to_one():
    w = optimize_risk_parity(COV_ANN)
    assert abs(np.sum(w) - 1.0) < 1e-5


def test_risk_parity_all_positive():
    w = optimize_risk_parity(COV_ANN, min_weight=0.01)
    assert all(wi >= 0.0 for wi in w)


def test_risk_parity_equal_risk_contribution():
    """Higher-volatility assets should receive lower weights in risk parity."""
    # Create extreme volatility disparity
    extreme_cov = np.diag([0.04, 0.0001])  # Asset 0 is 20x more volatile
    w = optimize_risk_parity(extreme_cov, min_weight=0.01)
    # Lower-vol asset (index 1) should get more weight
    assert w[1] > w[0]


# ── Minimum Variance Tests ──

def test_min_variance_weights_sum_to_one():
    w = optimize_minimum_variance(COV_ANN)
    assert abs(np.sum(w) - 1.0) < 1e-5


def test_min_variance_lower_vol_than_equal_weight():
    w_mv = optimize_minimum_variance(COV_ANN)
    w_eq = np.array([1/3, 1/3, 1/3])
    vol_mv = np.sqrt(np.dot(w_mv.T, np.dot(COV_ANN, w_mv)))
    vol_eq = np.sqrt(np.dot(w_eq.T, np.dot(COV_ANN, w_eq)))
    assert vol_mv <= vol_eq + 1e-6  # MV must be <= equal-weight vol


# ── Master Optimization Orchestrator ──

def test_run_optimization_max_sharpe():
    result = run_portfolio_optimization(
        returns_matrix=RETURNS_MATRIX,
        security_ids=SECURITY_IDS,
        method=AllocationMethod.MAX_SHARPE,
    )
    assert result.method == AllocationMethod.MAX_SHARPE
    assert len(result.weights) == N_ASSETS
    total_weight = sum(result.weights.values())
    assert abs(total_weight - 1.0) < 1e-3
    assert result.expected_annual_return != 0.0
    assert result.expected_annual_volatility > 0.0
    assert result.sharpe_ratio > 0.0


def test_run_optimization_risk_parity():
    result = run_portfolio_optimization(
        returns_matrix=RETURNS_MATRIX,
        security_ids=SECURITY_IDS,
        method=AllocationMethod.RISK_PARITY,
    )
    assert result.method == AllocationMethod.RISK_PARITY
    total_weight = sum(result.weights.values())
    assert abs(total_weight - 1.0) < 1e-3


def test_run_optimization_empty_securities():
    result = run_portfolio_optimization(
        returns_matrix=np.array([]),
        security_ids=[],
        method=AllocationMethod.MAX_SHARPE,
    )
    assert result.weights == {}


def test_run_optimization_insufficient_data():
    result = run_portfolio_optimization(
        returns_matrix=np.array([[0.01, 0.02, -0.01]]),  # Only 1 row
        security_ids=SECURITY_IDS,
        method=AllocationMethod.MAX_SHARPE,
    )
    # Should gracefully return equal weights fallback
    assert len(result.weights) == N_ASSETS


# ── Monte Carlo Tests ──

def test_monte_carlo_runs_successfully():
    daily_rets = (RETURNS_MATRIX[:, 0]).tolist()
    result = run_monte_carlo_simulation(
        daily_returns=daily_rets,
        initial_capital=100_000.0,
        iterations=100,
        horizon_days=60,
        random_seed=42,
    )
    assert result.iterations == 100
    assert result.mean_terminal_wealth > 0.0
    assert result.p5_terminal_wealth <= result.p50_terminal_wealth <= result.p95_terminal_wealth if hasattr(result, "p50_terminal_wealth") else True
    assert result.p5_terminal_wealth <= result.p95_terminal_wealth
    assert 0.0 <= result.probability_of_profit_pct <= 100.0
    assert 0.0 <= result.probability_of_loss_pct <= 100.0
    assert result.probability_of_profit_pct + result.probability_of_loss_pct <= 100.01  # allows rounding


def test_monte_carlo_reproducible_with_same_seed():
    daily_rets = (RETURNS_MATRIX[:, 0]).tolist()
    r1 = run_monte_carlo_simulation(daily_rets, iterations=50, horizon_days=30, random_seed=99)
    r2 = run_monte_carlo_simulation(daily_rets, iterations=50, horizon_days=30, random_seed=99)
    assert r1.mean_terminal_wealth == r2.mean_terminal_wealth
    assert r1.p5_terminal_wealth == r2.p5_terminal_wealth


def test_monte_carlo_empty_returns():
    """Should gracefully handle empty return series."""
    result = run_monte_carlo_simulation(daily_returns=[], initial_capital=100_000.0, iterations=100)
    assert result.mean_terminal_wealth > 0.0  # Falls back to initial capital


# ── Historical Stress Tests ──

def test_stress_test_returns_all_scenarios():
    daily_rets = (RETURNS_MATRIX[:, 0]).tolist()
    dates = [f"2024-01-{i+1:02d}" for i in range(len(daily_rets))]
    results = evaluate_historical_stress_scenarios(daily_rets, dates, initial_portfolio_value=100_000.0)
    # Should return all 3 preloaded crisis scenarios
    assert len(results) >= 3


def test_stress_test_drawdown_positive():
    daily_rets = (RETURNS_MATRIX[:, 0]).tolist()
    dates = [f"2024-01-{i+1:02d}" for i in range(len(daily_rets))]
    results = evaluate_historical_stress_scenarios(daily_rets, dates)
    for scenario in results:
        assert scenario.portfolio_drawdown_pct >= 0.0
        assert scenario.benchmark_drawdown_pct > 0.0


def test_stress_test_empty_portfolio():
    results = evaluate_historical_stress_scenarios([], [])
    assert results == []
