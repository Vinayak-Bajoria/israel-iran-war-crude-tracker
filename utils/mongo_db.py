"""
MongoDB Atlas persistence layer.
- Airflow DAG (local) WRITES to MongoDB Atlas
- Streamlit app (cloud) READS from MongoDB Atlas

Collection: daily_prices
Document schema:
    { symbol, source, category, date, open, high, low, close, volume }

Collection: fetch_log
    { fetch_time, source, symbols, status, message }
"""

import os
from datetime import datetime
from pymongo import MongoClient, UpdateOne
import pandas as pd
import certifi

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

_client = None
_db = None

# Connection string priority:
# 1. Streamlit secrets  (when deployed on Streamlit Cloud)
# 2. Environment variable MONGO_URI  (for local / Airflow)
# 3. Hardcoded default (for development)

DEFAULT_URI = "REDACTED"
DB_NAME = "oil_gas_war"


def _get_uri():
    """Resolve MongoDB URI from secrets / env / default."""
    # Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "mongo" in st.secrets:
            return st.secrets["mongo"]["uri"]
    except Exception:
        pass
    # Env var
    uri = os.environ.get("MONGO_URI")
    if uri:
        return uri
    return DEFAULT_URI


def _get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(
            _get_uri(),
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        _db = _client[DB_NAME]
    return _db


# ---------------------------------------------------------------------------
# Write helpers  (used by Airflow DAG / seed script)
# ---------------------------------------------------------------------------

def upsert_candles(symbol: str, source: str, category: str, candles: list[dict]):
    """Upsert daily candle rows into MongoDB."""
    db = _get_db()
    coll = db["daily_prices"]

    ops = []
    for c in candles:
        filt = {"symbol": symbol, "date": c["date"]}
        doc = {
            "symbol": symbol,
            "source": source,
            "category": category,
            "date": c["date"],
            "open": c.get("open"),
            "high": c.get("high"),
            "low": c.get("low"),
            "close": c["close"],
            "volume": c.get("volume"),
        }
        ops.append(UpdateOne(filt, {"$set": doc}, upsert=True))

    if ops:
        coll.bulk_write(ops, ordered=False)


def log_fetch(source: str, symbols: str, status: str, message: str = ""):
    """Log a data-fetch event."""
    db = _get_db()
    db["fetch_log"].insert_one({
        "fetch_time": datetime.now().isoformat(),
        "source": source,
        "symbols": symbols,
        "status": status,
        "message": message,
    })


# ---------------------------------------------------------------------------
# Read helpers  (used by Streamlit app)
# ---------------------------------------------------------------------------

def get_prices(
    symbols: list[str] | None = None,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Read daily close prices from MongoDB.
    Returns DataFrame with Date index, one column per symbol.
    """
    db = _get_db()
    query: dict = {}

    if symbols:
        query["symbol"] = {"$in": symbols}
    if category:
        query["category"] = category
    if start_date or end_date:
        date_q: dict = {}
        if start_date:
            date_q["$gte"] = start_date
        if end_date:
            date_q["$lte"] = end_date
        query["date"] = date_q

    cursor = db["daily_prices"].find(query, {"_id": 0, "symbol": 1, "date": 1, "close": 1}).sort("date", 1)
    rows = list(cursor)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    pivot = df.pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
    pivot.index = pd.to_datetime(pivot.index)
    pivot.index.name = "Date"
    return pivot.dropna(how="all")


def get_last_fetch_time() -> str | None:
    """Most recent successful fetch timestamp."""
    db = _get_db()
    doc = db["fetch_log"].find_one(
        {"status": "success"},
        sort=[("fetch_time", -1)],
    )
    return doc["fetch_time"] if doc else None
