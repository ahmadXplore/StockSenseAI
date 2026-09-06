"use client";

import { useEffect, useState, useCallback } from "react";
import { TrendingUp, TrendingDown, Wifi, WifiOff } from "lucide-react";
import { api, MarketOverview } from "@/lib/api";
import { useMarket } from "@/lib/marketContext";

interface TickerItem {
  label: string;
  price: string;
  change: string;
  up: boolean;
}

const REGIME_STYLES: Record<string, { label: string; color: string; bg: string }> = {
  bull:            { label: "BULL MARKET",     color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  bear:            { label: "BEAR MARKET",     color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20" },
  high_volatility: { label: "HIGH VOLATILITY", color: "text-orange-400",  bg: "bg-orange-500/10 border-orange-500/20" },
  mixed:           { label: "MIXED/NEUTRAL",   color: "text-yellow-400",  bg: "bg-yellow-500/10 border-yellow-500/20" },
};

function fmt(n: number, prefix = "$", decimals = 2): string {
  return `${prefix}${n.toFixed(decimals)}`;
}
function fmtPct(n: number): string {
  return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

export function MarketContextBar() {
  const { activeMarket, marketMeta } = useMarket();
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const data = await api.market.overview();
      setOverview(data);
      setIsLive(true);
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 60_000);
    return () => clearInterval(id);
  }, [fetchData]);

  // Build scrolling ticker items adapted to active region
  const items: TickerItem[] = [];

  if (activeMarket === "PK") {
    items.push(
      { label: "KSE-100", price: "78,250.40", change: "+1.35%", up: true },
      { label: "ENGRO", price: "Rs.348.50", change: "+1.80%", up: true },
      { label: "SYS", price: "Rs.420.00", change: "+3.40%", up: true },
      { label: "OGDC", price: "Rs.142.50", change: "-0.80%", up: false },
      { label: "LUCK", price: "Rs.890.25", change: "+2.10%", up: true },
      { label: "HBL", price: "Rs.124.75", change: "+0.90%", up: true }
    );
  } else if (activeMarket === "UK") {
    items.push(
      { label: "FTSE 100", price: "8,245.20", change: "+0.45%", up: true },
      { label: "AZN.L", price: "£122.50", change: "+0.85%", up: true },
      { label: "SHEL.L", price: "£28.40", change: "-0.30%", up: false },
      { label: "HSBA.L", price: "£6.85", change: "+0.60%", up: true },
      { label: "BP.L", price: "£4.62", change: "+0.20%", up: true }
    );
  } else {
    // US or Global default
    if (overview) {
      items.push(
        { label: "SPY", price: fmt(overview.spy_price), change: fmtPct(overview.spy_change_pct), up: overview.spy_change_pct >= 0 },
        { label: "QQQ", price: fmt(overview.qqq_price), change: fmtPct(overview.qqq_change_pct), up: overview.qqq_change_pct >= 0 },
        { label: "VIX", price: overview.vix_value.toFixed(2), change: fmtPct(overview.vix_change), up: overview.vix_change < 0 },
        { label: "REGIME", price: overview.regime.regime.toUpperCase().replace("_", " "), change: `${overview.regime.confidence.toFixed(0)}% conf`, up: ["bull"].includes(overview.regime.regime) },
        { label: "MACRO", price: `${overview.macro_score.toFixed(0)}/100`, change: "Macro Score", up: overview.macro_score >= 50 }
      );
    } else {
      items.push(
        { label: "SPY", price: "$560.20", change: "+0.85%", up: true },
        { label: "QQQ", price: "$482.40", change: "+1.10%", up: true },
        { label: "VIX", price: "15.45", change: "-0.50%", up: true },
        { label: "AAPL", price: "$228.40", change: "+1.20%", up: true },
        { label: "NVDA", price: "$124.50", change: "+2.40%", up: true }
      );
    }
  }

  // Duplicate for seamless infinite loop
  const doubled = [...items, ...items, ...items, ...items];

  const regime = overview
    ? (REGIME_STYLES[overview.regime.regime] ?? REGIME_STYLES.bull)
    : { label: `${marketMeta.name.toUpperCase()} ACTIVE`, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };

  return (
    <div className="w-full bg-background-elevated border-b border-border overflow-hidden" style={{ height: "34px" }}>
      <div className="max-w-full h-full flex items-center">
        {/* Connection & Active Market Flag indicator */}
        <div className="px-2.5 h-full flex items-center gap-1.5 border-r border-border shrink-0 text-xs">
          <span className="text-sm">{marketMeta.flag}</span>
          {isLive ? (
            <Wifi className="h-3 w-3 text-emerald-400" />
          ) : error ? (
            <WifiOff className="h-3 w-3 text-red-400" />
          ) : (
            <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          )}
        </div>

        {/* Animated Scrolling Ticker */}
        <div className="flex-1 overflow-hidden relative">
          <div
            className="absolute left-0 top-0 h-full w-12 z-10 pointer-events-none"
            style={{ background: "linear-gradient(to right, #0f1117, transparent)" }}
          />
          <div
            className="absolute right-0 top-0 h-full w-12 z-10 pointer-events-none"
            style={{ background: "linear-gradient(to left, #0f1117, transparent)" }}
          />

          <div
            className="flex items-center gap-0 whitespace-nowrap"
            style={{
              animation: "marquee 35s linear infinite",
              willChange: "transform",
            }}
          >
            {doubled.map((item, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 px-4 text-xs tabular-nums border-r border-border/40 h-[34px]">
                <span className="text-gray-400 font-medium">{item.label}</span>
                <span className="font-semibold text-white">{item.price}</span>
                <span className={`flex items-center gap-0.5 ${item.up ? "text-emerald-400" : "text-red-400"}`}>
                  {item.up ? <TrendingUp className="h-2.5 w-2.5" /> : <TrendingDown className="h-2.5 w-2.5" />}
                  {item.change}
                </span>
              </span>
            ))}
          </div>
        </div>

        {/* Right: Market Regime Badge */}
        <div className={`flex items-center gap-1.5 px-3 h-full border-l border-border text-xs font-semibold shrink-0 ${regime.bg} ${regime.color}`}>
          <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
          {regime.label}
        </div>
      </div>
    </div>
  );
}
