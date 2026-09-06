"""
StockSense AI — Dataset Validation CLI Tool
Usage:
    python -m app.data.validate_dataset [--file PATH] [--market MARKET] [--limit N]
"""

import sys
import os
import argparse
from datetime import datetime

from app.data.providers.psx.parser import parse_psx_csv_stream, extract_psx_securities_from_csv
from app.data.providers.psx.provider import DEFAULT_PSX_CSV_LOCATIONS
from app.data.validation.data_quality import data_quality_engine


def validate_dataset_cli():
    parser = argparse.ArgumentParser(description="StockSense AI Dataset Integrity Validator")
    parser.add_argument("--file", type=str, default=None, help="Path to CSV dataset file")
    parser.add_argument("--market", type=str, default="PK", help="Market code (PK, US, etc.)")
    parser.add_argument("--exchange", type=str, default="PSX", help="Exchange code (PSX, NASDAQ, etc.)")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of rows to validate")
    args = parser.parse_args()

    csv_path = args.file
    if not csv_path:
        for loc in DEFAULT_PSX_CSV_LOCATIONS:
            if os.path.exists(loc):
                csv_path = loc
                break

    if not csv_path or not os.path.exists(csv_path):
        print(f"❌ Error: Dataset file not found. Checked: {DEFAULT_PSX_CSV_LOCATIONS}")
        sys.exit(1)

    print(f"🔍 Analyzing Dataset: {csv_path}")
    print(f"🌍 Market: {args.market} | Exchange: {args.exchange}")
    print("⏳ Streaming and validating records...")

    raw_prices = []
    for price_dto, err in parse_psx_csv_stream(csv_path, limit=args.limit):
        if price_dto:
            raw_prices.append(price_dto)

    securities_map = extract_psx_securities_from_csv(csv_path, limit=args.limit)
    securities = list(securities_map.values())

    result = data_quality_engine.evaluate(
        provider="kaggle_psx_csv",
        market=args.market,
        exchange=args.exchange,
        prices=raw_prices,
        securities=securities,
    )

    print("\n============================================================")
    print("           STOCKSENSE AI DATA QUALITY REPORT                ")
    print("============================================================")
    print(f" Provider:                  {result.provider}")
    print(f" Market:                    {result.market} ({args.market})")
    print(f" Exchange:                  {result.exchange}")
    print(f" Date Range:                {result.date_range[0]} to {result.date_range[1]}")
    print(f" Unique Securities:         {result.securities_count:,}")
    print(f" Total Rows Checked:        {result.records_checked:,}")
    print(f" Records Accepted:          {result.records_accepted:,}")
    print(f" Records Rejected:          {result.records_rejected:,}")
    print(f" Exact Duplicates:          {result.duplicates_count:,}")
    print(f" Invalid Values:            {result.invalid_values_count:,}")
    print(f" Extreme Moves (>30%):      {result.extreme_moves_count:,}")
    print(f" Delisted / Inactive:       {result.delisted_count:,}")
    print(f" Quality Score:             {result.quality_score:.2f} / 100.00")
    print(f" Overall Status:            {result.status}")
    print(f" Licensing:                 {result.licensing_notes}")
    if result.survivorship_bias_warning:
        print(f" Survivorship Bias:         ⚠️ {result.survivorship_bias_warning}")
    else:
        print(f" Survivorship Bias:         ✅ Delisted securities tracked")
    print("============================================================\n")

    if result.warnings:
        print("Top Quality Warnings:")
        for w in result.warnings[:5]:
            print(f"  • {w}")
        print()

    return result


if __name__ == "__main__":
    validate_dataset_cli()
