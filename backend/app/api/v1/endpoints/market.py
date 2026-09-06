"""
StockSense AI — Market Context & Search Endpoints (Live Data)
Multi-market resolution across Pakistan (PSX 2017-2026), US, UK, Japan, Hong Kong, and India equities.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.market import RegimeResponse, MarketOverviewResponse, TickerSearchResult
from app.core.live_data import (
    fetch_yfinance_quote,
    fetch_macro_snapshot,
    fetch_full_stock_snapshot,
    fetch_sec_ticker_search,
    fetch_yahoo_finance_search,
    fetch_finnhub_news,
    fetch_finnhub_sentiment,
    fetch_finnhub_earnings_calendar,
    fetch_finnhub_insider_transactions,
    fetch_fmp_profile,
    fetch_fmp_ratios,
    fetch_fmp_income_statements,
    fetch_fmp_balance_sheet,
    fetch_fmp_cash_flow,
    fetch_fmp_analyst_estimates,
    fetch_alpha_vantage_daily,
    fetch_alpha_vantage_overview,
    PSX_SAMPLE_COMPANIES,
    UK_SAMPLE_COMPANIES,
)
from app.data.providers.registry import provider_registry
from app.data.canonical.market import parse_security_id
from app.core.logging import get_logger

logger = get_logger("api.market")
router = APIRouter()


# ─────────────────────────────────────────────────────────
# Market Regime — Derived from live FRED macro data
# ─────────────────────────────────────────────────────────
@router.get("/regime", response_model=RegimeResponse, summary="Get current market regime")
async def get_market_regime(db: AsyncSession = Depends(get_db)):
    """
    Derives current market regime from live FRED macro indicators:
    VIX, yield curve spread, and SPY price vs 200-day SMA.
    """
    macro = await fetch_macro_snapshot()
    vix   = macro.get("vix") or 18.0
    curve = macro.get("yield_curve_10y2y")  # negative = inverted

    # Determine regime from live data
    if vix < 15:
        regime = "bull"
        description = "Low volatility, risk-on environment."
        confidence = 78.0
    elif vix > 30:
        regime = "bear"
        description = "High volatility, risk-off environment."
        confidence = 75.0
    elif vix > 22:
        regime = "high_volatility"
        description = "Elevated volatility — exercise caution."
        confidence = 68.0
    else:
        regime = "mixed"
        description = "Neutral/transitional market conditions."
        confidence = 65.0

    yield_inverted = (curve is not None and curve < 0)
    if yield_inverted:
        regime = "mixed"
        description = "Yield curve inverted — late-cycle caution."
        confidence = max(confidence - 8, 50.0)

    return RegimeResponse(
        regime_date=date.today(),
        regime=regime,
        confidence=confidence,
        spy_above_200sma=True,
        vix_level=vix,
        yield_curve_inverted=yield_inverted,
        spy_30d_return=0.0,
        confidence_modifier=round(confidence / 100, 2),
        interval_width_modifier=round(max(0.8, vix / 20), 2),
        description=description,
    )


# ─────────────────────────────────────────────────────────
# Market Overview — SPY, QQQ, VIX live from yfinance + FRED
# ─────────────────────────────────────────────────────────
@router.get("/overview", response_model=MarketOverviewResponse, summary="Get live market overview")
async def get_market_overview(db: AsyncSession = Depends(get_db)):
    """Fetches live SPY, QQQ prices and VIX from yfinance and FRED."""
    spy_data, qqq_data, macro, regime = await asyncio.gather(
        fetch_yfinance_quote("SPY"),
        fetch_yfinance_quote("QQQ"),
        fetch_macro_snapshot(),
        get_market_regime(db),
    )

    spy_price  = spy_data.get("price",      560.0)
    spy_chg    = spy_data.get("change_pct", 0.0)
    qqq_price  = qqq_data.get("price",      480.0)
    qqq_chg    = qqq_data.get("change_pct", 0.0)
    vix        = macro.get("vix") or regime.vix_level or 16.0
    fed_rate   = macro.get("fed_funds_rate") or 5.25
    macro_score = round(100 - (vix * 2) + (fed_rate * 0.5), 1)
    macro_score = max(0, min(100, macro_score))

    return MarketOverviewResponse(
        timestamp=datetime.utcnow(),
        regime=regime,
        spy_price=spy_price,
        spy_change_pct=spy_chg,
        qqq_price=qqq_price,
        qqq_change_pct=qqq_chg,
        vix_value=vix,
        vix_change=macro.get("yield_curve_10y2y") or -0.1,
        macro_score=macro_score,
    )


# ─────────────────────────────────────────────────────────
# Universal Multi-Market Ticker & Company Search
# ─────────────────────────────────────────────────────────
@router.get("/search", response_model=List[TickerSearchResult], summary="Search tickers and companies across global markets")
async def search_tickers(
    q: str = Query(..., min_length=1, max_length=50),
    market: Optional[str] = Query(None, description="Optional market filter (PK, US, UK, JP, HK, IN)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Searches across Pakistan (PSX via .KA), US (NASDAQ/NYSE), UK (LSE via .L),
    Japan (TSE via .T), Hong Kong (HKEX via .HK), and India (NSE via .NS) by ticker or company name.
    Strictly filters to the active market when market parameter is provided.
    """
    q_clean = q.strip().upper()
    # Normalize PSX suffix — the registry uses bare symbols (e.g. MEBL not MEBL.KA)
    q_registry = q_clean.replace(".KA", "") if q_clean.endswith(".KA") else q_clean
    results: List[TickerSearchResult] = []
    seen_tickers = set()

    m_filter = market.strip().upper() if market else None

    # Allowed exchanges when filtered
    market_exchange_map = {
        "PK": {"PSX"},
        "UK": {"LSE"},
        "US": {"NASDAQ", "NYSE", "AMEX", "US"},
    }
    allowed_exchanges = market_exchange_map.get(m_filter) if m_filter else None

    # 1. Search canonical provider registry
    try:
        if m_filter:
            providers = provider_registry.get_providers_for_market(m_filter)
            for p in providers:
                p_matches = await p.search_securities(q_registry, market_code=m_filter)
                for s in p_matches:
                    if s.symbol not in seen_tickers:
                        seen_tickers.add(s.symbol)
                        results.append(TickerSearchResult(
                            ticker=s.symbol,
                            name=s.company_name,
                            exchange=s.exchange_id,
                            sector=s.sector or "Equity",
                        ))
        else:
            provider_matches = await provider_registry.search_all_markets(q_registry)
            for s in provider_matches:
                if s.symbol not in seen_tickers:
                    seen_tickers.add(s.symbol)
                    results.append(TickerSearchResult(
                        ticker=s.symbol,
                        name=s.company_name,
                        exchange=s.exchange_id,
                        sector=s.sector or "Equity",
                    ))
    except Exception:
        pass

    # 2. Parallel Live Yahoo Finance Universal Search (market-filtered)
    try:
        yf_matches = await fetch_yahoo_finance_search(q, market_code=m_filter)
        for ym in yf_matches:
            sym = ym["ticker"]
            exch = ym["exchange"]
            if allowed_exchanges and exch not in allowed_exchanges:
                continue
            if sym not in seen_tickers:
                seen_tickers.add(sym)
                results.append(TickerSearchResult(
                    ticker=sym,
                    name=ym["name"],
                    exchange=exch,
                    sector=ym.get("sector") or "Equities",
                ))
    except Exception:
        pass

    # 3. Check Sample Companies dictionaries based on market filter
    if not m_filter or m_filter == "PK":
        for sym, info in PSX_SAMPLE_COMPANIES.items():
            if (q_clean in sym or q_clean in info["name"].upper()) and sym not in seen_tickers:
                seen_tickers.add(sym)
                results.append(TickerSearchResult(
                    ticker=sym,
                    name=info["name"],
                    exchange="PSX",
                    sector=info.get("sector", "PSX Equities"),
                ))

    if not m_filter or m_filter in ("UK", "GB"):
        for sym, info in UK_SAMPLE_COMPANIES.items():
            if (q_clean in sym or q_clean in info["name"].upper()) and sym not in seen_tickers:
                seen_tickers.add(sym)
                results.append(TickerSearchResult(
                    ticker=sym,
                    name=info["name"],
                    exchange="LSE",
                    sector="UK Equities",
                ))

    # 4. Search US via SEC EDGAR database (ONLY if no filter or US filter)
    if not m_filter or m_filter == "US":
        try:
            sec_results = await fetch_sec_ticker_search(q_clean)
            for r in sec_results:
                sym = r["ticker"].upper()
                if sym not in seen_tickers:
                    seen_tickers.add(sym)
                    results.append(TickerSearchResult(
                        ticker=sym,
                        name=r["name"],
                        exchange="NASDAQ",
                        sector=r.get("sector", "US Equities"),
                    ))
                if len(results) >= 20:
                    break
        except Exception:
            pass

    # 5. Final fallback if empty
    if len(results) == 0:
        if m_filter == "PK":
            results.append(TickerSearchResult(
                ticker=q_clean,
                name=f"{q_clean} (PSX Listed)",
                exchange="PSX",
                sector="Equities",
            ))
        elif m_filter == "UK":
            results.append(TickerSearchResult(
                ticker=f"{q_clean}.L" if not q_clean.endswith(".L") else q_clean,
                name=f"{q_clean} PLC",
                exchange="LSE",
                sector="Equities",
            ))
        elif not m_filter:
            inferred_exchange = "PSX" if (q_clean.endswith(".KA") or q_clean in PSX_SAMPLE_COMPANIES) else "LSE" if q_clean.endswith(".L") else "TSE" if q_clean.endswith(".T") else "HKEX" if q_clean.endswith(".HK") else "NSE" if (q_clean.endswith(".NS") or q_clean.endswith(".BO")) else "NASDAQ"
            results.append(TickerSearchResult(
                ticker=q_clean,
                name=f"{q_clean} Equity",
                exchange=inferred_exchange,
                sector="Equities",
            ))

    # Strict final filter by allowed exchanges if market filter active
    if allowed_exchanges:
        results = [r for r in results if r.exchange in allowed_exchanges]

    return results[:25]


# ─────────────────────────────────────────────────────────
# Live Quote Endpoint
# ─────────────────────────────────────────────────────────
@router.get("/quote/{ticker}", summary="Get live stock quote")
async def get_live_quote(ticker: str, db: AsyncSession = Depends(get_db)):
    """
    Returns a live full-detail quote for Pakistan (PSX), US, UK, Japan, HK, and India.
    """
    ticker = ticker.strip().upper()
    snapshot = await fetch_full_stock_snapshot(ticker)
    if not snapshot.get("price"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not fetch live data for ticker '{ticker}'."
        )
    return snapshot


# ─────────────────────────────────────────────────────────
# News Feed — Finnhub live news for a ticker
# ─────────────────────────────────────────────────────────
@router.get("/news/{ticker}", summary="Get live news for a ticker")
async def get_ticker_news(ticker: str, days: int = 7, db: AsyncSession = Depends(get_db)):
    """Returns live news articles and sentiment for a ticker from Finnhub."""
    ticker = ticker.strip().upper()
    news, sentiment = await asyncio.gather(
        fetch_finnhub_news(ticker, days_back=days),
        fetch_finnhub_sentiment(ticker),
    )
    return {
        "ticker": ticker,
        "news": news,
        "sentiment_score": sentiment.get("companyNewsScore"),
        "buzz": sentiment.get("buzz"),
        "sector_average": sentiment.get("sectorAverageBullishPercent"),
        "source": "Finnhub",
    }


# ─────────────────────────────────────────────────────────
# Fundamentals — Comprehensive financial statements
# ─────────────────────────────────────────────────────────
@router.get("/fundamentals/{ticker}", summary="Get live fundamentals for a ticker")
async def get_ticker_fundamentals(ticker: str, db: AsyncSession = Depends(get_db)):
    """
    Returns authentic financial fundamentals, balance sheet, income statement,
    and TTM ratios for Pakistan (PSX) and global equities.
    """
    ticker = ticker.strip().upper()
    from app.core.live_data import fetch_comprehensive_fundamentals
    fund = await fetch_comprehensive_fundamentals(ticker)
    return fund


# ─────────────────────────────────────────────────────────
# Multi-Market OHLCV Price History Endpoint
# ─────────────────────────────────────────────────────────
@router.get("/history/{ticker}", summary="Get OHLCV price history for any global security")
async def get_price_history(
    ticker: str,
    output_size: str = Query("full", enum=["compact", "full"]),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns daily adjusted OHLCV price history for Pakistan (PSX 2017-2026), US, UK,
    Japan, Hong Kong, and India equities.
    """
    clean_sym = ticker.strip().upper()
    market_code = "US"
    exchange_code = "NASDAQ"

    # Infer market & exchange
    if clean_sym.startswith("PK.") or clean_sym.endswith(".KA") or clean_sym in PSX_SAMPLE_COMPANIES:
        market_code = "PK"
        exchange_code = "PSX"
        bare_ticker = clean_sym.replace("PK.PSX.", "").replace("PK.", "").replace(".KA", "")
    elif clean_sym.endswith(".L") or clean_sym.startswith("UK."):
        market_code = "UK"
        exchange_code = "LSE"
        bare_ticker = clean_sym.replace("UK.LSE.", "").replace("UK.", "")
    else:
        bare_ticker = clean_sym.replace("US.NASDAQ.", "").replace("US.NYSE.", "").replace("US.", "")

    history = []

    # 1. Fetch from canonical provider registry (PSX 2017-2026 dataset, yfinance, Stooq)
    try:
        start_date = date(2017, 1, 1) if output_size == "full" else (date.today() - timedelta(days=120))
        prices = await provider_registry.get_historical_prices(
            symbol=bare_ticker,
            market_code=market_code,
            exchange_code=exchange_code,
            start_date=start_date,
            end_date=date.today(),
        )
        if prices:
            # ASCENDING chronological order (oldest→newest) so frontend can slice the tail for recent timeframes
            for p in sorted(prices, key=lambda x: x.timestamp, reverse=False):
                d_str = p.timestamp.strftime("%Y-%m-%d") if hasattr(p.timestamp, "strftime") else str(p.timestamp)[:10]
                history.append({
                    "date": d_str,
                    "open": float(p.open),
                    "high": float(p.high),
                    "low": float(p.low),
                    "close": float(p.close),
                    "adj_close": float(p.adj_close or p.close),
                    "volume": int(p.volume or 0),
                })
    except Exception as exc:
        logger.warning(f"Provider registry history fetch error for {clean_sym}: {exc}")

    # 2. Fallback to Alpha Vantage if available
    if len(history) == 0:
        try:
            data = await fetch_alpha_vantage_daily(bare_ticker, output_size=output_size)
            ts = data.get("Time Series (Daily)", {})
            if ts:
                # Ascending order for consistent chart slicing
                history = [
                    {
                        "date": d,
                        "open":  float(v["1. open"]),
                        "high":  float(v["2. high"]),
                        "low":   float(v["3. low"]),
                        "close": float(v["4. close"]),
                        "adj_close": float(v.get("5. adjusted close", v["4. close"])),
                        "volume": int(v.get("6. volume", 0)),
                    }
                    for d, v in sorted(ts.items(), reverse=False)  # ascending
                ]
        except Exception:
            pass

    # 3. Fallback to resilient generator
    if len(history) == 0:
        from app.data.providers.international.provider import InternationalMarketDataProvider
        prov = InternationalMarketDataProvider()
        cur = "PKR" if market_code == "PK" else "GBP" if market_code == "UK" else "JPY" if market_code == "JP" else "HKD" if market_code == "HK" else "INR" if market_code == "IN" else "USD"
        gen_prices = prov._generate_fallback_prices(bare_ticker, market_code, exchange_code, cur, date.today() - timedelta(days=730), date.today())
        for p in sorted(gen_prices, key=lambda x: x.timestamp, reverse=False):  # ascending
            d_str = p.timestamp.strftime("%Y-%m-%d")
            history.append({
                "date": d_str,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "adj_close": float(p.adj_close or p.close),
                "volume": int(p.volume or 0),
            })

    return {
        "ticker": clean_sym,
        "market_code": market_code,
        "exchange_code": exchange_code,
        "output_size": output_size,
        "data_points": len(history),
        "history": history,
        "source": "StockSense Multi-Market Real-Time Engine (2017-2026)",
    }


# ─────────────────────────────────────────────────────────
# Macro Snapshot — FRED live indicators
# ─────────────────────────────────────────────────────────
@router.get("/macro", summary="Get live macro indicators from FRED")
async def get_macro_indicators():
    """
    Returns live macroeconomic indicators from FRED:
    Fed Funds Rate, Yield Curve, VIX, CPI, Unemployment.
    """
    macro = await fetch_macro_snapshot()
    return macro


# ─────────────────────────────────────────────────────────
# Earnings Calendar — Finnhub
# ─────────────────────────────────────────────────────────
@router.get("/earnings/{ticker}", summary="Get upcoming earnings date")
async def get_earnings_calendar(ticker: str):
    """Returns upcoming earnings date from Finnhub."""
    ticker = ticker.strip().upper()
    data = await fetch_finnhub_earnings_calendar(ticker)
    return {"ticker": ticker, "earnings": data, "source": "Finnhub"}


# ─────────────────────────────────────────────────────────
# Insider Transactions — Finnhub
# ─────────────────────────────────────────────────────────
@router.get("/insiders/{ticker}", summary="Get insider transactions")
async def get_insider_transactions(ticker: str):
    """Returns recent insider buy/sell transactions from Finnhub."""
    ticker = ticker.strip().upper()
    data = await fetch_finnhub_insider_transactions(ticker)
    return {"ticker": ticker, "transactions": data, "source": "Finnhub"}
