"""
Page 2: Live Tracker — Real-time analysis starting Feb 15, 2026.
Placeholder page — will be activated once Airflow DAG starts populating live data.
"""

import streamlit as st
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

st.set_page_config(page_title="Live Tracker", page_icon="", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 1200px; }
    .coming-soon {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 3rem;
        text-align: center;
        margin: 2rem 0;
    }
    .coming-soon h1 { font-size: 3rem; margin: 0; }
    .coming-soon h2 {
        color: #90CAF9;
        margin: 0.5rem 0 1rem 0;
        font-weight: 500;
    }
    .coming-soon p { color: #78909C; font-size: 1rem; line-height: 1.7; }
    .step-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Live Tracker")
    st.markdown("**Start Date:** Feb 15, 2026")
    st.markdown("**Status:** Coming soon")

st.markdown("""
<div class="coming-soon">
    <h1>&nbsp;</h1>
    <h2>Live Tracker — Coming Soon</h2>
    <p>
        This page will provide <b>real-time analysis</b> of Oil & Gas stocks<br>
        starting from <b>February 15, 2026</b>, refreshed every 30 minutes via Airflow.<br><br>
        The same charts, comparisons, and deep-dives from the Wartime Analysis page,<br>
        but tracking <b>live market movements</b>.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Check if any live data exists ────────────────────────────────────────────
from utils.mongo_db import get_prices

live_data = get_prices(start_date="2026-02-15")
if not live_data.empty:
    st.success(f"Live data found: {len(live_data)} rows from {live_data.index.min().date()} "
               f"to {live_data.index.max().date()}")
    st.dataframe(live_data.tail(10), use_container_width=True)
else:
    st.info("No live data yet. Data will appear here once the pipeline is active.")
