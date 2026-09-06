"use client";

import { useState } from "react";
import {
  Brain, TrendingUp, TrendingDown, Minus, ShieldAlert,
  Target, Activity, CheckCircle2, DollarSign, Calculator,
  ArrowUpRight, ArrowDownRight, Info, AlertTriangle, Sparkles
} from "lucide-react";
import { MLPrediction } from "@/lib/types";
import { formatPercent, formatCurrency } from "@/lib/formatting";

interface PredictionCardProps {
  prediction?: MLPrediction | null;
  loading?: boolean;
  onHorizonChange?: (horizon: string) => void;
  currency?: string;
  ticker?: string;
  currentPrice?: number;
  className?: string;
}

const HORIZONS = [
  { id: "7d", label: "7 Days" },
  { id: "30d", label: "30 Days" },
  { id: "3m", label: "3 Months" },
  { id: "6m", label: "6 Months" },
  { id: "1y", label: "1 Year" },
];

export function PredictionCard({
  prediction,
  loading = false,
  onHorizonChange,
  currency = "USD",
  ticker = "SECURITY",
  currentPrice,
  className = "",
}: PredictionCardProps) {
  const [activeHorizon, setActiveHorizon] = useState("30d");
  const defaultInvestment = currency === "PKR" || currency === "JPY" || currency === "INR" ? 50000 : 1000;
  const [investmentAmount, setInvestmentAmount] = useState<number>(defaultInvestment);

  const handleHorizonClick = (h: string) => {
    setActiveHorizon(h);
    if (onHorizonChange) onHorizonChange(h);
  };

  if (loading) {
    return (
      <div className={`bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4 animate-pulse ${className}`}>
        <div className="h-6 w-48 bg-white/10 rounded-md" />
        <div className="h-24 w-full bg-white/5 rounded-xl" />
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="h-16 bg-white/5 rounded-xl" />
          <div className="h-16 bg-white/5 rounded-xl" />
          <div className="h-16 bg-white/5 rounded-xl" />
          <div className="h-16 bg-white/5 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className={`bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl text-center space-y-3 ${className}`}>
        <div className="h-10 w-10 mx-auto rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center text-brand">
          <Brain className="h-5 w-5" />
        </div>
        <h3 className="text-sm font-semibold text-white">AI Prediction Unavailable</h3>
        <p className="text-xs text-gray-400 max-w-sm mx-auto">
          Insufficient historical validation bars or model staged. Training pipelines run point-in-time walk-forward validation.
        </p>
      </div>
    );
  }

  const isUp = prediction.direction.toUpperCase() === "UP";
  const isDown = prediction.direction.toUpperCase() === "DOWN";
  const probUp = Math.round(prediction.probability_up * 100);
  const probDown = Math.round((prediction.probability_down || 1 - prediction.probability_up) * 100);
  const expReturn = prediction.expected_return_pct;

  // ─────────────────────────────────────────────────────────
  // Action Verdict Logic (Buy / Hold / Avoid)
  // ─────────────────────────────────────────────────────────
  let verdict: {
    label: string;
    sublabel: string;
    bg: string;
    border: string;
    text: string;
    badgeBg: string;
    badgeText: string;
    icon: any;
  };

  if (probUp >= 75 && expReturn >= 3.0) {
    verdict = {
      label: "STRONG BUY",
      sublabel: "High model confidence with strong positive return expectancy",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/40",
      text: "text-emerald-400",
      badgeBg: "bg-emerald-500 text-black font-extrabold",
      badgeText: "text-emerald-300",
      icon: TrendingUp,
    };
  } else if (probUp >= 58 && expReturn > 0.5) {
    verdict = {
      label: "BUY",
      sublabel: "Positive upward probability with favorable risk/reward ratio",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      text: "text-emerald-400",
      badgeBg: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40",
      badgeText: "text-emerald-300",
      icon: TrendingUp,
    };
  } else if (probDown >= 75 && expReturn <= -3.0) {
    verdict = {
      label: "STRONG AVOID / SELL",
      sublabel: "High downside probability with severe negative drift projected",
      bg: "bg-red-500/10",
      border: "border-red-500/40",
      text: "text-red-400",
      badgeBg: "bg-red-500 text-white font-extrabold",
      badgeText: "text-red-300",
      icon: TrendingDown,
    };
  } else if (probDown >= 58 || expReturn < -0.5) {
    verdict = {
      label: "AVOID / REDUCE",
      sublabel: "Elevated downward risk factors or negative expected return",
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      text: "text-red-400",
      badgeBg: "bg-red-500/20 text-red-400 border border-red-500/40",
      badgeText: "text-red-300",
      icon: TrendingDown,
    };
  } else {
    verdict = {
      label: "HOLD / NEUTRAL",
      sublabel: "Indecisive directional probability or balanced risk/reward",
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
      text: "text-amber-400",
      badgeBg: "bg-amber-500/20 text-amber-300 border border-amber-500/40",
      badgeText: "text-amber-300",
      icon: Minus,
    };
  }

  // ─────────────────────────────────────────────────────────
  // Investment Profit Calculations
  // ─────────────────────────────────────────────────────────
  const validAmount = isNaN(investmentAmount) || investmentAmount <= 0 ? 0 : investmentAmount;
  const estimatedProfit = validAmount * (expReturn / 100);
  const totalProjectedValue = validAmount + estimatedProfit;
  const lowerBoundProfit = validAmount * (prediction.lower_bound_pct / 100);
  const upperBoundProfit = validAmount * (prediction.upper_bound_pct / 100);
  const isProfitPositive = estimatedProfit >= 0;

  // ─────────────────────────────────────────────────────────
  // Key Reasons & Drivers
  // ─────────────────────────────────────────────────────────
  const positiveDrivers = (prediction.top_positive_features && prediction.top_positive_features.length > 0)
    ? prediction.top_positive_features.slice(0, 3).map((f: any) => typeof f === "string" ? f : f.feature_name || f.feature || "Bullish Momentum")
    : [
        "Favorable technical trend and multi-timeframe moving average alignment",
        "Expanding trading volume supporting upside price action",
        "Conformal interval indicates positive baseline expected return",
      ];

  const negativeDrivers = (prediction.top_negative_features && prediction.top_negative_features.length > 0)
    ? prediction.top_negative_features.slice(0, 3).map((f: any) => typeof f === "string" ? f : f.feature_name || f.feature || "Volatile Market")
    : [
        `Market volatility regime (${(prediction.predicted_volatility * 100).toFixed(1)}% ann. vol)`,
        "Short-term resistance overhead and macro yield curve considerations",
      ];

  return (
    <div className={`bg-[#0B0F19] border border-border rounded-2xl p-4 sm:p-6 shadow-xl space-y-6 ${className}`}>
      {/* Header with Horizon Selector */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-brand/15 border border-brand/30 flex items-center justify-center text-brand">
            <Brain className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              StockSense AI Multi-Factor Prediction Engine
            </h3>
            <span className="text-[10px] text-gray-500 font-mono">
              Model: {prediction.model_version || "v2.4-LightGBM-Conformal"} · Point-in-Time Calibrated
            </span>
          </div>
        </div>

        {/* Horizon Tabs */}
        <div className="flex items-center gap-1 bg-background-elevated border border-border p-1 rounded-xl">
          {HORIZONS.map((h) => (
            <button
              key={h.id}
              onClick={() => handleHorizonClick(h.id)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition-all ${
                activeHorizon === h.id
                  ? "bg-brand text-white shadow-sm font-semibold"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {h.label}
            </button>
          ))}
        </div>
      </div>

      {/* 1. Primary Buy/Hold/Avoid Recommendation Banner */}
      <div className={`p-4 sm:p-5 rounded-2xl border ${verdict.bg} ${verdict.border} space-y-3`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={`h-11 w-11 rounded-xl flex items-center justify-center font-bold shadow-inner ${verdict.badgeBg}`}>
              <verdict.icon className="h-6 w-6" />
            </div>
            <div>
              <div className="text-[10px] uppercase font-bold tracking-wider text-gray-400">
                AI Recommendation ({activeHorizon.toUpperCase()} Horizon)
              </div>
              <div className={`text-xl sm:text-2xl font-extrabold tracking-tight ${verdict.text}`}>
                {verdict.label}
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-[10px] text-gray-400 uppercase font-mono">Expected Return</div>
            <div className={`text-xl font-mono font-bold ${expReturn >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {formatPercent(expReturn, true, 2)}
            </div>
          </div>
        </div>
        <p className="text-xs text-gray-300 leading-relaxed font-sans border-t border-white/5 pt-2">
          {verdict.sublabel}
        </p>
      </div>

      {/* 2. Interactive Profit & Returns Calculator */}
      <div className="bg-[#0E1422] border border-border/80 rounded-2xl p-4 sm:p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/40 pb-3">
          <div className="flex items-center gap-2">
            <Calculator className="h-4 w-4 text-brand" />
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Projected Investment Profit ({ticker})
            </h4>
          </div>
          <span className="text-[10px] text-gray-500 font-mono">
            {activeHorizon.toUpperCase()} Horizon Model Projection
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          {/* Investment Amount Input */}
          <div className="md:col-span-4 space-y-1.5">
            <label className="text-[11px] font-semibold text-gray-300 flex items-center justify-between">
              <span>If You Invest ({currency}):</span>
            </label>
            <div className="relative">
              <input
                type="number"
                value={investmentAmount || ""}
                onChange={(e) => setInvestmentAmount(Number(e.target.value))}
                min={1}
                step={currency === "PKR" ? 1000 : 100}
                className="w-full bg-[#12192C] border border-border rounded-xl px-3 py-2 text-sm text-white font-mono font-bold focus:border-brand focus:outline-none"
                placeholder="Amount"
              />
              <span className="absolute right-3 top-2 text-xs text-gray-500 font-mono font-bold">
                {currency}
              </span>
            </div>
            <div className="text-[10px] text-gray-500 flex gap-1.5">
              {[
                currency === "PKR" ? 25000 : 500,
                currency === "PKR" ? 100000 : 2500,
                currency === "PKR" ? 500000 : 10000,
              ].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setInvestmentAmount(val)}
                  className="px-1.5 py-0.5 rounded bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                >
                  {val.toLocaleString()}
                </button>
              ))}
            </div>
          </div>

          {/* Profit Output Cards */}
          <div className="md:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Estimated Profit */}
            <div className="bg-background-elevated border border-border p-3 rounded-xl space-y-1">
              <div className="text-[10px] text-gray-400 uppercase font-mono">Estimated Profit / Loss</div>
              <div className={`text-base sm:text-lg font-bold font-mono ${isProfitPositive ? "text-emerald-400" : "text-red-400"}`}>
                {isProfitPositive ? "+" : ""}{formatCurrency(estimatedProfit, currency, 2)}
              </div>
              <div className="text-[10px] text-gray-500 font-mono">
                {formatPercent(expReturn, true, 2)} ROI
              </div>
            </div>

            {/* Total Projected Value */}
            <div className="bg-background-elevated border border-border p-3 rounded-xl space-y-1">
              <div className="text-[10px] text-gray-400 uppercase font-mono">Projected Total Value</div>
              <div className="text-base sm:text-lg font-bold font-mono text-white">
                {formatCurrency(totalProjectedValue, currency, 2)}
              </div>
              <div className="text-[10px] text-gray-500 font-mono">
                At {activeHorizon} horizon
              </div>
            </div>

            {/* 80% CI Range */}
            <div className="bg-background-elevated border border-border p-3 rounded-xl space-y-1">
              <div className="text-[10px] text-gray-400 uppercase font-mono">80% Conformal Range</div>
              <div className="text-xs font-mono font-semibold text-gray-300 truncate">
                {formatCurrency(lowerBoundProfit, currency, 0)} → {formatCurrency(upperBoundProfit, currency, 0)}
              </div>
              <div className="text-[10px] text-gray-500 font-mono">
                {formatPercent(prediction.lower_bound_pct, true, 1)} to {formatPercent(prediction.upper_bound_pct, true, 1)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. "Why Buy / Why Avoid" AI Reasoning Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Positive Catalysts */}
        <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-4 space-y-2.5">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold font-sans">
            <CheckCircle2 className="h-4 w-4" />
            <span>Why Buy / Positive Catalysts</span>
          </div>
          <ul className="space-y-1.5 text-xs text-gray-300 font-sans">
            {positiveDrivers.map((driver: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-emerald-400 font-bold mt-0.5">+</span>
                <span className="leading-snug">{driver}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Risk Factors / Caution */}
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-4 space-y-2.5">
          <div className="flex items-center gap-2 text-amber-400 text-xs font-bold font-sans">
            <AlertTriangle className="h-4 w-4" />
            <span>Risk Factors &amp; Headwinds</span>
          </div>
          <ul className="space-y-1.5 text-xs text-gray-300 font-sans">
            {negativeDrivers.map((risk: string, idx: number) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-400 font-bold mt-0.5">-</span>
                <span className="leading-snug">{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* 4. Probability Bar & Regime Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-background-elevated/80 border border-border/60 rounded-xl p-3.5 text-xs font-mono">
        <div>
          <div className="text-[10px] text-gray-400 uppercase">Direction Probability</div>
          <div className="font-bold text-white mt-0.5">{probUp}% Up · {probDown}% Down</div>
          <div className="w-full h-1.5 rounded-full bg-red-500/20 overflow-hidden flex mt-1.5">
            <div className="h-full bg-emerald-500" style={{ width: `${probUp}%` }} />
            <div className="h-full bg-red-500" style={{ width: `${probDown}%` }} />
          </div>
        </div>

        <div>
          <div className="text-[10px] text-gray-400 uppercase">Model Confidence</div>
          <div className="font-bold text-white mt-0.5">{(prediction.confidence_score * 100).toFixed(0)}%</div>
          <div className="text-[10px] text-gray-500">
            {prediction.confidence_score >= 0.7 ? "High Confidence" : "Moderate Confidence"}
          </div>
        </div>

        <div>
          <div className="text-[10px] text-gray-400 uppercase">Predicted Volatility</div>
          <div className="font-bold text-white mt-0.5">{(prediction.predicted_volatility * 100).toFixed(1)}%</div>
          <div className="text-[10px] text-gray-500">Annualized Forecast</div>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-500/5 border border-amber-500/15 text-amber-300/90 text-xs font-sans">
        <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
        <span className="leading-relaxed">
          <strong>Mandatory Disclaimer:</strong> StockSense AI provides analytical and model-based probabilistic forecasts. Predictions and calculated returns are quantitative estimates, not guaranteed outcomes, and do not constitute personalized financial advice.
        </span>
      </div>
    </div>
  );
}

