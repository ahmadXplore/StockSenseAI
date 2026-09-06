/**
 * StockSense AI — Multi-Market Utilities & Metadata
 * Provides market identifiers, currency symbols, canonical security ID helpers, and data freshness rules.
 */

import { MarketCode, ExchangeCode, DataFreshnessInfo } from "./types";

export interface MarketMeta {
  code: MarketCode;
  name: string;
  country: string;
  flag: string;
  defaultExchange: ExchangeCode;
  exchanges: ExchangeCode[];
  currency: string;
  currencySymbol: string;
  benchmarkSymbol: string;
  benchmarkName: string;
  timezone: string;
  tradingHours: string;
  dataSource: string;
  defaultDataFreshness: "LIVE" | "DELAYED" | "LATEST_AVAILABLE_EOD";
  sampleSecurities: Array<{ id: string; ticker: string; name: string }>;
}

export const SUPPORTED_MARKETS_CONFIG: Record<string, MarketMeta> = {
  PK: {
    code: "PK",
    name: "Pakistan",
    country: "Pakistan",
    flag: "🇵🇰",
    defaultExchange: "PSX",
    exchanges: ["PSX"],
    currency: "PKR",
    currencySymbol: "Rs.",
    benchmarkSymbol: "KSE100",
    benchmarkName: "KSE-100 Index",
    timezone: "Asia/Karachi",
    tradingHours: "09:30 - 15:30 PKT",
    dataSource: "Yahoo Finance Live (.KA) / PSX Official",
    defaultDataFreshness: "LIVE",
    sampleSecurities: [
      { id: "PK.PSX.FFC", ticker: "FFC", name: "Fauji Fertilizer Company Limited" },
      { id: "PK.PSX.FFBL", ticker: "FFBL", name: "Fauji Fertilizer Bin Qasim Limited" },
      { id: "PK.PSX.ENGRO", ticker: "ENGRO", name: "Engro Corporation Limited" },
      { id: "PK.PSX.MEBL", ticker: "MEBL", name: "Meezan Bank Limited" },
      { id: "PK.PSX.HBL", ticker: "HBL", name: "Habib Bank Limited" },
      { id: "PK.PSX.OGDC", ticker: "OGDC", name: "Oil & Gas Development Co" },
    ],
  },
  US: {
    code: "US",
    name: "United States",
    country: "United States",
    flag: "🇺🇸",
    defaultExchange: "NASDAQ",
    exchanges: ["NASDAQ", "NYSE"],
    currency: "USD",
    currencySymbol: "$",
    benchmarkSymbol: "SPY",
    benchmarkName: "S&P 500 (SPY)",
    timezone: "America/New_York",
    tradingHours: "09:30 - 16:00 EST",
    dataSource: "Alpha Vantage / Finnhub / SEC EDGAR",
    defaultDataFreshness: "DELAYED",
    sampleSecurities: [
      { id: "US.NASDAQ.AAPL", ticker: "AAPL", name: "Apple Inc." },
      { id: "US.NASDAQ.MSFT", ticker: "MSFT", name: "Microsoft Corporation" },
      { id: "US.NASDAQ.NVDA", ticker: "NVDA", name: "NVIDIA Corporation" },
      { id: "US.NASDAQ.GOOGL", ticker: "GOOGL", name: "Alphabet Inc." },
      { id: "US.NYSE.JPM", ticker: "JPM", name: "JPMorgan Chase & Co." },
      { id: "US.NYSE.BRK_B", ticker: "BRK.B", name: "Berkshire Hathaway Inc." },
    ],
  },
  UK: {
    code: "UK",
    name: "United Kingdom",
    country: "United Kingdom",
    flag: "🇬🇧",
    defaultExchange: "LSE",
    exchanges: ["LSE"],
    currency: "GBP",
    currencySymbol: "£",
    benchmarkSymbol: "FTSE100",
    benchmarkName: "FTSE 100 Index",
    timezone: "Europe/London",
    tradingHours: "08:00 - 16:30 GMT",
    dataSource: "LSE Datafeed / Stooq",
    defaultDataFreshness: "DELAYED",
    sampleSecurities: [
      { id: "UK.LSE.AZN_L", ticker: "AZN.L", name: "AstraZeneca PLC" },
      { id: "UK.LSE.SHEL_L", ticker: "SHEL.L", name: "Shell PLC" },
      { id: "UK.LSE.HSBA_L", ticker: "HSBA.L", name: "HSBC Holdings PLC" },
      { id: "UK.LSE.BP_L", ticker: "BP.L", name: "BP PLC" },
    ],
  },
};

/**
 * Parses canonical security identifier (e.g. "PK.PSX.ENGRO" or "US::NASDAQ::AAPL" or raw "AAPL")
 */
export function parseSecurityId(rawId: string, activeMarket?: string): {
  marketCode: MarketCode;
  exchangeCode: ExchangeCode;
  ticker: string;
  canonicalId: string;
} {
  if (!rawId) {
    const defaultM = (activeMarket?.toUpperCase() || "PK") as MarketCode;
    const defaultSec = defaultM === "PK" ? { marketCode: "PK", exchangeCode: "PSX", ticker: "FFC", canonicalId: "PK.PSX.FFC" } : { marketCode: "US", exchangeCode: "NASDAQ", ticker: "AAPL", canonicalId: "US.NASDAQ.AAPL" };
    return defaultSec as any;
  }

  const clean = rawId.replace(/::/g, ".");
  const parts = clean.split(".");

  if (parts.length >= 3) {
    const marketCode = parts[0].toUpperCase() as MarketCode;
    const exchangeCode = parts[1].toUpperCase() as ExchangeCode;
    let ticker = parts.slice(2).join(".").toUpperCase();

    // Normalize underscores from canonical format (e.g. AZN_L -> AZN.L)
    if (marketCode === "UK" && ticker.endsWith("_L")) ticker = `${ticker.slice(0, -2)}.L`;
    else if (marketCode === "PK" && (ticker.endsWith("_KA") || ticker.endsWith(".KA"))) ticker = ticker.replace(/(_KA|\.KA)$/, "");

    const cleanCanonicalSym = ticker.replace(/\.(L|KA)$/, "");
    return {
      marketCode,
      exchangeCode,
      ticker,
      canonicalId: `${marketCode}.${exchangeCode}.${cleanCanonicalSym}`,
    };
  }

  const upper = rawId.toUpperCase();

  // 1. Check known US mega/large-caps — these must NEVER be converted to PSX
  const usKnown = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "TSLA", "META", "NFLX", "AMD",
    "INTC", "JPM", "BAC", "V", "MA", "DIS", "WMT", "PG", "JNJ", "UNH", "HD", "XOM",
    "CVX", "BRK.B", "BRK.A", "SPY", "QQQ", "IWM", "COIN", "PLTR", "UBER", "ABNB",
    "CRM", "ORCL", "CSCO", "ADBE", "PYPL", "COST", "PEP", "KO", "AVGO", "TXN", "QCOM",
    "IBM", "BA", "GE", "CAT", "MMM", "GS", "MS", "WFC", "C", "AXP", "BLK", "SCHW"
  ];
  if (usKnown.includes(upper) || upper.startsWith("US.") || upper.startsWith("NASDAQ:") || upper.startsWith("NYSE:")) {
    const bare = upper.replace(/^US\.NASDAQ\./, "").replace(/^US\.NYSE\./, "").replace(/^US\./, "").replace(/^(NASDAQ|NYSE):/, "");
    return { marketCode: "US", exchangeCode: "NASDAQ", ticker: bare, canonicalId: `US.NASDAQ.${bare}` };
  }

  // 2. Explicit Suffix Heuristics
  if (upper.endsWith(".KA") || upper.endsWith("_KA") || upper.startsWith("PK.") || upper.startsWith("PSX:")) {
    const bare = upper.replace(/^PK\.PSX\./, "").replace(/^PK\./, "").replace(/^PSX:/, "").replace(/(\.KA|_KA)$/, "");
    return { marketCode: "PK", exchangeCode: "PSX", ticker: bare, canonicalId: `PK.PSX.${bare}` };
  }
  if (upper.endsWith(".L") || upper.endsWith("_L") || upper.startsWith("UK.")) {
    const bare = upper.replace(/^UK\.LSE\./, "").replace(/^UK\./, "").replace(/(\.L|_L)$/, "");
    return { marketCode: "UK", exchangeCode: "LSE", ticker: `${bare}.L`, canonicalId: `UK.LSE.${bare}` };
  }

  // 3. Check known PSX symbols
  const psxKnown = [
    "FFC", "FFBL", "ENGRO", "MEBL", "HBL", "MCB", "LUCK", "OGDC", "SYS", "UBL", "PPL",
    "EFERT", "HUBC", "PSO", "TRG", "KOSM", "BOP", "PAEL", "SEARL", "CHCC", "DGKC",
    "FCCL", "MLCF", "ATRL", "PRL", "SNGP", "SSGC", "BAFL", "BAHL", "AKBL", "NML", "LOTCHEM"
  ];
  if (psxKnown.includes(upper)) {
    return { marketCode: "PK", exchangeCode: "PSX", ticker: upper, canonicalId: `PK.PSX.${upper}` };
  }

  // 4. Active market awareness fallback for unknown symbols
  if (activeMarket?.toUpperCase() === "PK") {
    return { marketCode: "PK", exchangeCode: "PSX", ticker: upper, canonicalId: `PK.PSX.${upper}` };
  }
  if (activeMarket?.toUpperCase() === "UK") {
    return { marketCode: "UK", exchangeCode: "LSE", ticker: `${upper}.L`, canonicalId: `UK.LSE.${upper}` };
  }

  // Default to US NASDAQ
  return { marketCode: "US", exchangeCode: "NASDAQ", ticker: upper, canonicalId: `US.NASDAQ.${upper}` };
}

/**
 * Builds canonical security identifier
 */
export function buildSecurityId(marketCode: string, exchangeCode: string, ticker: string): string {
  return `${marketCode.toUpperCase()}.${exchangeCode.toUpperCase()}.${ticker.toUpperCase()}`;
}

/**
 * Determines accurate data freshness status and label
 */
export function getDataFreshnessInfo(
  marketCode: string,
  quoteOrPrice?: { is_delayed?: boolean; as_of_date?: string; source?: string }
): DataFreshnessInfo {
  const mkt = SUPPORTED_MARKETS_CONFIG[marketCode.toUpperCase()] || SUPPORTED_MARKETS_CONFIG.US;
  
  const src = quoteOrPrice?.source || mkt.dataSource;
  const isLive = src.includes("Yahoo Finance") || src.includes("Live") || quoteOrPrice?.is_delayed === false;

  if (isLive) {
    return {
      status: "LIVE",
      source: src,
    };
  }

  if (quoteOrPrice?.source === "PSX Official Historical Dataset (2017-2025)") {
    return {
      status: "LATEST_AVAILABLE_EOD",
      asOfDate: quoteOrPrice?.as_of_date || "2025-01-15",
      source: "PSX Official Daily EOD Dataset",
    };
  }

  return {
    status: mkt.defaultDataFreshness,
    delayMinutes: 15,
    asOfDate: quoteOrPrice?.as_of_date,
    source: src,
  };
}

