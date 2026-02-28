"""
Plotly chart builders for the Oil & Gas War Analysis app.
Clean, full-width charts with plotly_dark theme.
"""

import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from utils.constants import get_color


def _base_layout(title, yaxis_title="Indexed Price (Base = 100)"):
    return dict(
        title=dict(text=title, font=dict(size=16, color="#ECEFF1"), x=0.5, xanchor="center"),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color="#B0BEC5", size=13),
        xaxis=dict(
            title="", gridcolor="rgba(255,255,255,0.06)",
            showgrid=True, tickformat="%b %d", zeroline=False, tickfont=dict(size=11),
            dtick=86400000,  # one tick per day (ms)
            tickangle=-45,
        ),
        yaxis=dict(
            title=yaxis_title, gridcolor="rgba(255,255,255,0.06)",
            showgrid=True, zeroline=False, tickfont=dict(size=12), title_font=dict(size=13),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
            font=dict(size=12), bgcolor="rgba(0,0,0,0)", borderwidth=0, itemsizing="constant",
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(30,30,50,0.95)", font_size=13, namelength=-1),
        height=520,
        margin=dict(l=55, r=30, t=85, b=70),
    )


def _add_war_zone(fig, war_start, war_end):
    ws = war_start.strftime("%Y-%m-%d") if isinstance(war_start, datetime) else str(war_start)
    we = war_end.strftime("%Y-%m-%d") if isinstance(war_end, datetime) else str(war_end)
    fig.add_shape(type="rect", x0=ws, x1=we, y0=0, y1=1, yref="paper",
                  fillcolor="rgba(244,67,54,0.06)", line_width=0)
    fig.add_shape(type="line", x0=ws, x1=ws, y0=0, y1=1, yref="paper",
                  line=dict(color="#EF5350", width=1.5, dash="dash"))
    fig.add_annotation(x=ws, y=-0.12, yref="paper", text="War begins",
                       showarrow=False, font=dict(size=10, color="#EF5350"))
    fig.add_shape(type="line", x0=we, x1=we, y0=0, y1=1, yref="paper",
                  line=dict(color="#66BB6A", width=1.5, dash="dash"))
    fig.add_annotation(x=we, y=-0.12, yref="paper", text="Ceasefire",
                       showarrow=False, font=dict(size=10, color="#66BB6A"))
    fig.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,0.12)", line_width=1)


def _hex_to_rgba(hex_color, alpha=0.1):
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return f"rgba(255,255,255,{alpha})"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def chart_sector_vs_crude(crude_n, upstream_avg, downstream_avg, nifty_n,
                          war_start, war_end, gas_avg=None):
    fig = go.Figure()
    crude_dashes = ["dash", "dot"]
    for i, col in enumerate(crude_n.columns):
        fig.add_trace(go.Scatter(
            x=crude_n.index, y=crude_n[col], name=col, mode="lines+markers",
            line=dict(color=get_color(col), width=2.5, dash=crude_dashes[i % 2]),
            marker=dict(size=4, symbol="diamond" if i == 0 else "square"),
            hovertemplate="%{y:.1f}<extra></extra>",
        ))
    if not nifty_n.empty:
        for col in nifty_n.columns:
            fig.add_trace(go.Scatter(
                x=nifty_n.index, y=nifty_n[col], name=col, mode="lines+markers",
                line=dict(color=get_color(col), width=2, dash="dashdot"),
                marker=dict(size=3, symbol="circle"),
                hovertemplate="%{y:.1f}<extra></extra>",
            ))
    traces = [(upstream_avg, "Upstream Avg"), (downstream_avg, "Downstream Avg")]
    if gas_avg is not None:
        traces.append((gas_avg, "Gas Avg"))
    for series, name in traces:
        c = get_color(name)
        fig.add_trace(go.Scatter(
            x=series.index, y=series, name=name, mode="lines+markers",
            line=dict(color=c, width=3),
            marker=dict(size=5),
            hovertemplate="%{y:.1f}<extra></extra>",
        ))
    _add_war_zone(fig, war_start, war_end)
    fig.update_layout(**_base_layout("Sector Averages vs Crude Oil & Nifty 50"))
    return fig


def chart_single_stock(crude_n, stock_series, stock_name, war_start, war_end,
                       segment_avg=None):
    fig = go.Figure()
    for col in crude_n.columns:
        fig.add_trace(go.Scatter(
            x=crude_n.index, y=crude_n[col], name=col, mode="lines+markers",
            line=dict(color=get_color(col), width=2, dash="dash"),
            marker=dict(size=3),
            hovertemplate="%{y:.1f}<extra></extra>",
        ))
    if segment_avg is not None:
        fig.add_trace(go.Scatter(
            x=segment_avg.index, y=segment_avg, name=segment_avg.name, mode="lines",
            line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dot"),
            hovertemplate="%{y:.1f}<extra></extra>",
        ))
    c = get_color(stock_name)
    fig.add_trace(go.Scatter(
        x=stock_series.index, y=stock_series, name=stock_name,
        mode="lines+markers",
        line=dict(color=c, width=3),
        marker=dict(size=5, color=c),
        hovertemplate="%{y:.1f}<extra></extra>",
        fill="tonexty" if segment_avg is not None else None,
        fillcolor=_hex_to_rgba(c, 0.05),
    ))
    _add_war_zone(fig, war_start, war_end)
    fig.update_layout(**_base_layout(f"{stock_name} vs WTI & Brent Crude"))
    return fig


def chart_nifty_vs_crude(crude_n, nifty_n, war_start, war_end,
                         upstream_avg=None, downstream_avg=None, gas_avg=None):
    """Chart Nifty 50 against crude benchmarks and optional sector averages."""
    fig = go.Figure()
    crude_dashes = ["dash", "dot"]
    for i, col in enumerate(crude_n.columns):
        fig.add_trace(go.Scatter(
            x=crude_n.index, y=crude_n[col], name=col, mode="lines+markers",
            line=dict(color=get_color(col), width=2.5, dash=crude_dashes[i % 2]),
            marker=dict(size=4, symbol="diamond" if i == 0 else "square"),
            hovertemplate="%{y:.1f}<extra></extra>",
        ))
    if not nifty_n.empty:
        for col in nifty_n.columns:
            fig.add_trace(go.Scatter(
                x=nifty_n.index, y=nifty_n[col], name=col, mode="lines+markers",
                line=dict(color=get_color(col), width=3),
                marker=dict(size=6, symbol="circle"),
                hovertemplate="%{y:.1f}<extra></extra>",
            ))
    avgs = [(upstream_avg, "Upstream Avg"), (downstream_avg, "Downstream Avg"), (gas_avg, "Gas Avg")]
    for series, name in avgs:
        if series is not None:
            c = get_color(name)
            fig.add_trace(go.Scatter(
                x=series.index, y=series, name=name, mode="lines",
                line=dict(color=c, width=1.5, dash="dot"),
                opacity=0.6,
                hovertemplate="%{y:.1f}<extra></extra>",
            ))
    _add_war_zone(fig, war_start, war_end)
    fig.update_layout(**_base_layout("Nifty 50 vs Crude Oil & Sector Averages"))
    return fig


def normalize_to_100(df):
    if df.empty:
        return df
    first = df.iloc[0].replace(0, float("nan"))
    return (df / first) * 100


def compute_segment_avg(df, label="Avg"):
    return normalize_to_100(df).mean(axis=1).rename(label)
