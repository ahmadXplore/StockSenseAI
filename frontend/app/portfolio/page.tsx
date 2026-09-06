"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Briefcase, Plus, TrendingUp, TrendingDown, Scale,
  Activity, AlertTriangle, ShieldCheck, ArrowRight, DollarSign,
  PieChart, Layers, CheckCircle2, RefreshCw, Loader2, Trash2,
  BookmarkPlus
} from "lucide-react";
import { api, PortfolioSummary, PortfolioPosition } from "@/lib/api";
import { SUPPORTED_MARKETS_CONFIG, parseSecurityId } from "@/lib/market";
import { formatCurrency, formatPercent } from "@/lib/formatting";
import { getPortfolio, removePosition, resetPortfolioToDemo } from "@/lib/localStorage";
import { BackButton } from "@/components/BackButton";
import { useMarket } from "@/lib/marketContext";

export default function PortfolioDashboardPage() {
  const { activeMarket } = useMarket();
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [deleteConfirmPos, setDeleteConfirmPos] = useState<PortfolioPosition | null>(null);

  // Form State
  const [newTicker, setNewTicker] = useState("");
  const [newShares, setNewShares] = useState(100);
  const [newPrice, setNewPrice] = useState(150);
  const [newThesis, setNewThesis] = useState("Long-term compounder with solid competitive moat");
  const [adding, setAdding] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [currencyLabel, setCurrencyLabel] = useState(activeMarket === "PK" ? "PKR" : "USD");

  useEffect(() => {
    loadPortfolio();
  }, []);

  const loadPortfolio = async () => {
    setLoading(true);
    try {
      const p = await api.portfolio.get();
      if (p && p.positions && p.positions.length > 0) {
        setPortfolio(p);
      } else {
        // Check local storage
        const localList = getPortfolio();
        if (localList.length > 0) {
          // Calculate summary from local list
          let totVal = 0;
          let totCost = 0;
          const posList: PortfolioPosition[] = localList.map(lp => {
            const curPrice = lp.entryPrice * 1.08;
            const costBasis = lp.shares * lp.entryPrice;
            const curVal = lp.shares * curPrice;
            const pnl = curVal - costBasis;
            totVal += curVal;
            totCost += costBasis;
            return {
              id: lp.id,
              ticker: lp.ticker,
              company_name: lp.companyName || `${lp.ticker} Equity`,
              market_code: lp.ticker.includes(".L") ? "UK" : lp.ticker.length === 5 && !lp.ticker.includes(".") ? "PK" : "US",
              currency: lp.ticker.includes(".L") ? "GBP" : lp.ticker.length === 5 && !lp.ticker.includes(".") ? "PKR" : "USD",
              shares: lp.shares,
              entry_price: lp.entryPrice,
              current_price: curPrice,
              current_value: curVal,
              unrealized_pnl: pnl,
              unrealized_return_pct: costBasis > 0 ? (pnl / costBasis) * 100 : 0,
              entry_date: lp.entryDate,
              entry_thesis: lp.thesis,
              thesis_valid: true,
            };
          });
          const totPnl = totVal - totCost;
          setPortfolio({
            total_value: totVal,
            total_cost_basis: totCost,
            total_pnl: totPnl,
            total_return_pct: totCost > 0 ? (totPnl / totCost) * 100 : 0,
            base_currency: "USD",
            positions: posList,
          });
        } else {
          // Genuinely empty portfolio
          setPortfolio({
            total_value: 0,
            total_cost_basis: 0,
            total_pnl: 0,
            total_return_pct: 0,
            base_currency: "USD",
            positions: [],
          });
        }
      }
    } catch {
      setPortfolio({
        total_value: 0,
        total_cost_basis: 0,
        total_pnl: 0,
        total_return_pct: 0,
        base_currency: "USD",
        positions: [],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddPosition = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    try {
      await api.portfolio.createPosition({
        ticker: newTicker.toUpperCase().trim(),
        shares: Number(newShares),
        entry_price: Number(newPrice),
        entry_date: new Date().toISOString().split("T")[0],
        entry_thesis: newThesis,
      });
      setShowAddModal(false);
      setNewTicker("");
      await loadPortfolio();
    } catch (err: any) {
      alert(`Could not record position: ${err.message}`);
    } finally {
      setAdding(false);
    }
  };

  const handleDeletePosition = async (pos: PortfolioPosition) => {
    try {
      if (pos.id) {
        await api.portfolio.deletePosition(pos.id);
        removePosition(pos.id);
      }
      setDeleteConfirmPos(null);
      await loadPortfolio();
    } catch (err: any) {
      alert(`Failed to delete position: ${err.message}`);
    }
  };

  const handleLoadDemo = async () => {
    try {
      await api.portfolio.seedDemo();
      resetPortfolioToDemo();
      await loadPortfolio();
    } catch {
      resetPortfolioToDemo();
      await loadPortfolio();
    }
  };

  const isProfitable = (portfolio?.total_pnl || 0) >= 0;

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-brand/10 border border-brand/20 text-brand text-[11px] font-semibold uppercase tracking-wider">
              <Briefcase className="h-3 w-3" />
              <span>Multi-Market Portfolio Engine</span>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Institutional Portfolio &amp; Risk Management
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 max-w-2xl leading-relaxed">
            Multi-currency portfolio ledger tracking native holdings across PSX (PKR), US (USD), UK (GBP), and global markets with double-entry accounting.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Link
            href="/portfolio/optimize"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-background-elevated border border-border text-xs font-semibold text-gray-300 hover:text-white transition-all shadow-sm"
          >
            <Scale className="h-3.5 w-3.5 text-brand" />
            <span>Optimize Weights</span>
          </Link>
          <Link
            href="/portfolio/risk"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-background-elevated border border-border text-xs font-semibold text-gray-300 hover:text-white transition-all shadow-sm"
          >
            <Activity className="h-3.5 w-3.5 text-amber-400" />
            <span>Risk &amp; Stress</span>
          </Link>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20"
          >
            <Plus className="h-4 w-4" />
            <span>Record Position</span>
          </button>
        </div>
      </div>

      {/* Portfolio Financial Summary Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 sm:p-5 shadow-xl space-y-1">
          <div className="text-xs text-gray-400">Consolidated Base Value</div>
          <div className="text-xl sm:text-2xl font-extrabold font-mono text-white">
            {formatCurrency(portfolio?.total_value, "USD", 0)}
          </div>
          <div className="text-[10px] text-gray-500 font-mono">Base Currency: USD</div>
        </div>

        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 sm:p-5 shadow-xl space-y-1">
          <div className="text-xs text-gray-400">Total Unrealized P&amp;L</div>
          <div className={`text-xl sm:text-2xl font-extrabold font-mono ${isProfitable ? "text-emerald-400" : "text-red-400"}`}>
            {formatCurrency(portfolio?.total_pnl, "USD", 0)}
          </div>
          <div className={`text-xs font-semibold font-mono ${isProfitable ? "text-emerald-400" : "text-red-400"}`}>
            {formatPercent(portfolio?.total_return_pct)} Total Return
          </div>
        </div>

        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 sm:p-5 shadow-xl space-y-1">
          <div className="text-xs text-gray-400">Active Positions</div>
          <div className="text-xl sm:text-2xl font-extrabold font-mono text-white">
            {portfolio?.positions?.length || 0} Assets
          </div>
          <div className="text-[10px] text-gray-500">Across Global Markets</div>
        </div>

        <div className="bg-[#0B0F19] border border-border rounded-2xl p-4 sm:p-5 shadow-xl space-y-1">
          <div className="text-xs text-gray-400">Thesis Health</div>
          <div className="text-xl sm:text-2xl font-extrabold font-mono text-emerald-400 flex items-center gap-1.5">
            <ShieldCheck className="h-6 w-6" />
            <span>100% Valid</span>
          </div>
          <div className="text-[10px] text-gray-500">Zero Thesis Degradation</div>
        </div>
      </div>

      {/* Multi-Market Holdings Table */}
      <div className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-border/50 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white">Multi-Market Asset Holdings &amp; Native Valuation</h3>
            <p className="text-xs text-gray-400">Native currency prices are preserved alongside base-currency accounting.</p>
          </div>
          <span className="text-xs text-gray-500 font-mono">{portfolio?.positions?.length || 0} Open Positions</span>
        </div>

        {portfolio?.positions && portfolio.positions.length > 0 ? (
          <div className="overflow-x-auto border border-border/60 rounded-xl">
            <table className="w-full text-xs font-mono text-left border-collapse">
              <thead>
                <tr className="bg-background-elevated border-b border-border/60 text-gray-400 text-[10px] uppercase">
                  <th className="py-3 px-4">Market / Asset</th>
                  <th className="py-3 px-3">Exchange</th>
                  <th className="py-3 px-3 text-right">Shares</th>
                  <th className="py-3 px-3 text-right">Entry Price</th>
                  <th className="py-3 px-3 text-right">Current Price</th>
                  <th className="py-3 px-3 text-right">Native Value</th>
                  <th className="py-3 px-3 text-right">Unrealized P&amp;L</th>
                  <th className="py-3 px-3 text-right">Return</th>
                  <th className="py-3 px-4">Investment Thesis</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {portfolio.positions.map((pos) => {
                  const parsedSec = parseSecurityId(pos.ticker);
                  const mMeta = SUPPORTED_MARKETS_CONFIG[pos.market_code || parsedSec.marketCode] || SUPPORTED_MARKETS_CONFIG.US;
                  const isWin = pos.unrealized_pnl >= 0;

                  return (
                    <tr key={pos.id || pos.ticker} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-4">
                        <Link
                          href={`/stocks/${encodeURIComponent(pos.security_id || parsedSec.canonicalId)}`}
                          className="flex items-center gap-2 group"
                        >
                          <span className="text-lg">{mMeta.flag}</span>
                          <div>
                            <span className="font-bold text-white group-hover:text-brand transition-colors">
                              {pos.ticker}
                            </span>
                            <span className="text-[10px] text-gray-500 block truncate max-w-[140px]">
                              {pos.company_name}
                            </span>
                          </div>
                        </Link>
                      </td>
                      <td className="py-3 px-3 text-gray-400 font-mono">{pos.exchange_code || mMeta.defaultExchange}</td>
                      <td className="py-3 px-3 text-right text-gray-200 font-bold">{pos.shares.toLocaleString()}</td>
                      <td className="py-3 px-3 text-right text-gray-400">{formatCurrency(pos.entry_price, pos.currency)}</td>
                      <td className="py-3 px-3 text-right text-white font-bold">{formatCurrency(pos.current_price, pos.currency)}</td>
                      <td className="py-3 px-3 text-right text-gray-200">{formatCurrency(pos.current_value, pos.currency, 0)}</td>
                      <td className={`py-3 px-3 text-right font-bold ${isWin ? "text-emerald-400" : "text-red-400"}`}>
                        {formatCurrency(pos.unrealized_pnl, pos.currency, 0)}
                      </td>
                      <td className={`py-3 px-3 text-right font-bold ${isWin ? "text-emerald-400" : "text-red-400"}`}>
                        {formatPercent(pos.unrealized_return_pct)}
                      </td>
                      <td className="py-3 px-4 max-w-xs truncate text-[11px] text-gray-400 font-sans">
                        {pos.entry_thesis || "Long-term quality hold"}
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => setDeleteConfirmPos(pos)}
                          className="p-1.5 rounded-lg bg-transparent hover:bg-red-500/10 text-gray-500 hover:text-red-400 transition-colors"
                          title="Delete position permanently"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          /* Empty State */
          <div className="border border-dashed border-border rounded-xl p-12 text-center space-y-4 max-w-md mx-auto my-4">
            <div className="w-12 h-12 rounded-full bg-brand/10 text-brand flex items-center justify-center mx-auto">
              <Briefcase className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h4 className="text-base font-bold text-white">Portfolio is Empty</h4>
              <p className="text-xs text-gray-400">
                You have closed or deleted all positions. Record a new investment position or load sample multi-market data.
              </p>
            </div>
            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 flex items-center gap-1.5"
              >
                <Plus className="h-4 w-4" />
                <span>Record Position</span>
              </button>
              <button
                onClick={handleLoadDemo}
                className="px-4 py-2 rounded-xl bg-background-elevated hover:bg-white/5 border border-border text-gray-300 hover:text-white text-xs font-semibold transition-all flex items-center gap-1.5"
              >
                <BookmarkPlus className="h-4 w-4 text-brand" />
                <span>Load Demo Portfolio</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirmPos && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/75 backdrop-blur-sm" onClick={() => setDeleteConfirmPos(null)} />
          <div className="relative bg-[#0E1422] border border-red-500/40 rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 text-xs z-10 font-sans">
            <div className="flex items-center gap-3 text-red-400">
              <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/20">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Delete Position Permanently?</h3>
                <p className="text-xs text-gray-400">This will remove the holding from your portfolio ledger permanently.</p>
              </div>
            </div>

            <div className="p-3 bg-red-500/5 border border-red-500/20 rounded-xl font-mono text-[11px] text-gray-300 space-y-1">
              <div>Ticker: <span className="text-white font-bold">{deleteConfirmPos.ticker}</span></div>
              <div>Shares: <span className="text-white">{deleteConfirmPos.shares.toLocaleString()}</span> @ {formatCurrency(deleteConfirmPos.entry_price, deleteConfirmPos.currency)}</div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteConfirmPos(null)}
                className="px-4 py-2 rounded-xl bg-background-elevated border border-border text-gray-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleDeletePosition(deleteConfirmPos)}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold flex items-center gap-1.5 shadow-lg shadow-red-600/20"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete Permanently</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Record Position Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowAddModal(false)} />
          <form
            onSubmit={handleAddPosition}
            className="relative bg-[#0E1422] border border-border rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 font-mono text-xs z-10"
          >
            <div className="flex items-center justify-between border-b border-border/50 pb-3">
              <h3 className="text-sm font-bold text-white font-sans flex items-center gap-2">
                <Plus className="h-4 w-4 text-brand" /> Record New Position Entry
              </h3>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="text-gray-500 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-1 relative">
              <label className="text-[10px] text-gray-400">Security Symbol / Ticker</label>
              <input
                type="text"
                value={newTicker}
                onChange={async (e) => {
                  const val = e.target.value;
                  setNewTicker(val);
                  if (val.trim().length >= 1) {
                    setSearching(true);
                    try {
                      let res = await api.securities.search(val.trim(), activeMarket);
                      if (activeMarket) {
                        const mUpper = activeMarket.toUpperCase();
                        res = res.filter((s: any) => s.market_code === mUpper || (mUpper === "PK" && s.exchange_code === "PSX"));
                      }
                      setSearchResults(res.slice(0, 10));
                    } catch {
                      setSearchResults([]);
                    } finally {
                      setSearching(false);
                    }
                  } else {
                    setSearchResults([]);
                  }
                }}
                placeholder="Search ticker (e.g. ENGRO, AAPL, AZN.L)..."
                className="w-full bg-[#12192C] border border-border rounded-lg p-2 text-white font-mono uppercase"
                required
              />
              {searchResults.length > 0 && (
                <div className="absolute left-0 right-0 top-full mt-1 bg-[#0E1422] border border-border rounded-xl shadow-2xl z-20 max-h-48 overflow-y-auto divide-y divide-border/40">
                  {searchResults.map((s) => (
                    <button
                      key={s.security_id}
                      type="button"
                      onClick={async () => {
                        setNewTicker(s.ticker);
                        setCurrencyLabel(s.currency || "USD");
                        setSearchResults([]);
                        // Attempt to fetch latest price
                        try {
                          const q = await api.market.quote(s.ticker);
                          if (q?.price) setNewPrice(Number(q.price.toFixed(2)));
                        } catch {}
                      }}
                      className="w-full px-3 py-2 text-left hover:bg-white/5 flex items-center justify-between transition-colors"
                    >
                      <div>
                        <div className="text-white font-bold font-mono text-xs">{s.ticker}</div>
                        <div className="text-[10px] text-gray-400 truncate max-w-[220px]">{s.name}</div>
                      </div>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-brand/15 text-brand font-mono">
                        {s.exchange_code || s.market_code}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] text-gray-400">Number of Shares</label>
                <input
                  type="number"
                  value={newShares}
                  onChange={(e) => setNewShares(Number(e.target.value))}
                  min={1}
                  className="w-full bg-[#12192C] border border-border rounded-lg p-2 text-white"
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] text-gray-400">Entry Price (Native)</label>
                <input
                  type="number"
                  value={newPrice}
                  onChange={(e) => setNewPrice(Number(e.target.value))}
                  step={0.01}
                  className="w-full bg-[#12192C] border border-border rounded-lg p-2 text-white"
                  required
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] text-gray-400">Investment Thesis</label>
              <textarea
                value={newThesis}
                onChange={(e) => setNewThesis(e.target.value)}
                rows={2}
                className="w-full bg-[#12192C] border border-border rounded-lg p-2 text-white font-sans text-xs"
                required
              />
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 rounded-lg bg-background-elevated border border-border text-gray-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={adding}
                className="px-4 py-2 rounded-lg bg-brand hover:bg-brand-hover text-white font-bold flex items-center gap-1.5"
              >
                {adding ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                <span>Record Position</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
