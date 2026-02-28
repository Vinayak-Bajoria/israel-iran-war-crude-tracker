"""
Airflow DAG: Oil & Gas Data Fetcher
Runs every 30 minutes during market hours to fetch stock and crude oil data
from Groww API and Yahoo Finance, then stores it in MongoDB Atlas.

Setup:
    ln -sf /Users/vbajoria/temp/oil-gas-war/dags/oil_gas_fetcher_dag.py ~/airflow/dags/
"""

import sys
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Add project root to path so we can import utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


# ══════════════════════════════════════════════════════════════════════════════
# TASK FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def fetch_indian_stocks(**context):
    """Fetch all 15 Nifty Oil & Gas stocks from Groww API → SQLite."""
    from utils.groww_api import fetch_historical_candles
    from utils.mongo_db import upsert_candles, log_fetch
    from utils.constants import (
        UPSTREAM_TICKERS, DOWNSTREAM_TICKERS, GAS_TICKERS,
    )
    import time

    # Fetch last 5 trading days to handle any gaps
    end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_dt = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d 09:00:00")

    segment_map = {
        "upstream": UPSTREAM_TICKERS,
        "downstream": DOWNSTREAM_TICKERS,
        "gas": GAS_TICKERS,
    }

    total_rows = 0
    errors = []

    for category, tickers in segment_map.items():
        for display_name, nse_symbol in tickers.items():
            try:
                candles = fetch_historical_candles(
                    trading_symbol=nse_symbol,
                    start_date=start_dt,
                    end_date=end_dt,
                    exchange="NSE",
                    interval_minutes=1440,
                )
                if candles:
                    upsert_candles(display_name, "groww", category, candles)
                    total_rows += len(candles)
                    print(f"✅ {display_name}: {len(candles)} candles")

                time.sleep(0.5)  # Rate limit

            except Exception as e:
                err = f"{display_name}: {e}"
                errors.append(err)
                print(f"❌ {err}")

    symbols_str = ", ".join(
        list(UPSTREAM_TICKERS.keys()) +
        list(DOWNSTREAM_TICKERS.keys()) +
        list(GAS_TICKERS.keys())
    )

    if errors:
        log_fetch("groww", symbols_str, "partial",
                  f"{total_rows} rows, {len(errors)} errors: {'; '.join(errors[:3])}")
    else:
        log_fetch("groww", symbols_str, "success", f"{total_rows} rows inserted")


def fetch_nifty50(**context):
    """Fetch Nifty 50 index data from Groww API → SQLite."""
    from utils.groww_api import fetch_nifty50 as _fetch_nifty
    from utils.mongo_db import upsert_candles, log_fetch

    end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_dt = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d 09:00:00")

    try:
        candles = _fetch_nifty(start_dt, end_dt)
        if candles:
            upsert_candles("Nifty 50", "groww", "index", candles)
            log_fetch("groww", "Nifty 50", "success", f"{len(candles)} candles")
            print(f"✅ Nifty 50: {len(candles)} candles")
        else:
            log_fetch("groww", "Nifty 50", "empty", "No candles returned")
            print("⚠️ Nifty 50: no candles")
    except Exception as e:
        log_fetch("groww", "Nifty 50", "error", str(e))
        print(f"❌ Nifty 50: {e}")


def fetch_crude_oil(**context):
    """Fetch WTI & Brent crude from Yahoo Finance → SQLite."""
    import yfinance as yf
    from utils.mongo_db import upsert_candles, log_fetch
    from utils.constants import CRUDE_YF_TICKERS

    end_dt = datetime.now().strftime("%Y-%m-%d")
    start_dt = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    for label, yf_ticker in CRUDE_YF_TICKERS.items():
        try:
            df = yf.download(yf_ticker, start=start_dt, end=end_dt,
                             progress=False, auto_adjust=True)
            if df is None or df.empty:
                log_fetch("yfinance", label, "empty", "No data returned")
                print(f"⚠️ {label}: no data")
                continue

            # Handle multi-level columns
            if hasattr(df.columns, 'levels'):
                df.columns = df.columns.get_level_values(0)

            candles = []
            for idx, row in df.iterrows():
                candles.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": float(row.get("Volume", 0)),
                })

            upsert_candles(label, "yfinance", "crude", candles)
            log_fetch("yfinance", label, "success", f"{len(candles)} candles")
            print(f"✅ {label}: {len(candles)} candles")

        except Exception as e:
            log_fetch("yfinance", label, "error", str(e))
            print(f"❌ {label}: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# DAG DEFINITION
# ══════════════════════════════════════════════════════════════════════════════

default_args = {
    "owner": "oil-gas-analysis",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="oil_gas_data_fetcher",
    default_args=default_args,
    description="Fetch Oil & Gas stock + crude oil data every 30 min from Groww API & Yahoo Finance",
    schedule_interval="*/30 9-16 * * 1-5",  # Every 30 min, Mon-Fri, 9am-4pm IST
    start_date=datetime(2026, 2, 15),
    catchup=False,
    tags=["oil-gas", "market-data", "groww"],
    doc_md="""
    ## Oil & Gas Data Fetcher DAG

    Fetches daily OHLCV data for:
    - **15 Nifty Oil & Gas ETF stocks** from Groww API
    - **Nifty 50 index** from Groww API
    - **WTI & Brent Crude** from Yahoo Finance

    Data is stored in MongoDB Atlas (cloud).
    The Streamlit Cloud app reads from MongoDB.
    """,
) as dag:

    task_stocks = PythonOperator(
        task_id="fetch_indian_stocks",
        python_callable=fetch_indian_stocks,
        doc_md="Fetch all 15 Oil & Gas stocks from Groww API",
    )

    task_nifty = PythonOperator(
        task_id="fetch_nifty50",
        python_callable=fetch_nifty50,
        doc_md="Fetch Nifty 50 index from Groww API",
    )

    task_crude = PythonOperator(
        task_id="fetch_crude_oil",
        python_callable=fetch_crude_oil,
        doc_md="Fetch WTI & Brent crude from Yahoo Finance",
    )

    # All three tasks run in parallel (no dependency between them)
    [task_stocks, task_nifty, task_crude]
