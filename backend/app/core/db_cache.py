"""
StockSense AI — Database Persistence & Live Cache Service
Centralized service for persisting all live-fetched API data (Yahoo Finance quotes,
historical OHLCV bars, news, insider trades, backtests, and AI analysis reports)
directly into SQLite / PostgreSQL using SQLAlchemy ORM.
"""

import uuid
import asyncio
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional, Union, Tuple
from decimal import Decimal

from sqlalchemy import select, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.market_data import (
    Market,
    Exchange,
    SecurityMaster,
    Company,
    PriceData,
)
from app.models.news import NewsItem, InsiderTransaction
from app.models.backtest import BacktestRunRecord, BacktestTradeRecord
from app.models.analysis import AnalysisJob, AnalysisReport

logger = get_logger("core.db_cache")

# Shared upsert statement for price_data across SQLite and PostgreSQL
PRICE_UPSERT_SQL = text("""
    INSERT INTO price_data (
        time, ticker, security_id, open, high, low, close, adj_close, volume, currency, data_source, is_adjusted, quality_flag, retrieved_at
    ) VALUES (
        :time, :ticker, :security_id, :open, :high, :low, :close, :adj_close, :volume, :currency, :data_source, :is_adjusted, :quality_flag, :retrieved_at
    )
    ON CONFLICT(time, ticker) DO UPDATE SET
        open = excluded.open,
        high = excluded.high,
        low = excluded.low,
        close = excluded.close,
        adj_close = excluded.adj_close,
        volume = excluded.volume,
        currency = excluded.currency,
        data_source = excluded.data_source,
        is_adjusted = excluded.is_adjusted,
        quality_flag = excluded.quality_flag,
        retrieved_at = excluded.retrieved_at
""")

# Standard Market Definitions
MARKETS_DEF = {
    "PK": {
        "id": "PK", "code": "PSX", "name": "Pakistan Stock Exchange",
        "country": "Pakistan", "default_currency": "PKR", "timezone": "Asia/Karachi"
    },
    "US": {
        "id": "US", "code": "US", "name": "United States Markets",
        "country": "United States", "default_currency": "USD", "timezone": "America/New_York"
    },
    "UK": {
        "id": "UK", "code": "UK", "name": "London Stock Exchange",
        "country": "United Kingdom", "default_currency": "GBP", "timezone": "Europe/London"
    },
    "GB": {
        "id": "UK", "code": "UK", "name": "London Stock Exchange",
        "country": "United Kingdom", "default_currency": "GBP", "timezone": "Europe/London"
    },
    "JP": {
        "id": "JP", "code": "JP", "name": "Tokyo Stock Exchange",
        "country": "Japan", "default_currency": "JPY", "timezone": "Asia/Tokyo"
    },
    "HK": {
        "id": "HK", "code": "HK", "name": "Hong Kong Exchanges",
        "country": "Hong Kong", "default_currency": "HKD", "timezone": "Asia/Hong_Kong"
    },
    "IN": {
        "id": "IN", "code": "IN", "name": "National Stock Exchange of India",
        "country": "India", "default_currency": "INR", "timezone": "Asia/Kolkata"
    },
}

# Standard Exchange Definitions
EXCHANGES_DEF = {
    "PSX": {
        "id": "PSX", "market_id": "PK", "code": "PSX",
        "name": "Pakistan Stock Exchange", "country": "Pakistan", "currency": "PKR",
        "timezone": "Asia/Karachi", "mic_code": "XKAR", "website": "https://www.psx.com.pk"
    },
    "NASDAQ": {
        "id": "NASDAQ", "market_id": "US", "code": "NASDAQ",
        "name": "NASDAQ Stock Market", "country": "United States", "currency": "USD",
        "timezone": "America/New_York", "mic_code": "XNAS", "website": "https://www.nasdaq.com"
    },
    "NYSE": {
        "id": "NYSE", "market_id": "US", "code": "NYSE",
        "name": "New York Stock Exchange", "country": "United States", "currency": "USD",
        "timezone": "America/New_York", "mic_code": "XNYS", "website": "https://www.nyse.com"
    },
    "LSE": {
        "id": "LSE", "market_id": "UK", "code": "LSE",
        "name": "London Stock Exchange", "country": "United Kingdom", "currency": "GBP",
        "timezone": "Europe/London", "mic_code": "XLON", "website": "https://www.londonstockexchange.com"
    },
    "TSE": {
        "id": "TSE", "market_id": "JP", "code": "TSE",
        "name": "Tokyo Stock Exchange", "country": "Japan", "currency": "JPY",
        "timezone": "Asia/Tokyo", "mic_code": "XJPX", "website": "https://www.jpx.co.jp"
    },
    "HKEX": {
        "id": "HKEX", "market_id": "HK", "code": "HKEX",
        "name": "Hong Kong Exchanges and Clearing", "country": "Hong Kong", "currency": "HKD",
        "timezone": "Asia/Hong_Kong", "mic_code": "XHKG", "website": "https://www.hkex.com.hk"
    },
    "NSE": {
        "id": "NSE", "market_id": "IN", "code": "NSE",
        "name": "National Stock Exchange of India", "country": "India", "currency": "INR",
        "timezone": "Asia/Kolkata", "mic_code": "XNSE", "website": "https://www.nseindia.com"
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Session Context Manager
# ─────────────────────────────────────────────────────────────────────────────
class ManagedSession:
    """Provides an isolated AsyncSession for persistence, ensuring independent transactions."""
    def __init__(self, db: Optional[AsyncSession] = None):
        self.session = AsyncSessionLocal()

    async def __aenter__(self) -> AsyncSession:
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()


def dispatch_background(coro_fn, *args, **kwargs):
    """Safely dispatches a persistence coroutine in the background with its own DB session."""
    async def _runner():
        try:
            await coro_fn(*args, **kwargs, db=None)
        except Exception as e:
            logger.warning(f"[DB_CACHE] Background persistence error: {e}")
    asyncio.create_task(_runner())


# ─────────────────────────────────────────────────────────────────────────────
# Market & Exchange Helpers
# ─────────────────────────────────────────────────────────────────────────────
async def ensure_market_and_exchange(
    session: AsyncSession,
    market_code: str = "US",
    exchange_code: str = "NASDAQ"
) -> Tuple[str, str]:
    """Ensures Market and Exchange rows exist in the DB."""
    m_code = market_code.strip().upper()
    if m_code in ("GB", "UK"):
        m_id = "UK"
    elif m_code == "PK":
        m_id = "PK"
    else:
        m_id = m_code

    e_id = exchange_code.strip().upper()
    if e_id not in EXCHANGES_DEF:
        if m_id == "PK":
            e_id = "PSX"
        elif m_id == "UK":
            e_id = "LSE"
        elif m_id == "JP":
            e_id = "TSE"
        elif m_id == "IN":
            e_id = "NSE"
        else:
            e_id = "NASDAQ"

    # 1. Ensure Market
    res_m = await session.execute(select(Market).where(Market.id == m_id))
    if not res_m.scalars().first():
        m_def = MARKETS_DEF.get(m_id, MARKETS_DEF["US"])
        now = datetime.now(timezone.utc)
        m_model = Market(
            id=m_def["id"],
            code=m_def["code"],
            name=m_def["name"],
            country=m_def["country"],
            default_currency=m_def["default_currency"],
            timezone=m_def["timezone"],
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )
        session.add(m_model)
        await session.flush()

    # 2. Ensure Exchange
    res_e = await session.execute(select(Exchange).where(Exchange.id == e_id))
    if not res_e.scalars().first():
        e_def = EXCHANGES_DEF.get(e_id, EXCHANGES_DEF["NASDAQ"])
        now = datetime.now(timezone.utc)
        e_model = Exchange(
            id=e_def["id"],
            market_id=m_id,
            code=e_def["code"],
            name=e_def["name"],
            country=e_def["country"],
            currency=e_def["currency"],
            timezone=e_def["timezone"],
            mic_code=e_def.get("mic_code"),
            website=e_def.get("website"),
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )
        session.add(e_model)
        await session.flush()

    return m_id, e_id


# ─────────────────────────────────────────────────────────────────────────────
# Company & Security Master Helpers
# ─────────────────────────────────────────────────────────────────────────────
async def ensure_company_and_security(
    session: AsyncSession,
    ticker: str,
    name: Optional[str] = None,
    exchange: str = "NASDAQ",
    market: str = "US",
    currency: str = "USD",
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    market_cap: Optional[int] = None,
    data_source: str = "yfinance",
) -> Company:
    """Ensures Company and SecurityMaster exist, updating metadata if richer info is available."""
    clean_sym = ticker.strip().upper()
    m_id, e_id = await ensure_market_and_exchange(session, market, exchange)

    sec_id = f"{m_id}.{e_id}.{clean_sym}"
    comp_name = name or f"{clean_sym} Corp."

    # Check Company
    res_c = await session.execute(select(Company).where(Company.ticker == clean_sym))
    comp = res_c.scalars().first()

    now = datetime.now(timezone.utc)
    if not comp:
        comp = Company(
            ticker=clean_sym,
            security_id=sec_id,
            name=comp_name,
            exchange=e_id,
            country=MARKETS_DEF.get(m_id, {}).get("country", "United States"),
            currency=currency,
            sector=sector or "Equity",
            industry=industry or "Equities",
            market_cap=market_cap,
            is_active=True,
            data_source=data_source,
            created_at=now,
            updated_at=now,
        )
        session.add(comp)
        await session.flush()
    else:
        # Update details if richer info provided
        updated = False
        if name and (comp.name == f"{clean_sym} Corp." or not comp.name):
            comp.name = name
            updated = True
        if sector and (not comp.sector or comp.sector == "Equity"):
            comp.sector = sector
            updated = True
        if industry and (not comp.industry or comp.industry == "Equities"):
            comp.industry = industry
            updated = True
        if market_cap and not comp.market_cap:
            comp.market_cap = market_cap
            updated = True
        if updated:
            comp.updated_at = now
            await session.flush()

    # Check SecurityMaster
    res_s = await session.execute(select(SecurityMaster).where(SecurityMaster.symbol == clean_sym))
    sec = res_s.scalars().first()
    if not sec:
        sec = SecurityMaster(
            security_id=sec_id,
            exchange_id=e_id,
            market_id=m_id,
            symbol=clean_sym,
            company_name=comp_name,
            country=MARKETS_DEF.get(m_id, {}).get("country", "United States"),
            currency=currency,
            sector=sector or "Equity",
            industry=industry or "Equities",
            security_type="COMMON_STOCK",
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )
        session.add(sec)
        await session.flush()

    return comp


# ─────────────────────────────────────────────────────────────────────────────
# Price Data Persistence (Historical OHLCV and Live Quotes)
# ─────────────────────────────────────────────────────────────────────────────
async def upsert_historical_prices(
    ticker: str,
    prices: List[Dict[str, Any]],
    market: str = "US",
    exchange: str = "NASDAQ",
    currency: str = "USD",
    data_source: str = "yfinance",
    db: Optional[AsyncSession] = None
) -> int:
    """
    Persists a list of historical OHLCV bars into `price_data`.
    Avoids duplicating existing (ticker, time) records.
    Returns the number of rows inserted or updated.
    """
    if not prices:
        return 0

    clean_sym = ticker.strip().upper()
    inserted_count = 0

    async with ManagedSession(db) as session:
        # Ensure parent company exists
        await ensure_company_and_security(
            session=session,
            ticker=clean_sym,
            exchange=exchange,
            market=market,
            currency=currency,
            data_source=data_source,
        )

        sec_id = f"{market}.{exchange}.{clean_sym}"
        now_utc = datetime.now(timezone.utc)

        # Parse rows and gather timestamps
        parsed_bars = []
        for p in prices:
            try:
                raw_d = p.get("date") or p.get("timestamp") or p.get("time")
                if not raw_d:
                    continue

                if isinstance(raw_d, str):
                    if len(raw_d) == 10:
                        bar_time = datetime.strptime(raw_d, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    else:
                        bar_time = datetime.fromisoformat(raw_d.replace("Z", "+00:00"))
                elif isinstance(raw_d, date) and not isinstance(raw_d, datetime):
                    bar_time = datetime(raw_d.year, raw_d.month, raw_d.day, tzinfo=timezone.utc)
                elif isinstance(raw_d, datetime):
                    bar_time = raw_d if raw_d.tzinfo else raw_d.replace(tzinfo=timezone.utc)
                else:
                    continue

                c_open = float(p.get("open") or p.get("close") or 0.0)
                c_high = float(p.get("high") or c_open)
                c_low = float(p.get("low") or c_open)
                c_close = float(p.get("close") or c_open)
                c_adj = float(p.get("adj_close") or c_close)
                c_vol = int(p.get("volume") or 0)

                # Defensive sanity check
                if c_high < c_low:
                    c_high, c_low = c_low, c_high

                parsed_bars.append({
                    "time": bar_time,
                    "open": c_open,
                    "high": c_high,
                    "low": c_low,
                    "close": c_close,
                    "adj_close": c_adj,
                    "volume": c_vol,
                })
            except Exception as e:
                continue

        if not parsed_bars:
            return 0

        # Batch upsert all parsed bars using ON CONFLICT DO UPDATE
        rows_to_upsert = [
            {
                "time": b["time"],
                "ticker": clean_sym,
                "security_id": sec_id,
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "adj_close": b["adj_close"],
                "volume": b["volume"],
                "currency": currency,
                "data_source": data_source,
                "is_adjusted": 1,
                "quality_flag": "ok",
                "retrieved_at": now_utc,
            }
            for b in parsed_bars
        ]

        await session.execute(PRICE_UPSERT_SQL, rows_to_upsert)
        inserted_count = len(rows_to_upsert)

        logger.info(f"[DB_CACHE] Upserted {inserted_count} price bars for {clean_sym}")

    return inserted_count


async def save_live_quote(
    quote: Dict[str, Any],
    db: Optional[AsyncSession] = None
) -> None:
    """
    Persists a live quote snapshot as today's OHLCV record into `price_data`,
    and updates `companies` table with the latest market metadata.
    """
    if not quote or not quote.get("ticker"):
        return

    ticker = quote["ticker"].strip().upper()
    bare_ticker = (
        ticker.replace(".KA", "")
              .replace(".L", "")
              .replace("PK.PSX.", "")
              .replace("UK.LSE.", "")
              .replace("US.NASDAQ.", "")
              .replace("US.NYSE.", "")
              .replace("US.", "")
    )

    market = quote.get("market_code") or ("PK" if ".KA" in ticker or "PSX" in quote.get("exchange", "") else "UK" if ".L" in ticker or "LSE" in quote.get("exchange", "") else "US")
    exchange = quote.get("exchange") or ("PSX" if market == "PK" else "LSE" if market == "UK" else "NASDAQ")
    currency = quote.get("currency") or ("PKR" if market == "PK" else "GBP" if market == "UK" else "USD")

    price = float(quote.get("price") or 0.0)
    if price <= 0:
        return

    async with ManagedSession(db) as session:
        # Ensure company & security
        await ensure_company_and_security(
            session=session,
            ticker=bare_ticker,
            name=quote.get("name") or quote.get("company_name"),
            exchange=exchange,
            market=market,
            currency=currency,
            sector=quote.get("sector"),
            industry=quote.get("industry"),
            data_source="yahoo_finance_live",
        )

        # Today's UTC midnight date
        now = datetime.now(timezone.utc)
        today_bar_time = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        sec_id = f"{market}.{exchange}.{bare_ticker}"

        prev_close = float(quote.get("prev_close") or price)
        open_price = float(quote.get("open") or prev_close)
        high_price = max(price, open_price, float(quote.get("high") or price))
        low_price = min(price, open_price, float(quote.get("low") or price))
        vol = int(quote.get("volume") or 100000)

        live_row = {
            "time": today_bar_time,
            "ticker": bare_ticker,
            "security_id": sec_id,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": price,
            "adj_close": price,
            "volume": vol,
            "currency": currency,
            "data_source": "yahoo_finance_live",
            "is_adjusted": 1,
            "quality_flag": "ok",
            "retrieved_at": now,
        }

        await session.execute(PRICE_UPSERT_SQL, [live_row])
        logger.info(f"[DB_CACHE] Saved live quote for {bare_ticker} at {price} {currency}")


# ─────────────────────────────────────────────────────────────────────────────
# News Persistence
# ─────────────────────────────────────────────────────────────────────────────
async def save_news_items(
    ticker: str,
    news_list: List[Dict[str, Any]],
    db: Optional[AsyncSession] = None
) -> int:
    """Saves news articles into `news_items`, skipping duplicates by URL."""
    if not news_list:
        return 0

    clean_sym = ticker.strip().upper()
    bare_sym = clean_sym.replace(".KA", "").replace(".L", "").replace("PK.PSX.", "").replace("US.NASDAQ.", "")
    saved_count = 0

    async with ManagedSession(db) as session:
        # Ensure company exists
        await ensure_company_and_security(session=session, ticker=bare_sym)

        now = datetime.now(timezone.utc)

        # Get existing URLs for this ticker to avoid duplicates
        res = await session.execute(
            select(NewsItem.url).where(NewsItem.ticker == bare_sym)
        )
        existing_urls = set(u for u in res.scalars().all() if u)

        for item in news_list:
            headline = (item.get("headline") or item.get("title") or "").strip()
            if not headline:
                continue

            url = (item.get("url") or item.get("link") or "").strip()
            if url and url in existing_urls:
                continue

            pub_raw = item.get("datetime") or item.get("published_at")
            if isinstance(pub_raw, (int, float)):
                pub_time = datetime.fromtimestamp(pub_raw, tz=timezone.utc)
            elif isinstance(pub_raw, str):
                try:
                    pub_time = datetime.fromisoformat(pub_raw.replace("Z", "+00:00"))
                except Exception:
                    pub_time = now
            else:
                pub_time = now

            news_model = NewsItem(
                id=uuid.uuid4(),
                ticker=bare_sym,
                headline=headline[:1000],
                summary=(item.get("summary") or item.get("description") or "")[:5000],
                url=url[:2000] if url else None,
                published_at=pub_time,
                data_available_date=now,
                retrieved_at=now,
                source_name=(item.get("source") or "Finnhub")[:100],
                source_type="news",
                sentiment_score=float(item.get("sentiment_score") or item.get("score") or 0.0),
                sentiment_label=item.get("sentiment_label") or "neutral",
            )
            session.add(news_model)
            if url:
                existing_urls.add(url)
            saved_count += 1

        logger.info(f"[DB_CACHE] Saved {saved_count} news items for {bare_sym}")

    return saved_count


# ─────────────────────────────────────────────────────────────────────────────
# Insider Transactions Persistence
# ─────────────────────────────────────────────────────────────────────────────
async def save_insider_transactions(
    ticker: str,
    transactions: List[Dict[str, Any]],
    db: Optional[AsyncSession] = None
) -> int:
    """Saves insider transactions into `insider_transactions`."""
    if not transactions:
        return 0

    clean_sym = ticker.strip().upper()
    bare_sym = clean_sym.replace(".KA", "").replace(".L", "").replace("US.NASDAQ.", "")
    saved = 0

    async with ManagedSession(db) as session:
        await ensure_company_and_security(session=session, ticker=bare_sym)
        now = datetime.now(timezone.utc)

        for tx in transactions:
            try:
                tx_date_raw = tx.get("transactionDate") or tx.get("date")
                if isinstance(tx_date_raw, str):
                    tx_date = datetime.strptime(tx_date_raw[:10], "%Y-%m-%d").date()
                else:
                    tx_date = now.date()

                filing_date_raw = tx.get("filingDate") or tx_date_raw
                if isinstance(filing_date_raw, str):
                    filing_date = datetime.strptime(filing_date_raw[:10], "%Y-%m-%d").date()
                else:
                    filing_date = tx_date

                insider_name = tx.get("name") or tx.get("insiderName") or "Insider"
                shares = int(tx.get("share") or tx.get("shares") or 0)
                price = float(tx.get("transactionPrice") or tx.get("price") or 0.0)

                rec = InsiderTransaction(
                    ticker=bare_sym,
                    transaction_date=tx_date,
                    filing_date=filing_date,
                    data_available_date=now.date(),
                    insider_name=insider_name[:255],
                    insider_title=(tx.get("title") or "Executive")[:255],
                    transaction_type=(tx.get("transactionCode") or tx.get("type") or "buy")[:20],
                    shares=shares,
                    price_per_share=price,
                    total_value=int(shares * price),
                    shares_owned_after=int(tx.get("sharesAfter") or 0),
                    created_at=now,
                )
                session.add(rec)
                saved += 1
            except Exception as exc:
                continue

        logger.info(f"[DB_CACHE] Saved {saved} insider transactions for {bare_sym}")

    return saved


# ─────────────────────────────────────────────────────────────────────────────
# Backtest Results Persistence (Cross-Platform ORM for SQLite & PostgreSQL)
# ─────────────────────────────────────────────────────────────────────────────
async def save_backtest_run(
    result: Any,
    db: Optional[AsyncSession] = None
) -> None:
    """
    Persists backtest run record and individual trade logs using ORM models.
    Works seamlessly across SQLite and PostgreSQL (replaces broken raw SQL).
    """
    if not result or not getattr(result, "run_id", None):
        return

    async with ManagedSession(db) as session:
        # Check if already saved
        res = await session.execute(
            select(BacktestRunRecord).where(BacktestRunRecord.run_id == result.run_id)
        )
        if res.scalars().first():
            return

        now = datetime.now(timezone.utc)
        record_id = uuid.uuid4()

        perf = getattr(result, "performance", None)
        cfg = getattr(result, "config", None)
        risk = getattr(result, "risk", None)
        attr = getattr(result, "attribution", None)

        def to_dict(obj):
            if hasattr(obj, "dict"):
                return obj.dict()
            if isinstance(obj, dict):
                return obj
            return {}

        run_record = BacktestRunRecord(
            id=record_id,
            run_id=result.run_id,
            name=getattr(cfg, "name", "Backtest"),
            configuration_hash=getattr(result, "configuration_hash", "hash"),
            market_code=getattr(cfg, "market_code", "US"),
            exchange_code=getattr(cfg, "exchange_code", "NASDAQ"),
            strategy_type=getattr(cfg.strategy_type, "value", str(cfg.strategy_type)) if hasattr(cfg, "strategy_type") else "CUSTOM",
            start_date=cfg.start_date if hasattr(cfg, "start_date") else now.date(),
            end_date=cfg.end_date if hasattr(cfg, "end_date") else now.date(),
            initial_capital=float(getattr(perf, "initial_capital", 100000.0)),
            ending_capital=float(getattr(perf, "ending_capital", 100000.0)),
            total_return_pct=float(getattr(perf, "total_return_pct", 0.0)),
            cagr_pct=float(getattr(perf, "cagr_pct", 0.0)) if getattr(perf, "cagr_pct", None) is not None else None,
            sharpe_ratio=float(getattr(perf, "sharpe_ratio", 0.0)) if getattr(perf, "sharpe_ratio", None) is not None else None,
            sortino_ratio=float(getattr(perf, "sortino_ratio", 0.0)) if getattr(perf, "sortino_ratio", None) is not None else None,
            calmar_ratio=float(getattr(perf, "calmar_ratio", 0.0)) if getattr(perf, "calmar_ratio", None) is not None else None,
            max_drawdown_pct=float(getattr(perf, "max_drawdown_pct", 0.0)) if getattr(perf, "max_drawdown_pct", None) is not None else None,
            win_rate_pct=float(getattr(perf, "win_rate_pct", 0.0)) if getattr(perf, "win_rate_pct", None) is not None else None,
            profit_factor=float(getattr(perf, "profit_factor", 0.0)) if getattr(perf, "profit_factor", None) is not None else None,
            total_trades=int(getattr(perf, "total_trades", 0)),
            portfolio_volatility=float(getattr(risk, "portfolio_volatility", 0.0)) if risk and getattr(risk, "portfolio_volatility", None) is not None else None,
            var_95_daily=float(getattr(risk, "var_95_daily", 0.0)) if risk and getattr(risk, "var_95_daily", None) is not None else None,
            cvar_95_daily=float(getattr(risk, "cvar_95_daily", 0.0)) if risk and getattr(risk, "cvar_95_daily", None) is not None else None,
            configuration_json=to_dict(cfg),
            performance_json=to_dict(perf),
            risk_json=to_dict(risk) if risk else None,
            attribution_json=to_dict(attr) if attr else None,
            monthly_returns_json=getattr(result, "monthly_returns_heatmap", None),
            reproducibility_seed=getattr(result, "reproducibility_seed", 42),
            execution_duration_seconds=float(getattr(result, "execution_duration_seconds", 0.0)),
            created_at=now,
        )
        session.add(run_record)
        await session.flush()

        # Save individual trades if present
        trades = getattr(result, "trades", [])
        if trades:
            for t in trades:
                try:
                    entry_dt = t.get("entry_date") if isinstance(t, dict) else getattr(t, "entry_date", now.date())
                    exit_dt = t.get("exit_date") if isinstance(t, dict) else getattr(t, "exit_date", now.date())
                    if isinstance(entry_dt, str):
                        entry_dt = datetime.strptime(entry_dt[:10], "%Y-%m-%d").date()
                    if isinstance(exit_dt, str):
                        exit_dt = datetime.strptime(exit_dt[:10], "%Y-%m-%d").date()

                    trade_model = BacktestTradeRecord(
                        id=uuid.uuid4(),
                        backtest_run_id=record_id,
                        trade_id=str(t.get("trade_id") if isinstance(t, dict) else getattr(t, "trade_id", uuid.uuid4())),
                        security_id=str(t.get("security_id") if isinstance(t, dict) else getattr(t, "security_id", "US.NASDAQ.UNKNOWN")),
                        ticker=str(t.get("ticker") if isinstance(t, dict) else getattr(t, "ticker", "UNKNOWN")),
                        market_code=getattr(cfg, "market_code", "US"),
                        side=str(t.get("side") if isinstance(t, dict) else getattr(t, "side", "LONG")),
                        entry_date=entry_dt,
                        entry_price=float(t.get("entry_price") if isinstance(t, dict) else getattr(t, "entry_price", 0.0)),
                        exit_date=exit_dt,
                        exit_price=float(t.get("exit_price") if isinstance(t, dict) else getattr(t, "exit_price", 0.0)),
                        shares=float(t.get("shares") if isinstance(t, dict) else getattr(t, "shares", 1.0)),
                        gross_pnl=float(t.get("gross_pnl") if isinstance(t, dict) else getattr(t, "gross_pnl", 0.0)),
                        net_pnl=float(t.get("net_pnl") if isinstance(t, dict) else getattr(t, "net_pnl", 0.0)),
                        return_pct=float(t.get("return_pct") if isinstance(t, dict) else getattr(t, "return_pct", 0.0)),
                        holding_period_days=int(t.get("holding_period_days") if isinstance(t, dict) else getattr(t, "holding_period_days", 1)),
                        exit_reason=str(t.get("exit_reason") if isinstance(t, dict) else getattr(t, "exit_reason", "SIGNAL")),
                    )
                    session.add(trade_model)
                except Exception as trade_err:
                    continue

        logger.info(f"[DB_CACHE] Successfully persisted backtest run {result.run_id} to database")
