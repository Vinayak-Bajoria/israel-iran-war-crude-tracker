# ⛽ Oil & Gas War Analysis

**Real-time and historical comparison of Nifty Oil & Gas ETF constituents against WTI & Brent Crude Oil benchmarks.**

Built to analyze the impact of the **Iran-Israel War (June 2025)** on Indian oil & gas equities, and provide ongoing live tracking.

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     DATA INGESTION LAYER                      │
│                                                               │
│   ┌─────────────┐              ┌──────────────┐              │
│   │  Groww API   │              │ Yahoo Finance │              │
│   │  (MCP-style) │              │  (WTI/Brent)  │              │
│   │  Indian Stks │              │  Crude Oil    │              │
│   └──────┬──────┘              └──────┬───────┘              │
│          │                            │                       │
│          ▼                            ▼                       │
│   ┌─────────────────────────────────────────┐                │
│   │       Airflow DAG (every 30 min)        │                │
│   │  PythonOperator → groww_api.py wrapper  │                │
│   │  PythonOperator → yfinance fetch        │                │
│   └──────────────────┬──────────────────────┘                │
│                      │                                        │
└──────────────────────┼────────────────────────────────────────┘
                       │ INSERT/UPSERT
                       ▼
              ┌─────────────────┐
              │   SQLite DB     │
              │  market_data.db │
              │                 │
              │  Tables:        │
              │  • daily_prices │
              │  • fetch_log    │
              └────────┬────────┘
                       │ READ
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                         │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐   │
│   │              Streamlit App (port 8502)                │   │
│   │                                                      │   │
│   │  Sidebar:                                            │   │
│   │  ├── 🏠 Home        → Overview & architecture        │   │
│   │  ├── ⛽ War Analysis → Jun 2025 Iran-Israel period   │   │
│   │  └── 📡 Live Tracker→ Real-time from Feb 15, 2026   │   │
│   │                                                      │   │
│   │  Charts (Plotly):                                    │   │
│   │  • Sector avgs vs Crude & Nifty50                    │   │
│   │  • Upstream individual vs Crude                      │   │
│   │  • Downstream individual vs Crude                    │   │
│   │  • Single stock deep-dive (dropdown)                 │   │
│   │  • Performance leaderboard (bar chart)               │   │
│   └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
oil-gas-war/
├── README.md
├── requirements.txt
├── app.py                          # Streamlit entry point (Home page)
├── pages/
│   ├── 1_⛽_War_Analysis.py        # Historical Jun 2025 analysis
│   └── 2_📡_Live_Tracker.py        # Real-time tracker (Feb 15+)
├── utils/
│   ├── __init__.py
│   ├── constants.py                # Tickers, segments, colors, events
│   ├── db.py                       # SQLite CRUD layer
│   ├── groww_api.py                # Groww REST API wrapper (mirrors MCP)
│   └── charts.py                   # Plotly chart builders
├── scripts/
│   └── seed_war_data.py            # One-time: seed Jun 2025 data
├── dags/
│   └── oil_gas_fetcher_dag.py      # Airflow DAG (symlink to ~/airflow/dags/)
└── data/
    └── market_data.db              # SQLite DB (auto-created)
```

---

## 🔧 Setup

### 1. Install dependencies

```bash
cd oil-gas-war
pip install -r requirements.txt
```

### 2. Seed historical war data (June 2025)

```bash
python scripts/seed_war_data.py
```

This populates `data/market_data.db` with daily close prices from Groww API.

### 3. Set up Airflow DAG

```bash
# Symlink the DAG into Airflow's dags folder
ln -sf $(pwd)/dags/oil_gas_fetcher_dag.py ~/airflow/dags/oil_gas_fetcher_dag.py
```

### 4. Run the Streamlit app

```bash
streamlit run app.py --server.port 8502
```

---

## 📊 Data Sources

| Data | Source | Frequency |
|------|--------|-----------|
| Indian Stocks (NSE) | **Groww API** (same endpoints as Groww MCP) | Via Airflow DAG (30 min) |
| WTI Crude (CL=F) | **Yahoo Finance** | Via Airflow DAG (30 min) |
| Brent Crude (BZ=F) | **Yahoo Finance** | Via Airflow DAG (30 min) |
| Nifty 50 Index | **Groww API** | Via Airflow DAG (30 min) |

---

## ⛽ Nifty Oil & Gas ETF Constituents

### Upstream (Oil Producers)
ONGC, Oil India, Reliance Industries

### Downstream (Refiners & Marketers)
IOC, BPCL, HPCL (Hindustan Petroleum), MRPL

### Gas Distribution
GAIL, Petronet LNG, IGL, MGL, Gujarat Gas, Adani Total Gas, GSPL

### Others
Castrol India

---

## 🔑 Key Concepts

- **Indexed to 100**: All prices rebased so Day 1 = 100. A value of 108 means +8% from start.
- **Upstream vs Downstream**: When crude spikes, upstream (producers) benefit; downstream (refiners) get margin-squeezed.
- **War Period**: Jun 13 (Israel strikes Iran) → Jun 24 (ceasefire). Crude spiked ~17% (WTI).

---

## 📡 How the Pipeline Works

1. **Airflow DAG** triggers every 30 minutes
2. **Task 1**: Calls Groww API for all 15 Indian stock daily candles → inserts into SQLite
3. **Task 2**: Calls Yahoo Finance for WTI & Brent daily quotes → inserts into SQLite
4. **Task 3**: Logs the fetch timestamp into `fetch_log` table
5. **Streamlit** reads from SQLite on every page load (cached for 5 min)

The SQLite DB acts as the **single source of truth** between Airflow and Streamlit.
