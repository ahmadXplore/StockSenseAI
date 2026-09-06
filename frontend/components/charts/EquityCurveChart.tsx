"use client";

import {
  ResponsiveContainer, ComposedChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, Area
} from "recharts";
import { EquityCurvePoint } from "@/lib/types";
import { formatCurrency, formatPercent, formatDate } from "@/lib/formatting";

interface EquityCurveChartProps {
  data: EquityCurvePoint[];
  currency?: string;
  className?: string;
}

export function EquityCurveChart({ data, currency = "USD", className = "" }: EquityCurveChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 text-xs">
        No equity curve data available.
      </div>
    );
  }

  const initialVal = data[0]?.portfolio_value || 100000;
  const finalVal = data[data.length - 1]?.portfolio_value || initialVal;
  const isProfit = finalVal >= initialVal;
  const strokeColor = isProfit ? "#10b981" : "#ef4444";

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Portfolio Value & Benchmark */}
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
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
              stroke="#4A5568"
              tick={{ fontSize: 10 }}
              orientation="right"
              tickFormatter={(v) => formatCurrency(v, currency, 0)}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload as EquityCurvePoint;
                return (
                  <div className="bg-[#0E1422] border border-border rounded-xl p-3 shadow-2xl text-xs space-y-1 font-mono">
                    <div className="text-gray-400 font-sans font-semibold border-b border-border/50 pb-1">
                      {formatDate(d.date)}
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-400">Portfolio:</span>
                      <span className="text-white font-bold">{formatCurrency(d.portfolio_value, currency)}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-400">Return:</span>
                      <span className={d.cumulative_return_pct >= 0 ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                        {formatPercent(d.cumulative_return_pct)}
                      </span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-400">Drawdown:</span>
                      <span className="text-red-400">-{(d.drawdown_pct ?? 0).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-400">Positions:</span>
                      <span className="text-gray-300">{d.number_of_positions ?? 0}</span>
                    </div>
                  </div>
                );
              }}
            />
            <Area type="monotone" dataKey="portfolio_value" stroke={strokeColor} strokeWidth={2} fill="url(#equityGrad)" />
            {data[0]?.benchmark_value && (
              <Line type="monotone" dataKey="benchmark_value" stroke="#64748b" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Drawdown Curve */}
      <div className="h-20 w-full border-t border-border/40 pt-2">
        <div className="text-[10px] font-mono text-red-400 font-semibold mb-1">Underwater Drawdown (%)</div>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
            <YAxis domain={["dataMin", 0]} stroke="#4A5568" tick={{ fontSize: 9 }} orientation="right" tickFormatter={(v) => `-${(v ?? 0).toFixed(0)}%`} />
            <Area type="monotone" dataKey="drawdown_pct" stroke="#ef4444" strokeWidth={1} fill="#ef4444" fillOpacity={0.2} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
