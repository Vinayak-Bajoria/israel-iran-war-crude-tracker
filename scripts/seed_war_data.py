#!/usr/bin/env python3
"""
One-time seed script: Populate MongoDB Atlas with June 2025 war period data.
Uses the Groww API wrapper for Indian stocks,
and Yahoo Finance for WTI/Brent crude.

Usage:
    cd oil-gas-war
    python scripts/seed_war_data.py
"""

import sys, os, time

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from utils.groww_api import fetch_historical_candles, fetch_nifty50
from utils.mongo_db import upsert_candles, log_fetch
from utils.constants import (
    UPSTREAM_TICKERS, DOWNSTREAM_TICKERS, GAS_TICKERS,
    CRUDE_YF_TICKERS, WAR_PERIOD_START, WAR_PERIOD_END,
)


def seed_indian_stocks():
    """Fetch all 15 Oil & Gas stocks from Groww API."""
    print("\n" + "=" * 60)
    print("📡 Fetching Indian stocks from Groww API...")
    print("=" * 60)

    segment_map = {
        "upstream": UPSTREAM_TICKERS,
        "downstream": DOWNSTREAM_TICKERS,
        "gas": GAS_TICKERS,
    }

    total = 0
    for category, tickers in segment_map.items():
        for display_name, nse_symbol in tickers.items():
            try:
                candles = fetch_historical_candles(
                    trading_symbol=nse_symbol,
                    start_date=f"{WAR_PERIOD_START} 09:00:00",
                    end_date=f"{WAR_PERIOD_END} 15:30:00",
                    exchange="NSE",
                    interval_minutes=1440,
                )
                if candles:
                    upsert_candles(display_name, "groww", category, candles)
                    total += len(candles)
                    print(f"  ✅ {display_name:<18} {len(candles):>3} candles ({category})")
                else:
                    print(f"  ⚠️  {display_name:<18} no candles returned")

                time.sleep(0.5)
            except Exception as e:
                print(f"  ❌ {display_name:<18} ERROR: {e}")

    print(f"\n  Total Indian stock rows: {total}")
    log_fetch("groww", "seed_war_data", "success", f"{total} rows seeded")


def seed_nifty50():
    """Fetch Nifty 50 index."""
    print("\n📡 Fetching Nifty 50 index from Groww API...")
    try:
        candles = fetch_nifty50(
            f"{WAR_PERIOD_START} 09:00:00",
            f"{WAR_PERIOD_END} 15:30:00",
        )
        if candles:
            upsert_candles("Nifty 50", "groww", "index", candles)
            print(f"  ✅ Nifty 50: {len(candles)} candles")
            log_fetch("groww", "Nifty 50", "success", f"{len(candles)} candles seeded")
        else:
            print("  ⚠️  Nifty 50: no candles — will try yfinance fallback")
            _seed_nifty_fallback()
    except Exception as e:
        print(f"  ❌ Nifty 50 Groww: {e} — trying yfinance fallback")
        _seed_nifty_fallback()


def _seed_nifty_fallback():
    """Fallback: fetch Nifty 50 from yfinance."""
    try:
        import yfinance as yf
        df = yf.download("^NSEI", start=WAR_PERIOD_START, end=WAR_PERIOD_END,
                         progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            if hasattr(df.columns, 'levels'):
                df.columns = df.columns.get_level_values(0)
            candles = [{"date": idx.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]), "high": float(row["High"]),
                        "low": float(row["Low"]), "close": float(row["Close"]),
                        "volume": float(row.get("Volume", 0))}
                       for idx, row in df.iterrows()]
            upsert_candles("Nifty 50", "yfinance", "index", candles)
            print(f"  ✅ Nifty 50 (yfinance fallback): {len(candles)} candles")
    except Exception as e:
        print(f"  ❌ Nifty 50 yfinance fallback: {e}")


def seed_crude_oil():
    """Fetch WTI & Brent crude from Yahoo Finance."""
    print("\n📡 Fetching crude oil from Yahoo Finance...")
    try:
        import yfinance as yf
    except ImportError:
        print("  ❌ yfinance not installed. Run: pip install yfinance")
        return

    for label, yf_ticker in CRUDE_YF_TICKERS.items():
        try:
            df = yf.download(yf_ticker, start=WAR_PERIOD_START, end=WAR_PERIOD_END,
                             progress=False, auto_adjust=True)
            if df is None or df.empty:
                print(f"  ⚠️  {label}: no data from yfinance")
                continue

            if hasattr(df.columns, 'levels'):
                df.columns = df.columns.get_level_values(0)

            candles = [{"date": idx.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]), "high": float(row["High"]),
                        "low": float(row["Low"]), "close": float(row["Close"]),
                        "volume": float(row.get("Volume", 0))}
                       for idx, row in df.iterrows()]

            upsert_candles(label, "yfinance", "crude", candles)
            print(f"  ✅ {label}: {len(candles)} candles")

        except Exception as e:
            print(f"  ❌ {label}: {e}")


def main():
    print("🚀 Seeding MongoDB Atlas with June 2025 war period data")
    print(f"   Period: {WAR_PERIOD_START} → {WAR_PERIOD_END}")
    print(f"   DB:     MongoDB Atlas (oil_gas_war)")

    seed_indian_stocks()
    seed_nifty50()
    seed_crude_oil()

    print("\n" + "=" * 60)
    print("✅ Seed complete! Data is in MongoDB Atlas.")
    print("   streamlit run app.py --server.port 8502")
    print("=" * 60)


if __name__ == "__main__":
    main()
