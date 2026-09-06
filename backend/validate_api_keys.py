"""Quick API key validation script — run from backend/ directory."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    from app.core.live_data import (
        fetch_finnhub_quote, fetch_finnhub_news, fetch_finnhub_sentiment,
        fetch_alpha_vantage_overview, fetch_alpha_vantage_daily,
        fetch_fred_series, fetch_macro_snapshot,
        fetch_sec_ticker_search, fetch_full_stock_snapshot
    )
    print("=" * 60)
    print("🚀 StockSense AI — Live Real Data Verification")
    print("=" * 60)

    # 1. Finnhub Quote & News
    try:
        q = await fetch_finnhub_quote("AAPL")
        news = await fetch_finnhub_news("AAPL", 7)
        sent = await fetch_finnhub_sentiment("AAPL")
        print(f"✅ Finnhub:       AAPL Price = ${q.get('price')} (Change: {q.get('change_pct')}%)")
        print(f"   ✓ Live News:   {len(news)} articles analyzed via VADER NLP")
        print(f"   ✓ Sentiment:   Score = {sent.get('sentiment_score')}/100 ({sent.get('bullish_pct')}% Bullish)")
    except Exception as e:
        print(f"❌ Finnhub:       {e}")

    # 2. Alpha Vantage
    try:
        av = await fetch_alpha_vantage_overview("AAPL")
        print(f"✅ Alpha Vantage: {av.get('Name')} | Sector: {av.get('Sector')}")
        print(f"   ✓ Trailing PE: {av.get('TrailingPE')} | Beta: {av.get('Beta')} | 52W High: ${av.get('52WeekHigh')}")
    except Exception as e:
        print(f"❌ Alpha Vantage: {e}")

    # 3. FRED
    try:
        macro = await fetch_macro_snapshot()
        print(f"✅ FRED:          Live VIX = {macro.get('vix')} | Fed Funds Rate = {macro.get('fed_funds_rate')}%")
    except Exception as e:
        print(f"❌ FRED:          {e}")

    # 4. SEC EDGAR
    try:
        sec = await fetch_sec_ticker_search("apple")
        print(f"✅ SEC EDGAR:     Found {len(sec)} active registered companies for query 'apple'")
    except Exception as e:
        print(f"❌ SEC EDGAR:     {e}")

    # 5. Composite Snapshot
    try:
        snap = await fetch_full_stock_snapshot("AAPL")
        print("\n📊 Master Live Snapshot Generated:")
        print(f"   Ticker: {snap['ticker']} ({snap['name']})")
        print(f"   Price: ${snap['price']} | P/E: {snap['pe_ratio']} | Sentiment: {snap['sentiment_score']}/100")
        print(f"   Live Sources Active: {snap['live_sources']}")
    except Exception as e:
        print(f"❌ Snapshot:      {e}")

    print("=" * 60)

asyncio.run(main())
