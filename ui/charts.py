"""Plotly charts for the RizzML app. One measure per axis; phase colours match the ML team's figures.

Every chart takes `dark` (the app follows the user's theme, the HTML report is light) and `t`, the
translator from i18n.py. Both palettes are the validated reference steps (dataviz palette.md).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

LIGHT = dict(oil="#2a78d6", water="#eb6834", gas="#1baf7a", ink="#232323", ink2="#555555", muted="#8a8a8a",
             grid="#e3e3e3", shade="rgba(0,119,166,0.10)", surface="#ffffff", template="plotly_white",
             cat=["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"])
DARK = dict(oil="#3987e5", water="#d95926", gas="#199e70", ink="#f5f5f5", ink2="#b3b3b3", muted="#7a7a7a",
            grid="#2e2e2e", shade="rgba(0,163,224,0.16)", surface="#121212", template="plotly_dark",
            cat=["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"])
PHASES = [("oil_rate_stbd", "Oil", "oil"), ("water_rate_stbd", "Water", "water"), ("gas_rate_mscfd", "Gas", "gas")]
SYMBOLS = ["circle", "square", "diamond", "triangle-up", "x", "cross", "triangle-down", "star"]


def _same(s):
    return s


def _pal(dark: bool) -> dict:
    return DARK if dark else LIGHT


def _style(fig, c, height=420, title=None, legend_y=-0.14, hover="x unified"):
    """Legend below the plot, so it never covers a title. Dark charts sit on the page background."""
    bg = "rgba(0,0,0,0)" if c is DARK else c["surface"]
    fig.update_layout(template=c["template"], height=height, title=title, paper_bgcolor=bg, plot_bgcolor=bg,
                      margin=dict(l=10, r=10, t=56 if title else 30, b=90),
                      font=dict(family="system-ui, sans-serif", size=13, color=c["ink2"]), hovermode=hover,
                      legend=dict(orientation="h", yanchor="top", y=legend_y, xanchor="left", x=0, title_text=""))
    fig.update_xaxes(gridcolor=c["grid"], linecolor=c["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=c["grid"], linecolor=c["grid"], zeroline=False)
    return fig


def sensors(hourly_w: pd.DataFrame, cols: list[str], labels: dict, events_w: pd.DataFrame, dark=True):
    """Small multiples, one sensor per panel (units differ), shut-ins shaded. `labels` arrive translated."""
    c = _pal(dark)
    fig = make_subplots(rows=len(cols), cols=1, shared_xaxes=True, vertical_spacing=0.09,
                        subplot_titles=[labels[k] for k in cols])
    for i, k in enumerate(cols, 1):
        fig.add_trace(go.Scatter(x=hourly_w.timestamp, y=hourly_w[k], mode="lines", name=labels[k],
                                 line=dict(width=1.6, color=c["oil"]), showlegend=False), row=i, col=1)
    for ev in events_w.itertuples(index=False):
        fig.add_vrect(x0=ev.start, x1=ev.end, fillcolor=c["shade"], line_width=0, layer="below")
    return _style(fig, c, height=max(260, 190 * len(cols)))


def rates(rates_w: pd.DataFrame, tests_w: pd.DataFrame | None, dark=True, t=_same):
    """Liquids and gas in separate panels (different units); measured tests as dots."""
    c = _pal(dark)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        subplot_titles=[t("Oil and water (stb/d)"), t("Gas (Mscf/d)")])
    when = pd.to_datetime(rates_w.timestamp)
    for col, name, key in PHASES:
        row = 2 if key == "gas" else 1
        fig.add_trace(go.Scatter(x=when, y=rates_w[col], mode="lines", name=t("{name}, daily estimate").format(name=t(name)),
                                 line=dict(width=2, color=c[key])), row=row, col=1)
        if tests_w is not None and len(tests_w):
            fig.add_trace(go.Scatter(x=tests_w.test_start, y=tests_w[col], mode="markers",
                                     name=t("{name}, measured test").format(name=t(name)),
                                     marker=dict(size=9, color=c[key], line=dict(width=2, color=c["surface"]))),
                          row=row, col=1)
    return _style(fig, c, height=600, legend_y=-0.08)


def history(plot: dict, dark=True, t=_same):
    c = _pal(dark)
    h = plot["history"]
    fig = go.Figure(go.Scatter(x=h.index, y=h.values, mode="lines", name=t("Downhole pressure"),
                               line=dict(width=1.6, color=c["ink"])))
    fig.add_vrect(x0=plot["start"], x1=plot["end"], fillcolor=c["shade"], line_width=0, layer="below",
                  annotation_text=t("shut-in"), annotation_position="top left")
    fig.update_yaxes(title=t("Downhole pressure (psia)"))
    return _style(fig, c, height=320, title=t("Pressure history"))


def loglog(plot: dict, dark=True, t=_same):
    c = _pal(dark)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot["tg"], y=plot["dpg"], mode="markers", name=t("Pressure change Δp"),
                             marker=dict(size=6, color=c["ink"])))
    ok = np.isfinite(plot["der"]) & (plot["der"] > 0)
    fig.add_trace(go.Scatter(x=plot["tg"][ok], y=plot["der"][ok], mode="markers", name=t("Bourdet derivative"),
                             marker=dict(size=6, color=c["oil"])))
    fig.add_trace(go.Scatter(x=plot["tg"], y=plot["mdp"], mode="lines", name=t("Model match Δp"),
                             line=dict(width=2, color=c["ink"], dash="dot")))
    mok = np.isfinite(plot["mder"]) & (plot["mder"] > 0)
    fig.add_trace(go.Scatter(x=plot["tg"][mok], y=plot["mder"][mok], mode="lines", name=t("Model match derivative"),
                             line=dict(width=2, color=c["oil"], dash="dot")))
    fig.add_vrect(x0=plot["t0"], x1=plot["t1"], fillcolor=c["shade"], line_width=0, layer="below",
                  annotation_text=t("radial flow window"), annotation_position="top left")
    fig.update_xaxes(type="log", title=t("Shut-in time Δt (h)"))
    fig.update_yaxes(type="log", title="psi")
    return _style(fig, c, height=420, title=t("Log-log diagnostic"), legend_y=-0.24)


def horner(plot: dict, p_star: float, dark=True, t=_same):
    c = _pal(dark)
    ratio = 10 ** plot["hx"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ratio, y=plot["p"], mode="markers", name=t("Build-up pressure"),
                             marker=dict(size=4, color=c["muted"])))
    fig.add_trace(go.Scatter(x=ratio[plot["win"]], y=plot["p"][plot["win"]], mode="markers", name=t("Radial flow points"),
                             marker=dict(size=5, color=c["oil"])))
    xs = np.array([1.0, ratio.max()])
    fig.add_trace(go.Scatter(x=xs, y=plot["c0"] + plot["c1"] * np.log10(xs), mode="lines",
                             name=t("Horner line: m = {m:.1f} psi/cycle, p* = {p:.0f} psia").format(m=-plot["c1"], p=p_star),
                             line=dict(width=2, color=c["ink"], dash="dash")))
    mr = (plot["tp"] + plot["tg"]) / plot["tg"]
    fig.add_trace(go.Scatter(x=mr, y=plot["pwf"] + plot["mdp"], mode="lines", name=t("Model match"),
                             line=dict(width=2, color=c["oil"], dash="dot")))
    fig.update_xaxes(type="log", autorange="reversed", title=t("Horner time (tp + Δt) / Δt"))
    fig.update_yaxes(title=t("Downhole pressure (psia)"))
    return _style(fig, c, height=420, title=t("Horner plot"), legend_y=-0.24)


def custom(df: pd.DataFrame, kind: str, y: str, labels: dict, slots: dict, *, x: str | None = None,
           time: str | None = None, agg: str = "mean", dark=True, t=_same):
    """Graph builder. kind: trend | cross | box | hist | bar. `slots` maps well -> fixed palette slot (0-7),
    so a well keeps its colour when others are added or removed. Past 8 wells there are not enough
    distinguishable colours, so trend and cross-plot switch to one panel per well."""
    c = _pal(dark)
    wells = sorted(df.well_name.unique())
    lab = {**labels, "well_name": t("Well")}
    colour = {w: c["cat"][slots[w]] for w in wells if w in slots}
    per_well = kind in ("trend", "cross") and len(wells) <= 8
    common = dict(labels=lab, category_orders={"well_name": wells})
    if per_well:
        common.update(color="well_name", color_discrete_map=colour)
    else:
        common.update(color_discrete_sequence=[c["oil"]])
    facet = {} if per_well or kind in ("box", "bar") or len(wells) == 1 else dict(facet_col="well_name", facet_col_wrap=3)
    rows = -(-len(wells) // 3) if facet else 1
    if kind == "trend":
        fig = px.line(df.sort_values(time), x=time, y=y, render_mode="webgl", **common, **facet)
        hover = "x unified"
    elif kind == "cross":
        fig = px.scatter(df, x=x, y=y, render_mode="webgl", **common, **facet,
                         **(dict(symbol="well_name", symbol_sequence=SYMBOLS) if per_well else {}))
        fig.update_traces(marker=dict(size=7, opacity=0.75))
        hover = "closest"
    elif kind == "box":
        fig = px.box(df, x="well_name", y=y, **common)
        hover = "closest"
    elif kind == "hist":
        fig = px.histogram(df, x=y, **common, **facet)
        fig.update_yaxes(title_text=t("Count"))
        fig.update_traces(marker_line=dict(width=1, color=c["surface"]))
        hover = "closest"
    else:   # bar: one statistic per well
        a = df.groupby("well_name", as_index=False, observed=True)[y].agg(agg)
        fig = px.bar(a, x="well_name", y=y, **common)
        fig.update_traces(marker_line=dict(width=0))
        hover = "closest"
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))   # facet titles: just the well
    return _style(fig, c, height=520 if rows == 1 else 230 * rows + 120, hover=hover)
