/**
 * StockSense AI — localStorage helpers for Watchlist & Portfolio
 * Full persistent state with permanent deletion protection.
 */

// ─────────────────────────────────────────────────────────
// Watchlist
// ─────────────────────────────────────────────────────────

const WATCHLIST_KEY = "stocksense_watchlist";
const WATCHLIST_INIT_KEY = "stocksense_watchlist_initialized";

export interface WatchlistEntry {
  ticker: string;
  addedAt: string; // ISO string
}

export function getWatchlist(): WatchlistEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const isInitialized = localStorage.getItem(WATCHLIST_INIT_KEY);
    const raw = localStorage.getItem(WATCHLIST_KEY);
    
    // If first time ever opening app, seed default demo watchlist once
    if (!isInitialized) {
      const defaultList: WatchlistEntry[] = [
        { ticker: "ENGRO", addedAt: new Date().toISOString() },
        { ticker: "AAPL", addedAt: new Date().toISOString() },
        { ticker: "AZN.L", addedAt: new Date().toISOString() },
      ];
      localStorage.setItem(WATCHLIST_KEY, JSON.stringify(defaultList));
      localStorage.setItem(WATCHLIST_INIT_KEY, "true");
      return defaultList;
    }

    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addToWatchlist(ticker: string): void {
  if (typeof window === "undefined") return;
  const list = getWatchlist();
  const cleanTicker = ticker.toUpperCase().trim();
  if (!list.find((e) => e.ticker === cleanTicker)) {
    list.push({ ticker: cleanTicker, addedAt: new Date().toISOString() });
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
    localStorage.setItem(WATCHLIST_INIT_KEY, "true");
  }
}

export function removeFromWatchlist(ticker: string): void {
  if (typeof window === "undefined") return;
  const cleanTicker = ticker.toUpperCase().trim();
  const list = getWatchlist().filter(
    (e) => e.ticker !== cleanTicker
  );
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
  localStorage.setItem(WATCHLIST_INIT_KEY, "true");
}

export function isInWatchlist(ticker: string): boolean {
  return getWatchlist().some((e) => e.ticker === ticker.toUpperCase().trim());
}

export function resetWatchlistToDemo(): void {
  if (typeof window === "undefined") return;
  const defaultList: WatchlistEntry[] = [
    { ticker: "ENGRO", addedAt: new Date().toISOString() },
    { ticker: "AAPL", addedAt: new Date().toISOString() },
    { ticker: "AZN.L", addedAt: new Date().toISOString() },
  ];
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(defaultList));
  localStorage.setItem(WATCHLIST_INIT_KEY, "true");
}

// ─────────────────────────────────────────────────────────
// Portfolio
// ─────────────────────────────────────────────────────────

const PORTFOLIO_KEY = "stocksense_portfolio";
const PORTFOLIO_INIT_KEY = "stocksense_portfolio_initialized";

export interface PortfolioPosition {
  id: string;
  ticker: string;
  companyName: string;
  entryPrice: number;
  shares: number;
  entryDate: string; // YYYY-MM-DD
  stopLoss?: number;
  thesis?: string;
  addedAt: string; // ISO
}

export function getPortfolio(): PortfolioPosition[] {
  if (typeof window === "undefined") return [];
  try {
    const isInit = localStorage.getItem(PORTFOLIO_INIT_KEY);
    const raw = localStorage.getItem(PORTFOLIO_KEY);

    // If first time ever opening app, initialize once
    if (!isInit) {
      const defaultPositions: PortfolioPosition[] = [
        {
          id: "pos_demo_1",
          ticker: "AAPL",
          companyName: "Apple Inc.",
          entryPrice: 175.5,
          shares: 200,
          entryDate: "2024-01-15",
          thesis: "Ecosystem pricing power and hardware upgrade cycle",
          addedAt: new Date().toISOString(),
        },
        {
          id: "pos_demo_2",
          ticker: "ENGRO",
          companyName: "Engro Corporation Limited",
          entryPrice: 275.0,
          shares: 1000,
          entryDate: "2024-02-10",
          thesis: "Strong fertilizer margins, high dollar-linked dividends",
          addedAt: new Date().toISOString(),
        },
        {
          id: "pos_demo_3",
          ticker: "AZN.L",
          companyName: "AstraZeneca PLC",
          entryPrice: 105.0,
          shares: 350,
          entryDate: "2024-03-01",
          thesis: "Oncology pipeline expansion and international growth",
          addedAt: new Date().toISOString(),
        },
      ];
      localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(defaultPositions));
      localStorage.setItem(PORTFOLIO_INIT_KEY, "true");
      return defaultPositions;
    }

    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addPosition(pos: Omit<PortfolioPosition, "id" | "addedAt">): PortfolioPosition {
  const positions = getPortfolio();
  const newPos: PortfolioPosition = {
    ...pos,
    id: crypto.randomUUID ? crypto.randomUUID() : `pos_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    addedAt: new Date().toISOString(),
  };
  positions.push(newPos);
  localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(positions));
  localStorage.setItem(PORTFOLIO_INIT_KEY, "true");
  return newPos;
}

export function removePosition(id: string): void {
  const positions = getPortfolio().filter((p) => p.id !== id);
  localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(positions));
  localStorage.setItem(PORTFOLIO_INIT_KEY, "true");
}

export function updatePosition(id: string, updates: Partial<PortfolioPosition>): void {
  const positions = getPortfolio().map((p) =>
    p.id === id ? { ...p, ...updates } : p
  );
  localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(positions));
  localStorage.setItem(PORTFOLIO_INIT_KEY, "true");
}

export function resetPortfolioToDemo(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(PORTFOLIO_INIT_KEY);
  getPortfolio(); // triggers re-initialization
}
