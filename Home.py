"""
Israel-Iran War Crude Commodity Tracker — Home Page
"""

import streamlit as st
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="Israel-Iran War Crude Commodity Tracker",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .block-container { padding-top: 1.5rem; max-width: 1200px; }

    .hero-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(220,53,69,0.12) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-card h1 {
        font-family: 'Inter', sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        background: linear-gradient(90deg, #ECEFF1, #90CAF9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-card p {
        color: #78909C;
        font-size: 1.1rem;
        line-height: 1.6;
        margin: 0;
    }

    .arch-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
    }
    .arch-card h4 {
        color: #90CAF9;
        margin: 0 0 0.8rem 0;
        font-size: 1rem;
    }
    .arch-card p, .arch-card li {
        color: #78909C;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .tech-badge {
        display: inline-block;
        background: rgba(102,187,106,0.12);
        color: #66BB6A;
        border: 1px solid rgba(102,187,106,0.2);
        border-radius: 6px;
        padding: 0.2rem 0.6rem;
        font-size: 0.8rem;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Israel-Iran War Crude Commodity Tracker")
    st.markdown("---")

    # Show last data refresh
    from utils.mongo_db import get_last_fetch_time
    last_fetch = get_last_fetch_time()
    if last_fetch:
        st.caption(f"Last data refresh: {last_fetch[:19]}")
    else:
        st.caption("No data yet. Run: python scripts/seed_war_data.py")

# ── Hero Card ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-card">
    <h1>Israel-Iran War Crude Commodity Tracker</h1>
    <p>
        Real-time and historical analysis of <b>Nifty Oil & Gas ETF constituents</b>
        against <b>WTI & Brent Crude Oil</b> benchmarks.<br>
        Built to study the impact of the <b>Israel-Iran War (June 2025)</b>
        on Indian oil & gas equities.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Architecture Overview ────────────────────────────────────────────────────
st.markdown("### How It Works")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="arch-card">
        <h4>Data Ingestion</h4>
        <p>
            An <b>Airflow DAG</b> runs every 30 min and fetches data from two sources:
        </p>
        <ul>
            <li><b>Groww API</b> — All 15 Indian oil & gas stocks (NSE)</li>
            <li><b>Yahoo Finance</b> — WTI & Brent crude oil benchmarks</li>
        </ul>
        <p style="margin-top:0.8rem;">
            <span class="tech-badge">Airflow 2.10</span>
            <span class="tech-badge">Groww API</span>
            <span class="tech-badge">yfinance</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="arch-card">
        <h4>Persistence Layer</h4>
        <p>
            All fetched data is stored in <b>MongoDB Atlas</b> (cloud):
        </p>
        <ul>
            <li><code>daily_prices</code> — OHLCV candles per symbol</li>
            <li><code>fetch_log</code> — Audit trail of every fetch</li>
        </ul>
        <p>
            MongoDB Atlas acts as the <b>single source of truth</b> between
            Airflow (writes locally) and Streamlit Cloud (reads remotely).
        </p>
        <p style="margin-top:0.8rem;">
            <span class="tech-badge">MongoDB Atlas</span>
            <span class="tech-badge">Pandas</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="arch-card">
        <h4>Visualization</h4>
        <p>
            This <b>Streamlit app</b> reads from SQLite and renders
            interactive Plotly charts:
        </p>
        <ul>
            <li>Sector averages vs Crude & Nifty 50</li>
            <li>Individual upstream / downstream stocks</li>
            <li>Single-stock deep-dive (dropdown)</li>
            <li>Performance leaderboard</li>
        </ul>
        <p style="margin-top:0.8rem;">
            <span class="tech-badge">Streamlit</span>
            <span class="tech-badge">Plotly</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── ETF Constituents ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### Nifty Oil & Gas ETF — 14 Constituents")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    **Upstream** _(Producers)_
    - ONGC
    - Oil India
    - Reliance Industries

    _Benefit from rising crude prices._
    """)

with c2:
    st.markdown("""
    **Downstream** _(Refiners)_
    - IOC
    - BPCL
    - HPCL
    - MRPL

    _Hurt by crude spikes — input cost rises._
    """)

with c3:
    st.markdown("""
    **Gas Distribution**
    - GAIL
    - Petronet LNG
    - IGL
    - MGL
    - Gujarat Gas
    - Adani Total Gas
    - GSPL
    """)

# ── Key Concepts ─────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("What does 'Indexed to 100' mean?", expanded=False):
    st.markdown("""
    All prices are **rebased** so Day 1 = **100**. Each subsequent value
    shows the percentage change from that starting point.

    **Formula:** `Indexed Value = (Current Price / Day 1 Price) × 100`

    - A value of **108** means the asset is **up 8%** from Day 1
    - A value of **95** means it's **down 5%** from Day 1

    This lets us compare assets with wildly different prices
    (e.g. Reliance at ₹1,400 vs MRPL at ₹140 vs WTI at $63) on the
    **same chart and same scale**.
    """)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style="color:#455A64; font-size:0.8rem; text-align:center;">
    Built with Streamlit • Data from Groww API & Yahoo Finance •
    Orchestrated by Apache Airflow • Stored in MongoDB Atlas
</p>
""", unsafe_allow_html=True)
