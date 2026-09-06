"use client";

import { formatPercent } from "@/lib/formatting";

interface MonthlyHeatmapProps {
  heatmap: Record<string, Record<string, number>>; // {"2024": {"01": 2.4, "02": -1.2, ...}}
  yearly?: Record<string, number>;
  className?: string;
}

const MONTHS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"];
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function MonthlyHeatmap({ heatmap, yearly = {}, className = "" }: MonthlyHeatmapProps) {
  const years = Object.keys(heatmap || {}).sort().reverse();

  if (years.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-gray-500 text-xs">
        No monthly returns available yet.
      </div>
    );
  }

  const getColorClass = (val: number | undefined) => {
    if (val === undefined) return "bg-white/[0.02] text-gray-600";
    if (val > 5) return "bg-emerald-500/40 text-emerald-100 font-bold";
    if (val > 2) return "bg-emerald-500/25 text-emerald-200 font-semibold";
    if (val > 0) return "bg-emerald-500/10 text-emerald-300";
    if (val === 0) return "bg-white/5 text-gray-400";
    if (val > -2) return "bg-red-500/10 text-red-300";
    if (val > -5) return "bg-red-500/25 text-red-200 font-semibold";
    return "bg-red-500/40 text-red-100 font-bold";
  };

  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full text-xs font-mono border-collapse">
        <thead>
          <tr className="border-b border-border/60 text-gray-400 text-[10px] uppercase">
            <th className="py-2 px-2 text-left">Year</th>
            {MONTH_NAMES.map((m) => (
              <th key={m} className="py-2 px-1 text-center font-normal">{m}</th>
            ))}
            <th className="py-2 px-2 text-right font-bold text-gray-300">YTD</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/20">
          {years.map((year) => {
            const months = heatmap[year] || {};
            const ytd = yearly[year];
            return (
              <tr key={year} className="hover:bg-white/[0.02]">
                <td className="py-2 px-2 font-bold text-white text-left">{year}</td>
                {MONTHS.map((m) => {
                  const val = months[m];
                  return (
                    <td key={m} className="p-0.5 text-center">
                      <div
                        className={`py-1.5 px-1 rounded text-[10px] transition-all ${getColorClass(val)}`}
                        title={val !== undefined ? `${year}-${m}: ${formatPercent(val)}` : "No data"}
                      >
                        {val !== undefined ? formatPercent(val, true, 1) : "—"}
                      </div>
                    </td>
                  );
                })}
                <td className="py-2 px-2 text-right font-bold">
                  {ytd !== undefined ? (
                    <span className={ytd >= 0 ? "text-emerald-400" : "text-red-400"}>
                      {formatPercent(ytd, true, 1)}
                    </span>
                  ) : (
                    "—"
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
