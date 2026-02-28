"""
Page 1: Crude Commodity June 2025 Wartime Analysis
Clean layout: one chart per section, dropdown selection, full-width.
"""

import streamlit as st
import pandas as pd
import os, sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from utils.mongo_db import get_prices, get_last_fetch_time
from utils.constants import (
    UPSTREAM_TICKERS, DOWNSTREAM_TICKERS, GAS_TICKERS,
    WAR_START, WAR_END, WAR_PERIOD_START, WAR_PERIOD_END,
)
from utils.charts import (
    normalize_to_100, compute_segment_avg,
    chart_sector_vs_crude, chart_single_stock, chart_nifty_vs_crude,
)

st.set_page_config(page_title="Crude Commodity June 2025 Wartime Analysis", page_icon="", layout="wide")

# CSS
st.markdown("""
<style>
    .block-container { padding-top: 1rem; max-width: 1200px; }
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 0.6rem 0.8rem; border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.05); overflow: visible;
    }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; white-space: nowrap; overflow: visible; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; white-space: nowrap; overflow: visible; }
    [data-testid="stMetricDelta"] { font-size: 0.82rem !important; }
    .segment-hdr {
        background: linear-gradient(90deg, rgba(255,111,0,0.12), transparent);
        padding: 0.6rem 1.2rem; border-left: 3px solid #FF6F00;
        border-radius: 0 8px 8px 0; margin: 1.8rem 0 0.8rem 0;
    }
    .segment-hdr h3 { margin: 0; font-size: 1.1rem; }
    .segment-hdr p  { color: #78909C; margin: 0.2rem 0 0 0; font-size: 0.85rem; }
    .dn-hdr { border-left-color: #1565C0; background: linear-gradient(90deg, rgba(21,101,192,0.12), transparent); }
    .gas-hdr { border-left-color: #2E7D32; background: linear-gradient(90deg, rgba(46,125,50,0.12), transparent); }
    .oth-hdr { border-left-color: #6A1B9A; background: linear-gradient(90deg, rgba(106,27,154,0.12), transparent); }
    .stat-row { display: flex; gap: 1.5rem; margin: 0.4rem 0 0 0; font-size: 0.88rem; color: #90A4AE; }
    .stat-row span { color: #ECEFF1; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### Wartime Analysis")
    st.markdown("**Period:** Jun 2 - Jun 30, 2025")
    st.markdown("**Event:** Israel-Iran War")
    st.divider()
    last_fetch = get_last_fetch_time()
    if last_fetch:
        st.caption(f"Data: {last_fetch[:16]}")
    else:
        st.warning("No data in DB.")

# Header
st.markdown("## Crude Commodity June 2025 Wartime Analysis")
st.caption("14 Nifty Oil & Gas ETF constituents vs WTI & Brent Crude | Jun 2025 | Indexed to 100")

# Load data
@st.cache_data(ttl=300)
def load_war_data():
    crude   = get_prices(symbols=["WTI Crude", "Brent Crude"], start_date=WAR_PERIOD_START, end_date=WAR_PERIOD_END)
    nifty   = get_prices(symbols=["Nifty 50"], start_date=WAR_PERIOD_START, end_date=WAR_PERIOD_END)
    upstream   = get_prices(symbols=list(UPSTREAM_TICKERS.keys()), start_date=WAR_PERIOD_START, end_date=WAR_PERIOD_END)
    downstream = get_prices(symbols=list(DOWNSTREAM_TICKERS.keys()), start_date=WAR_PERIOD_START, end_date=WAR_PERIOD_END)
    gas        = get_prices(symbols=list(GAS_TICKERS.keys()), start_date=WAR_PERIOD_START, end_date=WAR_PERIOD_END)
    return crude, nifty, upstream, downstream, gas

crude, nifty, upstream, downstream, gas = load_war_data()

if crude.empty and upstream.empty:
    st.error("No data in DB. Run: python scripts/seed_war_data.py")
    st.stop()

# Full-period normalized data (for metric cards only)
crude_n      = normalize_to_100(crude)
nifty_n      = normalize_to_100(nifty)
upstream_avg   = compute_segment_avg(upstream, "Upstream Avg")
downstream_avg = compute_segment_avg(downstream, "Downstream Avg")
gas_avg        = compute_segment_avg(gas, "Gas Avg")


def _pret(s):
    s = s.dropna()
    return round(s.iloc[-1] - 100, 1) if len(s) >= 2 else 0.0


# Metric cards
st.divider()
m1, m2, m3, m4, m5 = st.columns(5)
wti_r = _pret(crude_n["WTI Crude"]) if "WTI Crude" in crude_n else 0
brent_r = _pret(crude_n["Brent Crude"]) if "Brent Crude" in crude_n else 0
up_r = _pret(upstream_avg)
dn_r = _pret(downstream_avg)
nifty_r = _pret(nifty_n.iloc[:, 0]) if not nifty_n.empty else 0
m1.metric("WTI Crude", f"{wti_r:+.1f}%", delta=f"{wti_r:+.1f}%")
m2.metric("Brent Crude", f"{brent_r:+.1f}%", delta=f"{brent_r:+.1f}%")
m3.metric("Upstream Avg", f"{up_r:+.1f}%", delta=f"{up_r:+.1f}%")
m4.metric("Downstream Avg", f"{dn_r:+.1f}%", delta=f"{dn_r:+.1f}%")
m5.metric("Nifty 50", f"{nifty_r:+.1f}%", delta=f"{nifty_r:+.1f}%")
st.divider()


# Helper for stats row
def _stats_row(name, norm_series):
    s = norm_series.dropna()
    if len(s) < 2:
        return
    total_r = round(s.iloc[-1] - 100, 1)
    peak_r = round(s.max() - 100, 1)
    trough_r = round(s.min() - 100, 1)
    st.markdown(f"""
    <div class="stat-row">
        Period return: <span>{total_r:+.1f}%</span> &nbsp;&middot;&nbsp;
        Peak: <span>{peak_r:+.1f}%</span> &nbsp;&middot;&nbsp;
        Trough: <span>{trough_r:+.1f}%</span> &nbsp;&middot;&nbsp;
        Range: <span>{peak_r - trough_r:.1f}pp</span>
    </div>
    """, unsafe_allow_html=True)


# ── Date bounds for all pickers ──────────────────────────────────────────────
_MIN_DATE = date(2025, 6, 1)
_MAX_DATE = date(2025, 7, 2)
_DEFAULT_START = date(2025, 6, 2)
_DEFAULT_END = date(2025, 6, 30)


def _date_picker(label, key):
    """Inline date-range picker clamped to the June war period."""
    c1, c2 = st.columns(2)
    with c1:
        d0 = st.date_input(f"{label} — Start", value=_DEFAULT_START,
                           min_value=_MIN_DATE, max_value=_MAX_DATE, key=f"{key}_s")
    with c2:
        d1 = st.date_input(f"{label} — End", value=_DEFAULT_END,
                           min_value=_MIN_DATE, max_value=_MAX_DATE, key=f"{key}_e")
    return d0, d1


def _slice(df, d0, d1):
    """Slice a DataFrame between two dates (inclusive) then re-normalise to 100."""
    if df.empty:
        return df
    mask = (df.index >= pd.Timestamp(d0)) & (df.index <= pd.Timestamp(d1))
    sliced = df.loc[mask]
    return sliced


def _slice_and_norm(df, d0, d1):
    """Slice then normalise so the first value in the window = 100."""
    sliced = _slice(df, d0, d1)
    return normalize_to_100(sliced)


def _slice_avg(raw_df, d0, d1, label):
    """Slice raw prices, then compute normalised segment average."""
    sliced = _slice(raw_df, d0, d1)
    return compute_segment_avg(sliced, label)


# SECTION 1: Sector Overview ──────────────────────────────────────────────────
st.markdown("""
<div class="segment-hdr">
    <h3>Sector Overview</h3>
    <p>Equal-weighted average of upstream, downstream & gas sectors vs crude benchmarks.</p>
</div>
""", unsafe_allow_html=True)

s1_d0, s1_d1 = _date_picker("Sector Overview", "sec")
s1_crude = _slice_and_norm(crude, s1_d0, s1_d1)
s1_nifty = _slice_and_norm(nifty, s1_d0, s1_d1)
s1_up_avg = _slice_avg(upstream, s1_d0, s1_d1, "Upstream Avg")
s1_dn_avg = _slice_avg(downstream, s1_d0, s1_d1, "Downstream Avg")
s1_gas_avg = _slice_avg(gas, s1_d0, s1_d1, "Gas Avg")

fig1 = chart_sector_vs_crude(s1_crude, s1_up_avg, s1_dn_avg, s1_nifty,
                             WAR_START, WAR_END, gas_avg=s1_gas_avg)
st.plotly_chart(fig1, use_container_width=True, key="c_sector")


# SECTION 2: Nifty 50 ────────────────────────────────────────────────────────
st.markdown("""
<div class="segment-hdr oth-hdr">
    <h3>Nifty 50 — Market Benchmark</h3>
    <p>How the broader Indian market moved relative to crude oil and oil & gas sectors during the war.</p>
</div>
""", unsafe_allow_html=True)

n_d0, n_d1 = _date_picker("Nifty 50", "nifty")
n_crude = _slice_and_norm(crude, n_d0, n_d1)
n_nifty = _slice_and_norm(nifty, n_d0, n_d1)
n_up_avg = _slice_avg(upstream, n_d0, n_d1, "Upstream Avg")
n_dn_avg = _slice_avg(downstream, n_d0, n_d1, "Downstream Avg")
n_gas_avg = _slice_avg(gas, n_d0, n_d1, "Gas Avg")

fig_nifty = chart_nifty_vs_crude(n_crude, n_nifty, WAR_START, WAR_END,
                                  upstream_avg=n_up_avg, downstream_avg=n_dn_avg,
                                  gas_avg=n_gas_avg)
st.plotly_chart(fig_nifty, use_container_width=True, key="c_nifty")
if not n_nifty.empty:
    _stats_row("Nifty 50", n_nifty.iloc[:, 0])


# SECTION 3: Upstream ─────────────────────────────────────────────────────────
st.markdown("""
<div class="segment-hdr">
    <h3>Upstream — Oil Producers</h3>
    <p>Producers benefit from rising crude — they sell oil at higher prices.</p>
</div>
""", unsafe_allow_html=True)

up_choice = st.selectbox("Select an upstream company", list(UPSTREAM_TICKERS.keys()), key="sel_up")
u_d0, u_d1 = _date_picker("Upstream", "up")
u_crude = _slice_and_norm(crude, u_d0, u_d1)
u_upstream_n = _slice_and_norm(upstream, u_d0, u_d1)
u_up_avg = _slice_avg(upstream, u_d0, u_d1, "Upstream Avg")
if up_choice and up_choice in u_upstream_n.columns:
    fig_up = chart_single_stock(u_crude, u_upstream_n[up_choice], up_choice,
                                WAR_START, WAR_END, segment_avg=u_up_avg)
    st.plotly_chart(fig_up, use_container_width=True, key="c_up")
    _stats_row(up_choice, u_upstream_n[up_choice])


# SECTION 4: Downstream ───────────────────────────────────────────────────────
st.markdown("""
<div class="segment-hdr dn-hdr">
    <h3>Downstream — Refiners & Marketers</h3>
    <p>Refiners get squeezed when crude spikes — input cost rises, regulated fuel prices lag.</p>
</div>
""", unsafe_allow_html=True)

dn_choice = st.selectbox("Select a downstream company", list(DOWNSTREAM_TICKERS.keys()), key="sel_dn")
d_d0, d_d1 = _date_picker("Downstream", "dn")
d_crude = _slice_and_norm(crude, d_d0, d_d1)
d_downstream_n = _slice_and_norm(downstream, d_d0, d_d1)
d_dn_avg = _slice_avg(downstream, d_d0, d_d1, "Downstream Avg")
if dn_choice and dn_choice in d_downstream_n.columns:
    fig_dn = chart_single_stock(d_crude, d_downstream_n[dn_choice], dn_choice,
                                WAR_START, WAR_END, segment_avg=d_dn_avg)
    st.plotly_chart(fig_dn, use_container_width=True, key="c_dn")
    _stats_row(dn_choice, d_downstream_n[dn_choice])


# SECTION 5: Gas Distribution ─────────────────────────────────────────────────
st.markdown("""
<div class="segment-hdr gas-hdr">
    <h3>Gas Distribution</h3>
    <p>City gas distributors and pipeline companies.</p>
</div>
""", unsafe_allow_html=True)

gas_choice = st.selectbox("Select a gas company", list(GAS_TICKERS.keys()), key="sel_gas")
g_d0, g_d1 = _date_picker("Gas", "gas")
g_crude = _slice_and_norm(crude, g_d0, g_d1)
g_gas_n = _slice_and_norm(gas, g_d0, g_d1)
g_gas_avg = _slice_avg(gas, g_d0, g_d1, "Gas Avg")
if gas_choice and gas_choice in g_gas_n.columns:
    fig_gas = chart_single_stock(g_crude, g_gas_n[gas_choice], gas_choice,
                                 WAR_START, WAR_END, segment_avg=g_gas_avg)
    st.plotly_chart(fig_gas, use_container_width=True, key="c_gas")
    _stats_row(gas_choice, g_gas_n[gas_choice])


# Footer
st.divider()
st.caption("Data: Groww API (stocks) | Yahoo Finance (crude) | MongoDB Atlas | Airflow")
