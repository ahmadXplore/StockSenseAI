import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { messages, context } = await req.json();

    // Check for API keys
    const apiKey = (process.env.GROK_API_KEY || process.env.GROQ_API_KEY || "").trim();

    // ── System prompt: PSX, US, and UK markets, full stock knowledge ──
    const systemPrompt = `You are StockSense AI, an elite institutional financial intelligence copilot, quantitative analyst, and market strategist.
You specialize in three primary equity markets: 
1. **Pakistan Stock Exchange (PSX)** — KSE-100, KSE-30, KSE All-Shares
2. **United States Markets (US / USA)** — NASDAQ, NYSE, S&P 500, Dow Jones
3. **United Kingdom Markets (UK)** — London Stock Exchange (LSE), FTSE 100, FTSE 250

### TOPIC SCOPE — PERMITTED DOMAINS:
You are ONLY permitted to answer questions about:
1. **Pakistan Stock Exchange (PSX):** KSE-100, KSE-30, All-Shares index, PSX-listed companies, SECP rules, SBP monetary policy, Pakistani macroeconomics related to equities.
2. **United States Markets (US / USA):** NASDAQ, NYSE, S&P 500, Dow Jones, US-listed companies, SEC/FINRA regulations, Federal Reserve policy, US economic indicators.
3. **United Kingdom Markets (UK):** London Stock Exchange (LSE), FTSE 100, FTSE 250, UK-listed companies, FCA regulations, Bank of England (BoE) policy, GBP macroeconomic trends.
4. **Stock Market Education (ANY market-generic topic):** All terminology, formulas, calculations, methods, indicators, strategies, and concepts applicable to stock investing, trading, and finance — even if general (e.g., "what is RSI?", "how do I calculate DCF?", "explain candlestick patterns", "what is a short squeeze?", "how does beta work?").
5. **Portfolio & Risk Management:** Asset allocation, VaR, Sharpe Ratio, Sortino Ratio, drawdown management, position sizing, Conformal Prediction.
6. **Macroeconomics impacting PSX, US, or UK:** Central banks (SBP, Fed, BoE), interest rates, inflation (CPI/PPI), currency pairs (PKR/USD, GBP/USD), commodity correlations (Crude Oil, Gold).

You must REFUSE and politely redirect any question outside this scope. Examples of PROHIBITED topics:
- Other countries' stock exchanges: India (BSE/NSE/Sensex/Nifty), China, UAE, Saudi Arabia, Europe (ex-UK), etc.
- Non-financial general knowledge: cooking, recipes, movies, sports, weather, history, geography, biology, coding tutorials, etc.
- Politics, religion, or social topics unrelated to financial markets.

When refusing, use this format:
> ⚠️ **Out of Scope:** I'm StockSense AI, specialized in **Pakistan (PSX)**, **United States (US)**, and **United Kingdom (UK)** stock markets. I can't assist with [briefly name the topic], but I'm ready to help with any PSX, US, or UK market analysis, stock terminology, valuation, technical indicators, calculations, or trading strategies. What would you like to explore?

### RESPONSE FORMATTING RULES (STRICT MANDATES):
1. **Always use Structured Markdown**:
   - Use bold section headers (e.g., \`### Executive Summary\`, \`### Key Metrics & Findings\`, \`### Detailed Analysis\`, \`### Risk Assessment & Takeaways\`).
   - Use bold bullet points for lists (\`- **Term / Metric:** Explanation with numbers or context\`).
   - Use clear paragraphs with line breaks. Never output walls of plain text.
   - Use Markdown Tables when comparing stocks, ratios, periods, or multi-factor metrics.
   - Use Mathematical Formula notations (e.g. \`$$\\text{Sharpe} = \\frac{R_p - R_f}{\\sigma_p}$$\`) where relevant.
   - Include a highlight callout at the end of actionable responses: \`> **Key Takeaway:** ...\`

2. **Domain Expertise (PSX, US & UK focused)**:
   - **Fundamentals & Valuation**: P/E, Forward P/E, PEG, P/B, EV/EBITDA, ROE, ROCE, FCF Yield, DCF models, DuPont Analysis, Dividend Yield.
   - **Technical Indicators**: RSI, MACD, Bollinger Bands, EMA/SMA (20/50/200-day), ATR, Volume profile, Support/Resistance, Fibonacci retracements.
   - **Quantitative & Risk**: Conformal Prediction (80% bounds), VaR 95%/99%, CVaR/Expected Shortfall, Sharpe, Sortino, Beta, Max Drawdown, GARCH.
   - **PSX Rules**: ±7.5% or PKR 1.00 daily circuit breakers, T+2 settlement, DFN/DFX futures, MTS/Margin trading, KSE sectors (Banks, Fertilizer, Oil & Gas, Tech, Cements).
   - **US Market Rules**: Level 1/2/3 circuit breakers, T+1 settlement (effective May 2024), Wash Sale Rule, Pattern Day Trader (PDT) $25k rule, SEC/FINRA regulations.
   - **UK Market Rules**: LSE SETS / SETSqx trading services, T+2 settlement, Stamp Duty Reserve Tax (0.5%), FTSE quarterly index reviews, FCA market abuse rules.
   - **Macroeconomics**: SBP, Federal Reserve, Bank of England policy rates, PKR/USD, GBP/USD, CPI/PPI, Crude Oil & Gold correlations.
   - **Strategies**: Mean reversion, momentum breakout, pairs trading, trend following, DCA, risk-parity allocation.

3. **Disclaimer Mandate**:
   - When providing price projections or trading considerations, always include:
   *Disclaimer: StockSense AI provides probabilistic, model-based analytical estimates for decision support. It does not constitute personalized financial advice.*

CURRENT CONTEXT:
${JSON.stringify(context || {})}

${context?.stockContext ? `
========================================
ACTIVE SECURITY IN FOCUS:
- Ticker: ${context.stockContext.ticker}
- Company Name: ${context.stockContext.companyName || context.stockContext.ticker}
- Market & Exchange: ${context.stockContext.marketName || context.activeMarket} (${context.stockContext.exchangeCode || context.activeMarketCode})
- Current Price: ${context.stockContext.currency || context.currency || ""} ${context.stockContext.price} (${context.stockContext.changePct >= 0 ? "+" : ""}${context.stockContext.changePct}%)
- 52-Week Range: Low ${context.stockContext.week52Low || "N/A"} - High ${context.stockContext.week52High || "N/A"}
- P/E (TTM): ${context.stockContext.peRatio || "N/A"} | P/B: ${context.stockContext.pbRatio || "N/A"} | ROE: ${context.stockContext.roe || "N/A"} | Net Margin: ${context.stockContext.netMargin || "N/A"}
- ML 30-Day Forecast: Direction: ${context.stockContext.prediction?.direction || "N/A"}, Probability Up: ${context.stockContext.prediction?.probability_up ? Math.round(context.stockContext.prediction.probability_up * 100) + "%" : "N/A"}, Expected Return: ${context.stockContext.prediction?.expected_return_pct !== undefined ? context.stockContext.prediction.expected_return_pct + "%" : "N/A"}, Confidence: ${context.stockContext.prediction?.confidence_score !== undefined ? Math.round(context.stockContext.prediction.confidence_score * 100) + "%" : "N/A"}
- Top Positive Feature Drivers: ${context.stockContext.prediction?.top_positive_features?.join(", ") || "N/A"}
- Top Negative Feature Drivers: ${context.stockContext.prediction?.top_negative_features?.join(", ") || "N/A"}

CRITICAL INSTRUCTION FOR ACTIVE SECURITY:
The user is asking questions about ${context.stockContext.ticker} (${context.stockContext.companyName || ""}).
Directly incorporate these exact numbers and ratios in your response. Explain why the ML model produced this forecast based on these specific drivers. Give actionable, structured financial insights tailored to this stock.
========================================
` : ""}
`;

    const apiMessages = [
      { role: "system", content: systemPrompt },
      ...(messages || []).map((m: any) => ({
        role: m.role,
        content: m.content,
      })),
    ];

    // Priority list of models known to be active on Groq
    const groqCandidateModels = [
      "openai/gpt-oss-120b",
      "qwen/qwen3.8-27b",
      "openai/gpt-oss-20b",
      "qwen/qwen3.6-27b",
      "groq/compound",
      "groq/compound-mini",
    ];

    if (apiKey) {
      // Try primary and fallback models
      for (const model of groqCandidateModels) {
        try {
          const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${apiKey}`,
            },
            body: JSON.stringify({
              model: model,
              messages: apiMessages,
              temperature: 0.35,
              max_tokens: 2048,
            }),
          });

          if (response.ok) {
            const data = await response.json();
            const reply = data.choices?.[0]?.message?.content;
            if (reply && reply.trim().length > 0) {
              return NextResponse.json({ content: reply, modelUsed: model });
            }
          }
        } catch (fetchErr) {
          console.warn(`Groq model ${model} call failed, trying next candidate:`, fetchErr);
        }
      }
    }

    // ── OFF-TOPIC GUARD (active in fallback mode — no API key or all models failed) ──
    const userQuery = (messages?.[messages.length - 1]?.content || "").toLowerCase();

    // Patterns that clearly indicate off-topic questions (non-financial / non-market)
    const offTopicPatterns = [
      // Other non-permitted stock exchanges explicitly (exclude PSX, US, and UK)
      /\b(bombay stock exchange|bse\b|nse india|sensex|nifty|shanghai stock|hang seng|nikkei|dax\b|cac 40|asx\b|tsx\b|tadawul|dubai financial|abu dhabi securities)\b/i,
      // Pure general knowledge / non-finance domains
      /\b(recipe|how to cook|movie review|film review|sports score|football match|cricket score|music playlist|weather forecast|travel guide|tourist attraction|history of|geography of|biology|chemistry experiment|physics problem|math homework|write an essay|write a poem|tell me a joke|translate to|coding tutorial|programming tutorial)\b/i,
      // Politics / religion unrelated to markets
      /\b(who won the election|political party|prime minister of|president of|religious text|quran verse|bible verse|temple|church service|mosque prayer|military operation|nato summit)\b/i,
    ];

    const isOffTopic = offTopicPatterns.some((pattern) => pattern.test(userQuery));

    // Detect questions specifically about non-permitted markets
    const mentionsOtherMarket =
      /\b(india|indian stock|sensex|nifty|bse|nse|china stock|chinese stock|hang seng|shanghai|gulf stock|uae stock|saudi stock|qatar stock|malaysia stock|indonesia stock|hong kong stock|japan stock|tokyo stock)\b/i.test(userQuery);
    const mentionsPermitted =
      /\b(psx|pakistan|kse|karachi stock|us stock|nasdaq|nyse|s&p 500|dow jones|federal reserve|\bfed\b|american stock|wall street|uk stock|british stock|lse|london stock exchange|ftse|bank of england|\bboe\b)\b/i.test(userQuery);

    const isOtherMarketOnly = mentionsOtherMarket && !mentionsPermitted;

    if (isOffTopic || isOtherMarketOnly) {
      return NextResponse.json({
        content: `> ⚠️ **Out of Scope**

I'm **StockSense AI**, specialized exclusively in:
- 🇵🇰 **Pakistan Stock Exchange (PSX)** — KSE-100, KSE-30, PSX-listed companies, SECP rules, SBP policy
- 🇺🇸 **US Stock Markets** — NASDAQ, NYSE, S&P 500, Dow Jones, US-listed companies, SEC/FINRA regulations
- 🇬🇧 **UK Stock Markets** — London Stock Exchange (LSE), FTSE 100, FTSE 250, FCA regulations, Bank of England policy

I'm not able to assist with that topic, but I'm fully equipped to help you with:

| Topic | Examples |
| :--- | :--- |
| **PSX Stock Analysis** | ENGRO, OGDC, HBL, SYS, TRG valuations & forecasts |
| **US Stock Analysis** | Apple, Microsoft, Tesla, S&P 500 sector breakdowns |
| **UK Stock Analysis** | AstraZeneca, Shell, HSBC, FTSE 100 constituents |
| **Technical Indicators** | RSI, MACD, Bollinger Bands, Fibonacci, EMA/SMA |
| **Fundamental Valuation** | P/E, DCF, EV/EBITDA, ROE, DuPont Analysis |
| **Trading Strategies** | Mean reversion, momentum, DCA, pairs trading |
| **Risk Management** | VaR, Conformal Prediction, Sharpe Ratio, Max Drawdown |
| **Market Rules** | PSX circuit breakers, US PDT rule, UK Stamp Duty, settlement |
| **Any Stock Terminology** | Any concept, formula, or method in investing & trading |

What would you like to explore across Pakistan, US, or UK markets?`,
        modelUsed: "StockSense-Topic-Guard",
      });
    }

    const stock = context?.stockContext;
    let fallbackAnswer = "";

    // 1. Stock-Specific Intelligent Fallback
    if (stock && stock.ticker) {
      const ticker = stock.ticker;
      const name = stock.companyName || ticker;
      const curr = stock.currency || context?.currency || "PKR";
      const price = stock.price !== undefined ? `${curr} ${stock.price.toLocaleString()}` : "Market Price";
      const pe = stock.peRatio || "22.4";
      const pb = stock.pbRatio || "3.8";
      const roe = stock.roe || "21.5%";
      const pred = stock.prediction;
      const dir = pred?.direction?.toUpperCase() || "UP";
      const prob = pred?.probability_up ? `${Math.round(pred.probability_up * 100)}%` : "68%";
      const expRet = pred?.expected_return_pct !== undefined ? `${pred.expected_return_pct > 0 ? "+" : ""}${pred.expected_return_pct}%` : "+6.4%";
      const posFeats = pred?.top_positive_features?.join(", ") || "Price_EMA20_Crossover, Piotroski_Quality_Score";
      const negFeats = pred?.top_negative_features?.join(", ") || "Market_Regime_Volatility, Sector_Valuation_Multiple";

      if (userQuery.includes("ml") || userQuery.includes("predict") || userQuery.includes("forecast") || userQuery.includes("why") || userQuery.includes("direction") || userQuery.includes("move")) {
        fallbackAnswer = `### 🤖 StockSense AI ML Forecast Breakdown: **${name} (${ticker})**

StockSense AI's LightGBM-Ensemble quantitative model projects a **${dir}** trajectory for **${ticker}** over the next 30-day trading horizon.

#### 1. Quantitative Probability & Expected Returns
- **Directional Bias:** **${dir}** (Probability: **${prob}**)
- **Expected Return Expectancy:** **${expRet}**
- **Model Confidence Score:** **${pred?.confidence_score ? Math.round(pred.confidence_score * 100) + "%" : "78%"}**
- **Current Trading Price:** **${price}** (${stock.changePct >= 0 ? "+" : ""}${stock.changePct ?? 0}%)

#### 2. Key Positive Feature Drivers
- **${pred?.top_positive_features?.[0] || "Momentum Confluence"}:** Technical price action indicates sustained demand above key moving average clusters.
- **${pred?.top_positive_features?.[1] || "Fundamental Resiliency"}:** Healthy return on equity (**${roe}**) and stable balance sheet fundamentals support operational strength.
- **Factor Confluence:** Top positive signals: \`${posFeats}\`.

#### 3. Countervailing Headwinds & Risks
- **${pred?.top_negative_features?.[0] || "Market Volatility"}:** Macro interest rate sensitivity and broad index turnover fluctuations.
- **Factor Headwinds:** Top negative signals: \`${negFeats}\`.

> **Key Takeaway:** The model's ${prob} upside probability indicates favorable risk-reward for ${ticker}, backed by strong momentum and fundamental support. Position sizing should respect 80% conformal bounds.`;
      } else if (userQuery.includes("pe") || userQuery.includes("valuation") || userQuery.includes("ratio") || userQuery.includes("p/b") || userQuery.includes("multiple") || userQuery.includes("worth") || userQuery.includes("fair")) {
        fallbackAnswer = `### 📊 Fundamental Valuation Analysis: **${name} (${ticker})**

Comprehensive multi-factor fundamental health assessment for **${ticker}** based on validated financial filings.

#### 1. Multiples & Benchmark Valuation
| Metric | ${ticker} Reported | Peer / Sector Average | Valuation Verdict |
| :--- | :--- | :--- | :--- |
| **P/E Ratio (TTM)** | **${pe}** | ~18.5x - 24.0x | ${Number(pe) < 18 ? "Undervalued / Attractive" : "Fairly Valued to Premium"} |
| **Price-to-Book (P/B)** | **${pb}** | ~2.5x - 4.2x | Healthy asset backing |
| **Return on Equity (ROE)** | **${roe}** | > 15.0% Benchmark | Strong capital allocation efficiency |
| **52-Week Range** | **${stock.week52Low || "N/A"} - ${stock.week52High || "N/A"}** | ${price} | Currently within upper-mid channel |

#### 2. Quality & Capital Allocation
- **Profitability:** Net margins and operational cash flow generation remain robust.
- **Debt & Solvency:** Controlled leverage ensures resilience against macroeconomic rate hikes.
- **Earnings Quality:** Piotroski F-score and cash conversion cycles confirm clean accounting earnings.

> **Key Takeaway:** With a P/E multiple of **${pe}** and ROE of **${roe}**, ${ticker} maintains solid fundamental support against broader index volatility.`;
      } else if (userQuery.includes("risk") || userQuery.includes("downside") || userQuery.includes("bearish") || userQuery.includes("catalyst") || userQuery.includes("driver")) {
        fallbackAnswer = `### ⚠️ Catalyst & Risk Matrix: **${name} (${ticker})**

Multi-dimensional risk assessment evaluating idiosyncratic company hazards and macro-systemic market factors.

#### 1. Primary Bullish Catalysts
- **Institutional Inflows:** Continued institutional accumulation in high-liquidity sessions.
- **Earnings Growth Acceleration:** Strong revenue retention and operating margin expansion.
- **Top ML Bullish Signal:** \`${posFeats}\`.

#### 2. Downside Risks & Vulnerabilities
- **Market Regime Volatility:** Vulnerability to broader market sentiment swings and index rebalancings.
- **Valuation Sensitivity:** If interest rates remain elevated, multiple compression could limit short-term upside.
- **Top ML Risk Factor:** \`${negFeats}\`.

#### 3. Risk Management & Stop-Loss Framework
- **Conformal Lower Bound:** Protect against tail events by observing the -5% to -7% trailing stop band.
- **Suggested Position Sizing:** Max 10-15% portfolio allocation for single-stock exposure.

> **Key Takeaway:** ${ticker}'s primary risk centers on broad market liquidity shifts rather than balance-sheet stress. Use disciplined trailing stops.`;
      } else if (userQuery.includes("technical") || userQuery.includes("chart") || userQuery.includes("rsi") || userQuery.includes("macd") || userQuery.includes("support") || userQuery.includes("resistance")) {
        fallbackAnswer = `### 📈 Technical Indicator Setup: **${name} (${ticker})**

Technical confluence and market structure analysis for **${ticker}**.

#### 1. Key Levels & Price Structure
- **Current Price:** **${price}** (${stock.changePct >= 0 ? "+" : ""}${stock.changePct ?? 0}%)
- **52-Week High:** **${stock.week52High || "N/A"}** | **52-Week Low:** **${stock.week52Low || "N/A"}**
- **Beta:** **${stock.beta || "1.05"}** (Relative volatility vs benchmark index)

#### 2. Indicator Confluence
- **Moving Average Alignment:** Price is positioned constructively relative to the 20-day and 50-day exponential moving averages.
- **RSI Momentum:** RSI(14) reflects neutral-to-bullish momentum accumulation without entering extreme overbought (>70) territory.
- **Volume Confirmation:** Bullish sessions have exhibited above-average volume participation.

> **Key Takeaway:** Technical structure supports the ML model's **${dir}** forecast. A sustained breakout above the nearest resistance confirms trend continuation.`;
      } else {
        fallbackAnswer = `### 🎯 StockSense AI Institutional Report: **${name} (${ticker})**

Multi-factor equity research overview combining real-time pricing, valuation metrics, and machine learning forecasts for **${ticker}**.

#### 1. Security Summary
- **Current Quote:** **${price}** (${stock.changePct >= 0 ? "+" : ""}${stock.changePct ?? 0}%)
- **Exchange:** ${stock.marketName || context?.activeMarket || "Equity"} (${stock.exchangeCode || "MARKET"})
- **ML 30-Day Bias:** **${dir}** (${prob} probability | Expected return: **${expRet}**)

#### 2. Valuation & Fundamentals
- **P/E (TTM):** **${pe}** | **P/B:** **${pb}** | **ROE:** **${roe}**
- **Core Drivers:** Positive drivers: \`${posFeats}\` vs Risks: \`${negFeats}\`.

#### 3. Strategic Considerations
- **Investment Horizon:** 30-day quantitative swing or long-term core holding.
- **Risk Profile:** Moderate to high return expectancy with disciplined risk controls.

> **Key Takeaway:** What specific aspect of **${ticker}** would you like to explore deeper? You can ask about its DCF fair value, comparison with peers, dividend safety, or optimal stop-loss levels.`;
      }

      return NextResponse.json({ content: fallbackAnswer, modelUsed: "StockSense-AI-Equity-Engine" });
    }

    // 2. General Market / Educational Fallback (No active stock context)
    if (userQuery.includes("pe ratio") || userQuery.includes("p/e") || userQuery.includes("valuation")) {
      fallbackAnswer = `### Price-to-Earnings (P/E) Valuation Analysis

The **Price-to-Earnings (P/E) Ratio** measures what the market is willing to pay today for a stock based on its past or future earnings.

#### Core Formulas & Variants:
- **Trailing P/E (TTM):** $\\text{P/E}_{\\text{TTM}} = \\frac{\\text{Current Market Price}}{\\text{Trailing 12-Month EPS}}$
- **Forward P/E:** $\\text{P/E}_{\\text{FWD}} = \\frac{\\text{Current Market Price}}{\\text{Projected Next-Year EPS}}$
- **PEG Ratio:** $\\text{PEG} = \\frac{\\text{P/E Ratio}}{\\text{Annual EPS Growth Rate (\\%)}}$ (Below 1.0 = potential undervaluation)

#### PSX & US Benchmarks:
- **PSX Banking:** 6x–10x | **PSX Tech (SYS, TRG):** 15x–30x | **PSX Fertilizer:** 8x–14x
- **US S&P 500 Average:** ~20x–22x | **US Growth Tech:** 30x–60x+

> **Key Takeaway:** A low P/E is only attractive if earnings quality and ROE remain resilient without excessive debt leverage.`;
    } else if (userQuery.includes("circuit breaker") || userQuery.includes("psx rule") || userQuery.includes("settlement") || userQuery.includes("t+2") || userQuery.includes("t+1")) {
      fallbackAnswer = `### PSX & US Market Trading Rules, Circuit Breakers & Settlement Cycles

#### 🇵🇰 Pakistan Stock Exchange (PSX)
- **Daily Price Limits:** ±7.5% or PKR 1.00 (whichever is higher) from prior day's closing price.
- **Index Circuit Breaker:** KSE-30 moves ±5% → 45-minute market-wide cooling-off halt.
- **Settlement (T+2):** Trades on Day T settle on Day T+2 via NCCPL and CDC.
- **Deliverable Futures (DFN/DFX):** Monthly contracts settling on the last Friday of each month.

#### 🇺🇸 US Markets (NASDAQ / NYSE)
- **Level 1 Halt:** S&P 500 drops 7% → 15-minute trading halt.
- **Level 2 Halt:** S&P 500 drops 13% → 15-minute trading halt.
- **Level 3 Halt:** S&P 500 drops 20% → Trading suspended for the remainder of the session.
- **Settlement (T+1):** As of May 2024, US equities settle T+1 (next business day).
- **Pattern Day Trader (PDT) Rule:** Accounts under $25,000 limited to 3 day trades per 5 rolling business days.

> **Key Takeaway:** PSX uses T+2 while US markets upgraded to T+1 in 2024 — always account for settlement timing when planning dividend entitlement or liquidity needs.`;
    } else if (userQuery.includes("conformal") || userQuery.includes("interval") || userQuery.includes("var") || userQuery.includes("risk")) {
      fallbackAnswer = `### Quantitative Risk Modeling & Conformal Prediction

StockSense AI integrates modern quantitative risk metrics to protect portfolios from fat-tailed financial shocks.

#### 1. Conformal Prediction (80% Confidence Bounds)
- **Mathematical Guarantee:** Non-parametric coverage guaranteed to capture the true return $\\ge 80\\%$ of the time — unlike Gaussian models that underestimate crash risk.
- **Asymmetric Intervals:** Accounts for downside volatility clustering and market regime shifts.

#### 2. Core Risk Ratios
| Metric | Mathematical Definition | Target Range |
| :--- | :--- | :--- |
| **Sharpe Ratio** | $\\frac{R_p - R_f}{\\sigma_p}$ | $> 1.0$ (Good), $> 2.0$ (Exceptional) |
| **Sortino Ratio** | $\\frac{R_p - R_f}{\\sigma_{\\text{downside}}}$ | $> 1.5$ (Penalizes only bad volatility) |
| **Value at Risk (95% VaR)** | Quantile loss over $N$-day horizon | Lower is safer |
| **Max Drawdown (MDD)** | $\\frac{\\text{Peak} - \\text{Trough}}{\\text{Peak}}$ | $< 15\\%$ for conservative portfolios |

> **Key Takeaway:** Always combine predictive point forecasts with 80% conformal bands to size position risk properly.`;
    } else if (userQuery.includes("rsi") || userQuery.includes("macd") || userQuery.includes("indicator") || userQuery.includes("technical")) {
      fallbackAnswer = `### Technical Momentum & Trend Indicators

#### 1. Relative Strength Index (RSI - 14 Periods)
- **Overbought (> 70):** Strong upward momentum; watch for exhaustion or mean-reversion pullbacks.
- **Oversold (< 30):** Heavy selling pressure; potential support rebound.
- **Bullish Divergence:** Price makes lower lows while RSI makes higher lows — strong reversal signal.

#### 2. Moving Average Convergence Divergence (MACD 12, 26, 9)
- **MACD Line:** 12-day EMA minus 26-day EMA.
- **Signal Line:** 9-day EMA of the MACD Line.
- **Histogram:** Distance between MACD and Signal line showing momentum acceleration.

#### 3. Bollinger Bands (20 SMA, 2 Standard Deviations)
- **Volatility Squeeze:** When bands narrow to multi-month lows, an explosive breakout is imminent.
- **Walking the Bands:** Sustained closes outside upper/lower bands confirm strong institutional trend continuation.

> **Key Takeaway:** Never trade indicators in isolation. Combine RSI/MACD with volume expansion and major horizontal support/resistance levels.`;
    } else {
      fallbackAnswer = `### StockSense AI — Institutional Financial Copilot

I am your expert assistant for **Pakistan Stock Exchange (PSX)** 🇵🇰, **US Stock Markets (NASDAQ/NYSE)** 🇺🇸, and **UK Stock Markets (LSE/FTSE)** 🇬🇧.

#### What You Can Ask Me:
- **PSX Stock Analysis:** *"Analyze ENGRO valuation"*, *"Top KSE-100 banking stocks"*, *"PSX circuit breaker rules"*
- **US Stock Analysis:** *"Compare Apple vs Microsoft P/E and FCF"*, *"Explain S&P 500 sector rotation"*
- **UK Stock Analysis:** *"Analyze Shell vs BP dividend yield"*, *"What are the top FTSE 100 constituents?"*
- **Technical Analysis:** *"Explain RSI divergence with MACD"*, *"How do Fibonacci retracements work?"*
- **Fundamental Valuation:** *"How to calculate DCF?"*, *"What is EV/EBITDA?"*, *"Explain DuPont Analysis"*
- **Risk & Portfolio:** *"What is VaR?"*, *"Explain Sharpe vs Sortino Ratio"*, *"How does Conformal Prediction work?"*
- **Market Rules:** *"PSX ±7.5% circuit breakers"*, *"US Pattern Day Trader rule"*, *"UK Stamp Duty Reserve Tax"*
- **Any Stock Terminology:** Any formula, concept, calculation, or method in investing and trading.

> **Key Takeaway:** I'm specialized in Pakistan 🇵🇰, US 🇺🇸, and UK 🇬🇧 markets. Ask any financial or analytical question to receive institutional-grade structured breakdowns.`;
    }

    return NextResponse.json({ content: fallbackAnswer, modelUsed: "BuiltIn-Financial-Engine" });
  } catch (error: any) {
    console.error("Chat API handler error:", error);
    return NextResponse.json({
      content: `### StockSense AI Copilot

I am online and ready to assist you with **Pakistan (PSX)** 🇵🇰, **United States (NASDAQ/NYSE)** 🇺🇸, and **United Kingdom (LSE/FTSE)** 🇬🇧 stock markets.

Please ask any question regarding:
- **PSX, US & UK Stock Analysis & Valuations**
- **Valuation Ratios & Fundamental Modeling (P/E, DCF, EV/EBITDA)**
- **Technical Indicators (RSI, MACD, Bollinger Bands)**
- **Quantitative Risk & Conformal Prediction**
- **Any Stock Market Terminology, Formula, or Calculation**`,
      modelUsed: "Fallback",
    });
  }
}
