"use client";

import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid
} from "recharts";
import { MonteCarloSimulationResult } from "@/lib/types";
import { formatCurrency, formatPercent } from "@/lib/formatting";

interface MonteCarloChartProps {
  result: MonteCarloSimulationResult;
  currency?: string;
  className?: string;
}

export function MonteCarloChart({ result, currency = "USD", className = "" }: MonteCarloChartProps) {
  const trajectories = result.sample_trajectories || [];
  if (trajectories.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500 text-xs">
        No simulation paths available. Run a Monte Carlo simulation.
      </div>
    );
  }

  const horizon = result.simulated_horizon_days || 252;
  const nPoints = trajectories[0]?.length || horizon;

  // Convert array of trajectories to recharts data points: [{day: 0, path0: 100000, path1: 100000, ...}]
  const data = [];
  for (let t = 0; t < nPoints; t++) {
    const pt: Record<string, number> = { day: t };
    trajectories.forEach((traj, idx) => {
      pt[`path_${idx}`] = Math.round(traj[t] || 0);
    });
    data.push(pt);
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Simulation KPI Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="bg-background-elevated border border-border p-3 rounded-xl">
          <div className="text-gray-400 text-[10px]">Expected Final Wealth</div>
          <div className="text-base font-bold text-white mt-0.5">
            {formatCurrency(result.mean_terminal_wealth, currency)}
          </div>
        </div>
        <div className="bg-background-elevated border border-border p-3 rounded-xl">
          <div className="text-gray-400 text-[10px]">95% Worst Case (P5)</div>
          <div className="text-base font-bold text-amber-400 mt-0.5">
            {formatCurrency(result.p5_terminal_wealth, currency)}
          </div>
        </div>
        <div className="bg-background-elevated border border-border p-3 rounded-xl">
          <div className="text-gray-400 text-[10px]">Probability of Profit</div>
          <div className="text-base font-bold text-emerald-400 mt-0.5">
            {formatPercent(result.probability_of_profit_pct, false)}
          </div>
        </div>
        <div className="bg-background-elevated border border-border p-3 rounded-xl">
          <div className="text-gray-400 text-[10px]">Probability of Ruin</div>
          <div className="text-base font-bold text-red-400 mt-0.5">
            {formatPercent(result.probability_of_ruin_pct, false)}
          </div>
        </div>
      </div>

      {/* Fan Chart */}
      <div className="h-64 w-full bg-[#0B0F19] border border-border rounded-2xl p-3">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1A2234" vertical={false} />
            <XAxis dataKey="day" stroke="#4A5568" tick={{ fontSize: 10 }} tickFormatter={(d) => `D+${d}`} />
            <YAxis stroke="#4A5568" tick={{ fontSize: 10 }} orientation="right" tickFormatter={(v) => formatCurrency(v, currency, 0)} />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const d = payload[0].payload;
                return (
                  <div className="bg-[#0E1422] border border-border rounded-xl p-2.5 text-xs font-mono">
                    <div className="text-gray-400 font-sans font-semibold border-b border-border/40 pb-1">
                      Trading Day +{d.day}
                    </div>
                    <div className="text-gray-300 pt-1">
                      Sample Simulated Wealth: {formatCurrency(d.path_0, currency)}
                    </div>
                  </div>
                );
              }}
            />
            {trajectories.map((_, idx) => (
              <Line
                key={`path_${idx}`}
                type="monotone"
                dataKey={`path_${idx}`}
                stroke={idx === 0 ? "#38bdf8" : "#3b82f6"}
                strokeWidth={idx === 0 ? 2 : 1}
                opacity={idx === 0 ? 0.9 : 0.25}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="text-[10px] text-gray-500 italic text-center">
        Monte Carlo paths generated via random block-bootstrapping over {result.iterations} iterations. Past performance does not guarantee future results.
      </div>
    </div>
  );
}
