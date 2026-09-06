"""
StockSense AI -- PSX 2020-2026 Kaggle Dataset Parser
Parses the new-format Kaggle PSX dataset with lowercase column headers,
including enriched fields (company_name, sector, moving averages, macro indicators).
"""

from __future__ import annotations
import csv
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Generator, Tuple, Optional, Dict

from app.data.canonical.market import build_security_id
from app.data.canonical.price import CanonicalPriceDTO


def _safe_decimal(val: str, fallback: Decimal = Decimal("0")) -> Decimal:
    """Safe Decimal parse that handles empty strings and commas."""
    try:
        return Decimal(str(val).replace(",", "").strip() or "0")
    except (InvalidOperation, ValueError):
        return fallback


def _safe_int(val: str) -> int:
    """Safe int parse for volume fields."""
    try:
        return int(float(str(val).replace(",", "").strip() or "0"))
    except (ValueError, TypeError):
        return 0


def parse_new_psx_csv_stream(
    csv_path: str,
    limit: Optional[int] = None,
) -> Generator[Tuple[Optional[CanonicalPriceDTO], Optional[str]], None, None]:
    """
    Generator streaming CanonicalPriceDTO instances from the 2020-2026 PSX CSV format.
    Column format: date, symbol, open, high, low, close, volume (lowercase headers)
    Also handles enriched files that include company_name, sector, macro indicators, etc.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"PSX 2020-2026 CSV not found at: {csv_path}")

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        count = 0

        for raw_row in reader:
            # --- Symbol ---
            symbol = str(raw_row.get("symbol", "")).strip().upper()
            if not symbol or symbol in ("SYMBOL", ""):
                yield None, "Empty symbol"
                continue

            # --- Date ---
            date_str = str(raw_row.get("date", "")).strip()
            if not date_str or len(date_str) < 10:
                yield None, f"Invalid date: {date_str!r}"
                continue
            date_str = date_str[:10]  # Normalize to YYYY-MM-DD

            try:
                dt_parsed = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                yield None, f"Bad date format: {date_str!r}"
                continue

            # --- OHLCV ---
            c_open = _safe_decimal(raw_row.get("open", "0"))
            c_high = _safe_decimal(raw_row.get("high", "0"))
            c_low = _safe_decimal(raw_row.get("low", "0"))
            c_close = _safe_decimal(raw_row.get("close", "0"))
            volume = _safe_int(raw_row.get("volume", "0"))

            # Skip completely zero rows
            if c_close <= 0 and c_open <= 0:
                yield None, f"Zero price row: {symbol} {date_str}"
                continue

            # Handle untraded sessions: use close as best available price
            if c_open <= 0:
                c_open = c_close
            if c_high <= 0:
                c_high = max(c_open, c_close)
            if c_low <= 0:
                c_low = min(c_open, c_close)

            # Enforce OHLC geometry validity
            if c_close > 0:
                c_high = max(c_high, c_open, c_close, c_low)
                c_low = min(c_low, c_open, c_close, c_high)
                if c_low <= 0:
                    c_low = min(c_open, c_close)

            # Volume should be non-negative
            if volume < 0:
                volume = 0

            # --- Quality flag ---
            q_flag = "ok"
            if c_close <= 0:
                q_flag = "zero_price"
            elif volume == 0:
                q_flag = "zero_volume"

            sec_id = build_security_id("PK", "PSX", symbol)

            price = CanonicalPriceDTO(
                security_id=sec_id,
                ticker=symbol,
                timestamp=dt_parsed,
                open=c_open,
                high=c_high,
                low=c_low,
                close=c_close,
                adj_close=c_close,  # Unadjusted close
                volume=volume,
                vwap=None,
                currency="PKR",
                split_factor=Decimal("1.0"),
                dividend_amount=Decimal("0.0"),
                source_id=f"psx_kaggle_2026_{date_str}_{symbol}",
                data_source="kaggle_psx_2026",
                is_adjusted=False,
                quality_flag=q_flag,
                retrieved_at=datetime.now(timezone.utc),
            )

            yield price, None
            count += 1
            if limit and count >= limit:
                break


def load_company_metadata(metadata_csv_path: str) -> Dict[str, Dict[str, str]]:
    """
    Loads company_metadata.csv into a dict: {SYMBOL: {name, sector}}.
    Used to enrich SecurityDTO records with real company names and sectors.
    """
    result: Dict[str, Dict[str, str]] = {}
    if not os.path.exists(metadata_csv_path):
        return result

    with open(metadata_csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = str(row.get("symbol", "")).strip().upper()
            if symbol:
                result[symbol] = {
                    "name": str(row.get("name", "")).strip(),
                    "sector": str(row.get("sector", "")).strip(),
                }
    return result
