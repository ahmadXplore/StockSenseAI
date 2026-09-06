"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Globe, Building2, TrendingUp, ArrowRight, ShieldCheck, Database, Check } from "lucide-react";
import { SUPPORTED_MARKETS_CONFIG, MarketMeta } from "@/lib/market";
import { DataFreshnessBadge } from "@/components/market/DataFreshnessBadge";
import { useMarket } from "@/lib/marketContext";

import { BackButton } from "@/components/BackButton";

export default function MarketsCatalogPage() {
  const router = useRouter();
  const { activeMarket, setActiveMarket } = useMarket();
  const markets = Object.values(SUPPORTED_MARKETS_CONFIG);

  const handleSwitchAndGo = (code: string) => {
    setActiveMarket(code);
    router.push("/dashboard");
  };

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="space-y-2 border-b border-border/60 pb-4">
        <div className="flex items-center gap-2">
          <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand/10 border border-brand/20 text-brand text-xs font-semibold uppercase tracking-wider">
            <Globe className="h-3.5 w-3.5" />
            <span>Global Multi-Market Architecture</span>
          </div>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Supported Global Equity Markets
        </h1>
        <p className="text-xs sm:text-sm text-gray-400 max-w-2xl leading-relaxed">
          StockSense AI treats Pakistan (PSX) and global markets with equal architecture. Explore canonical exchanges, benchmark tracking, and active securities across all regions.
        </p>
      </div>

      {/* Markets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {markets.map((m: MarketMeta) => {
          const isActive = m.code === activeMarket;

          return (
            <div
              key={m.code}
              className={`bg-[#0B0F19] border rounded-2xl p-6 shadow-xl space-y-4 transition-all flex flex-col justify-between ${
                isActive ? "border-brand shadow-brand/10" : "border-border hover:border-brand/40"
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{m.flag}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-white">
                          {m.name}
                        </h3>
                        {isActive && (
                          <span className="px-2 py-0.5 rounded-full bg-brand/15 border border-brand/30 text-brand text-[10px] font-bold">
                            Active Focus
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-400 font-mono">
                        Market Code: <span className="text-gray-300 font-semibold">{m.code}</span>
                      </div>
                    </div>
                  </div>
                  <DataFreshnessBadge status={m.defaultDataFreshness} source={m.dataSource} />
                </div>

                {/* Market Specs */}
                <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-border/40">
                  <div className="bg-background-elevated p-2 rounded-lg">
                    <div className="text-gray-500 text-[10px]">Currency</div>
                    <div className="text-white font-bold">{m.currency} ({m.currencySymbol})</div>
                  </div>
                  <div className="bg-background-elevated p-2 rounded-lg">
                    <div className="text-gray-500 text-[10px]">Benchmark</div>
                    <div className="text-white font-bold">{m.benchmarkSymbol}</div>
                  </div>
                  <div className="bg-background-elevated p-2 rounded-lg">
                    <div className="text-gray-500 text-[10px]">Timezone</div>
                    <div className="text-gray-300 truncate">{m.timezone}</div>
                  </div>
                  <div className="bg-background-elevated p-2 rounded-lg">
                    <div className="text-gray-500 text-[10px]">Exchanges</div>
                    <div className="text-brand font-bold">{m.exchanges.join(", ")}</div>
                  </div>
                </div>

                {/* Sample Securities */}
                <div className="space-y-1.5 pt-2">
                  <div className="text-[11px] font-semibold text-gray-400">Featured Constituents:</div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.sampleSecurities.slice(0, 5).map((s) => (
                      <Link
                        key={s.id}
                        href={`/stocks/${encodeURIComponent(s.id)}`}
                        className="px-2 py-0.5 rounded bg-white/5 hover:bg-brand/15 hover:text-brand border border-border text-[11px] font-mono text-gray-300 transition-colors"
                      >
                        {s.ticker}
                      </Link>
                    ))}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-4 border-t border-border/40 flex items-center justify-between gap-2">
                {isActive ? (
                  <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                    <Check className="h-3.5 w-3.5" />
                    <span>Active Region</span>
                  </span>
                ) : (
                  <button
                    onClick={() => handleSwitchAndGo(m.code)}
                    className="text-xs font-semibold text-brand hover:text-brand-hover px-2.5 py-1 rounded-lg bg-brand/10 border border-brand/30 transition-colors"
                  >
                    Set as Active Focus
                  </button>
                )}

                <Link
                  href={`/stocks/${encodeURIComponent(m.sampleSecurities[0]?.id || "US.NASDAQ.AAPL")}`}
                  className="text-xs font-semibold text-gray-300 hover:text-white flex items-center gap-1"
                >
                  <span>Explore</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
