"""
Groww API wrapper — mirrors the Groww MCP `fetch_historical_candle_data` tool.
Calls the same REST endpoints that the MCP server wraps.

Used by:
  - Airflow DAG (scheduled every 30 min)
  - scripts/seed_war_data.py (one-time historical seed)
"""

import requests
import time
from datetime import datetime
from typing import Optional

GROWW_BASE = "https://groww.in/v1/api/charting_service/v4/chart/exchange"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Origin": "https://groww.in",
    "Referer": "https://groww.in/",
}

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def _to_epoch_ms(dt_str: str) -> int:
    """Convert 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' to epoch milliseconds."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return int(datetime.strptime(dt_str, fmt).timestamp() * 1000)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {dt_str}")


def fetch_historical_candles(
    trading_symbol: str,
    start_date: str,
    end_date: str,
    exchange: str = "NSE",
    interval_minutes: int = 1440,
) -> list[dict]:
    """
    Fetch daily OHLCV candles from Groww's charting API.

    Args:
        trading_symbol: NSE symbol (e.g. 'ONGC', 'RELIANCE')
        start_date: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
        end_date:   'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'
        exchange:   'NSE' (default) or 'BSE'
        interval_minutes: 1440 for daily (default)

    Returns:
        List of dicts: [{date, open, high, low, close, volume}, ...]
    """
    start_ms = _to_epoch_ms(start_date)
    end_ms = _to_epoch_ms(end_date)

    url = (
        f"{GROWW_BASE}/{exchange}/segment/CASH/{trading_symbol}"
        f"?startTimeInMillis={start_ms}"
        f"&endTimeInMillis={end_ms}"
        f"&intervalInMinutes={interval_minutes}"
    )

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            candles = []
            raw = data.get("candles", [])

            for c in raw:
                # Groww returns: [timestamp_epoch_sec, open, high, low, close, volume]
                if isinstance(c, list) and len(c) >= 5:
                    ts = c[0]
                    dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                    candles.append({
                        "date": dt,
                        "open": c[1],
                        "high": c[2],
                        "low": c[3],
                        "close": c[4],
                        "volume": c[5] if len(c) > 5 and c[5] is not None else 0,
                    })

            return candles

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429:  # Rate limit
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            raise
        except requests.exceptions.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise

    return []


def fetch_multiple_symbols(
    symbols: dict[str, str],
    start_date: str,
    end_date: str,
    delay_between: float = 0.5,
) -> dict[str, list[dict]]:
    """
    Fetch candles for multiple symbols with rate-limiting delay.

    Args:
        symbols: {display_label: nse_symbol} mapping
        start_date, end_date: date strings
        delay_between: seconds to wait between API calls

    Returns:
        {display_label: [candle_dicts]}
    """
    results = {}
    for label, nse_sym in symbols.items():
        try:
            candles = fetch_historical_candles(nse_sym, start_date, end_date)
            results[label] = candles
            if delay_between > 0:
                time.sleep(delay_between)
        except Exception as e:
            print(f"⚠️  Failed to fetch {label} ({nse_sym}): {e}")
            results[label] = []

    return results


def fetch_nifty50(start_date: str, end_date: str) -> list[dict]:
    """
    Fetch Nifty 50 index data from Groww.
    Groww uses a different endpoint pattern for indices.
    """
    start_ms = _to_epoch_ms(start_date)
    end_ms = _to_epoch_ms(end_date)

    # Try the indices endpoint
    urls = [
        f"https://groww.in/v1/api/charting_service/v4/chart/exchange/NSE/segment/CASH/NIFTY"
        f"?startTimeInMillis={start_ms}&endTimeInMillis={end_ms}&intervalInMinutes=1440",
        f"https://groww.in/v1/api/charting_service/v4/chart/index/GIDXNIFTY"
        f"?startTimeInMillis={start_ms}&endTimeInMillis={end_ms}&intervalInMinutes=1440",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                candles = []
                for c in data.get("candles", []):
                    if isinstance(c, list) and len(c) >= 5:
                        dt = datetime.fromtimestamp(c[0]).strftime("%Y-%m-%d")
                        candles.append({
                            "date": dt,
                            "open": c[1],
                            "high": c[2],
                            "low": c[3],
                            "close": c[4],
                            "volume": c[5] if len(c) > 5 and c[5] is not None else 0,
                        })
                if candles:
                    return candles
        except Exception:
            continue

    return []
