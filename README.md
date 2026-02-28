# Israel-Iran War Crude Commodity Tracker

**Real-time and historical analysis of Nifty Oil & Gas ETF constituents against WTI & Brent Crude Oil benchmarks and the Nifty 50 index.**

Built to study the impact of the **Israel-Iran War (June 2025)** on Indian oil & gas equities, with ongoing live tracking via Airflow.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     DATA INGESTION LAYER                      │
│                                                               │
│   ┌─────────────┐              ┌──────────────┐              │
│   │  Groww API   │              │ Yahoo Finance │              │
│   │  14 O&G stks │              │  WTI & Brent  │              │
│   │  + Nifty 50  │              │  Crude Oil    │              │
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
                       │ UPSERT
                       ▼
              ┌─────────────────┐
              │  MongoDB Atlas  │
              │    (cloud)      │
              │                 │
              │  Collections:   │
              │  - daily_prices │
              │  - fetch_log    │
              └────────┬────────┘
                       │ READ
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                         │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐   │
│   │          Streamlit Cloud (Home.py)                    │   │
│   │                                                      │   │
│   │  Pages:                                              │   │
│   │  ├── Home              → Overview & architecture     │   │
│   │  ├── Wartime Analysis  → Jun 2025 Israel-Iran war    │   │
│   │  └── Live Tracker      → Real-time from Feb 2026    │   │
│   │                                                      │   │
│   │  Charts (Plotly):                                    │   │
│   │  - Sector averages vs Crude & Nifty 50               │   │
│   │  - Nifty 50 benchmark analysis                       │   │
│   │  - Upstream / Downstream / Gas deep-dives            │   │
│   │  - Per-section date range filtering                  │   │
│   └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
oil-gas-war/
├── Home.py                         # Streamlit entry point (Home page)
├── pages/
│   ├── 1_Wartime_Analysis.py       # Historical Jun 2025 war analysis
│   └── 2_Live_Tracker.py           # Real-time tracker (coming soon)
├── utils/
│   ├── __init__.py
│   ├── constants.py                # Tickers, segments, colors, war events
│   ├── mongo_db.py                 # MongoDB Atlas CRUD layer
│   ├── db.py                       # Legacy SQLite layer (unused)
│   ├── groww_api.py                # Groww REST API wrapper
│   └── charts.py                   # Plotly chart builders
├── scripts/
│   └── seed_war_data.py            # One-time: seed Jun 2025 data
├── dags/
│   └── oil_gas_fetcher_dag.py      # Airflow DAG
├── .streamlit/
│   └── config.toml                 # Theme config
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure MongoDB URI

Create `.streamlit/secrets.toml` (git-ignored):

```toml
[mongo]
uri = "mongodb+srv://USER:PASS@cluster.mongodb.net/?appName=Cluster0"
```

Or set the environment variable:

```bash
export MONGO_URI="mongodb+srv://USER:PASS@cluster.mongodb.net/?appName=Cluster0"
```

### 3. Seed historical war data (June 2025)

```bash
python scripts/seed_war_data.py
```

### 4. Run the Streamlit app

```bash
streamlit run Home.py --server.port 8502
```

### 5. (Optional) Set up Airflow DAG for live data

```bash
ln -sf $(pwd)/dags/oil_gas_fetcher_dag.py ~/airflow/dags/
airflow scheduler -D && airflow webserver -D
```

---

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select the repo, branch `main`, main file `Home.py`
4. Under **Advanced Settings > Secrets**, add your `[mongo] uri`
5. Ensure MongoDB Atlas Network Access allows `0.0.0.0/0`

---

## Data Sources

| Data | Source | Method |
|------|--------|--------|
| 14 Indian O&G stocks (NSE) | Groww API | Airflow DAG (30 min) |
| Nifty 50 Index | Groww API | Airflow DAG (30 min) |
| WTI Crude (CL=F) | Yahoo Finance | Airflow DAG (30 min) |
| Brent Crude (BZ=F) | Yahoo Finance | Airflow DAG (30 min) |

---

## Tracked Stocks (14 Nifty Oil & Gas ETF Constituents)

| Segment | Stocks |
|---------|--------|
| **Upstream** (Producers) | ONGC, Oil India, Reliance Industries |
| **Downstream** (Refiners) | IOC, BPCL, HPCL, MRPL |
| **Gas Distribution** | GAIL, Petronet LNG, IGL, MGL, Gujarat Gas, Adani Total Gas, GSPL |

**Benchmark:** Nifty 50 Index

---

## Key Concepts

- **Indexed to 100** — All prices rebased so Day 1 = 100. A value of 108 means +8% from start.
- **Upstream vs Downstream** — When crude spikes, upstream producers benefit while downstream refiners get margin-squeezed.
- **War Period** — Jun 13 (Israel strikes Iran) to Jun 24 (ceasefire). WTI crude spiked ~17%.
- **Date Range Filtering** — Each section has its own date picker to zoom into specific periods within June 2025.

---

## Pipeline Flow

1. **Airflow DAG** triggers every 30 minutes
2. **Task 1**: Fetches daily candles for 14 stocks + Nifty 50 via Groww API → upserts into MongoDB Atlas
3. **Task 2**: Fetches WTI & Brent via Yahoo Finance → upserts into MongoDB Atlas
4. **Task 3**: Logs the fetch timestamp into `fetch_log` collection
5. **Streamlit** reads from MongoDB Atlas on page load (cached 5 min)

MongoDB Atlas serves as the **single source of truth** between the local Airflow pipeline and the cloud-hosted Streamlit app.
