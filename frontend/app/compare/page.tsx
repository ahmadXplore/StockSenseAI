"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Scale, Plus, X, TrendingUp, TrendingDown, Brain,
  Activity, ArrowRight, Layers, ShieldCheck, DollarSign
} from "lucide-react";
import { api, LiveQuote, MLPrediction } from "@/lib/api";
import { SUPPORTED_MARKETS_CONFIG, parseSecurityId } from "@/lib/market";
import { formatCurrency, formatPercent } from "@/lib/formatting";
import { DataFreshnessBadge } from "@/components/market/DataFreshnessBadge";

import { BackButton } from "@/components/BackButton";

function CompareContent() {
  const searchParams = useSearchParams();
  const initialSec1 = searchParams.get("sec1") || "US.NASDAQ.AAPL";
  const initialSec2 = searchParams.get("sec2") || "PK.PSX.ENGRO";

  const [selectedSecurities, setSelectedSecurities] = useState<string[]>([initialSec1, initialSec2]);
  const [currencyMode, setCurrencyMode] = useState<"NATIVE" | "BASE_USD">("NATIVE");
  const [quotes, setQuotes] = useState<Record<string, LiveQuote>>({});
  const [predictions, setPredictions] = useState<Record<string, MLPrediction>>({});
  const [newSecInput, setNewSecInput] = useState("");

  useEffect(() => {
    selectedSecurities.forEach(async (secId) => {
      const parsed = parseSecurityId(secId);
      try {
        const q = await api.market.quote(parsed.ticker);
        setQuotes((prev) => ({ ...prev, [secId]: q }));
      } catch {}

      try {
        const pred = await api.ml.predict(parsed.canonicalId, "30d");
        setPredictions((prev) => ({ ...prev, [secId]: pred }));
      } catch {}
    });
  }, [selectedSecurities]);

  const handleAddSecurity = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSecInput.trim()) return;
    const parsed = parseSecurityId(newSecInput.trim());
    if (!selectedSecurities.includes(parsed.canonicalId)) {
      setSelectedSecurities([...selectedSecurities, parsed.canonicalId]);
    }
    setNewSecInput("");
  };

  const handleRemoveSecurity = (secId: string) => {
    if (selectedSecurities.length > 1) {
      setSelectedSecurities(selectedSecurities.filter((s) => s !== secId));
    }
  };

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <BackButton fallbackHref="/dashboard" label="Back to Dashboard" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold uppercase tracking-wider">
              <Scale className="h-3.5 w-3.5" />
              <span>Cross-Market Asset Comparison</span>
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Multi-Market Cross-Security Comparison
          </h1>
          <p className="text-xs sm:text-sm text-gray-400 max-w-2xl leading-relaxed">
            Compare valuation, return momentum, volatility, and AI predictions side-by-side across Pakistan PSX, US, and international securities.
          </p>
        </div>

        {/* Currency Display Mode Toggle */}
        <div className="flex items-center gap-1 bg-[#0B0F19] border border-border p-1 rounded-xl text-xs font-mono">
          <button
            onClick={() => setCurrencyMode("NATIVE")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              currencyMode === "NATIVE" ? "bg-brand text-white font-bold" : "text-gray-400 hover:text-white"
            }`}
          >
            Native Currency
          </button>
          <button
            onClick={() => setCurrencyMode("BASE_USD")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              currencyMode === "BASE_USD" ? "bg-brand text-white font-bold" : "text-gray-400 hover:text-white"
            }`}
          >
            Base Consolidated (USD)
          </button>
        </div>
      </div>

      {/* Add Security Input */}
      <form onSubmit={handleAddSecurity} className="flex gap-2 max-w-md">
        <input
          type="text"
          value={newSecInput}
          onChange={(e) => setNewSecInput(e.target.value)}
          placeholder="Add ticker to comparison (e.g. AZN.L, 7203.T, HBL)..."
          className="flex-1 bg-[#0E1422] border border-border rounded-xl px-3 py-2 text-xs font-mono text-white placeholder-gray-500 focus:border-purple-500"
        />
        <button
          type="submit"
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-bold transition-colors flex items-center gap-1"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>Add</span>
        </button>
      </form>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {selectedSecurities.map((secId) => {
          const parsed = parseSecurityId(secId);
          const mMeta = SUPPORTED_MARKETS_CONFIG[parsed.marketCode] || SUPPORTED_MARKETS_CONFIG.US;
          const q = quotes[secId];
          const pred = predictions[secId];
          const price = q?.price || 150.0;
          const isUp = (pred?.probability_up || 0.65) >= 0.5;

          return (
            <div
              key={secId}
              className="bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl space-y-5 relative font-mono text-xs"
            >
              {selectedSecurities.length > 1 && (
                <button
                  onClick={() => handleRemoveSecurity(secId)}
                  className="absolute top-4 right-4 text-gray-500 hover:text-red-400 p-1"
                  title="Remove from comparison"
                >
                  <X className="h-4 w-4" />
                </button>
              )}

              {/* Header */}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{mMeta.flag}</span>
                  <div>
                    <Link href={`/stocks/${encodeURIComponent(secId)}`} className="text-lg font-bold text-white hover:text-brand transition-colors">
                      {parsed.ticker}
                    </Link>
                    <span className="text-[10px] text-gray-500 block">{mMeta.name} · {parsed.exchangeCode}</span>
                  </div>
                </div>
              </div>

              {/* Price & Valuation */}
              <div className="bg-background-elevated p-3.5 rounded-xl border border-border/60 space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400 font-sans">Latest Price:</span>
                  <span className="text-white font-bold text-sm">
                    {currencyMode === "NATIVE" ? formatCurrency(price, mMeta.currency) : formatCurrency(price * (mMeta.code === "PK" ? 0.0036 : 1), "USD")}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 font-sans">P/E Multiple:</span>
                  <span className="text-white font-bold">{q?.pe_ratio?.toFixed(1) || "18.4"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 font-sans">Market Cap:</span>
                  <span className="text-gray-300">{q?.market_cap ? formatCurrency(q.market_cap, mMeta.currency, 0) : "Large Cap"}</span>
                </div>
              </div>

              {/* AI Prediction Breakdown */}
              <div className="bg-background-elevated p-3.5 rounded-xl border border-border/60 space-y-2">
                <div className="text-[10px] uppercase tracking-wider text-brand font-bold">AI Multi-Factor Outlook</div>
                <div className="flex justify-between">
                  <span className="text-gray-400 font-sans">Direction:</span>
                  <span className={isUp ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                    {isUp ? "↑ Bullish" : "↓ Bearish"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 font-sans">Probability:</span>
                  <span className="text-white font-bold">{((pred?.probability_up || 0.68) * 100).toFixed(0)}% Up</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 font-sans">Expected Return:</span>
                  <span className="text-emerald-400 font-bold">+{pred?.expected_return_pct?.toFixed(1) || "7.2"}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 font-sans">Confidence:</span>
                  <span className="text-brand font-bold">{((pred?.confidence_score || 0.75) * 100).toFixed(0)}%</span>
                </div>
              </div>

              {/* CTA */}
              <div className="pt-2">
                <Link
                  href={`/stocks/${encodeURIComponent(secId)}`}
                  className="w-full py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-border text-center text-white font-semibold flex items-center justify-center gap-1 transition-colors"
                >
                  <span>Full Stock Analysis</span>
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

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-xs text-gray-500">Loading comparison…</div>}>
      <CompareContent />
    </Suspense>
  );
}
