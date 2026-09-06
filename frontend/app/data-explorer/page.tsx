"use client";

import { useEffect, useState } from "react";
import { Database, Globe, Building2, Activity, CheckCircle, AlertTriangle, Loader2, RefreshCw, Search } from "lucide-react";
import { api, SupportedMarket, SupportedExchange, ProviderHealth } from "@/lib/api";

import { BackButton } from "@/components/BackButton";

const MARKET_FLAG: Record<string, string> = {
  PK: "🇵🇰", US: "🇺🇸", UK: "🇬🇧", JP: "🇯🇵", HK: "🇭🇰", IN: "🇮🇳",
};

export default function DataExplorerPage() {
  const [markets, setMarkets]     = useState<SupportedMarket[]>([]);
  const [exchanges, setExchanges] = useState<SupportedExchange[]>([]);
  const [providers, setProviders] = useState<ProviderHealth[]>([]);
  const [searchQ, setSearchQ]     = useState("");
  const [searchResults, setSearchResults] = useState<unknown[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedMarket, setSelectedMarket] = useState<string | null>(null);
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [m, e, p] = await Promise.allSettled([
        api.data.markets(),
        api.data.exchanges(),
        api.data.providersHealth(),
      ]);
      if (m.status === "fulfilled") setMarkets(m.value);
      if (e.status === "fulfilled") setExchanges(e.value);
      if (p.status === "fulfilled") setProviders(p.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAll();
    setRefreshing(false);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQ.trim()) return;
    setSearching(true);
    try {
      const res = await api.data.securitiesSearch(searchQ.trim(), selectedMarket ?? undefined);
      setSearchResults(res);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const filteredExchanges = selectedMarket
    ? exchanges.filter(e => e.market_id === markets.find(m => m.code === selectedMarket)?.id)
    : exchanges;

  const healthyProviders = providers.filter(p => p.status === "healthy" || p.status === "ok");

  return (
    <div className="space-y-6 py-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
            <span className="text-xs font-mono text-brand font-semibold uppercase">Canonical Master</span>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="h-5 w-5 text-brand" /> Multi-Market Data Explorer &amp; Health
          </h1>
          <p className="text-xs text-gray-400">
            Live canonical data layer — Pakistan, US, UK, Japan, Hong Kong, India
          </p>
        </div>
        <button onClick={handleRefresh} disabled={loading || refreshing}
          className="flex items-center gap-1.5 px-3 py-2 bg-background-elevated border border-border rounded-lg text-xs text-gray-300 hover:text-white transition-colors">
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Provider Health Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Markets", value: markets.length, icon: Globe },
          { label: "Exchanges", value: exchanges.length, icon: Building2 },
          { label: "Providers", value: providers.length, icon: Activity },
          { label: "Providers Live", value: healthyProviders.length, icon: CheckCircle },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="bg-background-elevated border border-border rounded-xl p-4 flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-brand/10 flex items-center justify-center shrink-0">
              <Icon className="h-4 w-4 text-brand" />
            </div>
            <div>
              <div className="text-xl font-bold font-mono text-white">{loading ? "—" : value}</div>
              <div className="text-[10px] text-gray-400">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Provider Health Table */}
      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <Activity className="h-4 w-4 text-brand" /> Data Provider Health
        </h2>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-10 bg-white/5 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : providers.length > 0 ? (
          <div className="divide-y divide-border">
            {providers.map((p) => {
              const isOk = p.status === "healthy" || p.status === "ok";
              return (
                <div key={p.provider_name} className="py-3 flex items-center justify-between first:pt-0 last:pb-0">
                  <div className="flex items-center gap-2.5">
                    <div className={`h-2 w-2 rounded-full ${isOk ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
                    <span className="text-sm font-medium text-white">{p.provider_name}</span>
                    {p.message && <span className="text-[10px] text-gray-500">{p.message}</span>}
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono tabular-nums">
                    {p.latency_ms !== undefined && (
                      <span className="text-gray-400">{p.latency_ms.toFixed(0)}ms</span>
                    )}
                    {p.rate_limit_remaining !== undefined && (
                      <span className="text-gray-500">{p.rate_limit_remaining} calls left</span>
                    )}
                    <span className={`font-bold ${isOk ? "text-emerald-400" : "text-red-400"}`}>
                      {p.status.toUpperCase()}
                    </span>
                    {p.error_count !== undefined && p.error_count > 0 && (
                      <span className="text-red-400">{p.error_count} errors</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-xs text-gray-500 py-4 text-center">No provider data. Ensure backend is running.</div>
        )}
      </div>

      {/* Markets Grid */}
      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <Globe className="h-4 w-4 text-brand" /> Supported Markets
        </h2>
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />)}
          </div>
        ) : markets.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {markets.map((m) => {
              const isSelected = selectedMarket === m.code;
              const exCount = exchanges.filter(e => e.market_id === m.id).length;
              return (
                <button
                  key={m.id}
                  onClick={() => setSelectedMarket(isSelected ? null : m.code)}
                  className={`text-left p-4 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-brand/10 border-brand/30 text-white"
                      : "bg-background border-border hover:border-border-active text-gray-300 hover:text-white"
                  }`}
                >
                  <div className="text-2xl mb-2">{MARKET_FLAG[m.code] ?? "🌐"}</div>
                  <div className="font-bold text-sm">{m.name}</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">
                    {m.code} · {m.default_currency} · {m.timezone}
                  </div>
                  <div className="text-[10px] text-brand mt-1">{exCount} exchange{exCount !== 1 ? "s" : ""}</div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="text-xs text-gray-500">No markets returned. Ensure backend is running.</div>
        )}
      </div>

      {/* Exchanges Table */}
      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Building2 className="h-4 w-4 text-brand" /> Stock Exchanges
            {selectedMarket && (
              <span className="text-xs text-brand bg-brand/10 px-2 py-0.5 rounded-full">
                Filtered: {selectedMarket}
              </span>
            )}
          </h2>
          {selectedMarket && (
            <button onClick={() => setSelectedMarket(null)} className="text-xs text-gray-500 hover:text-white transition-colors">
              Clear filter
            </button>
          )}
        </div>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-12 bg-white/5 rounded animate-pulse" />)}
          </div>
        ) : filteredExchanges.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-gray-400 border-b border-border font-semibold">
                <tr>
                  <th className="py-2.5 pr-4">Code</th>
                  <th className="py-2.5 pr-4">Name</th>
                  <th className="py-2.5 pr-4">Country</th>
                  <th className="py-2.5 pr-4">Currency</th>
                  <th className="py-2.5 pr-4">Timezone</th>
                  <th className="py-2.5 pr-4">MIC</th>
                  <th className="py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredExchanges.map((ex) => (
                  <tr key={ex.id} className="hover:bg-background-hover transition-colors">
                    <td className="py-3 pr-4 font-bold font-mono text-brand">{ex.code}</td>
                    <td className="py-3 pr-4 text-white">{ex.name}</td>
                    <td className="py-3 pr-4 text-gray-300">
                      {MARKET_FLAG[markets.find(m => m.id === ex.market_id)?.code ?? ""] ?? ""} {ex.country}
                    </td>
                    <td className="py-3 pr-4 font-mono text-gray-300">{ex.currency}</td>
                    <td className="py-3 pr-4 text-gray-400 font-mono text-[10px]">{ex.timezone}</td>
                    <td className="py-3 pr-4 font-mono text-gray-500 text-[10px]">{ex.mic_code ?? "—"}</td>
                    <td className="py-3">
                      <span className={`text-[10px] font-bold ${ex.status === "active" ? "text-emerald-400" : "text-gray-500"}`}>
                        {ex.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-xs text-gray-500 py-4">No exchanges found for this filter.</div>
        )}
      </div>

      {/* Multi-Market Security Search */}
      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <Search className="h-4 w-4 text-brand" /> Multi-Market Security Search
        </h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQ}
            onChange={(e) => setSearchQ(e.target.value)}
            placeholder="Search securities across all markets (e.g. ENGRO, AAPL, Reliance)…"
            className="flex-1 px-4 py-2.5 bg-background border border-border focus:border-brand rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none"
          />
          <select
            value={selectedMarket ?? ""}
            onChange={(e) => setSelectedMarket(e.target.value || null)}
            className="px-3 py-2.5 bg-background border border-border focus:border-brand rounded-lg text-sm text-white focus:outline-none"
          >
            <option value="">All Markets</option>
            {markets.map(m => <option key={m.code} value={m.code}>{m.code} — {m.name}</option>)}
          </select>
          <button type="submit" disabled={!searchQ.trim() || searching}
            className="px-5 py-2.5 bg-brand hover:bg-brand-hover disabled:bg-gray-800 disabled:text-gray-500 text-white rounded-lg font-medium text-sm transition-all flex items-center gap-2">
            {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Search
          </button>
        </form>

        {searchResults.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-gray-400 border-b border-border font-semibold">
                <tr>
                  <th className="py-2.5 pr-4">Security ID</th>
                  <th className="py-2.5 pr-4">Symbol</th>
                  <th className="py-2.5 pr-4">Company</th>
                  <th className="py-2.5 pr-4">Market</th>
                  <th className="py-2.5 pr-4">Sector</th>
                  <th className="py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(searchResults as Record<string, unknown>[]).map((r, i) => (
                  <tr key={i} className="hover:bg-background-hover transition-colors">
                    <td className="py-3 pr-4 font-mono text-[10px] text-gray-500">{String(r.security_id ?? "—")}</td>
                    <td className="py-3 pr-4 font-bold font-mono text-brand">{String(r.symbol ?? "—")}</td>
                    <td className="py-3 pr-4 text-white">{String(r.company_name ?? "—")}</td>
                    <td className="py-3 pr-4 text-gray-300">{String(r.market_id ?? "—")}</td>
                    <td className="py-3 pr-4 text-gray-400">{String(r.sector ?? "—")}</td>
                    <td className="py-3 text-[10px]">
                      <span className={String(r.status ?? "") === "active" ? "text-emerald-400 font-bold" : "text-gray-500"}>
                        {String(r.status ?? "—").toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {searchResults.length === 0 && searchQ && !searching && (
          <div className="text-xs text-gray-500 text-center py-4">No results. Try a different query or market filter.</div>
        )}
      </div>
    </div>
  );
}
