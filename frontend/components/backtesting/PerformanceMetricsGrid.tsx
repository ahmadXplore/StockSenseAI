"use client";

import { PerformanceMetrics, RiskMetricsReport } from "@/lib/types";
import { formatCurrency, formatPercent } from "@/lib/formatting";

interface PerformanceMetricsGridProps {
  metrics: PerformanceMetrics;
  risk?: RiskMetricsReport;
  currency?: string;
  className?: string;
}

export function PerformanceMetricsGrid({
  metrics,
  risk,
  currency = "USD",
  className = "",
}: PerformanceMetricsGridProps) {
  const isPos = metrics.total_return_pct >= 0;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Primary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-mono">
        <div className="bg-background-elevated border border-border p-3.5 rounded-xl space-y-1">
          <div className="text-gray-400 text-[10px]">Total Return</div>
          <div className={`text-lg font-bold ${isPos ? "text-emerald-400" : "text-red-400"}`}>
            {formatPercent(metrics.total_return_pct)}
          </div>
          <div className="text-[10px] text-gray-500">{formatCurrency(metrics.ending_capital - metrics.initial_capital, currency)}</div>
        </div>

        <div className="bg-background-elevated border border-border p-3.5 rounded-xl space-y-1">
          <div className="text-gray-400 text-[10px]">CAGR</div>
          <div className="text-lg font-bold text-white">
            {formatPercent(metrics.cagr_pct, false)}
          </div>
          <div className="text-[10px] text-gray-500">Annualized Compound</div>
        </div>

        <div className="bg-background-elevated border border-border p-3.5 rounded-xl space-y-1">
          <div className="text-gray-400 text-[10px]">Sharpe Ratio</div>
          <div className="text-lg font-bold text-brand">
            {(metrics.sharpe_ratio ?? 0).toFixed(2)}
          </div>
          <div className="text-[10px] text-gray-500">Sortino: {(metrics.sortino_ratio ?? 0).toFixed(2)}</div>
        </div>

        <div className="bg-background-elevated border border-border p-3.5 rounded-xl space-y-1">
          <div className="text-gray-400 text-[10px]">Max Drawdown</div>
          <div className="text-lg font-bold text-red-400">
            -{(metrics.max_drawdown_pct ?? 0).toFixed(2)}%
          </div>
          <div className="text-[10px] text-gray-500">Calmar: {(metrics.calmar_ratio ?? 0).toFixed(2)}</div>
        </div>

        <div className="bg-background-elevated border border-border p-3.5 rounded-xl space-y-1">
          <div className="text-gray-400 text-[10px]">Win Rate (%)</div>
          <div className="text-lg font-bold text-emerald-400">
            {(metrics.win_rate_pct ?? 0).toFixed(1)}%
          </div>
          <div className="text-[10px] text-gray-500">{metrics.winning_trades}W / {metrics.losing_trades}L</div>
        </div>

        <div className="bg-background-elevated border border-border p-3.5 rounded-xl space-y-1">
          <div className="text-gray-400 text-[10px]">Profit Factor</div>
          <div className="text-lg font-bold text-white">
            {(metrics.profit_factor ?? 0).toFixed(2)}
          </div>
          <div className="text-[10px] text-gray-500">Trades: {metrics.total_trades}</div>
        </div>
      </div>

      {/* Secondary Detailed Breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-background-elevated/60 border border-border/60 p-4 rounded-xl text-xs font-mono">
        <div className="space-y-1">
          <span className="text-gray-500 text-[10px]">Average Win</span>
          <div className="text-emerald-400 font-bold">{formatCurrency(metrics.average_win_amount, currency)}</div>
        </div>
        <div className="space-y-1">
          <span className="text-gray-500 text-[10px]">Average Loss</span>
          <div className="text-red-400 font-bold">{formatCurrency(metrics.average_loss_amount, currency)}</div>
        </div>
        <div className="space-y-1">
          <span className="text-gray-500 text-[10px]">Avg Holding Period</span>
          <div className="text-white font-bold">{(metrics.average_holding_period_days ?? 0).toFixed(1)} Days</div>
        </div>
        <div className="space-y-1">
          <span className="text-gray-500 text-[10px]">Total Friction Incurred</span>
          <div className="text-amber-400 font-bold">{formatCurrency(metrics.total_friction_cost, currency)}</div>
        </div>
      </div>
    </div>
  );
}
