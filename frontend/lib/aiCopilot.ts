/**
 * StockSense AI Copilot — Stock Context & Event Communication Layer
 * Connects the Stock Analysis page seamlessly with the institutional AI Copilot.
 */

export interface StockAIContext {
  ticker: string;
  canonicalId?: string;
  companyName?: string;
  marketCode?: string;
  marketName?: string;
  exchangeCode?: string;
  currency?: string;
  price?: number;
  changePct?: number;
  change?: number;
  previousClose?: number;
  volume?: number;
  marketCap?: number | string;
  week52High?: number;
  week52Low?: number;
  peRatio?: number | string;
  pbRatio?: number | string;
  roe?: number | string;
  roa?: number | string;
  netMargin?: number | string;
  beta?: number | string;
  prediction?: {
    direction?: string;
    probability_up?: number;
    probability_down?: number;
    expected_return_pct?: number;
    lower_bound_pct?: number;
    upper_bound_pct?: number;
    confidence_score?: number;
    top_positive_features?: string[];
    top_negative_features?: string[];
    model_version?: string;
  };
  newsHeadlines?: string[];
}

export interface OpenStockChatDetail {
  context: StockAIContext;
  initialPrompt?: string;
}

/**
 * Dispatches a custom window event to open the full-screen AI Copilot
 * with the active stock's context and an optional prompt.
 */
export function openStockAICopilot(context: StockAIContext, initialPrompt?: string) {
  if (typeof window !== "undefined") {
    const detail: OpenStockChatDetail = { context, initialPrompt };
    window.dispatchEvent(new CustomEvent("stocksense:open-stock-chat", { detail }));
  }
}

/**
 * Builds high-relevance prompt suggestion chips customized for this specific stock
 */
export function getStockSuggestedPrompts(ctx: StockAIContext): string[] {
  const ticker = ctx.ticker || "this security";
  const pred = ctx.prediction;
  const pe = ctx.peRatio;

  const prompts: string[] = [];

  if (pred?.direction) {
    const dir = pred.direction.toUpperCase();
    const prob = pred.probability_up ? Math.round(pred.probability_up * 100) : 68;
    prompts.push(`Why is the AI model predicting a ${dir} move (${prob}% probability) for ${ticker}?`);
  } else {
    prompts.push(`Explain the quantitative forecast and expected returns for ${ticker}`);
  }

  if (pe && pe !== "N/A") {
    prompts.push(`Is ${ticker}'s P/E multiple of ${pe} justified compared to historical & peer averages?`);
  } else {
    prompts.push(`Analyze ${ticker}'s valuation multiples and financial health metrics`);
  }

  if (pred?.top_positive_features?.length || pred?.top_negative_features?.length) {
    const pos = pred?.top_positive_features?.[0] || "Momentum";
    const neg = pred?.top_negative_features?.[0] || "Market Volatility";
    prompts.push(`Break down the primary bullish driver (${pos}) vs bearish risk (${neg}) for ${ticker}`);
  } else {
    prompts.push(`What are the key upside catalysts and downside risks for ${ticker}?`);
  }

  prompts.push(`Analyze technical momentum, RSI levels, and critical support/resistance for ${ticker}`);
  prompts.push(`What trading strategy or position sizing suits ${ticker} in the current market regime?`);

  return prompts;
}

/**
 * Generates an institutional initial greeting and briefing message for this stock
 */
export function buildStockInitialBrief(ctx: StockAIContext): string {
  const ticker = ctx.ticker;
  const name = ctx.companyName || ticker;
  const curr = ctx.currency || "USD";
  const priceStr = ctx.price !== undefined ? `${curr} ${ctx.price.toLocaleString()}` : "Market Price";
  const chgStr = ctx.changePct !== undefined ? `${ctx.changePct >= 0 ? "+" : ""}${ctx.changePct.toFixed(2)}%` : "";
  const dir = ctx.prediction?.direction?.toUpperCase() || "NEUTRAL";
  const prob = ctx.prediction?.probability_up ? `${Math.round(ctx.prediction.probability_up * 100)}%` : "N/A";
  const expRet = ctx.prediction?.expected_return_pct !== undefined ? `${ctx.prediction.expected_return_pct > 0 ? "+" : ""}${ctx.prediction.expected_return_pct.toFixed(1)}%` : "N/A";

  const posDrivers = ctx.prediction?.top_positive_features?.join(", ") || "Trend alignment, Earnings stability";
  const negDrivers = ctx.prediction?.top_negative_features?.join(", ") || "Macro volatility, Multiple compression";

  return `### 🎯 StockSense AI Copilot — Security Briefing: **${name} (${ticker})**

I have synchronized real-time multi-market data, fundamental statements, and quantitative ML drivers for **${ticker}**:

- **Current Market Quote:** **${priceStr}** ${chgStr ? `(\`${chgStr}\`)` : ""}
- **Exchange & Market:** ${ctx.marketName || "Equity Market"} (\`${ctx.exchangeCode || ctx.marketCode || "STOCK"}\`)
- **ML 30-Day Direction:** **${dir}** | **Probability:** **${prob}** | **Expected Return:** **${expRet}**
- **Valuation Multiples:** P/E (TTM): **${ctx.peRatio || "N/A"}** · P/B: **${ctx.pbRatio || "N/A"}** · ROE: **${ctx.roe || "N/A"}**
- **Top Bullish Drivers:** \`${posDrivers}\`
- **Top Risk Factors:** \`${negDrivers}\`

---

**How can I assist your analysis of ${ticker}?**
Select one of the quick inquiry chips below or ask anything about valuation, financial statements, technical setups, peer comparisons, or scenario stress testing!`;
}
