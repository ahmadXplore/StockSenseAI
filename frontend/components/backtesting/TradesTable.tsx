"use client";

import { useState } from "react";
import { TradeRecord } from "@/lib/types";
import { formatCurrency, formatPercent, formatDate } from "@/lib/formatting";
import { ArrowUpRight, ArrowDownRight, Filter, ChevronLeft, ChevronRight } from "lucide-react";

interface TradesTableProps {
  trades: TradeRecord[];
  currency?: string;
  className?: string;
}

export function TradesTable({ trades, currency = "USD", className = "" }: TradesTableProps) {
  const [filterSide, setFilterSide] = useState<string>("ALL");
  const [filterPnl, setFilterPnl] = useState<string>("ALL");
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const filtered = trades.filter((t) => {
    if (filterSide !== "ALL" && t.side !== filterSide) return false;
    if (filterPnl === "WIN" && t.net_pnl <= 0) return false;
    if (filterPnl === "LOSS" && t.net_pnl >= 0) return false;
    return true;
  });

  const totalPages = Math.ceil(filtered.length / pageSize) || 1;
  const paginated = filtered.slice((page - 1) * pageSize, page * pageSize);

  if (!trades || trades.length === 0) {
    return (
      <div className="h-36 flex items-center justify-center text-gray-500 text-xs">
        No executed trades recorded in this backtest simulation.
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Table Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-gray-400 font-semibold flex items-center gap-1">
            <Filter className="h-3 w-3" /> Filter Trades:
          </span>
          <select
            value={filterPnl}
            onChange={(e) => {
              setFilterPnl(e.target.value);
              setPage(1);
            }}
            className="bg-[#0E1422] border border-border rounded-lg px-2 py-1 text-white text-xs"
          >
            <option value="ALL">All Outcomes</option>
            <option value="WIN">Winning Trades</option>
            <option value="LOSS">Losing Trades</option>
          </select>
          <select
            value={filterSide}
            onChange={(e) => {
              setFilterSide(e.target.value);
              setPage(1);
            }}
            className="bg-[#0E1422] border border-border rounded-lg px-2 py-1 text-white text-xs"
          >
            <option value="ALL">All Sides</option>
            <option value="BUY">Long Trades</option>
            <option value="SELL_SHORT">Short Trades</option>
          </select>
        </div>

        <div className="text-gray-500 font-mono text-[11px]">
          Showing {paginated.length} of {filtered.length} trades
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-border/60 rounded-xl">
        <table className="w-full text-xs font-mono text-left border-collapse">
          <thead>
            <tr className="bg-background-elevated border-b border-border/60 text-gray-400 text-[10px] uppercase">
              <th className="py-2.5 px-3">Entry Date</th>
              <th className="py-2.5 px-3">Security</th>
              <th className="py-2.5 px-3">Side</th>
              <th className="py-2.5 px-3 text-right">Shares</th>
              <th className="py-2.5 px-3 text-right">Entry</th>
              <th className="py-2.5 px-3">Exit Date</th>
              <th className="py-2.5 px-3 text-right">Exit</th>
              <th className="py-2.5 px-3 text-right">Net P&L</th>
              <th className="py-2.5 px-3 text-right">Return</th>
              <th className="py-2.5 px-3">Exit Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/20">
            {paginated.map((t) => {
              const isWin = t.net_pnl > 0;
              return (
                <tr key={t.trade_id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-2.5 px-3 text-gray-400">{t.entry_date}</td>
                  <td className="py-2.5 px-3 font-bold text-white">
                    <span>{t.ticker}</span>
                    <span className="text-[9px] text-gray-500 block">{t.market_code}</span>
                  </td>
                  <td className="py-2.5 px-3">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      t.side === "BUY" ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                    }`}>
                      {t.side}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right text-gray-300">{(t.shares ?? 0).toFixed(1)}</td>
                  <td className="py-2.5 px-3 text-right text-gray-300">{formatCurrency(t.entry_price, t.native_currency || currency)}</td>
                  <td className="py-2.5 px-3 text-gray-400">{t.exit_date}</td>
                  <td className="py-2.5 px-3 text-right text-gray-300">{formatCurrency(t.exit_price, t.native_currency || currency)}</td>
                  <td className={`py-2.5 px-3 text-right font-bold ${isWin ? "text-emerald-400" : "text-red-400"}`}>
                    {formatCurrency(t.net_pnl, t.native_currency || currency)}
                  </td>
                  <td className={`py-2.5 px-3 text-right font-bold ${isWin ? "text-emerald-400" : "text-red-400"}`}>
                    {formatPercent(t.return_pct)}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="text-[10px] text-gray-400 bg-white/5 px-2 py-0.5 rounded">
                      {t.exit_reason?.replace(/_/g, " ")}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 text-xs">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 rounded-lg bg-background-elevated border border-border text-gray-400 hover:text-white disabled:opacity-40 flex items-center gap-1"
          >
            <ChevronLeft className="h-3 w-3" /> Previous
          </button>
          <span className="text-gray-500 font-mono text-[11px]">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 rounded-lg bg-background-elevated border border-border text-gray-400 hover:text-white disabled:opacity-40 flex items-center gap-1"
          >
            Next <ChevronRight className="h-3 w-3" />
          </button>
        </div>
      )}
    </div>
  );
}
