"""
Constants: Tickers, segments, color palettes, war event markers.
"""
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# TICKER MAPPINGS
# Keys = display labels, Values = NSE symbols (used in Groww API)
# ══════════════════════════════════════════════════════════════════════════════

UPSTREAM_TICKERS = {
    "ONGC": "ONGC",
    "Oil India": "OIL",
    "Reliance": "RELIANCE",
}

DOWNSTREAM_TICKERS = {
    "IOC": "IOC",
    "BPCL": "BPCL",
    "HPCL": "HINDPETRO",
    "MRPL": "MRPL",
}

GAS_TICKERS = {
    "GAIL": "GAIL",
    "Petronet LNG": "PETRONET",
    "IGL": "IGL",
    "MGL": "MGL",
    "Gujarat Gas": "GUJGASLTD",
    "Adani Total Gas": "ATGL",
    "GSPL": "GSPL",
}

OTHER_TICKERS = {}

# Merged map of all Oil & Gas stocks
ALL_OIL_GAS_TICKERS = {
    **UPSTREAM_TICKERS,
    **DOWNSTREAM_TICKERS,
    **GAS_TICKERS,
}

# Yahoo Finance tickers for crude oil (Groww doesn't list international crude)
CRUDE_YF_TICKERS = {
    "WTI Crude": "CL=F",
    "Brent Crude": "BZ=F",
}

# Nifty 50 (Groww symbol)
INDEX_TICKERS = {
    "Nifty 50": "NIFTY",
}

# ══════════════════════════════════════════════════════════════════════════════
# SEGMENT GROUPINGS
# ══════════════════════════════════════════════════════════════════════════════

SEGMENTS = {
    "Upstream": list(UPSTREAM_TICKERS.keys()),
    "Downstream": list(DOWNSTREAM_TICKERS.keys()),
    "Gas Distribution": list(GAS_TICKERS.keys()),
    "Others": list(OTHER_TICKERS.keys()),
}

# ══════════════════════════════════════════════════════════════════════════════
# WAR EVENTS
# ══════════════════════════════════════════════════════════════════════════════

WAR_START = datetime(2025, 6, 13)
WAR_END = datetime(2025, 6, 24)
WAR_PERIOD_START = "2025-06-01"  # data fetch start
WAR_PERIOD_END = "2025-07-02"    # data fetch end

WAR_EVENTS = [
    {"date": WAR_START, "label": "Israel strikes Iran", "color": "red"},
    {"date": WAR_END, "label": "Ceasefire announced", "color": "green"},
]

# ══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # Crude benchmarks — distinct warm tones
    "WTI Crude": "#FF4444",       # bright red
    "Brent Crude": "#FF8C00",     # dark orange (clearly different from WTI red)
    # Index
    "Nifty 50": "#AB47BC",        # purple
    # Upstream
    "ONGC": "#E65100",
    "Oil India": "#F57C00",
    "Reliance": "#FFB300",
    "Upstream Avg": "#FFD600",    # bright yellow — pops against dark bg
    # Downstream
    "IOC": "#1565C0",
    "BPCL": "#1E88E5",
    "HPCL": "#42A5F5",
    "MRPL": "#64B5F6",
    "Downstream Avg": "#29B6F6",  # light cyan-blue
    # Gas
    "GAIL": "#2E7D32",
    "Petronet LNG": "#388E3C",
    "IGL": "#43A047",
    "MGL": "#4CAF50",
    "Gujarat Gas": "#66BB6A",
    "Adani Total Gas": "#81C784",
    "GSPL": "#A5D6A7",
    "Gas Avg": "#00E676",         # bright green
}

FALLBACK_COLORS = [
    "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF",
    "#FF9F40", "#C9CBCF", "#7CB342", "#F06292", "#26A69A",
]


def get_color(name: str, idx: int = 0) -> str:
    """Get color for a ticker name, with fallback rotation."""
    return COLORS.get(name, FALLBACK_COLORS[idx % len(FALLBACK_COLORS)])
