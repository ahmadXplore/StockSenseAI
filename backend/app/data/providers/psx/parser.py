"""
StockSense AI — PSX Dataset Parser & Ingestion Streamer
Parses the Kaggle Pakistan Stock Market Dataset 2017-2025 and live daily feeds.
"""

from __future__ import annotations
import csv
import os
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Generator, List, Dict, Tuple, Optional

from app.data.canonical.market import build_security_id
from app.data.canonical.price import CanonicalPriceDTO
from app.data.canonical.security import SecurityDTO, SecurityStatus, SecurityType
from app.data.providers.psx.validator import sanitize_psx_row


def parse_psx_csv_stream(
    csv_path: str,
    limit: Optional[int] = None
) -> Generator[Tuple[CanonicalPriceDTO, Optional[str]], None, None]:
    """
    Generator streaming CanonicalPriceDTO instances from PSX CSV.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"PSX CSV file not found at {csv_path}")

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        count = 0
        for raw_row in reader:
            cleaned, err = sanitize_psx_row(raw_row)
            if err or not cleaned:
                yield None, err
                continue

            dt_parsed = datetime.strptime(cleaned["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            sec_id = build_security_id("PK", "PSX", cleaned["symbol"])
            
            # Check for zero close / untraded quality flag
            q_flag = "ok"
            if cleaned["close"] <= 0:
                q_flag = "zero_price"
            elif cleaned["volume"] == 0:
                q_flag = "zero_volume"

            price = CanonicalPriceDTO(
                security_id=sec_id,
                ticker=cleaned["symbol"],
                timestamp=dt_parsed,
                open=cleaned["open"],
                high=cleaned["high"],
                low=cleaned["low"],
                close=cleaned["close"],
                adj_close=cleaned["close"], # Unadjusted close defaults as base
                volume=cleaned["volume"],
                vwap=None,
                currency="PKR",
                split_factor=Decimal("1.0"),
                dividend_amount=Decimal("0.0"),
                source_id=f"psx_csv_{cleaned['date']}_{cleaned['symbol']}",
                data_source="kaggle_psx",
                is_adjusted=False,
                quality_flag=q_flag,
                retrieved_at=datetime.now(timezone.utc),
            )

            yield price, None
            count += 1
            if limit and count >= limit:
                break


def extract_psx_securities_from_csv(
    csv_path: str,
    limit: Optional[int] = None
) -> Dict[str, SecurityDTO]:
    """
    Scans the PSX CSV to build SecurityDTO records with detected listing date ranges.
    """
    if not os.path.exists(csv_path):
        return {}

    symbol_dates: Dict[str, Dict[str, Any]] = {}
    
    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        count = 0
        for raw_row in reader:
            sym = str(raw_row.get("SYMBOL", "")).strip().upper()
            d_str = str(raw_row.get("DATE", "")).strip()
            if not sym or not d_str or len(d_str) < 10:
                continue

            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            if sym not in symbol_dates:
                symbol_dates[sym] = {
                    "first_date": dt,
                    "last_date": dt,
                    "count": 1
                }
            else:
                if dt < symbol_dates[sym]["first_date"]:
                    symbol_dates[sym]["first_date"] = dt
                if dt > symbol_dates[sym]["last_date"]:
                    symbol_dates[sym]["last_date"] = dt
                symbol_dates[sym]["count"] += 1
            
            count += 1
            if limit and count >= limit:
                break

    securities: Dict[str, SecurityDTO] = {}
    latest_overall = max((s["last_date"] for s in symbol_dates.values()), default=date.today())

    for sym, info in symbol_dates.items():
        sec_id = build_security_id("PK", "PSX", sym)
        
        # If not traded in the last 180 days of dataset, flag as delisted/inactive
        is_delisted = (latest_overall - info["last_date"]).days > 180
        status = SecurityStatus.DELISTED if is_delisted else SecurityStatus.ACTIVE
        delist_date = info["last_date"] if is_delisted else None
        delist_reason = "No longer actively traded on PSX" if is_delisted else None

        sec = SecurityDTO(
            security_id=sec_id,
            exchange_id="PSX",
            market_id="PK",
            symbol=sym,
            company_name=f"{sym} (PSX Listed)",
            legal_name=f"{sym} Pakistan Ltd.",
            country="Pakistan",
            currency="PKR",
            sector="General",
            industry="Equities",
            security_type=SecurityType.COMMON_STOCK,
            status=status,
            listing_date=info["first_date"],
            delisting_date=delist_date,
            delisting_reason=delist_reason,
            primary_exchange="PSX",
            provider_security_id=f"PSX:{sym}",
        )
        securities[sym] = sec

    return securities
