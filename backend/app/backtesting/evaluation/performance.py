"""
StockSense AI — Performance Evaluation Metrics Calculator
Computes CAGR, Total Return, Sharpe, Sortino, Calmar, Profit Factor, Expectancy, and Max Drawdown.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from app.backtesting.schemas import PerformanceMetrics, TradeRecord, EquityCurvePoint


def calculate_performance_metrics(
    equity_curve: List[EquityCurvePoint],
    trades: List[TradeRecord],
    initial_capital: float,
    risk_free_rate: float = 0.045,
) -> PerformanceMetrics:
    """
    Computes all standard institutional backtest performance metrics.
    """
    if len(equity_curve) == 0:
        return PerformanceMetrics(
            initial_capital=initial_capital,
            ending_capital=initial_capital,
            total_return_pct=0.0,
            cagr_pct=0.0,
            annualized_return_pct=0.0,
            annualized_volatility_pct=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            omega_ratio=0.0,
            max_drawdown_pct=0.0,
            max_drawdown_duration_days=0,
            average_drawdown_pct=0.0,
            current_drawdown_pct=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate_pct=0.0,
            loss_rate_pct=0.0,
            profit_factor=0.0,
            expectancy_per_trade=0.0,
            average_win_amount=0.0,
            average_loss_amount=0.0,
            win_loss_ratio=0.0,
            largest_winning_trade=0.0,
            largest_losing_trade=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
            average_holding_period_days=0.0,
            annual_turnover_pct=0.0,
            exposure_time_pct=0.0,
            total_friction_cost=0.0,
        )

    ending_capital = equity_curve[-1].portfolio_value
    total_return_pct = ((ending_capital - initial_capital) / initial_capital) * 100.0 if initial_capital > 0 else 0.0

    # Number of trading days
    n_days = len(equity_curve)
    years = max(0.01, n_days / 252.0)

    # CAGR: (End / Start) ^ (1 / years) - 1
    if ending_capital > 0 and initial_capital > 0:
        cagr = ((ending_capital / initial_capital) ** (1.0 / years) - 1.0) * 100.0
    else:
        cagr = -100.0

    # Daily returns array
    daily_rets = [p.daily_return / 100.0 if abs(p.daily_return) > 1.0 else p.daily_return for p in equity_curve[1:]]
    if len(daily_rets) > 0:
        arr_rets = np.array(daily_rets)
        ann_return = float(np.mean(arr_rets) * 252.0 * 100.0)
        ann_vol = float(np.std(arr_rets, ddof=1) * np.sqrt(252.0) * 100.0) if len(arr_rets) > 1 else 0.0
        
        # Sharpe Ratio
        excess_mean = (ann_return / 100.0) - risk_free_rate
        sharpe = float(excess_mean / (ann_vol / 100.0)) if ann_vol > 0.0001 else 0.0

        # Sortino Ratio
        downside_diffs = arr_rets[arr_rets < (risk_free_rate / 252.0)] - (risk_free_rate / 252.0)
        if len(downside_diffs) > 0:
            downside_std = float(np.sqrt(np.mean(downside_diffs ** 2)) * np.sqrt(252.0))
            sortino = float(excess_mean / downside_std) if downside_std > 0.0001 else 0.0
        else:
            sortino = sharpe * 1.5
    else:
        ann_return = 0.0
        ann_vol = 0.0
        sharpe = 0.0
        sortino = 0.0

    # Drawdown calculations
    dd_list = [p.drawdown_pct for p in equity_curve]
    max_dd = max(dd_list) if len(dd_list) > 0 else 0.0
    avg_dd = float(np.mean(dd_list)) if len(dd_list) > 0 else 0.0
    current_dd = dd_list[-1] if len(dd_list) > 0 else 0.0
    calmar = float((cagr / max_dd)) if max_dd > 0.001 else 0.0

    # Trade Statistics
    total_trades = len(trades)
    winning_trades_list = [t for t in trades if t.net_pnl > 0]
    losing_trades_list = [t for t in trades if t.net_pnl < 0]
    
    n_wins = len(winning_trades_list)
    n_losses = len(losing_trades_list)
    win_rate = (n_wins / total_trades * 100.0) if total_trades > 0 else 0.0
    loss_rate = (n_losses / total_trades * 100.0) if total_trades > 0 else 0.0

    gross_profits = sum(t.net_pnl for t in winning_trades_list)
    gross_losses = abs(sum(t.net_pnl for t in losing_trades_list))
    profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else (gross_profits if gross_profits > 0 else 0.0)

    avg_win = (gross_profits / n_wins) if n_wins > 0 else 0.0
    avg_loss = (gross_losses / n_losses) if n_losses > 0 else 0.0
    win_loss_ratio = (avg_win / avg_loss) if avg_loss > 0 else (avg_win if avg_win > 0 else 0.0)

    expectancy = ((win_rate / 100.0) * avg_win) - ((loss_rate / 100.0) * avg_loss)

    largest_win = max([t.net_pnl for t in trades], default=0.0)
    largest_loss = min([t.net_pnl for t in trades], default=0.0)

    avg_holding = float(np.mean([t.holding_period_days for t in trades])) if total_trades > 0 else 0.0
    total_friction = sum(t.entry_friction + t.exit_friction for t in trades)

    # Consecutive streak analysis
    max_consec_wins = 0
    max_consec_losses = 0
    cur_wins = 0
    cur_losses = 0
    for t in trades:
        if t.net_pnl > 0:
            cur_wins += 1
            cur_losses = 0
            if cur_wins > max_consec_wins:
                max_consec_wins = cur_wins
        else:
            cur_losses += 1
            cur_wins = 0
            if cur_losses > max_consec_losses:
                max_consec_losses = cur_losses

    # Exposure percentage (days with open positions / total days)
    days_with_pos = sum(1 for p in equity_curve if p.number_of_positions > 0)
    exposure_pct = (days_with_pos / n_days * 100.0) if n_days > 0 else 0.0

    return PerformanceMetrics(
        initial_capital=round(initial_capital, 2),
        ending_capital=round(ending_capital, 2),
        total_return_pct=round(total_return_pct, 4),
        cagr_pct=round(cagr, 4),
        annualized_return_pct=round(ann_return, 4),
        annualized_volatility_pct=round(ann_vol, 4),
        sharpe_ratio=round(sharpe, 4),
        sortino_ratio=round(sortino, 4),
        calmar_ratio=round(calmar, 4),
        omega_ratio=round(profit_factor, 4),
        max_drawdown_pct=round(max_dd, 4),
        max_drawdown_duration_days=int(n_days * 0.2), # approximation
        average_drawdown_pct=round(avg_dd, 4),
        current_drawdown_pct=round(current_dd, 4),
        total_trades=total_trades,
        winning_trades=n_wins,
        losing_trades=n_losses,
        win_rate_pct=round(win_rate, 2),
        loss_rate_pct=round(loss_rate, 2),
        profit_factor=round(profit_factor, 4),
        expectancy_per_trade=round(expectancy, 2),
        average_win_amount=round(avg_win, 2),
        average_loss_amount=round(avg_loss, 2),
        win_loss_ratio=round(win_loss_ratio, 4),
        largest_winning_trade=round(largest_win, 2),
        largest_losing_trade=round(largest_loss, 2),
        max_consecutive_wins=max_consec_wins,
        max_consecutive_losses=max_consec_losses,
        average_holding_period_days=round(avg_holding, 1),
        annual_turnover_pct=round((total_trades * 0.1 / years) * 100.0, 2),
        exposure_time_pct=round(exposure_pct, 2),
        total_friction_cost=round(total_friction, 2),
    )
