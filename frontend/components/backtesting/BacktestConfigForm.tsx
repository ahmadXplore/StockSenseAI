"use client";

import { useState, useEffect } from "react";
import {
  Brain, Play, RotateCcw, Sliders, Shield, DollarSign,
  TrendingUp, Calendar, AlertCircle, Loader2, Check
} from "lucide-react";
import {
  BacktestConfig, StrategyType, PositionSizingMethod,
  AllocationMethod, SlippageModelType
} from "@/lib/types";
import { SUPPORTED_MARKETS_CONFIG } from "@/lib/market";

interface BacktestConfigFormProps {
  initialConfig?: Partial<BacktestConfig>;
  onRunBacktest: (config: BacktestConfig) => Promise<void>;
  loading?: boolean;
  className?: string;
}

const STRATEGIES: Array<{ type: StrategyType; name: string; desc: string }> = [
  { type: "AI_PREDICTION", name: "AI ML Prediction Strategy", desc: "Point-in-time machine learning predictions with probability thresholds." },
  { type: "MOMENTUM", name: "Moving Average Momentum", desc: "Fast/Slow MA crossovers with return velocity breakout filter." },
  { type: "TREND_FOLLOWING", name: "MACD Trend Following", desc: "MACD histogram expansion aligned with 200 SMA long-term trend." },
  { type: "MEAN_REVERSION", name: "RSI Mean Reversion", desc: "Oversold RSI <30 bounces off lower Bollinger Bands." },
  { type: "FUNDAMENTAL", name: "Fundamental Quality Factor", desc: "High ROE, low P/E, low Debt/Equity, and high Piotroski F-Score." },
  { type: "VOLATILITY_BREAKOUT", name: "Donchian Volatility Breakout", desc: "20-day high breakouts with adaptive ATR trailing stops." },
  { type: "ENSEMBLE", name: "Multi-Factor Ensemble", desc: "Weighted consensus across AI (50%), Momentum (30%), and Fundamentals (20%)." },
];

export function BacktestConfigForm({
  initialConfig,
  onRunBacktest,
  loading = false,
  className = "",
}: BacktestConfigFormProps) {
  const [marketCode, setMarketCode] = useState<string>(initialConfig?.market_code || "PK");
  const [strategyType, setStrategyType] = useState<StrategyType>(initialConfig?.strategy_type || "AI_PREDICTION");
  const [securitiesInput, setSecuritiesInput] = useState<string>(
    initialConfig?.securities?.join(", ") || "ENGRO"
  );
  const [startDate, setStartDate] = useState<string>(initialConfig?.start_date || "2022-01-01");
  const [endDate, setEndDate] = useState<string>(initialConfig?.end_date || "2024-12-31");
  const [initialCapital, setInitialCapital] = useState<number>(
    initialConfig?.initial_capital || (marketCode === "PK" ? 1000000 : 100000)
  );
  const [sizingMethod, setSizingMethod] = useState<PositionSizingMethod>(
    initialConfig?.position_sizing || "ATR_RISK"
  );
  const [stopLossPct, setStopLossPct] = useState<number>(initialConfig?.stop_loss_pct || 0.05);
  const [takeProfitPct, setTakeProfitPct] = useState<number>(initialConfig?.take_profit_pct || 0.15);
  const [trailingAtr, setTrailingAtr] = useState<number>(initialConfig?.trailing_stop_atr_mult || 1.5);
  const [slippageBps, setSlippageBps] = useState<number>(initialConfig?.slippage_bps || 5.0);
  const [commissionPct, setCommissionPct] = useState<number>(initialConfig?.commission_pct || 0.001);

  const marketMeta = SUPPORTED_MARKETS_CONFIG[marketCode] || SUPPORTED_MARKETS_CONFIG.US;

  // Sync initial capital and sample securities on market change
  const handleMarketChange = (newMkt: string) => {
    setMarketCode(newMkt);
    const m = SUPPORTED_MARKETS_CONFIG[newMkt] || SUPPORTED_MARKETS_CONFIG.US;
    setInitialCapital(newMkt === "PK" ? 1000000 : 100000);
    setSecuritiesInput(m.sampleSecurities.map((s) => s.ticker).slice(0, 3).join(", "));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const securities = securitiesInput
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length > 0);

    const config: BacktestConfig = {
      name: `${marketCode} ${strategyType} Strategy Backtest`,
      strategy_type: strategyType,
      market_code: marketCode,
      exchange_code: marketMeta.defaultExchange,
      securities: securities.length > 0 ? securities : [marketMeta.sampleSecurities[0]?.ticker || "AAPL"],
      benchmark_symbol: marketMeta.benchmarkSymbol,
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      base_currency: marketMeta.currency,
      position_sizing: sizingMethod,
      risk_per_trade_pct: 0.02,
      max_position_weight: 0.25,
      stop_loss_pct: stopLossPct,
      take_profit_pct: takeProfitPct,
      trailing_stop_atr_mult: trailingAtr,
      slippage_model: "FIXED_BPS",
      slippage_bps: slippageBps,
      commission_pct: commissionPct,
      dividend_handling: "REINVEST",
      apply_splits: true,
      random_seed: 42,
    };

    await onRunBacktest(config);
  };

  return (
    <form onSubmit={handleSubmit} className={`bg-[#0B0F19] border border-border rounded-2xl p-5 sm:p-6 shadow-xl space-y-6 ${className}`}>
      <div className="flex items-center justify-between border-b border-border/50 pb-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <Sliders className="h-4 w-4 text-brand" />
          Backtest Parameter Configuration Wizard
        </h3>
        <span className="text-[10px] text-gray-500 font-mono">Zero Lookahead Execution Standard</span>
      </div>

      {/* 1. Market Selection */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-gray-300">1. Target Market & Exchange</label>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {Object.values(SUPPORTED_MARKETS_CONFIG).map((m) => {
            const isSelected = m.code === marketCode;
            return (
              <button
                type="button"
                key={m.code}
                onClick={() => handleMarketChange(m.code)}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  isSelected
                    ? "bg-brand/15 border-brand text-white shadow-md shadow-blue-500/10"
                    : "bg-background-elevated border-border text-gray-400 hover:text-white"
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className="text-base">{m.flag}</span>
                  <span className="font-bold text-xs">{m.code}</span>
                </div>
                <div className="text-[10px] text-gray-500 truncate mt-0.5">{m.name}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. Strategy Archetype */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-gray-300">2. Strategy Archetype</label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {STRATEGIES.map((s) => {
            const isSelected = s.type === strategyType;
            return (
              <button
                type="button"
                key={s.type}
                onClick={() => setStrategyType(s.type)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isSelected
                    ? "bg-brand/15 border-brand/60 text-white"
                    : "bg-background-elevated border-border/60 text-gray-400 hover:text-white"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-bold ${isSelected ? "text-brand" : "text-white"}`}>
                    {s.name}
                  </span>
                  {isSelected && <Check className="h-3.5 w-3.5 text-brand" />}
                </div>
                <div className="text-[11px] text-gray-400 mt-1 leading-snug">{s.desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Universe & Securities */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-300">
            3. Securities / Constituents (comma-separated tickers)
          </label>
          <input
            type="text"
            value={securitiesInput}
            onChange={(e) => setSecuritiesInput(e.target.value)}
            placeholder="e.g. ENGRO, HBL, LUCK"
            className="w-full bg-[#0E1422] border border-border rounded-xl px-3 py-2.5 text-xs sm:text-sm font-mono text-white placeholder-gray-500 focus:border-brand"
            required
          />
          <div className="text-[10px] text-gray-500">
            Market defaults: {marketMeta.sampleSecurities.map((s) => s.ticker).join(", ")}
          </div>
        </div>

        {/* Capital */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-300">
            4. Initial Cash Capital ({marketMeta.currency})
          </label>
          <input
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
            min={1000}
            step={1000}
            className="w-full bg-[#0E1422] border border-border rounded-xl px-3 py-2.5 text-xs sm:text-sm font-mono text-white placeholder-gray-500 focus:border-brand"
            required
          />
        </div>
      </div>

      {/* 4. Date Range */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-300">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full bg-[#0E1422] border border-border rounded-xl px-3 py-2.5 text-xs font-mono text-white focus:border-brand"
            required
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-gray-300">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full bg-[#0E1422] border border-border rounded-xl px-3 py-2.5 text-xs font-mono text-white focus:border-brand"
            required
          />
        </div>
      </div>

      {/* 5. Risk Controls & Exits */}
      <div className="space-y-2 border-t border-border/40 pt-4">
        <div className="text-xs font-semibold text-gray-300">5. Dynamic Risk Exits & Sizing</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="space-y-1">
            <label className="text-[10px] text-gray-400">Position Sizing</label>
            <select
              value={sizingMethod}
              onChange={(e) => setSizingMethod(e.target.value as any)}
              className="w-full bg-[#0E1422] border border-border rounded-lg p-2 text-xs text-white"
            >
              <option value="ATR_RISK">ATR Volatility Risk</option>
              <option value="FIXED_PERCENTAGE">Fixed Percentage (5%)</option>
              <option value="CONFIDENCE_WEIGHTED">AI Confidence Sizing</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-[10px] text-gray-400">Stop Loss (%)</label>
            <input
              type="number"
              value={stopLossPct * 100}
              onChange={(e) => setStopLossPct(Number(e.target.value) / 100)}
              step={0.5}
              className="w-full bg-[#0E1422] border border-border rounded-lg p-2 text-xs text-white font-mono"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] text-gray-400">Take Profit (%)</label>
            <input
              type="number"
              value={takeProfitPct * 100}
              onChange={(e) => setTakeProfitPct(Number(e.target.value) / 100)}
              step={0.5}
              className="w-full bg-[#0E1422] border border-border rounded-lg p-2 text-xs text-white font-mono"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] text-gray-400">Slippage (BPS)</label>
            <input
              type="number"
              value={slippageBps}
              onChange={(e) => setSlippageBps(Number(e.target.value))}
              step={1}
              className="w-full bg-[#0E1422] border border-border rounded-lg p-2 text-xs text-white font-mono"
            />
          </div>
        </div>
      </div>

      {/* Submit CTA */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={loading}
          className="w-full py-3.5 px-6 rounded-xl bg-brand hover:bg-brand-hover text-white font-bold text-sm shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Simulating Event-Driven Timeline…</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4 fill-white" />
              <span>Execute Strategy Backtest ({marketCode})</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}
