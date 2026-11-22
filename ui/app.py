"""RizzML: daily well rates and well-test analysis from the sensors SOCAR already has.

Run from this folder, so .streamlit/config.toml (theme, 1 GB upload limit) applies:
    cd ui && streamlit run app.py
On a shared server add `--server.address 0.0.0.0`; engineers open http://<server>:8501 in a browser.
"""
from __future__ import annotations

import base64
import hashlib
import html
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import charts
import i18n
import pipeline as P
import store

st.set_page_config(page_title="RizzML", layout="wide", initial_sidebar_state="expanded")
HERE = Path(__file__).parent
SAMPLE = Path(os.environ.get("RIZZML_DATA_DIR", P.ROOT / "data"))
WIDE = dict(width="stretch")


def sample_ready() -> bool:
    return not P.missing_required(SAMPLE) and not P.is_lfs_pointer(SAMPLE / "high_freq_data.csv")


def save_uploads(files) -> Path:
    """Write uploads under their expected names (Excel converted to CSV) in a per-upload folder."""
    sig = hashlib.sha1("|".join(f"{f.name}:{f.size}" for f in files).encode()).hexdigest()[:12]
    folder = store.uploads() / sig       # kept, so History can reopen this analysis later
    folder.mkdir(parents=True, exist_ok=True)
    for f in files:
        name = P.canonical_name(f.name)
        if name is None:
            continue
        if f.name.lower().endswith((".xlsx", ".xls")):
            pd.read_excel(f).to_csv(folder / name, index=False)
        else:
            (folder / name).write_bytes(f.getbuffer())
    return folder


def report_html(r: dict, source: str) -> str:
    """One self-contained HTML file with the tables and every chart (opens offline)."""
    first = [True]

    def fig(f):
        out = f.to_html(full_html=False, include_plotlyjs=first[0])
        first[0] = False
        return out

    pta = P.pta_table(r)
    parts = [f"<h1>RizzML report</h1><p>Data: {html.escape(source)}. Generated {datetime.now():%d %b %Y %H:%M}.</p>",
             "<h2>Data quality</h2>", pd.Series(r["quality"]).to_frame("value").to_html()]
    if r["score"]:
        parts += ["<h2>Accuracy against measured tests</h2>", accuracy_table(r["score"]).to_html(index=False)]
    parts.append("<h2>Daily production rates (VFM)</h2>")
    for w in r["wells"]:
        parts += [f"<h3>{w}</h3>", fig(charts.rates(r["rates"][r["rates"].well_name == w], tests_for(r, w), dark=False))]
    parts += ["<h2>Well tests (PTA)</h2>", pta.to_html(index=False)]
    for res, plot in r["pta"]:
        if plot is None:
            continue
        parts += [f"<h3>{res['well_name']}, shut-in {res['shut_in_start']:%d %b %Y %H:%M}</h3>",
                  "<ul>" + "".join(f"<li>{html.escape(t).replace('**', '')}</li>" for t in P.explain(res)) + "</ul>",
                  fig(charts.horner(plot, res["p_star_gauge_psia"], dark=False)),
                  fig(charts.loglog(plot, dark=False)), fig(charts.history(plot, dark=False))]
    css = "body{font-family:system-ui,sans-serif;max-width:1100px;margin:40px auto;color:#0b0b0b}" \
          "table{border-collapse:collapse;font-size:14px}td,th{border-bottom:1px solid #e4e3df;padding:4px 10px;text-align:right}"
    return f"<!doctype html><meta charset='utf-8'><title>RizzML report</title><style>{css}</style>" + "\n".join(parts)


def accuracy_table(score: dict, t=lambda s: s) -> pd.DataFrame:
    rows = [{t("Phase"): t(ph.capitalize()), "MAPE %": v["MAPE_%"], "WAPE %": v["WAPE_%"], "R²": v["R2"]}
            for ph, v in score.items() if isinstance(v, dict)]
    return pd.DataFrame(rows)


def tests_for(r: dict, well: str):
    if r["tests"] is None:
        return None
    t = r["tests"][r["tests"].well_name == well].copy()
    t["test_start"] = pd.to_datetime(t.test_start)
    return t


def build_exports(r: dict, source: str) -> dict:
    pta = P.pta_table(r)
    acc = accuracy_table(r["score"]) if r["score"] else pd.DataFrame()
    sheets = {"VFM daily rates": r["rates"], "PTA results": pta,
              "Data quality": pd.Series(r["quality"]).rename_axis("check").reset_index(name="value")}
    if len(acc):
        sheets["Accuracy vs tests"] = acc
    return {"vfm_csv": P.to_csv(r["rates"]), "vfm_xlsx": P.to_excel({"VFM daily rates": r["rates"]}),
            "pta_csv": P.to_csv(pta), "pta_xlsx": P.to_excel({"PTA results": pta}),
            "all_xlsx": P.to_excel(sheets), "html": report_html(r, source).encode("utf-8")}


# ---------------------------------------------------------------------------------------- state
st.html(f"<style>{(HERE / 'style.css').read_text()}</style>")
ss, qp = st.session_state, st.query_params


def N_(s: str) -> str:
    """Marks a string for translation where t() is not yet known (i18n.py checks these too)."""
    return s


# key: (icon, title, subtitle, tile colour, needs an analysed data set)
# Colour says what a tile does: blue brings data in, red analyses it, green gets results out or sets things up.
MODULES = {
    "load": ("upload_file", N_("Load Data"), N_("Raw sensor files, CSV or Excel"), "blue", False),
    "sample": ("dataset", N_("Sample Data"), N_("Run on the hackathon field"), "blue", False),
    "field": ("monitoring", N_("Field Data"), N_("Sensor history per well"), "blue", True),
    "quality": ("fact_check", N_("Data Quality"), N_("Cleaning report"), "blue", True),
    "rates": ("oil_barrel", N_("Production Rates"), N_("Daily oil, water and gas (VFM)"), "red", True),
    "pta": ("speed", N_("Well Tests"), N_("Build-up analysis (PTA)"), "red", True),
    "graph": ("insert_chart", N_("Generate Graph"), N_("Any chart from the results"), "red", True),
    "export": ("download", N_("Export"), N_("Results and report"), "green", True),
    "convert": ("swap_horiz", N_("Convert"), N_("CSV and Excel"), "green", False),
    "history": ("history", N_("History"), N_("Your uploads and files"), "green", False),
    "settings": ("settings", N_("Settings"), N_("Theme and language"), "green", False),   # opened from the account bar
    "help": ("help", N_("Help"), N_("How to use RizzML"), "green", False),                  # opened from the account bar
}
# Top row is the workflow, left to right; the row below holds what each step needs less often.
ROWS = (("big", ["load", "rates", "pta", "graph", "export"]), ("small", ["sample", "field", "quality", "history", "convert"]))
BRAND = ["#00a3e0", "#e4002b", "#64a70b"]   # SOCAR blue, red, green (socar.az), for the wordmark only
# RizzML mark: a drop of oil with a rising rate line, in SOCAR's colours. Shown as an <img> because
# st.html sanitises inline <svg> away.
LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            '<rect width="64" height="64" rx="14" fill="#0077a6"/>'
            '<path d="M32 9C25 20 17 28 17 39a15 15 0 0 0 30 0c0-11-8-19-15-30z" fill="#fff"/>'
            '<path d="M23 44l6-6 5 4 7-8" fill="none" stroke="#e4002b" stroke-width="3.6" stroke-linecap="round"'
            ' stroke-linejoin="round"/><circle cx="41" cy="34" r="3.4" fill="#64a70b"/></svg>')
LOGO = (f'<img class="rz-logo" alt="RizzML logo" '
        f'src="data:image/svg+xml;base64,{base64.b64encode(LOGO_SVG.encode()).decode()}">')


def brand(tagline: str) -> str:
    bars = "".join(f"<span style='background:{c}'></span>" for c in BRAND)
    return (f"<div class='rz-brand'>{LOGO}<div><b>RizzML</b><small>{html.escape(tagline)}</small>"
            f"<div class='rz-sq'>{bars}</div></div></div>")


@st.cache_resource
def analysed() -> dict:
    """Analysed data sets by key ('sample' or an upload hash), kept for the life of the server, so a reload
    (the theme switch) or a colleague opening the same link finds the results instead of rerunning them."""
    return {}


if "lang" not in ss:   # first run of this browser session: language from its cookie, page and data from the URL
    ss.lang = st.context.cookies.get("rizzml_lang") if st.context.cookies.get("rizzml_lang") in i18n.LANGS else "en"
    ss.view = qp.get("view") if qp.get("view") in MODULES and qp.get("view") != "sample" else "home"
    if qp.get("data") in analysed():
        ss.data_key = qp["data"]
        ss.result, ss.exports, ss.source = analysed()[ss.data_key]
    ss.user = ss.get("user") or store.user_from(st.context.cookies.get("rizzml_user"))   # remembered sign-in
t = i18n.translator(ss.lang)
theme = st.context.cookies.get("rizzml_theme") if st.context.cookies.get("rizzml_theme") in ("dark", "light") else "dark"
dark = theme == "dark"
r = ss.get("result")
want = {"view": ss.view, **({"data": ss.data_key} if ss.get("data_key") else {})}
if qp.to_dict() != want:      # the URL always says where the user is, so a reload lands on the same page
    qp.from_dict(want)


def open_module(key: str):
    if key == "sample":
        ss.view, ss.run = "load", ("sample", "sample dataset")
    else:
        ss.view = key


def download(label: str, data, name: str, title: str, mime: str | None = None, **kw):
    """Every download also lands in the user's History, so it can be fetched again later."""
    st.download_button(label, data, name, mime, icon=":material/download:", on_click=store.keep,
                       args=(ss.user, name, data, title), **kw)


def browser(js: str):
    """Run an app-built snippet (never user input) against the app's window, from a same-origin iframe:
    a fresh document every time, so the script always runs. `w` is the app's window."""
    page = f"<script>const w = window.parent;{js}</script>"
    if hasattr(st, "iframe"):
        st.iframe(page, height=1)
    else:                                   # Streamlit before st.iframe
        import streamlit.components.v1 as components
        components.html(page, height=0)


YEAR = "max-age=31536000; path=/; samesite=lax"


def sync_theme(value: str):
    """Our cookie decides the theme. Streamlit reads its own copy once, at page load, from this browser's
    localStorage, so write ours there and reload if they differ (never otherwise, so it cannot loop).
    The URL carries the page and the data set, so the reload lands back in place with the results."""
    browser(f'w.document.cookie = "rizzml_theme={value}; {YEAR}";'
            f'const k = "stActiveTheme-" + w.location.pathname + "-v2", v = JSON.stringify("{value.capitalize()}");'
            'if (w.localStorage.getItem(k) !== v) { w.localStorage.setItem(k, v);'
            ' const s = w.document.createElement("script"); s.textContent = "location.reload()"; w.document.head.appendChild(s); }')


def header(key: str):
    """Page title behind a bar in its tile's colour. One element, not a container: Streamlit reuses a container
    in the same slot with its old children, so Home's account bar used to linger as ghost headings under the
    title while a page loaded (all ~30 s of an analysis)."""
    icon, title, _, colour, _ = MODULES[key]
    st.markdown(f":material/{icon}: <span class='rz-head rz-{colour}'>{html.escape(t(title))}</span>",
                unsafe_allow_html=True)


# Left-hand menu on every page except Home: same groups and colours as the tiles.
NAV = (["load", "field", "quality"], ["rates", "pta", "graph"], ["export", "history", "convert"])


def nav_item(key: str):
    icon, title, colour, locked = (("apps", "Home", "home", False) if key == "home" else
                                   (MODULES[key][0], MODULES[key][1], MODULES[key][3], MODULES[key][4] and r is None))
    if key in ("settings", "help"):   # account items, not a feature group: no colour bar
        colour = "none"
    active = "-active" if ss.view == key else ""
    st.button(t(title), key=f"nav_{colour}_{key}{active}", icon=f":material/{'lock' if locked else icon}:",
              type="tertiary", disabled=locked, on_click=open_module, args=(key,), **WIDE)


def sidebar():
    with st.sidebar:
        st.html(f"<div class='rz-side-brand'>{LOGO}<b>RizzML</b></div>")
        with st.container(key="navgroup_home"):
            nav_item("home")
        for i, group in enumerate(NAV):
            with st.container(key=f"navgroup_{i}"):
                for key in group:
                    nav_item(key)
        with st.container(key="navaccount"):
            st.caption(f":material/account_circle: {ss.user.replace('@', '@' + chr(0x200b))}")
            nav_item("help")
            nav_item("settings")
            st.button(t("Log out"), icon=":material/logout:", type="tertiary", key="nav_none_logout", on_click=logout, **WIDE)


def tile(key: str, size: str):
    icon, title, sub, colour, needs = MODULES[key]
    locked = needs and r is None
    off = locked or (key == "sample" and not sample_ready())
    if off:                     # say why it is unavailable instead of just greying it out
        sub = ":material/lock: " + t("Load data first" if locked else "Sample data not found")
    else:
        sub = t(sub)
    with st.container(key=f"tile_{size}_{colour}_{key}"):
        st.markdown(f":material/{icon}:\n\n**{t(title)}**\n\n{sub}")
        st.button(t(title), key=f"go_{key}", disabled=off, on_click=open_module, args=(key,))


def need_result() -> bool:
    if r is not None:
        return False
    st.info(t("No data analysed yet."), icon=":material/info:")
    st.button(t("Load Data"), icon=":material/upload_file:", type="primary", on_click=open_module, args=("load",))
    return True


COLUMN_LABELS = {
    "oil_rate_stbd": N_("Oil rate (stb/d)"), "water_rate_stbd": N_("Water rate (stb/d)"),
    "gas_rate_mscfd": N_("Gas rate (Mscf/d)"), "water_cut_pct": N_("Water cut (%)"),
    "gor_scf_stb": N_("Gas-oil ratio (scf/stb)"), "timestamp": N_("Date"), "test_start": N_("Date"),
    "permeability_md": N_("Permeability (md)"), "skin": N_("Skin"), "delta_p_skin_psi": N_("ΔP skin (psi)"),
    "horner_slope_psi_per_cycle": N_("Horner slope (psi/cycle)"), "flow_efficiency": N_("Flow efficiency"),
    "duration_h": N_("Shut-in duration (h)"), "p_star_gauge_psia": N_("p* at gauge (psia)"),
    "r_inv_ft": N_("Investigation radius (ft)"), **P.SENSOR_LABELS,
}


def label(col: str) -> str:
    return t(COLUMN_LABELS[col]) if col in COLUMN_LABELS else col


# ---------------------------------------------------------------------------------------- home
def page_home():
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", key="account"):
        st.markdown(f":material/account_circle: {ss.user.replace('@', '@' + chr(0x200b))}")   # no mailto link
        st.button(t("Help"), icon=":material/help:", type="tertiary", on_click=open_module, args=("help",))
        st.button(t("Settings"), icon=":material/settings:", type="tertiary", on_click=open_module, args=("settings",))
        st.button(t("Log out"), icon=":material/logout:", type="tertiary", on_click=logout)
    for size, keys in ROWS:
        for col, key in zip(st.columns(5, gap="small"), keys):
            with col:
                tile(key, size)
    st.html(f"<div class='rz-foot'>{brand(t('Daily well rates and well-test analysis'))}"
            "<small>SOCAR Hackathon 2026</small></div>")


# ---------------------------------------------------------------------------------------- load
def page_load():
    header("load")
    files = st.file_uploader(t("Raw files"), type=["csv", "xlsx", "xls"], accept_multiple_files=True,
                             label_visibility="collapsed")
    got = {P.canonical_name(f.name): f.name for f in files or [] if P.canonical_name(f.name)}
    st.markdown("&emsp;".join(
        f":green[:material/check_circle: {n.removesuffix('.csv')}]" if n in got
        else f":gray[:material/radio_button_unchecked: {n.removesuffix('.csv')}{'' if req else ' ' + t('(optional)')}]"
        for n, (req, _, _) in P.FILES.items()))
    ready = all(n in got for n, (req, _, _) in P.FILES.items() if req)
    with st.container(horizontal=True):
        run_upload = st.button(t("Run analysis"), type="primary", icon=":material/play_arrow:", disabled=not ready)
        run_sample = st.button(t("Run on sample data"), icon=":material/dataset:", disabled=not sample_ready())
    job = ss.get("run")                # (data key, source) from the Sample tile or History
    if job and not (run_upload or run_sample) and ss.get("prev_view") != "load":
        # Started from another page. Streamlit keeps that page's elements on screen (faded) until a run
        # ends, which would be the whole analysis. Let this run end first, then start a second later.
        st.info(t("Starting the analysis…"), icon=":material/hourglass_top:")

        @st.fragment(run_every=1)
        def start_when_drawn():
            if ss.get("prev_view") == "load":
                st.rerun()
        start_when_drawn()
        return
    ss.pop("run", None)
    if run_sample:
        job = ("sample", "sample dataset")
    if run_upload:
        folder = save_uploads(files)
        job = (folder.name, ", ".join(got.values()))
        store.log(ss.user, "upload", job[1], data_key=folder.name, size=sum(f.size for f in files))
    if not job:
        return
    key, source = job
    folder = SAMPLE if key == "sample" else store.uploads() / key
    with st.status(t("Analysing…"), expanded=True) as status:
        try:
            result = P.analyse(folder, progress=lambda m: status.write(t(m)))
            status.write(t("Preparing downloads"))
            exports = build_exports(result, source)
        except Exception as e:
            status.update(label=t("Analysis failed"), state="error")
            st.error(t("The data could not be analysed: {e}. Check that each file has the expected columns.").format(e=e))
            return
    cache = analysed()
    cache[key] = (result, exports, source)
    while len(cache) > 6:          # ponytail: oldest-first eviction; size it to the server's RAM if many uploads
        cache.pop(next(iter(cache)))
    name = t("Sample Data") if key == "sample" else source
    store.log(ss.user, "analysis", t("{source}: {wells} wells, {days} well-days, {shutins} build-ups").format(
        source=name, wells=len(result["wells"]), days=f"{len(result['rates']):,}",
        shutins=sum(plot is not None for _, plot in result["pta"])), data_key=key)
    # land on the first result an engineer wants: the daily rates
    ss.result, ss.exports, ss.source, ss.data_key, ss.view = result, exports, source, key, "rates"
    st.rerun()


# ---------------------------------------------------------------------------------------- field data
def page_field():
    header("field")
    if need_result():
        return
    c = st.columns([1, 3])
    well = c[0].selectbox(t("Well"), r["wells"], key="field_well")
    cols = c[1].multiselect(t("Sensors"), P.SENSORS, default=["dh_pressure_psia", "whp_psia", "gas_lift_rate_mscfd"],
                            format_func=label)
    if cols:
        st.plotly_chart(charts.sensors(r["hourly"][r["hourly"].well_name == well], cols, {k: label(k) for k in cols},
                                       r["events"][r["events"].well == well], dark=dark), **WIDE)


# ---------------------------------------------------------------------------------------- data quality
def page_quality():
    header("quality")
    if need_result():
        return
    q = r["quality"]
    c = st.columns(4)
    c[0].metric(t("Rows after cleaning"), f"{q['Rows after cleaning']:,}")
    c[1].metric(t("Missing-value codes masked"), f"{q['Missing-value codes (-999.25) masked']:,}")
    c[2].metric(t("Duplicate rows dropped"), f"{q['Duplicate rows dropped']:,}")
    c[3].metric(t("Low-coverage days"), q["Days with low sensor coverage (<80%)"])
    st.dataframe(pd.DataFrame({t("Check"): [t(k) for k in q],
                               t("Value"): [f"{v:,}" if isinstance(v, int) else v for v in q.values()]}), hide_index=True, **WIDE)


# ---------------------------------------------------------------------------------------- VFM
def page_rates():
    header("rates")
    if need_result():
        return
    ex = ss.exports
    if r["unseen"]:
        st.warning(t("Not in the trained model: {wells}. Rates use the field average.").format(wells=", ".join(r["unseen"])),
                   icon=":material/warning:")
    c = st.columns([1.3, 1, 1, 1.4, 1.2])
    well = c[0].selectbox(t("Well"), r["wells"], key="vfm_well")
    c[1].metric(t("Wells"), len(r["wells"]))
    c[2].metric(t("Well-days"), f"{len(r['rates']):,}")
    last = r["rates"][r["rates"].timestamp == r["rates"].timestamp.max()]
    c[3].metric(t("Field oil, {date}").format(date=last.timestamp.iloc[0]), f"{last.oil_rate_stbd.sum():,.0f} stb/d")
    if r["score"]:
        c[4].metric(t("Oil error vs tests"), f"{r['score']['oil']['MAPE_%']}%",
                    help=t("MAPE over {n} measured tests in this data.").format(n=r["score"]["tests_scored"]))
    st.plotly_chart(charts.rates(r["rates"][r["rates"].well_name == well], tests_for(r, well), dark=dark, t=t), **WIDE)
    c = st.columns([1, 2])
    if r["score"]:
        c[0].dataframe(accuracy_table(r["score"], t), hide_index=True, **WIDE)
    with c[1].expander(t("Daily rates, {well}").format(well=well)):
        st.dataframe(r["rates"][r["rates"].well_name == well], hide_index=True, **WIDE)
    with st.container(horizontal=True):
        download(t("Rates, CSV"), ex["vfm_csv"], "rizzml_vfm_daily_rates.csv", f"{t('Daily rates')} (CSV)", "text/csv")
        download(t("Rates, Excel"), ex["vfm_xlsx"], "rizzml_vfm_daily_rates.xlsx", f"{t('Daily rates')} (Excel)")


# ---------------------------------------------------------------------------------------- PTA
def page_pta():
    header("pta")
    if need_result():
        return
    ex = ss.exports
    ok = [(res, plot) for res, plot in r["pta"] if plot is not None]
    for res, _ in r["pta"]:
        if "error" in res:
            st.warning(t("{well}, shut-in {start}: {error}").format(well=res["well_name"], start=res["shut_in_start"],
                                                                     error=res["error"]), icon=":material/warning:")
    if not ok:
        st.info(t("No shut-ins in this data."), icon=":material/info:")
        return
    c = st.columns([1.6, 1, 1, 1, 1.2, 1])
    pick = c[0].selectbox(t("Shut-in"), range(len(ok)), format_func=lambda i: (
        f"{ok[i][0]['well_name']}, {ok[i][0]['shut_in_start']:%d %b %Y %H:%M}, {ok[i][0]['duration_h']:.0f} h"))
    res, plot = ok[pick]
    c[1].metric(t("Permeability"), f"{res['permeability_md']:.1f} md")
    c[2].metric(t("Skin"), f"{res['skin']:+.2f}")
    c[3].metric(t("ΔP skin"), f"{res['delta_p_skin_psi']:.0f} psi")
    c[4].metric(t("Horner slope, psi/cycle"), f"{res['horner_slope_psi_per_cycle']:.1f}")
    c[5].metric(t("Flow efficiency"), f"{res['flow_efficiency']:.0%}")
    with st.expander(t("Interpretation"), icon=":material/lightbulb:"):
        st.markdown("\n".join(f"- {line}" for line in P.explain(res, t)))
    c = st.columns(2)
    c[0].plotly_chart(charts.horner(plot, res["p_star_gauge_psia"], dark=dark, t=t), **WIDE)
    c[1].plotly_chart(charts.loglog(plot, dark=dark, t=t), **WIDE)
    st.plotly_chart(charts.history(plot, dark=dark, t=t), **WIDE)
    st.dataframe(P.pta_table(r), hide_index=True, **WIDE)
    none = sorted(set(r["wells"]) - {res["well_name"] for res, _ in ok})
    if none:
        st.caption(t("No shut-in: {wells}").format(wells=", ".join(none)))
    with st.container(horizontal=True):
        download(t("PTA, CSV"), ex["pta_csv"], "rizzml_pta_results.csv", f"{t('PTA results')} (CSV)", "text/csv")
        download(t("PTA, Excel"), ex["pta_xlsx"], "rizzml_pta_results.xlsx", f"{t('PTA results')} (Excel)")


# ---------------------------------------------------------------------------------------- graph builder
KINDS = {"trend": N_("Trend over time"), "cross": N_("Cross-plot"), "box": N_("Distribution by well"),
         "hist": N_("Histogram"), "bar": N_("Compare wells")}
STATS = {"mean": N_("Mean"), "sum": N_("Sum"), "min": N_("Minimum"), "max": N_("Maximum")}


def graph_sets() -> dict:
    """Every table the analysis produced, as (title, frame, time column or None)."""
    d = r["rates"].copy()
    d["timestamp"] = pd.to_datetime(d.timestamp)
    liquid = d.oil_rate_stbd + d.water_rate_stbd
    d["water_cut_pct"] = 100 * d.water_rate_stbd / liquid.where(liquid > 0)
    d["gor_scf_stb"] = 1000 * d.gas_rate_mscfd / d.oil_rate_stbd.where(d.oil_rate_stbd > 0)
    sets = {"rates": (t("Daily rates"), d, "timestamp"), "hourly": (t("Sensors, hourly"), r["hourly"], "timestamp")}
    if r["tests"] is not None:
        sets["tests"] = (t("Measured well tests"), r["tests"].assign(test_start=pd.to_datetime(r["tests"].test_start)),
                         "test_start")
    pta = P.pta_table(r)
    if len(pta):
        sets["pta"] = (t("PTA results"), pta, None)
    return sets


def well_slots(wells: list[str]) -> dict:
    """Colour slot per well, kept while the well stays selected: adding a well never repaints the others."""
    slots = {w: s for w, s in ss.get("slots", {}).items() if w in wells}
    free = [i for i in range(8) if i not in slots.values()]
    for w in wells:
        if w not in slots and free:
            slots[w] = free.pop(0)
    ss.slots = slots
    return slots


def page_graph():
    header("graph")
    if need_result():
        return
    sets = graph_sets()
    c = st.columns(4)
    ds = c[0].selectbox(t("Data"), list(sets), format_func=lambda k: sets[k][0], key="g_data")
    _, df, time = sets[ds]
    kinds = list(KINDS) if time else ["bar", "cross"]
    kind = c[1].selectbox(t("Chart"), kinds, format_func=lambda k: t(KINDS[k]), key=f"g_kind_{ds}")
    nums = [col for col in df.select_dtypes("number").columns if df[col].notna().any()]
    y = c[2].selectbox(t("Measure"), nums, format_func=label, key=f"g_y_{ds}")
    x, agg = None, "mean"
    if kind == "cross":
        x = c[3].selectbox(t("X axis"), [n for n in nums if n != y], format_func=label, key=f"g_x_{ds}")
    elif kind == "bar" and time:
        agg = c[3].selectbox(t("Statistic"), list(STATS), format_func=lambda k: t(STATS[k]), key="g_agg")
    all_wells = sorted(df.well_name.unique())
    wells = st.multiselect(t("Wells"), all_wells, default=all_wells if ds == "pta" else all_wells[:4], key=f"g_wells_{ds}")
    if not wells:
        st.info(t("Select at least one well."), icon=":material/info:")
        return
    d = df[df.well_name.isin(wells)].assign(well_name=lambda f: f.well_name.astype(str))
    labels = {col: label(col) for col in d.columns}
    st.plotly_chart(charts.custom(d, kind, y, labels, well_slots(wells), x=x, time=time, agg=agg, dark=dark, t=t), **WIDE)
    download(t("Download data (CSV)"), P.to_csv(d), f"rizzml_{ds}.csv",
             f"{t('Graph data')}: {sets[ds][0]}, {label(y)}", "text/csv")


# ---------------------------------------------------------------------------------------- export
def page_export():
    header("export")
    if need_result():
        return
    ex = ss.exports
    c = st.columns(3)
    with c[0].container(border=True):
        st.markdown(f"**{t('Production rates (VFM)')}**")
        download("CSV", ex["vfm_csv"], "rizzml_vfm_daily_rates.csv", f"{t('Daily rates')} (CSV)", "text/csv", **WIDE)
        download("Excel", ex["vfm_xlsx"], "rizzml_vfm_daily_rates.xlsx", f"{t('Daily rates')} (Excel)", **WIDE)
    with c[1].container(border=True):
        st.markdown(f"**{t('Well tests (PTA)')}**")
        download("CSV", ex["pta_csv"], "rizzml_pta_results.csv", f"{t('PTA results')} (CSV)", "text/csv", **WIDE)
        download("Excel", ex["pta_xlsx"], "rizzml_pta_results.xlsx", f"{t('PTA results')} (Excel)", **WIDE)
    with c[2].container(border=True):
        st.markdown(f"**{t('Everything')}**")
        download(t("Excel workbook"), ex["all_xlsx"], "rizzml_results.xlsx", t("Excel workbook"), **WIDE)
        download(t("Report with charts (HTML)"), ex["html"], "rizzml_report.html", t("Report with charts (HTML)"),
                 "text/html", **WIDE)


# ---------------------------------------------------------------------------------------- convert
def page_convert():
    header("convert")
    f = st.file_uploader(t("CSV or Excel file"), type=["csv", "xlsx", "xls"], key="convert", label_visibility="collapsed")
    if not f:
        return
    data = f.getvalue()
    excel = f.name.lower().endswith((".xlsx", ".xls"))
    sheet = st.selectbox(t("Sheet"), pd.ExcelFile(f).sheet_names) if excel else 0
    df = P.read_table(f.name, data, sheet)
    stem = Path(f.name).stem
    if excel:
        download(t("Download as CSV"), P.to_csv(df), f"{stem}.csv", f"{t('Converted')}: {stem}.csv", "text/csv",
                 type="primary")
    elif len(df) > 1_048_575:
        st.error(t("Too many rows for Excel (limit 1,048,576). Keep this one as CSV."))
    else:
        download(t("Download as Excel"), P.to_excel({stem[:31] or "data": df}), f"{stem}.xlsx",
                 f"{t('Converted')}: {stem}.xlsx", type="primary")
    st.caption(t("{rows} rows, {cols} columns").format(rows=f"{len(df):,}", cols=df.shape[1]))
    st.dataframe(df.head(200), hide_index=True, **WIDE)


# ---------------------------------------------------------------------------------------- settings
def set_lang():
    if ss.lang_pick:
        ss.lang, ss.save_lang = ss.lang_pick, True
    else:                      # clicking the active option would clear it: keep it selected
        ss.lang_pick = ss.lang


def set_theme():
    if ss.theme_pick:
        ss.apply_theme = ss.theme_pick
    else:
        ss.theme_pick = theme


def page_help():
    """The user guide, docs/guide.<lang>.md; each "## " section is a tab, so tab names come translated."""
    header("help")
    guide = HERE / "docs" / f"guide.{ss.lang}.md"
    text = (guide if guide.exists() else HERE / "docs" / "guide.en.md").read_text(encoding="utf-8")
    sections = [part.split("\n", 1) for part in re.split(r"^## ", text, flags=re.M)[1:]]
    for tab, (_, body) in zip(st.tabs([title.strip() for title, _ in sections]), sections):
        tab.markdown(body)


def page_settings():
    header("settings")
    st.segmented_control(t("Theme"), ["dark", "light"], default=theme, key="theme_pick", on_change=set_theme,
                         format_func=lambda v: f":material/{v}_mode: " + t(v.capitalize()))
    st.segmented_control(t("Language"), list(i18n.LANGS), default=ss.lang, key="lang_pick", on_change=set_lang,
                         format_func=i18n.LANGS.get)
    if (new := ss.pop("apply_theme", None)) and new != theme:
        sync_theme(new)


# ---------------------------------------------------------------------------------------- history
KINDS_HISTORY = {"upload": ("upload_file", N_("Upload")), "analysis": ("query_stats", N_("Analysis")),
                 "file": ("description", N_("File"))}
LAZY_DOWNLOADS = "callable" in (st.download_button.__doc__ or "")   # file read only on click (newer Streamlit)


def plain(text: str) -> str:
    """Show a stored title (it may hold user file names) as literal text, not Markdown, LaTeX or icons."""
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~:$])", r"\\\1", text)


def reopen(key: str, source: str):
    if key in analysed():
        ss.result, ss.exports, ss.source = analysed()[key]
        ss.data_key, ss.view = key, "rates"
    else:                                   # analyse the stored files again
        ss.view, ss.run = "load", (key, source)


def page_history():
    header("history")
    rows = store.events(ss.user)
    if not rows:
        st.info(t("Nothing yet. Uploads, analyses and downloaded files appear here."), icon=":material/info:")
        return
    for e in rows:
        icon, kind = KINDS_HISTORY[e["kind"]]
        size = "" if not e["size"] else f", {e['size'] / 1e6:.1f} MB" if e["size"] > 1e6 else f", {e['size'] / 1e3:.0f} KB"
        with st.container(border=True, horizontal=True, vertical_alignment="center", key=f"hist_{e['id']}"):
            st.markdown(f":material/{icon}: **{t(kind)}** &nbsp; {plain(e['title'])}  \n"
                        f":gray[{datetime.fromtimestamp(e['ts']):%d.%m.%Y %H:%M}{size}]")
            if e["kind"] == "file":
                path = Path(e["path"])
                name = path.name.split("_", 1)[-1]
                data = (lambda p=path: p.read_bytes()) if LAZY_DOWNLOADS else (path.read_bytes() if path.exists() else b"")
                st.download_button(t("Download"), data, name, icon=":material/download:", key=f"get_{e['id']}",
                                   disabled=not path.exists(), help=None if path.exists() else t("No longer available"))
            else:
                here = sample_ready() if e["data_key"] == "sample" else (store.uploads() / e["data_key"]).exists()
                st.button(t("Open"), icon=":material/open_in_new:", key=f"open_{e['id']}", disabled=not here,
                          help=None if here else t("No longer available"), on_click=reopen,
                          args=(e["data_key"], "sample dataset" if e["data_key"] == "sample" else e["title"]))


# ---------------------------------------------------------------------------------------- sign-in
def sign_in():
    user = store.check(ss.login_email, ss.login_password)
    if user:
        ss.user, ss.save_user, ss.login_error = user, True, False
    else:
        ss.login_error = True


def logout():
    for k in ("user", "result", "exports", "source", "data_key", "slots"):
        ss.pop(k, None)
    ss.user, ss.view, ss.forget_user = None, "home", True


def page_login():
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid, st.container(key="loginpage"):
        st.html(brand(t("Daily well rates and well-test analysis")))
        with st.form("login", border=True, enter_to_submit=True):
            st.markdown(f"**{t('Sign in')}**")
            st.text_input(t("Email"), placeholder="name@socar.az", key="login_email", autocomplete="username")
            st.text_input(t("Password"), type="password", key="login_password", autocomplete="current-password")
            st.form_submit_button(t("Sign in"), type="primary", icon=":material/login:", on_click=sign_in, **WIDE)
        if ss.get("login_error"):
            st.error(t("Wrong email or password."), icon=":material/error:")
        st.segmented_control(t("Language"), list(i18n.LANGS), default=ss.lang, key="lang_pick", on_change=set_lang,
                             format_func=i18n.LANGS.get, label_visibility="collapsed")
        st.caption("SOCAR Hackathon 2026")


if ss.user:
    if ss.view != "home":
        sidebar()
    {"home": page_home, "load": page_load, "field": page_field, "quality": page_quality, "rates": page_rates,
     "pta": page_pta, "graph": page_graph, "export": page_export, "convert": page_convert,
     "history": page_history, "help": page_help, "settings": page_settings}[ss.view]()
else:
    page_login()

ss.prev_view = ss.view if ss.user else None   # the page this run drew (page_load defers long jobs on a page change)

# Cookies and the theme are written by the browser, after the page is drawn.
if ss.pop("save_lang", False):     # remembered by this browser only: each engineer keeps their own
    browser(f'w.document.cookie = "rizzml_lang={ss.lang}; {YEAR}";')
if ss.pop("save_user", False):
    browser(f'w.document.cookie = "rizzml_user={store.token(ss.user)}; {YEAR}";')
if ss.pop("forget_user", False):
    browser('w.document.cookie = "rizzml_user=; max-age=0; path=/";')
if not ss.get("theme_synced"):   # once per session: a first visit gets dark, a cleared localStorage is restored
    ss.theme_synced = True
    sync_theme(theme)
