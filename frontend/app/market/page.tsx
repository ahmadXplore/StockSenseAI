"use client";

import { useEffect, useState } from "react";
import { Globe, Activity, TrendingUp, TrendingDown, Loader2, RefreshCw, AlertTriangle } from "lucide-react";
import { api, MarketOverview, MacroData, OHLCVPoint } from "@/lib/api";

const REGIME_DISPLAY: Record<string, { label: string; emoji: string; color: string; bg: string }> = {
  bull:            { label: "Bull Market Regime",     emoji: "🟢", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  bear:            { label: "Bear Market Regime",     emoji: "🔴", color: "text-red-400",     bg: "bg-red-500/10 border-red-500/20" },
  high_volatility: { label: "High Volatility Regime", emoji: "🟠", color: "text-orange-400",  bg: "bg-orange-500/10 border-orange-500/20" },
  mixed:           { label: "Mixed / Neutral",         emoji: "🟡", color: "text-yellow-400",  bg: "bg-yellow-500/10 border-yellow-500/20" },
};

function MacroRow({
  label, value, change, trend, valueClass
}: {
  label: string; value: string; change?: string; trend?: string; valueClass?: string;
}) {
  const isPos = change?.startsWith("+");
  return (
    <div className="py-3 flex items-center justify-between first:pt-0 last:pb-0">
      <span className="text-gray-300 text-xs">{label}</span>
      <div className="flex items-center gap-4 text-xs tabular-nums font-mono">
        <span className={`font-bold text-white ${valueClass ?? ""}`}>{value}</span>
        {change && (
          <span className={`font-semibold ${isPos ? "text-emerald-400" : "text-red-400"}`}>{change}</span>
        )}
        {trend && <span className="text-gray-400 font-sans text-[11px] min-w-[160px] text-right hidden md:block">{trend}</span>}
      </div>
    </div>
  );
}

// Simple mini price chart using SVG
function MiniChart({ history }: { history: OHLCVPoint[] }) {
  if (!history || history.length < 2) return null;
  const closes = history.map(h => h.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const w = 400, h = 80;
  const points = closes.map((c, i) => ({
    x: (i / (closes.length - 1)) * w,
    y: h - ((c - min) / (max - min || 1)) * h,
  }));
  const pathD = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const first = closes[0];
  const last = closes[closes.length - 1];
  const isUp = last >= first;

  return (
    <div className="w-full h-24 relative overflow-hidden rounded-lg bg-background">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
        <path d={pathD} fill="none" stroke={isUp ? "#34d399" : "#f87171"} strokeWidth="2" />
        <path d={pathD + ` L ${w} ${h} L 0 ${h} Z`} fill={isUp ? "rgba(52,211,153,0.08)" : "rgba(248,113,113,0.08)"} />
      </svg>
      <div className="absolute bottom-1 right-2 text-[10px] font-mono text-gray-500">
        {history.length}d
      </div>
    </div>
  );
}

export default function MarketRegimePage() {
  const [overview, setOverview] = useState<MarketOverview | null>(null);
  const [macro, setMacro] = useState<MacroData | null>(null);
  const [spyHistory, setSpyHistory] = useState<OHLCVPoint[]>([]);
  const [qqqHistory, setQqqHistory] = useState<OHLCVPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [ov, mc, spyH, qqqH] = await Promise.allSettled([
        api.market.overview(),
        api.market.macro(),
        api.market.history("SPY", "compact"),
        api.market.history("QQQ", "compact"),
      ]);
      if (ov.status === "fulfilled") setOverview(ov.value);
      if (mc.status === "fulfilled") setMacro(mc.value);
      if (spyH.status === "fulfilled") setSpyHistory(spyH.value.history.slice(0, 60).reverse());
      if (qqqH.status === "fulfilled") setQqqHistory(qqqH.value.history.slice(0, 60).reverse());
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const regime = overview?.regime;
  const rd = regime ? (REGIME_DISPLAY[regime.regime] ?? REGIME_DISPLAY.mixed) : null;

  function fmtNum(n?: number, prefix = ""): string {
    if (n === undefined || n === null) return "N/A";
    return `${prefix}${n.toFixed(2)}`;
  }

  return (
    <div className="space-y-6 py-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Globe className="h-5 w-5 text-brand" /> Market Regime &amp; Macroeconomic Context
          </h1>
          <p className="text-xs text-gray-400">Live FRED + yfinance data · {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Loading…"}</p>
        </div>
        <button
          onClick={fetchAll}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-2 bg-background-elevated border border-border rounded-lg text-xs text-gray-300 hover:text-white transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {/* Regime Banner */}
      {loading && !overview ? (
        <div className="h-28 bg-background-elevated border border-border rounded-xl animate-pulse" />
      ) : rd && regime ? (
        <div className={`rounded-xl border p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 ${rd.bg}`}>
          <div className="space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider text-gray-400">Active Classification</div>
            <div className={`text-2xl font-bold text-white`}>{rd.emoji} {rd.label}</div>
            <p className="text-xs text-gray-300">{regime.description}</p>
          </div>
          <div className="flex gap-6 sm:gap-8 text-right shrink-0">
            <div>
              <div className="text-[10px] text-gray-400">Confidence</div>
              <div className={`text-lg font-bold font-mono ${rd.color}`}>{regime.confidence.toFixed(0)}%</div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400">VIX</div>
              <div className="text-lg font-bold font-mono text-white">{regime.vix_level.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400">Yield Curve</div>
              <div className={`text-lg font-bold font-mono ${regime.yield_curve_inverted ? "text-red-400" : "text-emerald-400"}`}>
                {regime.yield_curve_inverted ? "INVERTED" : "NORMAL"}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Price Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[
          { label: "SPY (S&P 500 ETF)", history: spyHistory, price: overview?.spy_price, chg: overview?.spy_change_pct },
          { label: "QQQ (Nasdaq 100 ETF)", history: qqqHistory, price: overview?.qqq_price, chg: overview?.qqq_change_pct },
        ].map(({ label, history, price, chg }) => (
          <div key={label} className="bg-background-elevated border border-border rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-sm text-white">{label}</div>
              {price !== undefined && (
                <div className="text-right">
                  <div className="font-bold text-white font-mono">${price.toFixed(2)}</div>
                  {chg !== undefined && (
                    <div className={`text-xs font-semibold ${chg >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {chg >= 0 ? "+" : ""}{chg.toFixed(2)}%
                    </div>
                  )}
                </div>
              )}
            </div>
            {history.length > 0 ? (
              <MiniChart history={history} />
            ) : (
              <div className="h-24 bg-background rounded-lg animate-pulse" />
            )}
          </div>
        ))}
      </div>

      {/* Macro Indicators */}
      <div className="bg-background-elevated border border-border rounded-xl p-6 space-y-2">
        <h2 className="text-base font-semibold text-white flex items-center gap-2 pb-1">
          <Activity className="h-4 w-4 text-brand" /> Live Macroeconomic Indicators (FRED)
        </h2>
        {loading && !macro ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-8 bg-white/5 rounded animate-pulse" />
            ))}
          </div>
        ) : macro ? (
          <div className="divide-y divide-border">
            <MacroRow label="VIX (CBOE Volatility Index)" value={fmtNum(macro.vix)} trend={macro.vix && macro.vix < 15 ? "Low Volatility Zone (<15)" : macro.vix && macro.vix > 25 ? "High Stress (>25)" : "Moderate"} />
            <MacroRow label="Fed Funds Rate" value={macro.fed_funds_rate ? `${macro.fed_funds_rate.toFixed(2)}%` : "N/A"} trend="FOMC Target Rate" />
            <MacroRow label="10Y–2Y Yield Curve Spread" value={macro.yield_curve_10y2y !== undefined ? `${macro.yield_curve_10y2y.toFixed(2)}%` : "N/A"} trend={macro.yield_curve_10y2y !== undefined && macro.yield_curve_10y2y < 0 ? "⚠ Inverted (Recession Signal)" : "Normal (Positive Slope)"} valueClass={macro.yield_curve_10y2y !== undefined && macro.yield_curve_10y2y < 0 ? "text-red-400" : ""} />
            <MacroRow label="CPI (YoY Inflation)" value={macro.cpi_yoy !== undefined ? `${macro.cpi_yoy.toFixed(1)}%` : "N/A"} trend={macro.cpi_yoy !== undefined && macro.cpi_yoy > 3 ? "Above Fed 2% Target" : "Near Fed 2% Target"} />
            <MacroRow label="Unemployment Rate" value={macro.unemployment_rate !== undefined ? `${macro.unemployment_rate.toFixed(1)}%` : "N/A"} trend="Bureau of Labor Statistics" />
            {macro.gdp_growth !== undefined && (
              <MacroRow label="GDP Growth (Annualized)" value={`${macro.gdp_growth.toFixed(1)}%`} trend="Bureau of Economic Analysis" />
            )}
          </div>
        ) : (
          <div className="text-xs text-gray-500 py-4 text-center">Unable to load macro data from FRED. Ensure backend is running.</div>
        )}
      </div>
    </div>
  );
}
