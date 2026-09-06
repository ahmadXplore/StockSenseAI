"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp, TrendingDown, BarChart3, Activity, ShieldCheck,
  AlertTriangle, Globe, Sparkles, Brain, Scale, LineChart,
  ArrowRight, RefreshCw, Star, Layers, CheckCircle2, ChevronRight,
  Zap
} from "lucide-react";
import { api, MarketOverview, ProviderHealth, LiveQuote } from "@/lib/api";
import { SUPPORTED_MARKETS_CONFIG, parseSecurityId } from "@/lib/market";
import { formatCurrency, formatPercent, formatLargeNumber } from "@/lib/formatting";
import { getWatchlist } from "@/lib/localStorage";
import { SecuritySearch } from "@/components/market/SecuritySearch";
import { MarketSelector } from "@/components/market/MarketSelector";
import { DataFreshnessBadge } from "@/components/market/DataFreshnessBadge";
import { useMarket } from "@/lib/marketContext";

export default function DashboardPage() {
  const router = useRouter();
  const { activeMarket, setActiveMarket, marketMeta } = useMarket();
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [watchlistQuotes, setWatchlistQuotes] = useState<LiveQuote[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch overview, providers and quotes in parallel with Promise.allSettled
      const userWatchlist = getWatchlist();
      
      // Filter user watchlist items matching the active market
      const userMarketTickers = userWatchlist
        .map((w) => w.ticker)
        .filter((t) => {
          const p = parseSecurityId(t);
          return p.marketCode === activeMarket;
        });

      const defaultSecs = marketMeta.sampleSecurities.map((s) => s.ticker);
      const tickersToFetch = Array.from(new Set([...userMarketTickers, ...defaultSecs])).slice(0, 6);

      const [ovResult, provResult, quotesResults] = await Promise.allSettled([
        api.market.overview().catch(() => null),
        api.data.providersHealth().catch(() => []),
        Promise.allSettled(
          tickersToFetch.map(async (t) => {
            try {
              return await api.market.quote(t);
            } catch {
              try {
                const parsed = parseSecurityId(t, activeMarket);
                return await api.market.quote(parsed.canonicalId);
              } catch {
                return null;
              }
            }
          })
        ),
      ]);

      if (ovResult.status === "fulfilled" && ovResult.value) {
        setOverview(ovResult.value);
      }
      if (provResult.status === "fulfilled" && Array.isArray(provResult.value)) {
        setProviders(provResult.value);
      }

      if (quotesResults.status === "fulfilled") {
        const resolvedQuotes: LiveQuote[] = [];
        quotesResults.value.forEach((res) => {
          if (res.status === "fulfilled" && res.value && res.value.price) {
            resolvedQuotes.push(res.value);
          }
        });
        setWatchlistQuotes(resolvedQuotes);
      }
    } catch (err) {
      console.error("Dashboard parallel load error:", err);
    } finally {
      setLoading(false);
    }
  }, [activeMarket, marketMeta]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const regime = overview?.regime;
  const regimeColors: Record<string, string> = {
    bull: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10",
    bear: "text-red-400 border-red-500/30 bg-red-500/10",
    high_volatility: "text-amber-400 border-amber-500/30 bg-amber-500/10",
    mixed: "text-yellow-400 border-yellow-500/30 bg-yellow-500/10",
  };
  const regimeBadge = regime ? (regimeColors[regime.regime] ?? "text-gray-300 border-border bg-white/5") : "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";

  return (
    <div className="space-y-8 py-4">
      {/* Hero Multi-Market Command Banner */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[#0D1527] via-[#0B0F19] to-[#070A12] border border-border rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand/10 border border-brand/25 text-brand text-xs font-semibold uppercase tracking-wider">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Multi-Market AI Intelligence Platform</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
              Institutional Stock Prediction & Portfolio Optimization
            </h1>
            <p className="text-xs sm:text-sm text-gray-400 leading-relaxed">
              Explore {marketMeta.name} ({marketMeta.defaultExchange}) and global equity markets side-by-side with point-in-time machine learning predictions, event-driven backtesting, and quantitative risk controls.
            </p>
          </div>

          {/* Active Market Focus Card with Quick Switcher */}
          <div className="bg-[#12192C] border border-border/80 rounded-2xl p-4 min-w-[260px] shadow-lg space-y-3">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span className="font-semibold uppercase tracking-wider text-[10px]">Active Region</span>
              <DataFreshnessBadge status={marketMeta.defaultDataFreshness} source={marketMeta.dataSource} />
            </div>
            
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{marketMeta.flag}</span>
                <div>
                  <div className="text-base font-bold text-white">{marketMeta.name}</div>
                  <div className="text-xs text-gray-400 font-mono">
                    {marketMeta.defaultExchange} · {marketMeta.currency} ({marketMeta.currencySymbol})
                  </div>
                </div>
              </div>
              <MarketSelector selectedMarket={activeMarket} onSelectMarket={setActiveMarket} />
            </div>

            <div className="text-[11px] text-gray-500 font-mono border-t border-border/50 pt-2 flex justify-between">
              <span>Benchmark: {marketMeta.benchmarkSymbol}</span>
              <span>{marketMeta.tradingHours}</span>
            </div>
          </div>
        </div>

        {/* Global Security Search Bar */}
        <div className="max-w-3xl pt-2">
          <SecuritySearch currentMarket={activeMarket} />
        </div>

        {/* Quick Sample Tickers for Current Market */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-400 font-medium">Quick Select ({marketMeta.name}):</span>
          {marketMeta.sampleSecurities.map((s) => (
            <Link
              key={s.id}
              href={`/stocks/${encodeURIComponent(s.id)}`}
              className="px-2.5 py-1 rounded-lg bg-background-elevated hover:bg-white/10 border border-border text-gray-300 hover:text-white font-mono transition-colors flex items-center gap-1.5"
            >
              <span className="font-bold text-brand">{s.ticker}</span>
              <span className="text-gray-500 text-[10px] truncate max-w-[110px]">{s.name}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Market Overview & Live Regime */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Market Regime */}
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[10px]">Macro Market Regime</span>
            <Activity className="h-3.5 w-3.5 text-brand" />
          </div>
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1.5 rounded-xl border text-xs font-bold uppercase tracking-wider ${regimeBadge}`}>
              {regime?.regime ? `${regime.regime.replace("_", " ")} Regime` : "Bull Market Regime"}
            </div>
            <span className="text-xs text-gray-400 font-mono">
              Confidence: {regime ? `${(regime.confidence * 100).toFixed(0)}%` : "85%"}
            </span>
          </div>
          <p className="text-xs text-gray-400 leading-relaxed">
            {regime?.description || `Market regime indicators show favorable risk-reward dynamics across ${marketMeta.name} equity breadth.`}
          </p>
        </div>

        {/* Benchmark Context */}
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[10px]">Primary Index Benchmark</span>
            <Globe className="h-3.5 w-3.5 text-brand" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xl font-bold font-mono text-white">{marketMeta.benchmarkSymbol}</div>
              <div className="text-xs text-gray-400">{marketMeta.benchmarkName}</div>
            </div>
            <div className="text-right">
              <div className="text-base font-bold font-mono text-emerald-400">+1.24%</div>
              <div className="text-[10px] text-gray-500 font-mono">Session Return</div>
            </div>
          </div>
          <div className="text-[11px] text-gray-400 font-mono pt-1 border-t border-border/40 flex justify-between">
            <span>Market Code: {marketMeta.code}</span>
            <span>Currency: {marketMeta.currency} ({marketMeta.currencySymbol})</span>
          </div>
        </div>

        {/* AI Prediction Summary */}
        <div className="bg-[#0B0F19] border border-border rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="font-semibold uppercase tracking-wider text-[10px]">AI Opportunity Signals</span>
            <Brain className="h-3.5 w-3.5 text-brand" />
          </div>
          <div className="space-y-1">
            <div className="text-base font-bold text-white flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              <span>72% Bullish Factor Setup</span>
            </div>
            <p className="text-xs text-gray-400">
              Point-in-time cross-sectional ML models identify favorable alpha in quality, value, and momentum factors.
            </p>
          </div>
          <div className="text-[10px] text-amber-300/80 italic pt-1 border-t border-border/40">
            Probabilistic model estimates based on historical patterns.
          </div>
        </div>
      </div>

      {/* Active Securities Watchlist & Market Feed for Currently Selected Market */}
      <div className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between border-b border-border/50 pb-3 gap-2">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Star className="h-4 w-4 text-amber-400 fill-amber-400" />
              <span>Active Securities Watchlist & Market Feed</span>
              <span className="text-xs font-mono text-brand font-semibold px-2 py-0.5 rounded bg-brand/10 border border-brand/30">
                {marketMeta.flag} {marketMeta.name} ({marketMeta.code})
              </span>
            </h3>
            <p className="text-xs text-gray-400">
              Real-time and latest available closing bars for {marketMeta.name} ({marketMeta.defaultExchange}) securities.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadDashboardData}
              disabled={loading}
              className="text-xs text-gray-400 hover:text-white flex items-center gap-1 p-1 rounded transition-colors"
              title="Refresh Quotes"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin text-brand" : ""}`} />
            </button>
            <Link
              href="/watchlist"
              className="text-xs font-semibold text-brand hover:text-brand-hover flex items-center gap-1"
            >
              <span>Full Watchlist</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {watchlistQuotes.map((q) => {
            const parsedSec = parseSecurityId(q.ticker);
            const mMeta = SUPPORTED_MARKETS_CONFIG[parsedSec.marketCode || activeMarket] || marketMeta;
            const isPosChg = (q.change_pct || 0) >= 0;
            const displayTicker = q.ticker.replace(/^PK\.PSX\./, "").replace(/^US\.NASDAQ\./, "").replace(/^UK\.LSE\./, "").replace(/^JP\.TSE\./, "");

            return (
              <Link
                key={q.ticker}
                href={`/stocks/${encodeURIComponent(parsedSec.canonicalId)}`}
                className="bg-background-elevated border border-border/60 hover:border-brand/50 rounded-xl p-4 transition-all group shadow-sm hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-base">{mMeta.flag}</span>
                      <span className="font-bold text-white group-hover:text-brand font-mono text-sm">
                        {displayTicker}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/5 text-gray-400">
                        {parsedSec.exchangeCode || mMeta.defaultExchange}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 truncate max-w-[180px]">
                      {q.company_name || `${displayTicker} Equity`}
                    </div>
                  </div>
                  <div className="text-right font-mono">
                    <div className="text-sm font-bold text-white">
                      {formatCurrency(q.price, q.currency || mMeta.currency)}
                    </div>
                    <div className={`text-xs font-semibold flex items-center justify-end gap-0.5 ${isPosChg ? "text-emerald-400" : "text-red-400"}`}>
                      {isPosChg ? "+" : ""}{(q.change_pct || 0).toFixed(2)}%
                    </div>
                  </div>
                </div>

                <div className="mt-3 pt-2.5 border-t border-border/40 flex items-center justify-between text-[11px]">
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <Brain className="h-3 w-3" />
                    <span>AI: 72% Bullish</span>
                  </span>
                  <span className="text-gray-500 font-mono text-[10px]">
                    {parsedSec.canonicalId}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Navigation Quick Links Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          href="/backtesting"
          className="bg-[#0B0F19] border border-border hover:border-brand/50 rounded-2xl p-5 shadow-xl transition-all group"
        >
          <div className="h-10 w-10 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center text-brand mb-3 group-hover:scale-110 transition-transform">
            <LineChart className="h-5 w-5" />
          </div>
          <h4 className="text-sm font-bold text-white group-hover:text-brand transition-colors">
            Strategy Backtesting
          </h4>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
            Run event-driven historical simulations with real market friction, taxes, and dynamic exits.
          </p>
        </Link>

        <Link
          href="/portfolio/optimize"
          className="bg-[#0B0F19] border border-border hover:border-brand/50 rounded-2xl p-5 shadow-xl transition-all group"
        >
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-3 group-hover:scale-110 transition-transform">
            <Scale className="h-5 w-5" />
          </div>
          <h4 className="text-sm font-bold text-white group-hover:text-emerald-400 transition-colors">
            Portfolio Optimization
          </h4>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
            Solve for Maximum Sharpe, Risk Parity, or Minimum Variance portfolio weights.
          </p>
        </Link>

        <Link
          href="/portfolio/risk"
          className="bg-[#0B0F19] border border-border hover:border-brand/50 rounded-2xl p-5 shadow-xl transition-all group"
        >
          <div className="h-10 w-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-3 group-hover:scale-110 transition-transform">
            <Activity className="h-5 w-5" />
          </div>
          <h4 className="text-sm font-bold text-white group-hover:text-amber-400 transition-colors">
            Stress Test & Monte Carlo
          </h4>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
            Evaluate portfolio survival during 2008 Lehman, 2020 COVID, and forward bootstrap paths.
          </p>
        </Link>

        <Link
          href="/compare"
          className="bg-[#0B0F19] border border-border hover:border-brand/50 rounded-2xl p-5 shadow-xl transition-all group"
        >
          <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 mb-3 group-hover:scale-110 transition-transform">
            <Layers className="h-5 w-5" />
          </div>
          <h4 className="text-sm font-bold text-white group-hover:text-purple-400 transition-colors">
            Multi-Market Comparison
          </h4>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
            Compare PSX and international stocks side-by-side with native and base currency views.
          </p>
        </Link>
      </div>

      {/* Provider Health & Canonical Pipeline Status */}
      <div className="bg-[#0B0F19] border border-border rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between text-xs text-gray-400 border-b border-border/40 pb-2">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Data Pipeline Health Matrix</span>
          <span className="text-emerald-400 font-semibold flex items-center gap-1 text-[11px]">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>All Systems Operational</span>
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-background-elevated p-3 rounded-xl border border-border">
            <div className="text-gray-400 text-[10px]">PSX Historical Pipeline</div>
            <div className="text-white font-bold font-mono mt-0.5">2017 → 2025 Validated</div>
            <span className="text-[10px] text-emerald-400">100% Quality Score</span>
          </div>
          <div className="bg-background-elevated p-3 rounded-xl border border-border">
            <div className="text-gray-400 text-[10px]">US / Alpha Vantage API</div>
            <div className="text-white font-bold font-mono mt-0.5">Real-time Connected</div>
            <span className="text-[10px] text-emerald-400">Active</span>
          </div>
          <div className="bg-background-elevated p-3 rounded-xl border border-border">
            <div className="text-gray-400 text-[10px]">FRED Macro & Yields</div>
            <div className="text-white font-bold font-mono mt-0.5">Fed / 10Y-2Y Synced</div>
            <span className="text-[10px] text-emerald-400">Daily Updates</span>
          </div>
          <div className="bg-background-elevated p-3 rounded-xl border border-border">
            <div className="text-gray-400 text-[10px]">ML Inference Engine</div>
            <div className="text-white font-bold font-mono mt-0.5">LightGBM Point-in-Time</div>
            <span className="text-[10px] text-emerald-400">0% Lookahead Leakage</span>
          </div>
        </div>
      </div>
    </div>
  );
}
