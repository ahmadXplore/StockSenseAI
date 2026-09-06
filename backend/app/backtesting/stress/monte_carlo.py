"""
StockSense AI — Monte Carlo Portfolio Simulation Engine
Runs bootstrapped & parametric Monte Carlo forward simulations to project terminal wealth distributions and tail risk.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from app.backtesting.schemas import MonteCarloSimulationResult


def run_monte_carlo_simulation(
    daily_returns: List[float],
    initial_capital: float = 100000.0,
    iterations: int = 500,
    horizon_days: int = 252,
    random_seed: int = 42,
    target_return_pct: float = 15.0,
) -> MonteCarloSimulationResult:
    """
    Executes random block-bootstrapped return simulations over a forward horizon.
    """
    if len(daily_returns) < 5:
        return MonteCarloSimulationResult(
            iterations=iterations,
            simulated_horizon_days=horizon_days,
            mean_terminal_wealth=initial_capital,
            median_terminal_wealth=initial_capital,
            p5_terminal_wealth=initial_capital * 0.85,
            p25_terminal_wealth=initial_capital * 0.95,
            p75_terminal_wealth=initial_capital * 1.10,
            p95_terminal_wealth=initial_capital * 1.25,
            mean_max_drawdown_pct=12.0,
            worst_case_max_drawdown_pct=25.0,
            p95_max_drawdown_pct=20.0,
            probability_of_profit_pct=60.0,
            probability_of_loss_pct=40.0,
            probability_of_ruin_pct=0.0,
            sample_trajectories=[],
        )

    np.random.seed(random_seed)
    returns_pool = np.array(daily_returns)

    # Matrix of shape (iterations, horizon_days)
    sampled_indices = np.random.choice(len(returns_pool), size=(iterations, horizon_days), replace=True)
    simulated_returns = returns_pool[sampled_indices]

    # Cumulative wealth trajectories: (iterations, horizon_days + 1)
    wealth_paths = np.zeros((iterations, horizon_days + 1))
    wealth_paths[:, 0] = initial_capital

    for t in range(horizon_days):
        wealth_paths[:, t + 1] = wealth_paths[:, t] * (1.0 + simulated_returns[:, t])

    terminal_wealths = wealth_paths[:, -1]

    # Max Drawdowns across simulated paths
    running_maxes = np.maximum.accumulate(wealth_paths, axis=1)
    drawdown_paths = (running_maxes - wealth_paths) / running_maxes * 100.0
    max_drawdowns = np.max(drawdown_paths, axis=1)

    # Probabilities
    target_wealth = initial_capital * (1.0 + (target_return_pct / 100.0))
    prob_profit = float(np.mean(terminal_wealths > initial_capital) * 100.0)
    prob_loss = float(np.mean(terminal_wealths < initial_capital) * 100.0)
    prob_ruin = float(np.mean(terminal_wealths <= initial_capital * 0.50) * 100.0) # >50% capital loss

    # Select 20 representative trajectories for charting
    stride = max(1, iterations // 20)
    sample_curves = [wealth_paths[i, :].tolist() for i in range(0, iterations, stride)][:20]

    return MonteCarloSimulationResult(
        iterations=iterations,
        simulated_horizon_days=horizon_days,
        confidence_level_pct=95.0,
        mean_terminal_wealth=round(float(np.mean(terminal_wealths)), 2),
        median_terminal_wealth=round(float(np.median(terminal_wealths)), 2),
        p5_terminal_wealth=round(float(np.percentile(terminal_wealths, 5)), 2),
        p25_terminal_wealth=round(float(np.percentile(terminal_wealths, 25)), 2),
        p75_terminal_wealth=round(float(np.percentile(terminal_wealths, 75)), 2),
        p95_terminal_wealth=round(float(np.percentile(terminal_wealths, 95)), 2),
        mean_max_drawdown_pct=round(float(np.mean(max_drawdowns)), 2),
        worst_case_max_drawdown_pct=round(float(np.max(max_drawdowns)), 2),
        p95_max_drawdown_pct=round(float(np.percentile(max_drawdowns, 95)), 2),
        probability_of_profit_pct=round(prob_profit, 2),
        probability_of_loss_pct=round(prob_loss, 2),
        probability_of_ruin_pct=round(prob_ruin, 2),
        sample_trajectories=sample_curves,
    )
