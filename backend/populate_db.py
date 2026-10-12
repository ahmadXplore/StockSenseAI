"""
StockSense AI — Database Population Script
Imports compiled_psx_historical_2017_2025.csv into SQLite.

Order of operations (respects FK constraints):
  1. Market (PK)
  2. Exchange (PSX)
  3. Securities (one per unique SYMBOL)
  4. Companies (one per unique SYMBOL)
  5. PriceData (all OHLCV rows)
"""

import csv
import sqlite3
import os
from datetime import datetime, timezone

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "compiled_psx_historical_2017_2025.csv")
DB_PATH  = os.path.join(os.path.dirname(__file__), "stocksense.db")

MARKET_ID   = "PK"
EXCHANGE_ID = "PSX"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")   # 64 MB cache
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_market(conn: sqlite3.Connection):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT OR IGNORE INTO markets
            (id, code, name, country, default_currency, timezone, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (MARKET_ID, "PSX", "Pakistan Stock Exchange", "Pakistan",
          "PKR", "Asia/Karachi", "ACTIVE", now, now))
    conn.commit()
    print("[1/5] Market seeded (PK - Pakistan)")


def seed_exchange(conn: sqlite3.Connection):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT OR IGNORE INTO exchanges
            (id, market_id, code, name, country, currency, timezone,
             mic_code, website, status, trading_calendar_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (EXCHANGE_ID, MARKET_ID, "PSX",
          "Pakistan Stock Exchange", "Pakistan", "PKR", "Asia/Karachi",
          "XKAR", "https://www.psx.com.pk", "ACTIVE", "PSX", now, now))
    conn.commit()
    print("[2/5] Exchange seeded (PSX)")


def load_symbols_from_csv() -> list[dict]:
    """Read CSV once, return list of dicts per row."""
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    print(f"      CSV loaded: {len(rows):,} rows")
    return rows


def seed_securities_and_companies(conn: sqlite3.Connection, rows: list[dict]):
    symbols = {}
    for row in rows:
        sym = row["SYMBOL"].strip().upper()
        if sym and sym not in symbols:
            symbols[sym] = row

    now = datetime.now(timezone.utc).isoformat()

    sec_data = []
    comp_data = []
    for sym in symbols:
        security_id = f"PK.PSX.{sym}"
        sec_data.append((
            security_id, EXCHANGE_ID, MARKET_ID,
            sym, f"{sym} Listed on PSX",
            None,               # legal_name
            "Pakistan", "PKR",
            None, None,         # sector, industry
            "COMMON_STOCK", "ACTIVE",
            None, None, None,   # listing_date, delisting_date, delisting_reason
            EXCHANGE_ID,        # primary_exchange
            None, None, None,   # cik, isin, cusip
            None,               # provider_security_id
            now, now
        ))
        comp_data.append((
            sym, security_id,
            f"{sym} Corp.",
            EXCHANGE_ID,
            "Pakistan", "PKR",
            None, None,         # sector, industry
            1,                  # is_active
            0,                  # is_delisted
            None, None,         # delisted_date, delisted_reason
            "PSX_CSV",          # data_source
            now, now
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO securities
            (security_id, exchange_id, market_id, symbol, company_name,
             legal_name, country, currency, sector, industry,
             security_type, status,
             listing_date, delisting_date, delisting_reason,
             primary_exchange, cik, isin, cusip,
             provider_security_id, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, sec_data)

    conn.executemany("""
        INSERT OR IGNORE INTO companies
            (ticker, security_id, name, exchange, country, currency,
             sector, industry, is_active, is_delisted,
             delisted_date, delisted_reason, data_source,
             created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, comp_data)

    conn.commit()
    print(f"[3/5] Securities seeded  ({len(sec_data):,} symbols)")
    print(f"[4/5] Companies seeded   ({len(comp_data):,} symbols)")


def safe_decimal(val: str):
    try:
        v = float(val.strip()) if val and val.strip() else None
        return v
    except (ValueError, AttributeError):
        return None


def safe_int(val: str):
    try:
        return int(float(val.strip())) if val and val.strip() else None
    except (ValueError, AttributeError):
        return None


def seed_price_data(conn: sqlite3.Connection, rows: list[dict]):
    BATCH = 10_000
    now_str = datetime.now(timezone.utc).isoformat()
    batch = []
    inserted = 0
    skipped  = 0

    for row in rows:
        sym   = row["SYMBOL"].strip().upper()
        date_str = row["DATE"].strip()
        if not sym or not date_str:
            skipped += 1
            continue

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
                hour=9, minute=30, tzinfo=timezone.utc
            ).isoformat()
        except ValueError:
            skipped += 1
            continue

        security_id = f"PK.PSX.{sym}"
        open_  = safe_decimal(row.get("OPEN", ""))
        high   = safe_decimal(row.get("HIGH", ""))
        low    = safe_decimal(row.get("LOW", ""))
        close  = safe_decimal(row.get("CLOSE", ""))
        volume = safe_int(row.get("VOLUME", ""))

        batch.append((
            dt,              # time
            sym,             # ticker
            security_id,     # security_id
            open_,           # open
            high,            # high
            low,             # low
            close,           # close
            close,           # adj_close  (no adjustment factor in CSV)
            volume,          # volume
            None,            # vwap
            "PKR",           # currency
            None,            # split_factor
            None,            # dividend_amount
            None,            # source_id
            "PSX_CSV",       # data_source
            0,               # is_adjusted
            "OK",            # quality_flag
            now_str,         # retrieved_at
        ))

        if len(batch) >= BATCH:
            conn.executemany("""
                INSERT OR IGNORE INTO price_data
                    (time, ticker, security_id, open, high, low, close, adj_close,
                     volume, vwap, currency, split_factor, dividend_amount,
                     source_id, data_source, is_adjusted, quality_flag, retrieved_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, batch)
            conn.commit()
            inserted += len(batch)
            batch = []
            print(f"      ... {inserted:,} rows inserted", end="\r", flush=True)

    # Final batch
    if batch:
        conn.executemany("""
            INSERT OR IGNORE INTO price_data
                (time, ticker, security_id, open, high, low, close, adj_close,
                 volume, vwap, currency, split_factor, dividend_amount,
                 source_id, data_source, is_adjusted, quality_flag, retrieved_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
        conn.commit()
        inserted += len(batch)

    print(f"\n[5/5] Price data seeded  ({inserted:,} rows inserted, {skipped} skipped)")


def print_summary(conn: sqlite3.Connection):
    tables = ["markets", "exchanges", "securities", "companies", "price_data",
              "users", "lan_devices", "lan_access_logs", "watchlists", "watchlist_items"]
    print("\n" + "=" * 50)
    print("  DATABASE SUMMARY")
    print("=" * 50)
    for t in tables:
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
            print(f"  {t:<30} {count:>10,} rows")
        except Exception as e:
            print(f"  {t:<30} ERROR: {e}")
    print("=" * 50)


def main():
    print("\nStockSense AI - Database Population Starting...\n")

    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV not found at: {CSV_PATH}")
        return

    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("   Run: python init_sqlite_db.py  first.")
        return

    conn = connect()

    try:
        seed_market(conn)
        seed_exchange(conn)
        print("\n      Loading CSV into memory...")
        rows = load_symbols_from_csv()
        seed_securities_and_companies(conn, rows)
        seed_price_data(conn, rows)
        print_summary(conn)
        print("\nDone! Database fully populated!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
