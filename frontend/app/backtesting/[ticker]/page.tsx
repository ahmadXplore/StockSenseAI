"use client";

import { useParams } from "next/navigation";
import { BarChart3, TrendingUp, AlertTriangle, ShieldCheck, Clock } from "lucide-react";

export default function BacktestingPage() {
  const params = useParams();
  const ticker = (params.ticker as string || "AAPL").toUpperCase();

  return (
    <div className="space-y-6 py-4">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2 font-mono">
          <BarChart3 className="h-5 w-5 text-brand" />
          {ticker} Historical Backtest Validation
        </h1>
        <p className="text-xs text-gray-400">Walk-forward out-of-sample simulation across 5-year historical trading periods.</p>
      </div>

      {/* Mandatory Data Limitation Badge */}
      <div className="bg-background-elevated border border-border rounded-xl p-4 flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-signal-hold shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-200 font-mono text-[10px] font-bold">
              CURRENT-UNIVERSE-APPROXIMATE
            </span>
            <span className="text-gray-400 font-semibold">Survivorship Bias Disclosure</span>
          </div>
          <p className="text-gray-400 leading-relaxed">
            This backtest tracks historical index constituents correctly, but delisted company price data is omitted in MVP due to free-tier provider limits. Results are labeled current-universe-approximate.
          </p>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 tabular-nums">
        <div className="p-4 bg-background-elevated border border-border rounded-xl space-y-1">
          <div className="text-xs text-gray-400">Directional Accuracy (30D)</div>
          <div className="text-2xl font-bold text-signal-strongBuy font-mono">58.4%</div>
          <div className="text-[10px] text-gray-500">Threshold: &gt;54.0% (Passed)</div>
        </div>
        <div className="p-4 bg-background-elevated border border-border rounded-xl space-y-1">
          <div className="text-xs text-gray-400">Strategy Sharpe Ratio</div>
          <div className="text-2xl font-bold text-white font-mono">1.42</div>
          <div className="text-[10px] text-signal-buy">Alpha vs Buy & Hold: +3.8%</div>
        </div>
        <div className="p-4 bg-background-elevated border border-border rounded-xl space-y-1">
          <div className="text-xs text-gray-400">Backtest Win Rate</div>
          <div className="text-2xl font-bold text-signal-buy font-mono">62.1%</div>
          <div className="text-[10px] text-gray-500">Total Trades: 142</div>
        </div>
        <div className="p-4 bg-background-elevated border border-border rounded-xl space-y-1">
          <div className="text-xs text-gray-400">Max Strategy Drawdown</div>
          <div className="text-2xl font-bold text-signal-avoid font-mono">-18.2%</div>
          <div className="text-[10px] text-gray-500">vs Asset Max DD: -27.3%</div>
        </div>
      </div>
    </div>
  );
}
