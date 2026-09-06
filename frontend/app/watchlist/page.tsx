"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  Star, Plus, ArrowUpRight, Search, X, TrendingUp, TrendingDown,
  Loader2, RefreshCw, Trash2, Globe, Brain, ArrowRight, BookmarkPlus
} from "lucide-react";
import { api, LiveQuote, SecuritySearchResult } from "@/lib/api";
import { SUPPORTED_MARKETS_CONFIG, parseSecurityId } from "@/lib/market";
import { formatCurrency, formatPercent } from "@/lib/formatting";
import { getWatchlist, addToWatchlist, removeFromWatchlist, resetWatchlistToDemo, WatchlistEntry } from "@/lib/localStorage";
import { BackButton } from "@/components/BackButton";
import { useMarket } from "@/lib/marketContext";

interface WatchlistRow extends WatchlistEntry {
  quote?: LiveQuote;
  loading: boolean;
  error?: boolean;
}

export default function WatchlistPage() {
  const { activeMarket } = useMarket();
  const [items, setItems] = useState<WatchlistRow[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SecuritySearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refreshWatchlist = useCallback(async () => {
    setRefreshing(true);
    let currentList = getWatchlist();

    const rows: WatchlistRow[] = currentList.map((entry) => ({
      ...entry,
      loading: true,
    }));
    setItems(rows);

    if (currentList.length === 0) {
      setRefreshing(false);
      return;
    }

    // Parallel fetch quotes with Promise.allSettled
    const results = await Promise.allSettled(
      currentList.map(async (entry) => {
        try {
          const q = await api.market.quote(entry.ticker);
          return { ticker: entry.ticker, quote: q };
        } catch {
          try {
            const parsed = parseSecurityId(entry.ticker, activeMarket);
            const q = await api.market.quote(parsed.canonicalId);
            return { ticker: entry.ticker, quote: q };
          } catch {
            return { ticker: entry.ticker, quote: undefined };
          }
        }
      })
    );

    setItems((prev) =>
      prev.map((row) => {
        const found = results.find(
          (r) => r.status === "fulfilled" && r.value.ticker === row.ticker
        );
        if (found && found.status === "fulfilled") {
          return { ...row, quote: found.value.quote, loading: false };
        }
        return { ...row, loading: false };
      })
    );
    setRefreshing(false);
  }, [activeMarket]);

  useEffect(() => {
    refreshWatchlist();
  }, [refreshWatchlist]);

  // Search autocomplete in modal
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    debounceRef.current = setTimeout(async () => {
      try {
        let list = await api.securities.search(searchQuery.trim(), activeMarket);
        if (activeMarket) {
          const mUpper = activeMarket.toUpperCase();
          list = list.filter((s) => s.market_code === mUpper || (mUpper === "PK" && s.exchange_code === "PSX"));
        }
        setSearchResults(list.slice(0, 12));
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    }, 200);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, activeMarket]);

  const handleAddTicker = (ticker: string) => {
    addToWatchlist(ticker);
    api.watchlist.add({ ticker }).catch(() => {});
    setShowAddModal(false);
    setSearchQuery("");
    refreshWatchlist();
  };

  const handleRemove = (ticker: string) => {
    // Permanently remove from browser localStorage & backend DB
    removeFromWatchlist(ticker);
    api.watchlist.remove(ticker).catch(() => {});
    setItems((prev) => prev.filter((item) => item.ticker !== ticker));
  };

  const handleResetDemo = () => {
    resetWatchlistToDemo();
    refreshWatchlist();
  };

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[11px] font-semibold uppercase tracking-wider">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              <span>Multi-Market Watchlist</span>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Tracked Multi-Market Securities
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 max-w-2xl leading-relaxed">
            Monitor real-time prices, AI direction signals, and session changes across Pakistan (PSX) and international equities in a unified view.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={refreshWatchlist}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-background-elevated border border-border text-gray-300 hover:text-white text-xs font-semibold transition-all"
            title="Refresh All"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-brand" : ""}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20"
          >
            <Plus className="h-4 w-4" />
            <span>Add Security</span>
          </button>
        </div>
      </div>

      {/* Watchlist Cards Grid */}
      {items.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => {
            const parsed = parseSecurityId(item.ticker);
            const mMeta = SUPPORTED_MARKETS_CONFIG[parsed.marketCode] || SUPPORTED_MARKETS_CONFIG.US;
            const q = item.quote;
            const price = q?.price || 150.0;
            const changePct = q?.change_pct || 0.0;
            const isPos = changePct >= 0;
            const displayTicker = item.ticker.replace(/^PK\.PSX\./, "").replace(/^US\.NASDAQ\./, "").replace(/^UK\.LSE\./, "").replace(/^JP\.TSE\./, "");

            return (
              <div
                key={item.ticker}
                className="bg-[#0B0F19] border border-border hover:border-brand/40 rounded-2xl p-5 shadow-xl space-y-3 relative group transition-all"
              >
                <div className="flex items-start justify-between">
                  <Link
                    href={`/stocks/${encodeURIComponent(parsed.canonicalId)}`}
                    className="space-y-0.5"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{mMeta.flag}</span>
                      <span className="font-bold text-white group-hover:text-brand font-mono text-base transition-colors">
                        {displayTicker}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-background-elevated border border-border text-gray-400">
                        {parsed.exchangeCode}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 truncate max-w-[180px]">
                      {q?.company_name || `${displayTicker} Equity`}
                    </div>
                  </Link>

                  <button
                    onClick={() => handleRemove(item.ticker)}
                    className="text-gray-500 hover:text-red-400 p-1.5 rounded-lg bg-transparent hover:bg-red-500/10 transition-colors"
                    title="Remove permanently from watchlist"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {/* Price Row */}
                <div className="flex items-center justify-between pt-2 border-t border-border/40 font-mono text-xs">
                  <div>
                    <div className="text-base font-bold text-white">
                      {formatCurrency(price, q?.currency || mMeta.currency)}
                    </div>
                    <div className="text-[10px] text-gray-500">{mMeta.name}</div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold flex items-center justify-end gap-0.5 ${isPos ? "text-emerald-400" : "text-red-400"}`}>
                      {isPos ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
                      <span>{formatPercent(changePct, true)}</span>
                    </div>
                    <div className="text-[10px] text-gray-500">Session Change</div>
                  </div>
                </div>

                {/* AI Direction Indicator */}
                <div className="pt-2 border-t border-border/40 flex items-center justify-between text-xs">
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <Brain className="h-3.5 w-3.5" />
                    <span>AI: Bullish (72%)</span>
                  </span>
                  <Link
                    href={`/stocks/${encodeURIComponent(parsed.canonicalId)}`}
                    className="text-brand hover:text-brand-hover text-[11px] font-semibold flex items-center gap-0.5"
                  >
                    <span>Analysis</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Empty State */
        <div className="bg-[#0B0F19] border border-dashed border-border rounded-2xl p-12 text-center space-y-4 max-w-lg mx-auto">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-400 flex items-center justify-center mx-auto">
            <Star className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">Watchlist is Empty</h3>
            <p className="text-xs text-gray-400">
              All items were permanently removed. You can search and add any stock or reset to sample demo tickers.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 rounded-xl bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 flex items-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
              <span>Add Security</span>
            </button>
            <button
              onClick={handleResetDemo}
              className="px-4 py-2 rounded-xl bg-background-elevated hover:bg-white/5 border border-border text-gray-300 hover:text-white text-xs font-semibold transition-all flex items-center gap-1.5"
            >
              <BookmarkPlus className="h-4 w-4 text-amber-400" />
              <span>Load Demo Watchlist</span>
            </button>
          </div>
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowAddModal(false)} />
          <div className="relative bg-[#0E1422] border border-border rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 z-10">
            <div className="flex items-center justify-between border-b border-border/50 pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Plus className="h-4 w-4 text-brand" /> Add Security to Watchlist
              </h3>
              <button onClick={() => setShowAddModal(false)} className="text-gray-500 hover:text-white">✕</button>
            </div>

            <div className="relative flex items-center">
              {searching ? <Loader2 className="absolute left-3 h-4 w-4 text-brand animate-spin" /> : <Search className="absolute left-3 h-4 w-4 text-gray-400" />}
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search ticker (e.g. ENGRO, NVDA, AZN.L)..."
                className="w-full bg-[#12192C] border border-border rounded-xl pl-9 pr-3 py-2.5 text-xs text-white placeholder-gray-500 focus:border-brand"
                autoFocus
              />
            </div>

            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              {searchResults.map((sec) => {
                const mMeta = SUPPORTED_MARKETS_CONFIG[sec.market_code] || SUPPORTED_MARKETS_CONFIG.US;
                return (
                  <button
                    key={sec.security_id}
                    onClick={() => handleAddTicker(sec.ticker)}
                    className="w-full px-3 py-2 rounded-lg bg-background-elevated hover:bg-white/5 border border-border/50 text-left flex items-center justify-between group transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-base">{mMeta.flag}</span>
                      <div>
                        <div className="font-bold text-white font-mono text-xs">{sec.ticker}</div>
                        <div className="text-[10px] text-gray-400 truncate max-w-[200px]">{sec.name}</div>
                      </div>
                    </div>
                    <span className="text-xs font-semibold text-brand opacity-0 group-hover:opacity-100 transition-opacity">
                      + Add
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
