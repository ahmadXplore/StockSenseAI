"""
StockSense AI — International Multi-Source Payload Normalizer
Converts yfinance, Stooq, Alpha Vantage, and FMP payloads into CanonicalPriceDTO.
"""

from __future__ import annotations
from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.data.canonical.market import build_security_id
from app.data.canonical.price import CanonicalPriceDTO
from app.data.providers.international.validator import sanitize_international_candle


def parse_yfinance_dataframe(
    df: Any,
    ticker: str,
    market_code: str = "US",
    exchange_code: str = "NASDAQ",
    currency: str = "USD"
) -> List[CanonicalPriceDTO]:
    """
    Parses a pandas DataFrame returned by yfinance into CanonicalPriceDTO list.
    """
    canonical_prices: List[CanonicalPriceDTO] = []
    if df is None or df.empty:
        return canonical_prices

    # Flatten MultiIndex columns if present
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df = df.copy()
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    sec_id = build_security_id(market_code, exchange_code, ticker)
    is_uk = (market_code.upper() in ("UK", "GB") or exchange_code.upper() == "LSE" or ticker.upper().endswith(".L"))
    norm_currency = "GBP" if is_uk else currency.upper()

    for idx, row in df.iterrows():
        # idx can be Timestamp or string
        if isinstance(idx, (datetime, date)):
            ts = datetime(idx.year, idx.month, idx.day, tzinfo=timezone.utc)
            ts_str = ts.strftime("%Y-%m-%d")
        else:
            ts_str = str(idx).split(" ")[0]
            try:
                ts = datetime.strptime(ts_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        r_open = row.get("Open")
        r_high = row.get("High")
        r_low = row.get("Low")
        r_close = row.get("Close")
        r_adj_close = row.get("Adj Close", r_close)
        r_vol = row.get("Volume", 0)

        # Yahoo Finance quotes LSE (UK) stocks in pence (GBp). Convert to Pounds (GBP) so values match £ currency.
        if is_uk and r_close is not None:
            try:
                val = float(r_close)
                if val > 10.0:  # In pence (e.g. 11962p -> £119.62)
                    r_open = (float(r_open) / 100.0) if r_open is not None else None
                    r_high = (float(r_high) / 100.0) if r_high is not None else None
                    r_low = (float(r_low) / 100.0) if r_low is not None else None
                    r_close = val / 100.0
                    r_adj_close = (float(r_adj_close) / 100.0) if r_adj_close is not None else r_close
            except (ValueError, TypeError):
                pass

        cleaned, err = sanitize_international_candle(
            ticker=ticker,
            timestamp_str=ts_str,
            raw_open=r_open,
            raw_high=r_high,
            raw_low=r_low,
            raw_close=r_close,
            raw_adj_close=r_adj_close,
            raw_volume=r_vol,
            currency=norm_currency
        )
        if err or not cleaned:
            continue

        dto = CanonicalPriceDTO(
            security_id=sec_id,
            ticker=ticker.upper(),
            timestamp=ts,
            open=cleaned["open"],
            high=cleaned["high"],
            low=cleaned["low"],
            close=cleaned["close"],
            adj_close=cleaned["adj_close"],
            volume=cleaned["volume"],
            vwap=None,
            currency=norm_currency,
            split_factor=Decimal("1.0"),
            dividend_amount=Decimal("0.0"),
            source_id=f"yf_{ts_str}_{ticker.upper()}",
            data_source="yfinance",
            is_adjusted=True,
            quality_flag="ok",
            retrieved_at=datetime.now(timezone.utc)
        )
        canonical_prices.append(dto)

    canonical_prices.sort(key=lambda p: p.timestamp)
    return canonical_prices


def parse_alpha_vantage_daily_json(
    data: Dict[str, Any],
    ticker: str,
    market_code: str = "US",
    exchange_code: str = "NASDAQ",
    currency: str = "USD"
) -> List[CanonicalPriceDTO]:
    """
    Parses Alpha Vantage TIME_SERIES_DAILY JSON payload.
    """
    canonical_prices: List[CanonicalPriceDTO] = []
    ts_data = data.get("Time Series (Daily)") or data.get("Time Series (Daily Adjusted)") or {}
    sec_id = build_security_id(market_code, exchange_code, ticker)

    for date_str, bar in ts_data.items():
        try:
            ts = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        r_open = bar.get("1. open")
        r_high = bar.get("2. high")
        r_low = bar.get("3. low")
        r_close = bar.get("4. close")
        r_adj_close = bar.get("5. adjusted close", r_close)
        r_vol = bar.get("6. volume") or bar.get("5. volume") or 0

        cleaned, err = sanitize_international_candle(
            ticker=ticker,
            timestamp_str=date_str,
            raw_open=r_open,
            raw_high=r_high,
            raw_low=r_low,
            raw_close=r_close,
            raw_adj_close=r_adj_close,
            raw_volume=r_vol,
            currency=currency
        )
        if err or not cleaned:
            continue

        dto = CanonicalPriceDTO(
            security_id=sec_id,
            ticker=ticker.upper(),
            timestamp=ts,
            open=cleaned["open"],
            high=cleaned["high"],
            low=cleaned["low"],
            close=cleaned["close"],
            adj_close=cleaned["adj_close"],
            volume=cleaned["volume"],
            vwap=None,
            currency=currency.upper(),
            split_factor=Decimal("1.0"),
            dividend_amount=Decimal("0.0"),
            source_id=f"av_{date_str}_{ticker.upper()}",
            data_source="alpha_vantage",
            is_adjusted=True,
            quality_flag="ok",
            retrieved_at=datetime.now(timezone.utc)
        )
        canonical_prices.append(dto)

    canonical_prices.sort(key=lambda p: p.timestamp)
    return canonical_prices
