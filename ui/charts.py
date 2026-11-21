"""Plotly charts for the RizzML app. One measure per axis; phase colours match the ML team's figures."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

OIL, WATER, GAS = "#2a78d6", "#eb6834", "#1baf7a"   # ml/src/viz.py, validated palette
INK, INK2, MUTED, GRID, SHADE = "#0b0b0b", "#52514e", "#8a8982", "#e4e3df", "rgba(42,120,214,0.10)"
PHASES = [("oil_rate_stbd", "Oil", OIL, "stb/d"), ("water_rate_stbd", "Water", WATER, "stb/d"),
          ("gas_rate_mscfd", "Gas", GAS, "Mscf/d")]


def _style(fig, height=420, title=None, legend_y=-0.14):
    """Legend below the plot, so it never covers a title."""
    fig.update_layout(template="plotly_white", height=height, title=title, margin=dict(l=10, r=10, t=56 if title else 30, b=90),
                      font=dict(family="system-ui, sans-serif", size=13, color=INK2), hovermode="x unified",
                      legend=dict(orientation="h", yanchor="top", y=legend_y, xanchor="left", x=0))
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, zeroline=False)
    return fig


def sensors(hourly_w: pd.DataFrame, cols: list[str], labels: dict, events_w: pd.DataFrame):
    """Small multiples, one sensor per panel (units differ), shut-ins shaded."""
    fig = make_subplots(rows=len(cols), cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        subplot_titles=[labels[c] for c in cols])
    for i, c in enumerate(cols, 1):
        fig.add_trace(go.Scatter(x=hourly_w.timestamp, y=hourly_w[c], mode="lines", name=labels[c],
                                 line=dict(width=1.6, color=OIL), showlegend=False), row=i, col=1)
    for ev in events_w.itertuples(index=False):
        fig.add_vrect(x0=ev.start, x1=ev.end, fillcolor=SHADE, line_width=0, layer="below")
    return _style(fig, height=max(260, 190 * len(cols)))


def rates(rates_w: pd.DataFrame, tests_w: pd.DataFrame | None):
    """Liquids and gas in separate panels (different units); measured tests as dots."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=["Oil and water (stb/d)", "Gas (Mscf/d)"])
    t = pd.to_datetime(rates_w.timestamp)
    for col, name, colour, _ in PHASES:
        row = 2 if col.startswith("gas") else 1
        fig.add_trace(go.Scatter(x=t, y=rates_w[col], mode="lines", name=f"{name}, daily estimate",
                                 line=dict(width=2, color=colour)), row=row, col=1)
        if tests_w is not None and len(tests_w):
            fig.add_trace(go.Scatter(x=tests_w.test_start, y=tests_w[col], mode="markers", name=f"{name}, measured test",
                                     marker=dict(size=9, color=colour, line=dict(width=2, color="white"))), row=row, col=1)
    return _style(fig, height=600, legend_y=-0.08)


def history(plot: dict):
    h = plot["history"]
    fig = go.Figure(go.Scatter(x=h.index, y=h.values, mode="lines", name="Downhole pressure", line=dict(width=1.6, color=INK)))
    fig.add_vrect(x0=plot["start"], x1=plot["end"], fillcolor=SHADE, line_width=0, layer="below",
                  annotation_text="shut-in", annotation_position="top left")
    fig.update_yaxes(title="Downhole pressure (psia)")
    return _style(fig, height=320, title="Pressure history")


def loglog(plot: dict):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot["tg"], y=plot["dpg"], mode="markers", name="Pressure change Δp",
                             marker=dict(size=6, color=INK)))
    ok = np.isfinite(plot["der"]) & (plot["der"] > 0)
    fig.add_trace(go.Scatter(x=plot["tg"][ok], y=plot["der"][ok], mode="markers", name="Bourdet derivative",
                             marker=dict(size=6, color=OIL)))
    fig.add_vrect(x0=plot["t0"], x1=plot["t1"], fillcolor=SHADE, line_width=0, layer="below",
                  annotation_text="radial flow window", annotation_position="top left")
    fig.update_xaxes(type="log", title="Shut-in time Δt (h)")
    fig.update_yaxes(type="log", title="psi")
    return _style(fig, height=420, title="Log-log diagnostic", legend_y=-0.24)


def horner(plot: dict, slope: float, p_star: float):
    ratio = 10 ** plot["hx"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ratio, y=plot["p"], mode="markers", name="Build-up pressure",
                             marker=dict(size=4, color=MUTED)))
    fig.add_trace(go.Scatter(x=ratio[plot["win"]], y=plot["p"][plot["win"]], mode="markers", name="Radial flow points",
                             marker=dict(size=5, color=OIL)))
    xs = np.array([1.0, ratio.max()])
    fig.add_trace(go.Scatter(x=xs, y=plot["c0"] + plot["c1"] * np.log10(xs), mode="lines",
                             name=f"Straight line: m = {slope:.1f} psi/cycle, p* = {p_star:.0f} psia",
                             line=dict(width=2, color=INK, dash="dash")))
    fig.update_xaxes(type="log", autorange="reversed", title="Horner time (tp + Δt) / Δt")
    fig.update_yaxes(title="Downhole pressure (psia)")
    return _style(fig, height=420, title="Horner plot", legend_y=-0.24)
