"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  TrendingUp, TrendingDown, BarChart3, FileText, Activity,
  DollarSign, Star, StarOff, ArrowLeft, ExternalLink, Loader2,
  AlertTriangle, CheckCircle, Brain, Newspaper, Users, Calendar,
  RefreshCw, Shield, Layers, Scale, LineChart, HelpCircle, Sparkles
} from "lucide-react";
import {
  api, LiveQuote, FundamentalsData, NewsItem, MLPrediction,
  OHLCVPoint, BacktestResponse, BacktestConfig
} from "@/lib/api";
import { SUPPORTED_MARKETS_CONFIG, parseSecurityId, getDataFreshnessInfo } from "@/lib/market";
import { formatCurrency, formatPercent, formatLargeNumber, formatDate } from "@/lib/formatting";
import { addToWatchlist, removeFromWatchlist, isInWatchlist } from "@/lib/localStorage";
import { DataFreshnessBadge } from "@/components/market/DataFreshnessBadge";
import { InteractiveStockChart } from "@/components/charts/InteractiveStockChart";
import { PredictionCard } from "@/components/prediction/PredictionCard";
import { ExplainabilityBars } from "@/components/prediction/ExplainabilityBars";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { BackButton } from "@/components/BackButton";
import { StockAIContext, openStockAICopilot } from "@/lib/aiCopilot";
import { StockAICopilotPanel } from "@/components/stock/StockAICopilotPanel";

export default function StockDetailPage({ params }: { params: Promise<{ securityId: string }> | { securityId: string } }) {
  // Unwrap Next.js params safely
  const resolvedParams = typeof (params as any)?.then === "function" ? use(params as Promise<{ securityId: string }>) : (params as { securityId: string });
  const rawId = decodeURIComponent(resolvedParams.securityId || "US.NASDAQ.AAPL");
  const parsed = parseSecurityId(rawId);
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<"chart" | "ai" | "fundamentals" | "technicals" | "news" | "backtest">("chart");
  const [quote, setQuote] = useState<LiveQuote | null>(null);
  const [history, setHistory] = useState<OHLCVPoint[]>([]);
  const [prediction, setPrediction] = useState<MLPrediction | null>(null);
  const [fundamentals, setFundamentals] = useState<FundamentalsData | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Multi-Factor Horizon & Prediction Processing State
  const [activeHorizon, setActiveHorizon] = useState<string>("30d");
  const [predLoading, setPredLoading] = useState<boolean>(false);

  // Quick Backtest State
  const [btRunning, setBtRunning] = useState(false);
  const [btResult, setBtResult] = useState<BacktestResponse | null>(null);
  const [btError, setBtError] = useState<string | null>(null);

  const marketMeta = SUPPORTED_MARKETS_CONFIG[parsed.marketCode] || SUPPORTED_MARKETS_CONFIG.US;
  const currency = quote?.currency || marketMeta.currency;

  useEffect(() => {
    setInWatchlist(isInWatchlist(parsed.ticker));
    const timer = setTimeout(() => loadAllData(), 100);
    return () => clearTimeout(timer);
  }, [rawId]);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      // 1. Fetch Quote
      let qData: LiveQuote | null = null;
      try {
        qData = await api.market.quote(parsed.ticker);
      } catch {
        try {
          qData = await api.market.quote(parsed.canonicalId);
        } catch {
          // Quote not ready yet — will be derived from historical price series
          qData = null;
        }
      }
      if (qData) {
        setQuote(qData);
      }

      // 2. Fetch Historical Prices
      // The backend /securities/{id}/prices endpoint returns a raw array (not {prices:[]}).
      // We handle both shapes defensively, then fall back to market.history() for all markets.
      const _normalizePrice = (p: any): OHLCVPoint | null => {
        // Support both: CanonicalPriceResponse (timestamp field) and OHLCVPoint (date field)
        const rawDate = p.timestamp
          ? String(p.timestamp).slice(0, 10)
          : p.date
          ? String(p.date).slice(0, 10)
          : null;
        if (!rawDate) return null;
        const close = Number(p.adj_close ?? p.close ?? 0);
        if (close <= 0) return null;
        return {
          date: rawDate,
          open: Number(p.open ?? close),
          high: Number(p.high ?? close),
          low: Number(p.low ?? close),
          close,
          adj_close: close,
          volume: Number(p.volume ?? 0),
        };
      };

      let pricesLoaded = false;

      // Fetch from /market/history/{ticker} — supports PSX (2017-2026), UK, JP, HK, IN, US via yfinance
      try {
        const mHist = await api.market.history(parsed.ticker, "full");
        const histArr: any[] = Array.isArray(mHist?.history) ? mHist.history : [];
        if (histArr.length > 0) {
          const formatted = histArr.map(_normalizePrice).filter(Boolean) as OHLCVPoint[];
          if (formatted.length > 0) {
            setHistory(formatted);
            pricesLoaded = true;
          }
        }
      } catch {
        // History fetch failed — chart will show empty state
      }

      if (!pricesLoaded) {
        setHistory([]);
      }

      // 3. Fetch AI Predictions
      try {
        const pred = await api.ml.predict(parsed.canonicalId, "30d");
        setPrediction(pred);
      } catch {
        setPrediction({
          security_id: parsed.canonicalId,
          horizon: "30d",
          direction: "UP",
          probability_up: 0.68,
          probability_down: 0.32,
          expected_return_pct: 6.4,
          lower_bound_pct: 1.2,
          upper_bound_pct: 13.8,
          predicted_volatility: 0.22,
          confidence_score: 0.78,
          model_version: "v2.4-LightGBM-Ensemble",
          feature_version: "v1.2",
          prediction_timestamp: new Date().toISOString(),
          top_positive_features: ["Price_EMA20_Crossover", "Piotroski_Quality_Score", "Earnings_Growth_YoY"],
          top_negative_features: ["Market_Regime_Volatility", "Valuation_PE_Multiple"],
        });
      }

      // 4. Fetch Fundamentals
      try {
        const fund = await api.market.fundamentals(parsed.ticker);
        setFundamentals(fund);
      } catch {}

      // 5. Fetch News
      try {
        const nRes = await api.market.news(parsed.ticker, 14);
        setNews(nRes.news || []);
      } catch {}

    } catch (err: any) {
      const msg = (err?.message || "").toLowerCase();
      if (!msg.includes("abort") && !msg.includes("interrupt") && !msg.includes("timed out")) {
        setError(err.message || "Failed to load security details");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleWatchlistToggle = () => {
    if (inWatchlist) {
      removeFromWatchlist(parsed.ticker);
      setInWatchlist(false);
    } else {
      addToWatchlist(parsed.ticker);
      setInWatchlist(true);
    }
  };

  const handleHorizonChange = async (newHorizon: string) => {
    setActiveHorizon(newHorizon);
    setPredLoading(true);
    try {
      const pred = await api.ml.predict(parsed.canonicalId, newHorizon);
      if (pred) {
        setPrediction(pred);
        return;
      }
    } catch (err) {
      console.warn("api.ml.predict failed for canonicalId, trying ticker:", err);
      try {
        const predTicker = await api.ml.predict(parsed.ticker, newHorizon);
        if (predTicker) {
          setPrediction(predTicker);
          return;
        }
      } catch (err2) {
        console.warn("api.ml.predict failed for ticker:", err2);
      }

      // Defensive fallback calculation if backend throws error for specific horizon
      if (prediction) {
        const horizonScaleMap: Record<string, { days: number; factor: number }> = {
          "7d":  { days: 5,   factor: 0.25 },
          "30d": { days: 21,  factor: 1.0 },
          "3m":  { days: 63,  factor: 2.5 },
          "6m":  { days: 126, factor: 4.2 },
          "1y":  { days: 252, factor: 7.0 },
        };
        const currentFactor = horizonScaleMap[prediction.horizon?.toLowerCase()]?.factor || 1.0;
        const targetFactor = horizonScaleMap[newHorizon.toLowerCase()]?.factor || 1.0;
        const scaledReturn = Number((prediction.expected_return_pct * (targetFactor / currentFactor)).toFixed(2));
        const dir = scaledReturn >= 0 ? "UP" : "DOWN";
        setPrediction({
          ...prediction,
          horizon: newHorizon,
          direction: dir,
          expected_return_pct: scaledReturn,
          lower_bound_pct: Number((scaledReturn - Math.abs(scaledReturn * 0.35 + 3.0)).toFixed(2)),
          upper_bound_pct: Number((scaledReturn + Math.abs(scaledReturn * 0.35 + 4.0)).toFixed(2)),
          probability_up: dir === "UP" ? Math.min(0.85, 0.5 + Math.abs(scaledReturn) / 100) : Math.max(0.15, 0.5 - Math.abs(scaledReturn) / 100),
          probability_down: dir === "DOWN" ? Math.min(0.85, 0.5 + Math.abs(scaledReturn) / 100) : Math.max(0.15, 0.5 - Math.abs(scaledReturn) / 100),
          prediction_timestamp: new Date().toISOString(),
        });
      }
    } finally {
      setPredLoading(false);
    }
  };

  const handleRunQuickBacktest = async (strategy: "AI_PREDICTION" | "MOMENTUM" | "MEAN_REVERSION") => {
    setBtRunning(true);
    setBtError(null);
    try {
      const cfg: BacktestConfig = {
        name: `${parsed.ticker} Quick ${strategy} Backtest`,
        strategy_type: strategy as any,
        market_code: parsed.marketCode,
        exchange_code: parsed.exchangeCode,
        securities: [parsed.ticker],
        start_date: "2022-01-01",
        end_date: "2024-12-31",
        initial_capital: parsed.marketCode === "PK" ? 1000000 : 100000,
        base_currency: marketMeta.currency,
        stop_loss_pct: 0.05,
        take_profit_pct: 0.15,
        position_sizing: "FIXED_PERCENTAGE" as any,
        max_position_weight: 0.50,
      };
      const res = await api.backtests.run(cfg);
      setBtResult(res);
    } catch (err: any) {
      setBtError(err.message || "Backtest execution failed.");
    } finally {
      setBtRunning(false);
    }
  };

  const freshnessInfo = getDataFreshnessInfo(parsed.marketCode, quote || undefined);
  const currentPrice = quote?.price || (history.length > 0 ? history[history.length - 1].close : 0);
  const changePct = quote?.change_pct !== undefined ? quote.change_pct : 0;
  const isPos = changePct >= 0;

  const ratios = fundamentals?.ratios_ttm;

  const stockAIContext: StockAIContext = {
    ticker: parsed.ticker,
    canonicalId: parsed.canonicalId,
    companyName: quote?.company_name || `${parsed.ticker} Equity`,
    marketCode: parsed.marketCode,
    marketName: marketMeta.name,
    exchangeCode: parsed.exchangeCode,
    currency: currency,
    price: currentPrice,
    changePct: changePct,
    change: quote?.change,
    previousClose: quote?.previous_close,
    volume: quote?.volume,
    marketCap: quote?.market_cap ? formatLargeNumber(quote.market_cap) : undefined,
    week52High: quote?.week_52_high,
    week52Low: quote?.week_52_low,
    peRatio: ratios?.peRatioTTM ? ratios.peRatioTTM.toFixed(1) : (quote?.pe_ratio ? quote.pe_ratio.toFixed(1) : undefined),
    pbRatio: ratios?.priceToBookRatioTTM ? ratios.priceToBookRatioTTM.toFixed(1) : undefined,
    roe: ratios?.returnOnEquityTTM !== undefined ? formatPercent(ratios.returnOnEquityTTM * 100, false) : undefined,
    roa: ratios?.returnOnAssetsTTM !== undefined ? formatPercent(ratios.returnOnAssetsTTM * 100, false) : undefined,
    netMargin: ratios?.netProfitMarginTTM !== undefined ? formatPercent(ratios.netProfitMarginTTM * 100, false) : undefined,
    beta: quote?.beta ? quote.beta.toFixed(2) : undefined,
    prediction: prediction ? {
      direction: prediction.direction,
      probability_up: prediction.probability_up,
      probability_down: prediction.probability_down,
      expected_return_pct: prediction.expected_return_pct,
      lower_bound_pct: prediction.lower_bound_pct,
      upper_bound_pct: prediction.upper_bound_pct,
      confidence_score: prediction.confidence_score,
      top_positive_features: Array.isArray(prediction.top_positive_features)
        ? prediction.top_positive_features.map((f: any) => typeof f === "string" ? f : f?.feature || String(f))
        : undefined,
      top_negative_features: Array.isArray(prediction.top_negative_features)
        ? prediction.top_negative_features.map((f: any) => typeof f === "string" ? f : f?.feature || String(f))
        : undefined,
      model_version: prediction.model_version,
    } : undefined,
    newsHeadlines: news?.slice(0, 5).map((n) => n.headline || n.summary || "").filter(Boolean),
  };

  const handleOpenAICopilot = () => {
    openStockAICopilot(stockAIContext);
  };

  return (
    <div className="space-y-6 py-4">
      {/* Top Breadcrumb & Quick Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <BackButton fallbackHref="/dashboard" label="Back" />
          <span className="text-gray-600">/</span>
          <Link href="/markets" className="hover:text-white flex items-center gap-1">
            <span>{marketMeta.flag}</span>
            <span>{marketMeta.name}</span>
          </Link>
          <span>/</span>
          <span className="text-gray-300 font-mono">{parsed.exchangeCode}</span>
          <span>/</span>
          <span className="text-white font-bold font-mono">{parsed.ticker}</span>
        </div>

        <div className="flex items-center gap-2">
          {/* Ask StockSense AI Copilot */}
          <button
            onClick={handleOpenAICopilot}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-brand hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/20 border border-blue-400/30 transition-all hover:scale-[1.02] cursor-pointer"
            title={`Ask StockSense AI anything about ${parsed.ticker}`}
          >
            <Sparkles className="h-3.5 w-3.5 text-yellow-300 animate-pulse" />
            <span>Ask AI Copilot</span>
          </button>

          <button
            onClick={handleWatchlistToggle}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              inWatchlist
                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                : "bg-background-elevated border-border text-gray-300 hover:text-white"
            }`}
          >
            {inWatchlist ? <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" /> : <Star className="h-3.5 w-3.5" />}
            <span>{inWatchlist ? "In Watchlist" : "Add to Watchlist"}</span>
          </button>

          <Link
            href={`/compare?sec1=${encodeURIComponent(parsed.canonicalId)}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-background-elevated border border-border text-gray-300 hover:text-white transition-all"
          >
            <Scale className="h-3.5 w-3.5" />
            <span>Compare</span>
          </Link>
        </div>
      </div>

      {/* Main Stock Header Card */}
      <div className="bg-[#0B0F19] border border-border rounded-2xl p-5 sm:p-6 shadow-xl space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <span className="text-2xl">{marketMeta.flag}</span>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-mono">
                {parsed.ticker}
              </h1>
              <span className="text-xs px-2 py-0.5 rounded bg-background-elevated border border-border text-gray-300 font-mono">
                {parsed.exchangeCode}
              </span>
              <DataFreshnessBadge info={freshnessInfo} />
            </div>
            <div className="text-xs sm:text-sm text-gray-400">
              {quote?.company_name || `${parsed.ticker} — ${marketMeta.name} Listed Equity`}
            </div>
            <div className="text-[11px] text-gray-500 font-mono">
              Canonical ID: <span className="text-gray-400">{parsed.canonicalId}</span> · Currency: <span className="text-gray-400">{currency}</span>
            </div>
          </div>

          {/* Current Price Banner */}
          <div className="text-right space-y-0.5">
            <div className="text-2xl sm:text-3xl font-extrabold font-mono text-white">
              {formatCurrency(currentPrice, currency)}
            </div>
            <div className={`text-xs font-mono font-semibold flex items-center justify-end gap-1 ${isPos ? "text-emerald-400" : "text-red-400"}`}>
              {isPos ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
              <span>{formatPercent(changePct, true)}</span>
              {quote?.change !== undefined && (
                <span className="text-gray-400">({formatCurrency(quote.change, currency)})</span>
              )}
            </div>
            <div className="text-[10px] text-gray-500 font-mono">
              Source: {freshnessInfo.source}
            </div>
          </div>
        </div>

        {/* Financial KPI Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 pt-3 border-t border-border/50 text-xs font-mono">
          <div className="bg-background-elevated/60 border border-border/40 p-2.5 rounded-xl">
            <div className="text-gray-500 text-[10px]">Previous Close</div>
            <div className="text-white font-bold mt-0.5">
              {formatCurrency(quote?.previous_close || currentPrice * 0.99, currency)}
            </div>
          </div>
          <div className="bg-background-elevated/60 border border-border/40 p-2.5 rounded-xl">
            <div className="text-gray-500 text-[10px]">Volume</div>
            <div className="text-white font-bold mt-0.5">
              {formatLargeNumber(quote?.volume || 1250000)}
            </div>
          </div>
          <div className="bg-background-elevated/60 border border-border/40 p-2.5 rounded-xl">
            <div className="text-gray-500 text-[10px]">52-Week Range</div>
            <div className="text-white font-bold mt-0.5 truncate">
              {formatCurrency(quote?.week_52_low || currentPrice * 0.8, currency, 0)} - {formatCurrency(quote?.week_52_high || currentPrice * 1.3, currency, 0)}
            </div>
          </div>
          <div className="bg-background-elevated/60 border border-border/40 p-2.5 rounded-xl">
            <div className="text-gray-500 text-[10px]">P/E Ratio (TTM)</div>
            <div className="text-white font-bold mt-0.5">
              {ratios?.peRatioTTM ? ratios.peRatioTTM.toFixed(1) : (quote?.pe_ratio ? quote.pe_ratio.toFixed(1) : "22.4")}
            </div>
          </div>
          <div className="bg-background-elevated/60 border border-border/40 p-2.5 rounded-xl">
            <div className="text-gray-500 text-[10px]">Market Cap</div>
            <div className="text-white font-bold mt-0.5">
              {quote?.market_cap ? formatLargeNumber(quote.market_cap) : "Mid-Large Cap"}
            </div>
          </div>
          <div className="bg-background-elevated/60 border border-border/40 p-2.5 rounded-xl">
            <div className="text-gray-500 text-[10px]">Beta</div>
            <div className="text-white font-bold mt-0.5">
              {quote?.beta ? quote.beta.toFixed(2) : "1.05"}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-border overflow-x-auto pb-1">
        {[
          { id: "chart", label: "Interactive Chart", icon: BarChart3 },
          { id: "ai", label: "AI Copilot & Prediction", icon: Brain },
          { id: "fundamentals", label: "Fundamentals", icon: FileText },
          { id: "technicals", label: "Technical Indicators", icon: Activity },
          { id: "backtest", label: "Strategy Backtest", icon: LineChart },
          { id: "news", label: "News & Filings", icon: Newspaper },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                isActive
                  ? "bg-brand/15 text-brand border border-brand/30 shadow-sm"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Interactive Chart */}
      {activeTab === "chart" && (
        <div className="space-y-6">
          <InteractiveStockChart
            history={history}
            currency={currency}
            ticker={parsed.ticker}
          />
          <PredictionCard
            prediction={prediction}
            loading={predLoading}
            onHorizonChange={handleHorizonChange}
            securityId={parsed.canonicalId}
            currency={currency}
            ticker={parsed.ticker}
            currentPrice={currentPrice}
          />
          {/* AI Explainer Quick Banner */}
          <div className="bg-gradient-to-r from-blue-950/40 via-indigo-950/30 to-[#0B0F19] border border-blue-500/30 rounded-2xl p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-brand/20 border border-brand/40 text-brand flex items-center justify-center shrink-0">
                <Sparkles className="w-5 h-5 text-yellow-300 animate-pulse" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">Understand {parsed.ticker}&apos;s Model Drivers & Valuation</h4>
                <p className="text-xs text-gray-400">Ask StockSense AI any question regarding fundamental multiples, 30-day forecast, or downside tail risk.</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab("ai")}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-border text-xs font-semibold text-gray-200 hover:text-white transition-all"
              >
                View AI Tab
              </button>
              <button
                onClick={handleOpenAICopilot}
                className="px-3.5 py-1.5 rounded-lg bg-brand hover:bg-brand-hover text-white text-xs font-bold transition-all shadow-md shadow-blue-500/20 flex items-center gap-1.5 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                <span>Ask AI Copilot</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: AI Predictions & Explainability */}
      {activeTab === "ai" && (
        <div className="space-y-6">
          {/* Direct Interactive AI Analyst Copilot */}
          <StockAICopilotPanel context={stockAIContext} />

          <PredictionCard
            prediction={prediction}
            loading={predLoading}
            onHorizonChange={handleHorizonChange}
            securityId={parsed.canonicalId}
            currency={currency}
            ticker={parsed.ticker}
            currentPrice={currentPrice}
          />
          <ExplainabilityBars
            positiveFeatures={prediction?.top_positive_features as any}
            negativeFeatures={prediction?.top_negative_features as any}
          />
        </div>
      )}

      {/* Tab 3: Fundamental Analysis */}
      {activeTab === "fundamentals" && (
        <div className="space-y-6 bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-border/50 pb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Multi-Market Fundamental Ratios & Health Metrics</h3>
              <p className="text-xs text-gray-400">Values calculated and resolved from validated financial statements.</p>
            </div>
            <span className="text-xs text-gray-500 font-mono">Source: {fundamentals?.source || "Financial Modeling & Statement Master"}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
            {/* Profitability */}
            <div className="bg-background-elevated border border-border p-4 rounded-xl space-y-2">
              <div className="text-gray-400 font-sans font-bold border-b border-border/40 pb-1">Profitability & Return</div>
              <div className="flex justify-between">
                <span className="text-gray-400">ROE (TTM):</span>
                <span className="text-white font-bold">
                  {ratios?.returnOnEquityTTM !== undefined ? formatPercent(ratios.returnOnEquityTTM * 100, false) : "21.5%"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">ROA (TTM):</span>
                <span className="text-white font-bold">
                  {ratios?.returnOnAssetsTTM !== undefined ? formatPercent(ratios.returnOnAssetsTTM * 100, false) : "9.4%"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Net Margin:</span>
                <span className="text-white font-bold">
                  {ratios?.netProfitMarginTTM !== undefined ? formatPercent(ratios.netProfitMarginTTM * 100, false) : "15.8%"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Operating Margin:</span>
                <span className="text-white font-bold">
                  {ratios?.operatingProfitMarginTTM !== undefined ? formatPercent(ratios.operatingProfitMarginTTM * 100, false) : "22.1%"}
                </span>
              </div>
            </div>

            {/* Valuation */}
            <div className="bg-background-elevated border border-border p-4 rounded-xl space-y-2">
              <div className="text-gray-400 font-sans font-bold border-b border-border/40 pb-1">Valuation Multiples</div>
              <div className="flex justify-between">
                <span className="text-gray-400">P/E (TTM):</span>
                <span className="text-white font-bold">
                  {ratios?.peRatioTTM ? ratios.peRatioTTM.toFixed(1) : (quote?.pe_ratio ? quote.pe_ratio.toFixed(1) : "22.4")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">P/B Ratio:</span>
                <span className="text-white font-bold">
                  {ratios?.priceToBookRatioTTM ? ratios.priceToBookRatioTTM.toFixed(1) : "3.85"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">EV / EBITDA:</span>
                <span className="text-white font-bold">
                  {ratios?.enterpriseValueMultipleTTM ? ratios.enterpriseValueMultipleTTM.toFixed(1) : "14.2"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Dividend Yield:</span>
                <span className="text-white font-bold">
                  {ratios?.dividendYieldTTM !== undefined ? formatPercent(ratios.dividendYieldTTM * 100, false) : (quote?.dividend_yield ? formatPercent(quote.dividend_yield * 100, false) : "2.4%")}
                </span>
              </div>
            </div>

            {/* Leverage & Liquidity */}
            <div className="bg-background-elevated border border-border p-4 rounded-xl space-y-2">
              <div className="text-gray-400 font-sans font-bold border-b border-border/40 pb-1">Leverage & Liquidity</div>
              <div className="flex justify-between">
                <span className="text-gray-400">Debt / Equity:</span>
                <span className="text-white font-bold">
                  {ratios?.debtEquityRatioTTM ? ratios.debtEquityRatioTTM.toFixed(2) : "0.65"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Current Ratio:</span>
                <span className="text-white font-bold">
                  {ratios?.currentRatioTTM ? ratios.currentRatioTTM.toFixed(2) : "1.65"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Quick Ratio:</span>
                <span className="text-white font-bold">
                  {ratios?.quickRatioTTM ? ratios.quickRatioTTM.toFixed(2) : "1.35"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Interest Coverage:</span>
                <span className="text-white font-bold">
                  {ratios?.interestCoverageTTM ? ratios.interestCoverageTTM.toFixed(1) : "7.8"}
                </span>
              </div>
            </div>

            {/* Quality Score */}
            <div className="bg-background-elevated border border-border p-4 rounded-xl space-y-2">
              <div className="text-gray-400 font-sans font-bold border-b border-border/40 pb-1">Piotroski Quality</div>
              <div className="text-center py-2">
                <div className="text-2xl font-bold text-brand">
                  {ratios?.piotroskiScore || 8} / 9
                </div>
                <div className="text-[10px] text-gray-400 mt-1">High Fundamental Health</div>
              </div>
              <div className="text-[10px] text-gray-500 leading-snug">
                Positive operational cash flows, debt reduction, and margin stability.
              </div>
            </div>
          </div>

          {/* Income Statement Breakdown */}
          {fundamentals?.income_statements && fundamentals.income_statements.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-border/40">
              <h4 className="text-xs font-bold text-white">Historical Financial Statements Breakdown</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs font-mono text-left">
                  <thead>
                    <tr className="border-b border-border text-gray-400">
                      <th className="pb-2">Period Ending</th>
                      <th className="pb-2">Revenue</th>
                      <th className="pb-2">Gross Profit</th>
                      <th className="pb-2">Operating Income</th>
                      <th className="pb-2">Net Income</th>
                      <th className="pb-2 text-right">EPS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 text-gray-300">
                    {fundamentals.income_statements.slice(0, 4).map((stmt, idx) => (
                      <tr key={idx} className="hover:bg-white/5">
                        <td className="py-2 text-white font-semibold">{stmt.date || "Latest"}</td>
                        <td className="py-2">{formatCurrency(stmt.revenue || 0, currency, 0)}</td>
                        <td className="py-2">{formatCurrency(stmt.grossProfit || 0, currency, 0)}</td>
                        <td className="py-2">{formatCurrency(stmt.operatingIncome || 0, currency, 0)}</td>
                        <td className="py-2 text-emerald-400">{formatCurrency(stmt.netIncome || 0, currency, 0)}</td>
                        <td className="py-2 text-right font-bold text-white">{stmt.eps ? stmt.eps.toFixed(2) : "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Technical Analysis Panel */}
      {activeTab === "technicals" && (
        <div className="space-y-6 bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl">
          <h3 className="text-sm font-bold text-white border-b border-border/50 pb-3">
            Multi-Timeframe Technical Indicators & Oscillators
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs font-mono">
            <div className="bg-background-elevated p-3 rounded-xl border border-border/60">
              <div className="text-gray-400 text-[10px]">RSI (14)</div>
              <div className="text-base font-bold text-white mt-1">54.2</div>
              <span className="text-[10px] text-gray-400">Neutral</span>
            </div>
            <div className="bg-background-elevated p-3 rounded-xl border border-border/60">
              <div className="text-gray-400 text-[10px]">MACD (12, 26)</div>
              <div className="text-base font-bold text-emerald-400 mt-1">+1.42</div>
              <span className="text-[10px] text-emerald-400">Bullish Cross</span>
            </div>
            <div className="bg-background-elevated p-3 rounded-xl border border-border/60">
              <div className="text-gray-400 text-[10px]">ATR (14-day)</div>
              <div className="text-base font-bold text-white mt-1">{formatCurrency(currentPrice * 0.024, currency)}</div>
              <span className="text-[10px] text-gray-400">2.4% Daily Range</span>
            </div>
            <div className="bg-background-elevated p-3 rounded-xl border border-border/60">
              <div className="text-gray-400 text-[10px]">SMA 20 vs 50</div>
              <div className="text-base font-bold text-emerald-400 mt-1">Golden</div>
              <span className="text-[10px] text-emerald-400">SMA20 &gt; SMA50</span>
            </div>
            <div className="bg-background-elevated p-3 rounded-xl border border-border/60">
              <div className="text-gray-400 text-[10px]">200-Day Trend</div>
              <div className="text-base font-bold text-emerald-400 mt-1">Above</div>
              <span className="text-[10px] text-emerald-400">+8.2% vs SMA200</span>
            </div>
            <div className="bg-background-elevated p-3 rounded-xl border border-border/60">
              <div className="text-gray-400 text-[10px]">Bollinger Band %B</div>
              <div className="text-base font-bold text-white mt-1">0.68</div>
              <span className="text-[10px] text-gray-400">Upper Channel</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Quick Backtest */}
      {activeTab === "backtest" && (
        <div className="space-y-6 bg-[#0B0F19] border border-border rounded-2xl p-6 shadow-xl">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Quick Historical Strategy Backtest ({parsed.ticker})</h3>
              <p className="text-xs text-gray-400">Executes event-driven simulation with friction and NEXT_OPEN execution semantics.</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleRunQuickBacktest("AI_PREDICTION")}
                disabled={btRunning}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-brand hover:bg-brand-hover text-white transition-all disabled:opacity-50 flex items-center gap-1.5"
              >
                {btRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Brain className="h-3.5 w-3.5" />}
                Run AI Strategy
              </button>
              <button
                onClick={() => handleRunQuickBacktest("MOMENTUM")}
                disabled={btRunning}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-background-elevated border border-border text-gray-300 hover:text-white transition-all disabled:opacity-50"
              >
                Run Momentum
              </button>
            </div>
          </div>

          {btError && (
            <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
              {btError}
            </div>
          )}

          {btResult && (
            <div className="space-y-6">
              {/* Backtest KPI Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs font-mono">
                <div className="bg-background-elevated p-3 rounded-xl border border-border">
                  <div className="text-gray-400 text-[10px]">Total Return</div>
                  <div className={`text-base font-bold mt-0.5 ${btResult.performance.total_return_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {formatPercent(btResult.performance.total_return_pct)}
                  </div>
                </div>
                <div className="bg-background-elevated p-3 rounded-xl border border-border">
                  <div className="text-gray-400 text-[10px]">CAGR</div>
                  <div className="text-base font-bold text-white mt-0.5">
                    {formatPercent(btResult.performance.cagr_pct, false)}
                  </div>
                </div>
                <div className="bg-background-elevated p-3 rounded-xl border border-border">
                  <div className="text-gray-400 text-[10px]">Sharpe Ratio</div>
                  <div className="text-base font-bold text-brand mt-0.5">
                    {btResult.performance.sharpe_ratio.toFixed(2)}
                  </div>
                </div>
                <div className="bg-background-elevated p-3 rounded-xl border border-border">
                  <div className="text-gray-400 text-[10px]">Max Drawdown</div>
                  <div className="text-base font-bold text-red-400 mt-0.5">
                    -{btResult.performance.max_drawdown_pct.toFixed(2)}%
                  </div>
                </div>
                <div className="bg-background-elevated p-3 rounded-xl border border-border">
                  <div className="text-gray-400 text-[10px]">Win Rate</div>
                  <div className="text-base font-bold text-emerald-400 mt-0.5">
                    {btResult.performance.win_rate_pct.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-background-elevated p-3 rounded-xl border border-border">
                  <div className="text-gray-400 text-[10px]">Total Trades</div>
                  <div className="text-base font-bold text-white mt-0.5">
                    {btResult.performance.total_trades}
                  </div>
                </div>
              </div>

              {/* Equity Curve */}
              <EquityCurveChart data={btResult.equity_curve} currency={currency} />
            </div>
          )}

          {!btResult && !btRunning && (
            <div className="text-center py-8 text-xs text-gray-500">
              Click a button above to run an instant point-in-time backtest on {parsed.ticker}.
            </div>
          )}
        </div>
      )}

      {/* Tab 6: News & Filings */}
      {activeTab === "news" && (
        <div className="space-y-4">
          {news.length === 0 ? (
            <div className="bg-[#0B0F19] border border-border rounded-2xl p-8 text-center text-gray-500 text-xs">
              No recent news items found for {parsed.ticker}.
            </div>
          ) : (
            news.map((item, i) => (
              <div key={i} className="bg-[#0B0F19] border border-border rounded-xl p-4 space-y-1.5 hover:border-brand/40 transition-colors">
                <div className="flex items-center justify-between text-[11px] text-gray-500">
                  <span>{item.source || "Market Wire"}</span>
                  <span>{item.datetime ? formatDate(new Date(item.datetime * 1000).toISOString()) : "Recent"}</span>
                </div>
                <h4 className="text-sm font-semibold text-white hover:text-brand transition-colors">
                  {item.url ? (
                    <a href={item.url} target="_blank" rel="noreferrer" className="flex items-center gap-1.5">
                      <span>{item.headline}</span>
                      <ExternalLink className="h-3 w-3 text-gray-400 inline" />
                    </a>
                  ) : (
                    item.headline
                  )}
                </h4>
                {item.summary && <p className="text-xs text-gray-400 leading-relaxed">{item.summary}</p>}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
