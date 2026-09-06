/**
 * StockSense AI — Centralized Backend API Client
 * Strictly connects to backend /api/v1/* endpoints with in-memory caching and fast request resilience.
 */

import {
  MarketCode, ExchangeCode,
  SupportedMarket, SupportedExchange, SecurityDTO, SecuritySearchResult,
  LiveQuote, MarketOverview, MarketRegime, MacroData, PriceHistoryResponse,
  FundamentalsData, NewsItem, MLPrediction, ModelMetadata, DriftCheckResponse,
  BacktestConfig, BacktestResponse, BacktestRunSummary, OptimizationRequest,
  OptimizationResponse, HistoricalStressResult, MonteCarloSimulationResult,
  PortfolioSummary, PortfolioPosition, RiskLimit, RiskEvent, ProviderHealth,
  FaceUser, FaceAuthResponse, OHLCVPoint
} from "./types";

const BASE = "/api/v1";

// Lightweight in-memory client cache
const _CLIENT_CACHE: Record<string, { timestamp: number; data: any }> = {};

function getCached<T>(key: string, ttlMs = 30_000): T | null {
  const item = _CLIENT_CACHE[key];
  if (item && Date.now() - item.timestamp < ttlMs) {
    return item.data as T;
  }
  return null;
}

function setCached(key: string, data: any): void {
  _CLIENT_CACHE[key] = { timestamp: Date.now(), data };
}

async function apiFetch<T>(path: string, options?: RequestInit, timeoutMs = 30000): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    try {
      controller.abort(new Error(`Request to ${path} timed out after ${timeoutMs}ms`));
    } catch {}
  }, timeoutMs);

  let token = "";
  if (typeof window !== "undefined") {
    token = sessionStorage.getItem("stocksense_auth_token") || localStorage.getItem("stocksense_auth_token") || "";
    if (!token) {
      const userStr = sessionStorage.getItem("stocksense_user") || localStorage.getItem("stocksense_user");
      if (userStr) {
        try {
          const parsed = JSON.parse(userStr);
          token = parsed.token || "";
        } catch {}
      }
    }
  }

  const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  try {
    const res = await fetch(`${BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
        ...(options?.headers ?? {}),
      },
      signal: options?.signal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let detail = `API error ${res.status}`;
      try {
        const body = await res.json();
        detail = body?.detail || body?.message || detail;
      } catch {}
      throw new Error(detail);
    }
    return res.json() as Promise<T>;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err?.name === "AbortError" || String(err?.message || "").toLowerCase().includes("abort")) {
      throw new Error(`Request timed out or was interrupted. Please retry.`);
    }
    throw err;
  }
}

// ─────────────────────────────────────────────────────────
// API Service Namespace
// ─────────────────────────────────────────────────────────

export const api = {
  // 1. Markets & Exchanges
  markets: {
    list: () => apiFetch<SupportedMarket[]>("/markets"),
    exchanges: () => apiFetch<SupportedExchange[]>("/exchanges"),
    universe: (marketCode: string) => apiFetch<{ market_code: string; securities: string[] }>(`/universe/${marketCode}`),
  },

  // 2. Security Master & Prices
  securities: {
    search: async (query: string, market?: string) => {
      if (!query || !query.trim()) return [];
      const qClean = query.trim();
      const seenIds = new Set<string>();
      const combined: SecuritySearchResult[] = [];

      // 1. Instant local multi-exchange search (PSX 530+ companies, US, UK, JP, HK, IN)
      try {
        const localRes = await fetch(
          `/api/company-search?q=${encodeURIComponent(qClean)}${market ? `&market=${encodeURIComponent(market)}` : ""}&limit=20`
        );
        if (localRes.ok) {
          const localList: SecuritySearchResult[] = await localRes.json();
          for (const s of localList) {
            if (!seenIds.has(s.ticker.toUpperCase())) {
              seenIds.add(s.ticker.toUpperCase());
              combined.push(s);
            }
          }
        }
      } catch {}

      // 2. Query backend canonical /securities/search (Yahoo Finance live + DB) if 2+ characters
      if (qClean.length >= 2) {
        try {
          const raw = await apiFetch<any[]>(
            `/securities/search?q=${encodeURIComponent(qClean)}${market ? `&market=${market}` : ""}`,
            undefined,
            4000
          );
          if (Array.isArray(raw) && raw.length > 0) {
            for (const s of raw) {
              const sym = (s.symbol || s.ticker || s.security_id || "").toUpperCase();
              if (sym && !seenIds.has(sym)) {
                seenIds.add(sym);
                combined.push({
                  security_id: s.security_id || `${s.market_id || "US"}.${s.exchange_id || "NASDAQ"}.${sym}`,
                  ticker: s.symbol || s.ticker || s.security_id || "",
                  name: s.company_name || s.name || `${sym} Equity`,
                  market_code: (s.market_id || s.market_code || "US") as MarketCode,
                  exchange_code: (s.exchange_id || s.exchange_code || "NASDAQ") as ExchangeCode,
                  currency: s.currency || "USD",
                  sector: s.sector || "Equities",
                  is_active: s.status === "ACTIVE" || s.is_active !== false,
                });
              }
            }
          }
        } catch {}
      }

      // 3. Resilient fallback to /market/search if needed
      if (combined.length === 0) {
        try {
          const mResults = await apiFetch<Array<{ ticker: string; name: string; exchange: string; sector: string }>>(
            `/market/search?q=${encodeURIComponent(qClean)}${market ? `&market=${market}` : ""}`
          );
          for (const m of mResults || []) {
            const sym = m.ticker.toUpperCase();
            if (!seenIds.has(sym)) {
              seenIds.add(sym);
              const ex = (m.exchange || "NASDAQ").toUpperCase();
              const mCode = ex === "PSX" ? "PK" : ex === "LSE" ? "UK" : ex === "TSE" ? "JP" : ex === "HKEX" ? "HK" : ex === "NSE" || ex === "BSE" ? "IN" : "US";
              combined.push({
                security_id: `${mCode}.${ex}.${m.ticker}`,
                ticker: m.ticker,
                name: m.name,
                market_code: mCode as MarketCode,
                exchange_code: ex as ExchangeCode,
                currency: mCode === "PK" ? "PKR" : mCode === "UK" ? "GBP" : mCode === "JP" ? "JPY" : mCode === "HK" ? "HKD" : mCode === "IN" ? "INR" : "USD",
                sector: m.sector,
                is_active: true,
              });
            }
          }
        } catch {}
      }

      return combined;
    },
    get: (securityId: string) =>
      apiFetch<SecurityDTO>(`/securities/${encodeURIComponent(securityId)}`),
    prices: (securityId: string, startDate?: string, endDate?: string) =>
      apiFetch<{ security_id: string; prices: OHLCVPoint[] }>(
        `/securities/${encodeURIComponent(securityId)}/prices${
          startDate ? `?start_date=${startDate}${endDate ? `&end_date=${endDate}` : ""}` : ""
        }`
      ),
  },

  // 3. Machine Learning & Predictions
  ml: {
    predict: (securityId: string, horizon = "30d") =>
      apiFetch<MLPrediction>(`/ml/predict/${encodeURIComponent(securityId)}`, {
        method: "POST",
        body: JSON.stringify({ horizon }),
      }),
    features: (securityId: string) =>
      apiFetch<{ security_id: string; features: Record<string, unknown>; feature_version: string }>(
        `/ml/features/${encodeURIComponent(securityId)}`
      ),
    models: () => apiFetch<ModelMetadata[]>("/ml/models"),
    drift: (modelId: string) =>
      apiFetch<DriftCheckResponse>(`/ml/monitoring/drift/${encodeURIComponent(modelId)}`),
  },

  // 4. Backtesting & Quantitative Risk
  backtests: {
    run: (config: BacktestConfig) =>
      apiFetch<BacktestResponse>("/backtests/run", {
        method: "POST",
        body: JSON.stringify(config),
      }, 120_000), // 120s timeout — backtest can be CPU-intensive
    list: (marketCode?: string, strategyType?: string, limit = 20) =>
      apiFetch<{ runs: BacktestRunSummary[]; count: number }>(
        `/backtests/runs?limit=${limit}${marketCode ? `&market_code=${marketCode}` : ""}${
          strategyType ? `&strategy_type=${strategyType}` : ""
        }`
      ),
    get: (runId: string) =>
      apiFetch<BacktestResponse>(`/backtests/runs/${encodeURIComponent(runId)}`),
    optimize: (request: OptimizationRequest) =>
      apiFetch<OptimizationResponse>("/backtests/optimize", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    stress: (payload: {
      securities: string[];
      market_code?: string;
      start_date?: string;
      end_date?: string;
      initial_portfolio_value?: number;
    }) =>
      apiFetch<HistoricalStressResult[]>("/backtests/stress", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    monteCarlo: (payload: {
      securities: string[];
      market_code?: string;
      lookback_start?: string;
      lookback_end?: string;
      initial_capital?: number;
      iterations?: number;
      horizon_days?: number;
      random_seed?: number;
    }) =>
      apiFetch<MonteCarloSimulationResult>("/backtests/monte-carlo", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    strategies: () =>
      apiFetch<{ strategies: Array<{ type: string; name: string; description: string; markets: string[] }> }>(
        "/backtests/strategies"
      ),
    template: (market = "US", strategy = "AI_PREDICTION") =>
      apiFetch<{ template: BacktestConfig; market_info: Record<string, unknown> }>(
        `/backtests/config/template?market=${market}&strategy=${strategy}`
      ),
  },

  // 5. Market Live Context, Macro & Realtime Quotes
  market: {
    overview: async () => {
      const cached = getCached<MarketOverview>("overview", 30_000);
      if (cached) return cached;
      const res = await apiFetch<MarketOverview>("/market/overview");
      setCached("overview", res);
      return res;
    },
    regime: () => apiFetch<MarketRegime>("/market/regime"),
    macro: () => apiFetch<MacroData>("/market/macro"),
    search: (q: string, market?: string) =>
      apiFetch<Array<{ ticker: string; name: string; exchange: string; sector: string }>>(
        `/market/search?q=${encodeURIComponent(q)}${market ? `&market=${market}` : ""}`
      ),
    quote: async (ticker: string) => {
      const clean = ticker.trim().toUpperCase();
      const cacheKey = `quote_${clean}`;
      const cached = getCached<LiveQuote>(cacheKey, 30_000);
      if (cached) return cached;
      const res = await apiFetch<LiveQuote>(`/market/quote/${encodeURIComponent(clean)}`, undefined, 20000);
      setCached(cacheKey, res);
      return res;
    },
    news: (ticker: string, days = 7) =>
      apiFetch<{ ticker: string; news: NewsItem[]; sentiment_score?: number; buzz?: unknown }>(
        `/market/news/${ticker}?days=${days}`
      ),
    fundamentals: (ticker: string) =>
      apiFetch<FundamentalsData>(`/market/fundamentals/${ticker}`),
    history: (ticker: string, outputSize: "compact" | "full" = "compact") =>
      apiFetch<PriceHistoryResponse>(`/market/history/${ticker}?output_size=${outputSize}`),
    earnings: (ticker: string) =>
      apiFetch<{ ticker: string; earnings: Array<{ date?: string; epsActual?: number; epsEstimate?: number; surprisePct?: number }> }>(
        `/market/earnings/${ticker}`
      ),
    insiders: (ticker: string) =>
      apiFetch<{ ticker: string; transactions: Array<{ name?: string; share?: number; value?: number; transactionType?: string; transactionDate?: string }> }>(
        `/market/insiders/${ticker}`
      ),
  },

  // 6. Portfolio & Risk Tracking
  portfolio: {
    get: () => apiFetch<PortfolioSummary>("/portfolio"),
    createPosition: (payload: {
      ticker: string;
      shares: number;
      entry_price: number;
      entry_date: string;
      entry_thesis?: string;
      entry_stop_loss_price?: number;
    }) =>
      apiFetch<PortfolioPosition>("/portfolio/positions", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    deletePosition: (positionId: string) =>
      apiFetch<{ success: boolean; message: string }>(`/portfolio/positions/${encodeURIComponent(positionId)}`, {
        method: "DELETE",
      }),
    seedDemo: () =>
      apiFetch<{ success: boolean; message: string }>("/portfolio/seed-demo", {
        method: "POST",
      }),
  },

  // 7. Watchlist Tracking
  watchlist: {
    get: () => apiFetch<{ items: Array<{ id: number; ticker: string; company_name: string; added_at: string; user_notes?: string }>; total_count: number }>("/watchlist"),
    add: (payload: { ticker: string; user_notes?: string }) =>
      apiFetch<{ id: number; ticker: string; company_name: string; added_at: string }>("/watchlist", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    remove: (ticker: string) =>
      apiFetch<void>(`/watchlist/${encodeURIComponent(ticker)}`, {
        method: "DELETE",
      }),
  },

  // 8. Quantitative Risk & Limits
  risk: {
    limits: () => apiFetch<RiskLimit[]>("/risk/limits"),
    events: () => apiFetch<RiskEvent[]>("/risk/events"),
  },

  // 9. System & Data Health
  data: {
    providersHealth: () => apiFetch<ProviderHealth[]>("/data/providers/health"),
    markets: () => apiFetch<SupportedMarket[]>("/markets"),
    exchanges: () => apiFetch<SupportedExchange[]>("/exchanges"),
    securitiesSearch: (q: string, market?: string) =>
      apiFetch<SecuritySearchResult[]>(
        `/securities/search?q=${encodeURIComponent(q)}${market ? `&market=${market}` : ""}`
      ),
  },

  // 10. Biometric Face Authentication
  auth: {
    faceSignup: (data: { name: string; email?: string; role?: string; admin_pin?: string; descriptor: number[] }) =>
      apiFetch<FaceAuthResponse>("/auth/face-signup", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    faceLogin: (data: { identifier?: string; descriptor: number[]; threshold?: number }) =>
      apiFetch<FaceAuthResponse>("/auth/face-login", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    getFaceUsers: () => apiFetch<FaceUser[]>("/auth/face-users"),
    deleteFaceUser: (userId: string) =>
      apiFetch<{ success: boolean; message: string }>(`/auth/face-users/${userId}`, {
        method: "DELETE",
      }),
  },

  // 11. Admin Panel & Enterprise Data Operations
  admin: {
    stats: () => apiFetch<import("./types").AdminStats>("/admin/stats"),
    users: (q?: string, statusFilter?: string) =>
      apiFetch<import("./types").AdminUser[]>(
        `/admin/users${q || statusFilter ? `?${q ? `q=${encodeURIComponent(q)}` : ""}${statusFilter ? `&status_filter=${statusFilter}` : ""}` : ""}`
      ),
    createUser: (data: { name: string; email: string; role?: string; is_active?: boolean; is_admin?: boolean }) =>
      apiFetch<import("./types").AdminUser>("/admin/users", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    updateUser: (userId: string, data: Partial<{ name: string; email: string; role: string; is_active: boolean; is_admin: boolean }>) =>
      apiFetch<import("./types").AdminUser>(`/admin/users/${encodeURIComponent(userId)}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    toggleBlockUser: (userId: string) =>
      apiFetch<{ success: boolean; user_id: string; is_active: boolean; message: string }>(`/admin/users/${encodeURIComponent(userId)}/toggle-block`, {
        method: "PATCH",
      }),
    deleteUser: (userId: string) =>
      apiFetch<{ success: boolean; message: string }>(`/admin/users/${encodeURIComponent(userId)}`, {
        method: "DELETE",
      }),
    uploadData: async (formData: FormData) => {
      const res = await fetch("/api/v1/admin/data/upload", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        let detail = `Upload error ${res.status}`;
        try {
          const body = await res.json();
          detail = body?.detail ?? detail;
        } catch {}
        throw new Error(detail);
      }
      return res.json() as Promise<{ success: boolean; filename: string; records_accepted: number; message: string }>;
    },
    purgeData: (target: string, marketCode?: string) =>
      apiFetch<{ success: boolean; message: string }>(
        `/admin/data/purge?target=${encodeURIComponent(target)}${marketCode ? `&market_code=${marketCode}` : ""}`,
        { method: "DELETE" }
      ),
    auditLogs: (limit = 25) =>
      apiFetch<import("./types").AdminAuditLog[]>(`/admin/audit-logs?limit=${limit}`),
  },

  // Health
  health: () => apiFetch<{ status: string }>("/health"),
};

// Export all types for convenient direct import from @/lib/api
export * from "./types";
export * from "./market";
export * from "./formatting";
export * from "./marketContext";
