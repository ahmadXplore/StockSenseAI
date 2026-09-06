"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  LineChart, Sliders, History, Play, CheckCircle2,
  AlertTriangle, ArrowRight, Brain, RotateCcw, Loader2,
  ShieldCheck, FileText, Layers, Award
} from "lucide-react";
import {
  api, BacktestConfig, BacktestResponse, BacktestRunSummary
} from "@/lib/api";
import { formatCurrency, formatPercent, formatDate } from "@/lib/formatting";
import { BacktestConfigForm } from "@/components/backtesting/BacktestConfigForm";
import { PerformanceMetricsGrid } from "@/components/backtesting/PerformanceMetricsGrid";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { MonthlyHeatmap } from "@/components/charts/MonthlyHeatmap";
import { BackButton } from "@/components/BackButton";
import { TradesTable } from "@/components/backtesting/TradesTable";

export default function BacktestingStudioPage() {
  const [activeTab, setActiveTab] = useState<"new" | "history">("new");
  const [running, setRunning] = useState(false);
  const [currentResult, setCurrentResult] = useState<BacktestResponse | null>(null);
  const [pastRuns, setPastRuns] = useState<BacktestRunSummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => loadPastRuns(), 100);
    return () => clearTimeout(timer);
  }, []);

  const loadPastRuns = async () => {
    setLoadingHistory(true);
    try {
      const res = await api.backtests.list(undefined, undefined, 20);
      setPastRuns(res.runs || []);
    } catch (e: any) {
      const msg = (e?.message || "").toLowerCase();
      if (!msg.includes("abort") && !msg.includes("interrupt")) {
        // Non-abort errors: just show empty state
      }
      setPastRuns([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleRunBacktest = async (config: BacktestConfig) => {
    setRunning(true);
    setError(null);
    try {
      const res = await api.backtests.run(config);
      setCurrentResult(res);
      await loadPastRuns();
    } catch (err: any) {
      setError(err.message || "Failed to execute backtest simulation.");
    } finally {
      setRunning(false);
    }
  };

  const handleSelectPastRun = async (runId: string) => {
    setRunning(true);
    setError(null);
    try {
      const res = await api.backtests.get(runId);
      setCurrentResult(res);
      setActiveTab("new");
    } catch (err: any) {
      setError(err.message || "Failed to load past run.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand/10 border border-brand/20 text-brand text-xs font-semibold uppercase tracking-wider">
              <LineChart className="h-3.5 w-3.5" />
              <span>Event-Driven Quantitative Backtester</span>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Multi-Market Strategy Backtesting Studio
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 max-w-2xl leading-relaxed">
            Simulate point-in-time AI predictions and quantitative rules with NEXT_OPEN execution semantics, realistic transaction friction (slippage, broker commissions, SEC/CVT taxes), and dynamic risk exits.
          </p>
        </div>

        {/* View Switcher */}
        <div className="flex items-center gap-1 bg-[#0B0F19] border border-border p-1 rounded-xl">
          <button
            onClick={() => setActiveTab("new")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "new"
                ? "bg-brand text-white shadow-sm"
                : "text-gray-400 hover:text-white"
            }`}
          >
            <Sliders className="h-3.5 w-3.5" />
            <span>Simulation Studio</span>
          </button>
          <button
            onClick={() => setActiveTab("history")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "history"
                ? "bg-brand text-white shadow-sm"
                : "text-gray-400 hover:text-white"
            }`}
          >
            <History className="h-3.5 w-3.5" />
            <span>Run History ({pastRuns.length})</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/25 text-red-400 text-xs flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* View 1: New / Active Backtest Studio */}
      {activeTab === "new" && (
        <div className="space-y-8">
          <BacktestConfigForm onRunBacktest={handleRunBacktest} loading={running} />

          {/* Results Workspace */}
          {currentResult && (
            <div className="space-y-8 bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-2xl">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/50 pb-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-brand/15 text-brand border border-brand/30 font-bold font-mono">
                      {currentResult.config.market_code}
                    </span>
                    <h2 className="text-lg font-bold text-white font-mono">
                      {currentResult.config.name}
                    </h2>
                    <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      COMPLETED in {(currentResult.execution_duration_seconds ?? 0).toFixed(2)}s
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 font-mono">
                    Run ID: <span className="text-gray-300">{currentResult.run_id}</span> · Hash: <span className="text-gray-500">{currentResult.configuration_hash?.slice(0, 12) ?? "N/A"}…</span>
                  </div>
                </div>

                <div className="text-right text-xs font-mono">
                  <div className="text-gray-400">Backtest Horizon</div>
                  <div className="text-white font-bold">{currentResult.config.start_date} → {currentResult.config.end_date}</div>
                </div>
              </div>

              {/* Performance Metrics */}
              <PerformanceMetricsGrid
                metrics={currentResult.performance}
                risk={currentResult.risk}
                currency={currentResult.config.base_currency}
              />

              {/* Charts: Equity Curve vs Benchmark */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <LineChart className="h-4 w-4 text-brand" />
                  Portfolio Equity Curve vs Benchmark ({currentResult.config.benchmark_symbol || "SPY"})
                </h3>
                <EquityCurveChart
                  data={currentResult.equity_curve}
                  currency={currentResult.config.base_currency}
                />
              </div>

              {/* Monthly Returns Heatmap */}
              <div className="space-y-3 pt-4 border-t border-border/40">
                <h3 className="text-sm font-bold text-white">Monthly Compounded Returns Matrix (%)</h3>
                <MonthlyHeatmap
                  heatmap={currentResult.monthly_returns_heatmap}
                  yearly={currentResult.yearly_returns}
                />
              </div>

              {/* Risk Analytics Breakdown */}
              {currentResult.risk && (
                <div className="space-y-3 pt-4 border-t border-border/40">
                  <h3 className="text-sm font-bold text-white">Quantitative Risk Analytics & Tail Metrics</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs font-mono">
                    <div className="bg-background-elevated p-3 rounded-xl border border-border">
                      <div className="text-gray-400 text-[10px]">Daily VaR (95%)</div>
                      <div className="text-red-400 font-bold mt-0.5">-{(currentResult.risk.var_95_pct ?? 0).toFixed(2)}%</div>
                    </div>
                    <div className="bg-background-elevated p-3 rounded-xl border border-border">
                      <div className="text-gray-400 text-[10px]">Daily CVaR (95%)</div>
                      <div className="text-red-400 font-bold mt-0.5">-{(currentResult.risk.cvar_95_pct ?? 0).toFixed(2)}%</div>
                    </div>
                    <div className="bg-background-elevated p-3 rounded-xl border border-border">
                      <div className="text-gray-400 text-[10px]">Beta to Benchmark</div>
                      <div className="text-white font-bold mt-0.5">{(currentResult.risk.beta_to_benchmark ?? 0).toFixed(2)}</div>
                    </div>
                    <div className="bg-background-elevated p-3 rounded-xl border border-border">
                      <div className="text-gray-400 text-[10px]">Alpha (Annualized)</div>
                      <div className="text-emerald-400 font-bold mt-0.5">{formatPercent(currentResult.risk.alpha_annualized ?? 0)}</div>
                    </div>
                    <div className="bg-background-elevated p-3 rounded-xl border border-border">
                      <div className="text-gray-400 text-[10px]">Tracking Error</div>
                      <div className="text-white font-bold mt-0.5">{(currentResult.risk.tracking_error_pct ?? 0).toFixed(2)}%</div>
                    </div>
                    <div className="bg-background-elevated p-3 rounded-xl border border-border">
                      <div className="text-gray-400 text-[10px]">Information Ratio</div>
                      <div className="text-brand font-bold mt-0.5">{(currentResult.risk.information_ratio ?? 0).toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Execution Trades Log */}
              <div className="space-y-3 pt-4 border-t border-border/40">
                <h3 className="text-sm font-bold text-white flex items-center justify-between">
                  <span>Executed Trades Ledger ({currentResult.trades.length} trades)</span>
                </h3>
                <TradesTable
                  trades={currentResult.trades}
                  currency={currentResult.config.base_currency}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* View 2: History Catalog */}
      {activeTab === "history" && (
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-border/50 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <History className="h-4 w-4 text-brand" />
              Persisted Backtest Run Records
            </h3>
            <span className="text-xs text-gray-500 font-mono">Schema: analysis.backtest_run_records</span>
          </div>

          {pastRuns.length === 0 ? (
            <div className="py-12 text-center text-xs text-gray-500">
              No previous backtest runs recorded yet. Execute a simulation to build the history.
            </div>
          ) : (
            <div className="space-y-3">
              {pastRuns.map((r) => (
                <div
                  key={r.run_id}
                  className="bg-background-elevated border border-border/60 hover:border-brand/50 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-brand/15 text-brand text-xs font-bold font-mono">
                        {r.market_code}
                      </span>
                      <span className="font-bold text-sm text-white">{r.name}</span>
                      <span className="text-xs text-gray-500 font-mono">({r.strategy_type})</span>
                    </div>
                    <div className="text-xs text-gray-400 font-mono">
                      {r.start_date} → {r.end_date} · Capital: {formatCurrency(r.initial_capital, r.market_code === "PK" ? "PKR" : "USD", 0)}
                    </div>
                  </div>

                  <div className="flex items-center gap-6 font-mono text-xs">
                    <div className="text-right">
                      <div className="text-gray-400 text-[10px]">Return</div>
                      <div className={`font-bold ${r.total_return_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {formatPercent(r.total_return_pct)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-gray-400 text-[10px]">Sharpe</div>
                      <div className="font-bold text-brand">{r.sharpe_ratio?.toFixed(2) || "N/A"}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-gray-400 text-[10px]">Max DD</div>
                      <div className="font-bold text-red-400">-{(r.max_drawdown_pct ?? 0).toFixed(1)}%</div>
                    </div>
                    <button
                      onClick={() => handleSelectPastRun(r.run_id)}
                      className="px-3 py-1.5 rounded-lg bg-brand hover:bg-brand-hover text-white font-semibold text-xs transition-colors flex items-center gap-1"
                    >
                      <span>Inspect</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
