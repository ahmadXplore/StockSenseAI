"""
StockSense AI — Evaluation & Analytics Module
"""

from app.backtesting.evaluation.performance import calculate_performance_metrics
from app.backtesting.evaluation.benchmark import (
    compute_benchmark_comparison,
    DEFAULT_MARKET_BENCHMARKS,
)
from app.backtesting.evaluation.attribution import compute_performance_attribution
from app.backtesting.evaluation.statistics import (
    generate_monthly_returns_heatmap,
    generate_yearly_returns,
)

__all__ = [
    "calculate_performance_metrics",
    "compute_benchmark_comparison",
    "DEFAULT_MARKET_BENCHMARKS",
    "compute_performance_attribution",
    "generate_monthly_returns_heatmap",
    "generate_yearly_returns",
]
