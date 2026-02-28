"""
SQLite persistence layer.
Stores daily OHLCV data fetched by Airflow (via Groww API / yfinance).
Streamlit reads from this DB.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "market_data.db")


def _ensure_db():
    """Create DB directory and tables if they don't exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_prices (
            symbol      TEXT    NOT NULL,
            source      TEXT    NOT NULL,   -- 'groww' or 'yfinance'
            category    TEXT,               -- 'upstream', 'downstream', 'gas', 'crude', 'index', 'other'
            date        TEXT    NOT NULL,
            open        REAL,
            high        REAL,
            low         REAL,
            close       REAL,
            volume      REAL,
            PRIMARY KEY (symbol, date)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fetch_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fetch_time  TEXT    NOT NULL,
            source      TEXT    NOT NULL,
            symbols     TEXT,
            status      TEXT,
            message     TEXT
        )
    """)

    conn.commit()
    conn.close()


def upsert_candles(symbol: str, source: str, category: str, candles: list[dict]):
    """
    Insert or replace daily candle rows.
    candles: list of dicts with keys: date, open, high, low, close, volume
    """
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for candle in candles:
        c.execute("""
            INSERT OR REPLACE INTO daily_prices
                (symbol, source, category, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol,
            source,
            category,
            candle["date"],
            candle.get("open"),
            candle.get("high"),
            candle.get("low"),
            candle["close"],
            candle.get("volume"),
        ))

    conn.commit()
    conn.close()


def log_fetch(source: str, symbols: str, status: str, message: str = ""):
    """Log a data fetch event."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO fetch_log (fetch_time, source, symbols, status, message)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), source, symbols, status, message))
    conn.commit()
    conn.close()


def get_prices(symbols: list[str] | None = None,
               category: str | None = None,
               start_date: str | None = None,
               end_date: str | None = None) -> pd.DataFrame:
    """
    Read daily close prices from SQLite.
    Returns a DataFrame with Date index and one column per symbol.
    """
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)

    query = "SELECT symbol, date, close FROM daily_prices WHERE 1=1"
    params = []

    if symbols:
        placeholders = ",".join("?" * len(symbols))
        query += f" AND symbol IN ({placeholders})"
        params.extend(symbols)

    if category:
        query += " AND category = ?"
        params.append(category)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if df.empty:
        return pd.DataFrame()

    # Pivot to wide format: Date × Symbol
    pivot = df.pivot_table(index="date", columns="symbol", values="close", aggfunc="last")
    pivot.index = pd.to_datetime(pivot.index)
    pivot.index.name = "Date"

    return pivot.dropna(how="all")


def get_last_fetch_time() -> str | None:
    """Get the timestamp of the most recent successful fetch."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT fetch_time FROM fetch_log WHERE status='success' ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_categories() -> dict:
    """Get mapping of symbol → category from the DB."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT DISTINCT symbol, category FROM daily_prices", conn)
    conn.close()
    return dict(zip(df["symbol"], df["category"]))
