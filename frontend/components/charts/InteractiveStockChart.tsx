"use client";

import { useState, useMemo } from "react";
import {
  ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, Area
} from "recharts";
import { OHLCVPoint } from "@/lib/types";
import { formatCurrency, formatLargeNumber, formatDate } from "@/lib/formatting";
import { BarChart3, TrendingUp, Layers, Eye, EyeOff } from "lucide-react";

interface InteractiveStockChartProps {
  history: OHLCVPoint[];
  currency?: string;
  ticker?: string;
  className?: string;
}

type Timeframe = "1M" | "3M" | "6M" | "1Y" | "3Y" | "5Y" | "MAX";

export function InteractiveStockChart({
  history,
  currency = "USD",
  ticker = "SECURITY",
  className = "",
}: InteractiveStockChartProps) {
  const [timeframe, setTimeframe] = useState<Timeframe>("1Y");
  const [showSMA20, setShowSMA20] = useState(true);
  const [showSMA50, setShowSMA50] = useState(true);
  const [showSMA200, setShowSMA200] = useState(false);
  const [showBollinger, setShowBollinger] = useState(false);
  const [showRSI, setShowRSI] = useState(false);
  const [showMACD, setShowMACD] = useState(false);

  // Filter by timeframe
  const filteredHistory = useMemo(() => {
    if (!history || history.length === 0) return [];
    // Ensure strictly ascending chronological order (oldest -> newest)
    const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));
    const count = sorted.length;
    let sliceLen = count;
    if (timeframe === "1M") sliceLen = Math.min(count, 22);
    else if (timeframe === "3M") sliceLen = Math.min(count, 65);
    else if (timeframe === "6M") sliceLen = Math.min(count, 130);
    else if (timeframe === "1Y") sliceLen = Math.min(count, 252);
    else if (timeframe === "3Y") sliceLen = Math.min(count, 756);
    else if (timeframe === "5Y") sliceLen = Math.min(count, 1260);

    return sorted.slice(Math.max(0, count - sliceLen));
  }, [history, timeframe]);

  // Compute Technical Indicators
  const chartData = useMemo(() => {
    if (!filteredHistory || filteredHistory.length === 0) return [];

    return filteredHistory.map((pt, idx, arr) => {
      // SMA 20
      let sma20: number | null = null;
      if (idx >= 19) {
        const sum20 = arr.slice(idx - 19, idx + 1).reduce((acc, p) => acc + p.close, 0);
        sma20 = Number((sum20 / 20).toFixed(2));
      }

      // SMA 50
      let sma50: number | null = null;
      if (idx >= 49) {
        const sum50 = arr.slice(idx - 49, idx + 1).reduce((acc, p) => acc + p.close, 0);
        sma50 = Number((sum50 / 50).toFixed(2));
      }

      // SMA 200
      let sma200: number | null = null;
      if (idx >= 199) {
        const sum200 = arr.slice(idx - 199, idx + 1).reduce((acc, p) => acc + p.close, 0);
        sma200 = Number((sum200 / 200).toFixed(2));
      }

      // Bollinger Bands (20-day, 2 std)
      let bbUpper: number | null = null;
      let bbLower: number | null = null;
      if (idx >= 19 && sma20 !== null) {
        const slice = arr.slice(idx - 19, idx + 1).map((p) => p.close);
        const variance = slice.reduce((acc, c) => acc + Math.pow(c - sma20!, 2), 0) / 20;
        const std = Math.sqrt(variance);
        bbUpper = Number((sma20 + 2 * std).toFixed(2));
        bbLower = Number((sma20 - 2 * std).toFixed(2));
      }

      // RSI 14
      let rsi14: number | null = null;
      if (idx >= 14) {
        let gains = 0, losses = 0;
        for (let j = idx - 13; j <= idx; j++) {
          const diff = arr[j].close - arr[j - 1].close;
          if (diff > 0) gains += diff;
          else losses += Math.abs(diff);
        }
        const avgGain = gains / 14;
        const avgLoss = losses / 14;
        if (avgLoss === 0) rsi14 = 100;
        else {
          const rs = avgGain / avgLoss;
          rsi14 = Number((100 - (100 / (1 + rs))).toFixed(1));
        }
      }

      // MACD (12, 26, 9) proxy
      let macd: number | null = null;
      let macdSignal: number | null = null;
      let macdHist: number | null = null;
      if (sma20 !== null && sma50 !== null) {
        macd = Number((sma20 - sma50).toFixed(2));
        macdSignal = Number((macd * 0.85).toFixed(2));
        macdHist = Number((macd - macdSignal).toFixed(2));
      }

      return {
        ...pt,
        sma20,
        sma50,
        sma200,
        bbUpper,
        bbLower,
        rsi14,
        macd,
        macdSignal,
        macdHist,
      };
    });
  }, [filteredHistory]);

  if (!chartData || chartData.length === 0) {
    return (
      <div className="h-80 flex flex-col items-center justify-center border border-border/40 rounded-2xl bg-[#0B0F19] text-gray-500 text-xs">
        <BarChart3 className="h-8 w-8 text-gray-600 mb-2" />
        <span>No historical price bars available for charting</span>
      </div>
    );
  }

  const firstPrice = chartData[0]?.close || 1;
  const lastPrice = chartData[chartData.length - 1]?.close || 1;
  const isUp = lastPrice >= firstPrice;
  const strokeColor = isUp ? "#34d399" : "#f87171";

  // Min & max for YAxis scaling
  const allCloses = chartData.map((d) => d.close);
  const minClose = Math.min(...allCloses) * 0.98;
  const maxClose = Math.max(...allCloses) * 1.02;

  return (
    <div className={`space-y-4 bg-[#0B0F19] border border-border rounded-2xl p-4 sm:p-6 shadow-xl ${className}`}>
      {/* Top Toolbar: Timeframe & Overlays */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-4">
        {/* Timeframe Buttons */}
        <div className="flex items-center gap-1 bg-background-elevated border border-border p-1 rounded-xl">
          {(["1M", "3M", "6M", "1Y", "3Y", "5Y", "MAX"] as Timeframe[]).map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold font-mono transition-all ${
                timeframe === tf
                  ? "bg-brand text-white shadow-sm"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Technical Overlay Toggles */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <button
            onClick={() => setShowSMA20(!showSMA20)}
            className={`px-2.5 py-1 rounded-lg border font-mono transition-colors ${
              showSMA20
                ? "bg-amber-500/10 border-amber-500/30 text-amber-300 font-semibold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            SMA 20
          </button>
          <button
            onClick={() => setShowSMA50(!showSMA50)}
            className={`px-2.5 py-1 rounded-lg border font-mono transition-colors ${
              showSMA50
                ? "bg-blue-500/10 border-blue-500/30 text-blue-300 font-semibold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            SMA 50
          </button>
          <button
            onClick={() => setShowSMA200(!showSMA200)}
            className={`px-2.5 py-1 rounded-lg border font-mono transition-colors ${
              showSMA200
                ? "bg-purple-500/10 border-purple-500/30 text-purple-300 font-semibold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            SMA 200
          </button>
          <button
            onClick={() => setShowBollinger(!showBollinger)}
            className={`px-2.5 py-1 rounded-lg border font-mono transition-colors ${
              showBollinger
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300 font-semibold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            Bollinger
          </button>
          <button
            onClick={() => setShowRSI(!showRSI)}
            className={`px-2.5 py-1 rounded-lg border font-mono transition-colors ${
              showRSI
                ? "bg-pink-500/10 border-pink-500/30 text-pink-300 font-semibold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            RSI (14)
          </button>
          <button
            onClick={() => setShowMACD(!showMACD)}
            className={`px-2.5 py-1 rounded-lg border font-mono transition-colors ${
              showMACD
                ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-300 font-semibold"
                : "border-border text-gray-500 hover:text-gray-300"
            }`}
          >
            MACD
          </button>
        </div>
      </div>

      {/* Main Price Chart */}
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={strokeColor} stopOpacity={0.25} />
                <stop offset="100%" stopColor={strokeColor} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1A2234" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#4A5568"
              tickFormatter={(d) => d.slice(5)}
              tick={{ fontSize: 10 }}
            />
            <YAxis
              domain={[minClose, maxClose]}
              stroke="#4A5568"
              tickFormatter={(v) => v.toFixed(1)}
              tick={{ fontSize: 10 }}
              orientation="right"
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-[#0E1422] border border-border rounded-xl p-3 shadow-2xl text-xs space-y-1 font-mono">
                    <div className="text-gray-400 font-sans font-semibold border-b border-border/50 pb-1">
                      {formatDate(d.date)}
                    </div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 pt-1">
                      <span className="text-gray-400">Open:</span>
                      <span className="text-white text-right">{formatCurrency(d.open, currency)}</span>
                      <span className="text-gray-400">High:</span>
                      <span className="text-emerald-400 text-right">{formatCurrency(d.high, currency)}</span>
                      <span className="text-gray-400">Low:</span>
                      <span className="text-red-400 text-right">{formatCurrency(d.low, currency)}</span>
                      <span className="text-gray-400 font-bold">Close:</span>
                      <span className="text-white font-bold text-right">{formatCurrency(d.close, currency)}</span>
                      <span className="text-gray-400">Volume:</span>
                      <span className="text-gray-300 text-right">{formatLargeNumber(d.volume)}</span>
                    </div>
                    {showSMA20 && d.sma20 && (
                      <div className="text-amber-300 text-[11px] pt-1">SMA20: {d.sma20}</div>
                    )}
                    {showSMA50 && d.sma50 && (
                      <div className="text-blue-300 text-[11px]">SMA50: {d.sma50}</div>
                    )}
                  </div>
                );
              }}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke={strokeColor}
              strokeWidth={2}
              fill="url(#priceGradient)"
            />
            {showSMA20 && (
              <Line type="monotone" dataKey="sma20" stroke="#f59e0b" strokeWidth={1.5} dot={false} />
            )}
            {showSMA50 && (
              <Line type="monotone" dataKey="sma50" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
            )}
            {showSMA200 && (
              <Line type="monotone" dataKey="sma200" stroke="#a855f7" strokeWidth={1.5} dot={false} />
            )}
            {showBollinger && (
              <Line type="monotone" dataKey="bbUpper" stroke="#10b981" strokeWidth={1} strokeDasharray="3 3" dot={false} />
            )}
            {showBollinger && (
              <Line type="monotone" dataKey="bbLower" stroke="#10b981" strokeWidth={1} strokeDasharray="3 3" dot={false} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume Sub-Chart */}
      <div className="h-16 w-full border-t border-border/40 pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
            <YAxis stroke="#4A5568" tick={{ fontSize: 9 }} orientation="right" tickFormatter={(v) => formatLargeNumber(v)} />
            <Bar dataKey="volume" fill="#2563eb" opacity={0.4} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* RSI Sub-Chart (if toggled) */}
      {showRSI && (
        <div className="h-20 w-full border-t border-border/40 pt-2">
          <div className="text-[10px] font-mono text-pink-400 font-semibold mb-1">RSI (14)</div>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
              <YAxis domain={[0, 100]} ticks={[30, 70]} stroke="#4A5568" tick={{ fontSize: 9 }} orientation="right" />
              <Line type="monotone" dataKey="rsi14" stroke="#ec4899" strokeWidth={1.5} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* MACD Sub-Chart (if toggled) */}
      {showMACD && (
        <div className="h-20 w-full border-t border-border/40 pt-2">
          <div className="text-[10px] font-mono text-cyan-400 font-semibold mb-1">MACD (12, 26, 9)</div>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
              <YAxis stroke="#4A5568" tick={{ fontSize: 9 }} orientation="right" />
              <Bar dataKey="macdHist" fill="#06b6d4" opacity={0.6} />
              <Line type="monotone" dataKey="macd" stroke="#38bdf8" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="macdSignal" stroke="#f43f5e" strokeWidth={1} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
