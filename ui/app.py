"""RizzML: daily well rates and well-test analysis from the sensors SOCAR already has.

Run from this folder, so .streamlit/config.toml (theme, 1 GB upload limit) applies:
    cd ui && streamlit run app.py
On a shared server add `--server.address 0.0.0.0`; engineers open http://<server>:8501 in a browser.
"""
from __future__ import annotations

import hashlib
import html
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import charts
import pipeline as P

st.set_page_config(page_title="RizzML", layout="wide")
SAMPLE = Path(os.environ.get("RIZZML_DATA_DIR", P.ROOT / "data"))
WIDE = dict(width="stretch")


def sample_ready() -> bool:
    return not P.missing_required(SAMPLE) and not P.is_lfs_pointer(SAMPLE / "high_freq_data.csv")


def save_uploads(files) -> Path:
    """Write uploads under their expected names (Excel converted to CSV) in a per-upload folder."""
    sig = hashlib.sha1("|".join(f"{f.name}:{f.size}" for f in files).encode()).hexdigest()[:12]
    folder = Path(tempfile.gettempdir()) / "rizzml" / sig
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
        parts += [f"<h3>{w}</h3>", fig(charts.rates(r["rates"][r["rates"].well_name == w], tests_for(r, w)))]
    parts += ["<h2>Well tests (PTA)</h2>", pta.to_html(index=False)]
    for res, plot in r["pta"]:
        if plot is None:
            continue
        parts += [f"<h3>{res['well_name']}, shut-in {res['shut_in_start']:%d %b %Y %H:%M}</h3>",
                  "<ul>" + "".join(f"<li>{html.escape(t).replace('**', '')}</li>" for t in P.explain(res)) + "</ul>",
                  fig(charts.horner(plot, res["horner_slope_psi_per_cycle"], res["p_star_gauge_psia"])),
                  fig(charts.loglog(plot)), fig(charts.history(plot))]
    css = "body{font-family:system-ui,sans-serif;max-width:1100px;margin:40px auto;color:#0b0b0b}" \
          "table{border-collapse:collapse;font-size:14px}td,th{border-bottom:1px solid #e4e3df;padding:4px 10px;text-align:right}"
    return f"<!doctype html><meta charset='utf-8'><title>RizzML report</title><style>{css}</style>" + "\n".join(parts)


def accuracy_table(score: dict) -> pd.DataFrame:
    rows = [{"Phase": ph.capitalize(), "MAPE %": v["MAPE_%"], "WAPE %": v["WAPE_%"], "R²": v["R2"]}
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


# ---------------------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("RizzML")
    st.caption("Daily well rates and well-test analysis from the sensors you already have.")
    st.subheader("Load well data")
    files = st.file_uploader("Raw files (CSV or Excel)", type=["csv", "xlsx", "xls"], accept_multiple_files=True,
                             help="Select all files at once. A file is recognised if its name contains "
                                  "high_freq, choke, pvt, completion or test.")
    got = {P.canonical_name(f.name): f.name for f in files or [] if P.canonical_name(f.name)}
    st.dataframe(pd.DataFrame([{"File": n.removesuffix(".csv"),
                                "Status": "✓ found" if n in got else ("missing" if req else "optional")}
                               for n, (req, _, _) in P.FILES.items()]), hide_index=True, **WIDE)
    ready = all(n in got for n, (req, _, _) in P.FILES.items() if req)
    run_upload = st.button("Run analysis", type="primary", disabled=not ready, **WIDE)
    run_sample = st.button("Use the sample dataset", disabled=not sample_ready(), **WIDE,
                           help="The hackathon data set in the repository's data folder.")
    if "source" in st.session_state:
        st.caption(f"Loaded: {st.session_state.source}")
    st.divider()
    st.caption("Model: ml/models/vfm.pkl, a physics-based choke model (oil error 2.6%, time-forward). "
               "PTA: Horner build-up analysis, single-phase oil.")

if run_upload or run_sample:
    folder, source = (save_uploads(files), ", ".join(got.values())) if run_upload else (SAMPLE, "sample dataset")
    with st.status("Analysing the data…", expanded=True) as status:
        try:
            result = P.analyse(folder, progress=status.write)
            status.write("Preparing downloads and the report")
            st.session_state.exports = build_exports(result, source)
        except Exception as e:
            status.update(label="Analysis failed", state="error")
            st.error(f"The data could not be analysed: {e}. Check that each file has the expected columns.")
            st.stop()
        status.update(label=f"Analysis done in {result['seconds']} s", state="complete", expanded=False)
    st.session_state.result, st.session_state.source = result, source

r = st.session_state.get("result")
if r is None:
    st.header("Well rates and well tests from the sensors you already have")
    st.markdown(
        "1. **Load** the raw well data on the left (or use the sample dataset).\n"
        "2. **Run analysis.** Cleaning, rate prediction and well-test analysis take about half a minute.\n"
        "3. **Read** the results in the tabs: field data, production rates, well tests.\n"
        "4. **Export** results and a report for both parts.")
    st.subheader("Files the app expects")
    st.dataframe(pd.DataFrame([{"File": n, "Required": "yes" if req else "no", "Contents": desc}
                               for n, (req, desc, _) in P.FILES.items()]), hide_index=True, **WIDE)
    st.stop()

st.caption(f"Data: {st.session_state.source}. {len(r['wells'])} wells, analysed in {r['seconds']} s.")
tab_field, tab_vfm, tab_pta, tab_export, tab_convert = st.tabs(
    ["1. Field data", "2. Production rates (VFM)", "3. Well tests (PTA)", "4. Export", "Convert files"])
ex = st.session_state.exports

# ---------------------------------------------------------------------------------------- 1 field data
with tab_field:
    st.caption("Cleaned sensor data, averaged per hour. Shaded bands are shut-ins (choke at 0%).")
    q = r["quality"]
    c = st.columns(4)
    c[0].metric("Rows after cleaning", f"{q['Rows after cleaning']:,}")
    c[1].metric("Missing-value codes masked", f"{q['Missing-value codes (-999.25) masked']:,}")
    c[2].metric("Duplicate rows dropped", f"{q['Duplicate rows dropped']:,}")
    c[3].metric("Low-coverage days", q["Days with low sensor coverage (<80%)"])
    well = st.selectbox("Well", r["wells"], key="field_well")
    cols = st.multiselect("Sensors", P.SENSORS, default=["dh_pressure_psia", "whp_psia", "gas_lift_rate_mscfd"],
                          format_func=P.SENSOR_LABELS.get)
    if cols:
        st.plotly_chart(charts.sensors(r["hourly"][r["hourly"].well_name == well], cols, P.SENSOR_LABELS,
                                       r["events"][r["events"].well == well]), **WIDE)
    with st.expander("All data-quality checks"):
        st.dataframe(pd.Series(q).rename_axis("Check").reset_index(name="Value"), hide_index=True)

# ---------------------------------------------------------------------------------------- 2 VFM
with tab_vfm:
    st.caption("Daily oil, water and gas rates predicted by the trained model from the sensor data. "
               "Dots are measured well tests, when the upload includes them.")
    if r["unseen"]:
        st.warning(f"Wells the model was not trained on: {', '.join(r['unseen'])}. Their rates use the field "
                   "average and are not reliable until a few well tests calibrate them.")
    c = st.columns(4)
    c[0].metric("Wells", len(r["wells"]))
    c[1].metric("Well-days", f"{len(r['rates']):,}")
    last = r["rates"][r["rates"].timestamp == r["rates"].timestamp.max()]
    c[2].metric(f"Field oil, {last.timestamp.iloc[0]}", f"{last.oil_rate_stbd.sum():,.0f} stb/d")
    if r["score"]:
        c[3].metric("Oil error vs tests (MAPE)", f"{r['score']['oil']['MAPE_%']}%",
                    help=f"Checked against {r['score']['tests_scored']} measured tests in this data.")
    well = st.selectbox("Well", r["wells"], key="vfm_well")
    st.plotly_chart(charts.rates(r["rates"][r["rates"].well_name == well], tests_for(r, well)), **WIDE)
    if r["score"]:
        st.markdown("**Accuracy against the measured tests in this data**")
        st.dataframe(accuracy_table(r["score"]), hide_index=True)
    with st.expander(f"Daily rates table, {well}"):
        st.dataframe(r["rates"][r["rates"].well_name == well], hide_index=True, **WIDE)
    c = st.columns(2)
    c[0].download_button("Download rates (CSV)", ex["vfm_csv"], "rizzml_vfm_daily_rates.csv", "text/csv", **WIDE)
    c[1].download_button("Download rates (Excel)", ex["vfm_xlsx"], "rizzml_vfm_daily_rates.xlsx", **WIDE)

# ---------------------------------------------------------------------------------------- 3 PTA
with tab_pta:
    st.caption("Every shut-in is found from the choke data and analysed as a pressure build-up "
               "(Horner method, single-phase oil), using the predicted daily oil rate.")
    ok = [(res, plot) for res, plot in r["pta"] if plot is not None]
    for res, _ in r["pta"]:
        if "error" in res:
            st.warning(f"{res['well_name']}, shut-in {res['shut_in_start']}: could not be analysed ({res['error']}).")
    if not ok:
        st.info("No shut-ins in this data, so there is no build-up to analyse.")
    else:
        pick = st.selectbox("Shut-in", range(len(ok)), format_func=lambda i: (
            f"{ok[i][0]['well_name']}, {ok[i][0]['shut_in_start']:%d %b %Y %H:%M}, {ok[i][0]['duration_h']:.0f} h"))
        res, plot = ok[pick]
        c = st.columns(5)
        c[0].metric("Permeability", f"{res['permeability_md']:.1f} md")
        c[1].metric("Skin", f"{res['skin']:+.2f}")
        c[2].metric("ΔP skin", f"{res['delta_p_skin_psi']:.0f} psi")
        c[3].metric("Horner slope", f"{res['horner_slope_psi_per_cycle']:.1f} psi/cycle")
        c[4].metric("Flow efficiency", f"{res['flow_efficiency']:.0%}")
        with st.container(border=True):
            st.markdown("**Interpretation**\n\n" + "\n".join(f"- {t}" for t in P.explain(res)))
        c = st.columns(2)
        c[0].plotly_chart(charts.horner(plot, res["horner_slope_psi_per_cycle"], res["p_star_gauge_psia"]), **WIDE)
        c[1].plotly_chart(charts.loglog(plot), **WIDE)
        st.plotly_chart(charts.history(plot), **WIDE)
        st.subheader("All shut-ins")
        st.dataframe(P.pta_table(r), hide_index=True, **WIDE)
        none = sorted(set(r["wells"]) - {res["well_name"] for res, _ in ok})
        if none:
            st.caption(f"No shut-in in this data for {', '.join(none)}, so no build-up analysis is possible there.")
        c = st.columns(2)
        c[0].download_button("Download PTA results (CSV)", ex["pta_csv"], "rizzml_pta_results.csv", "text/csv", **WIDE)
        c[1].download_button("Download PTA results (Excel)", ex["pta_xlsx"], "rizzml_pta_results.xlsx", **WIDE)

# ---------------------------------------------------------------------------------------- 4 export
with tab_export:
    st.caption("Results for both parts. CSV for other tools, Excel for reading, the HTML report for sharing.")
    c = st.columns(2)
    with c[0]:
        st.markdown("**Production rates (VFM)**")
        st.download_button("Daily rates, CSV", ex["vfm_csv"], "rizzml_vfm_daily_rates.csv", "text/csv", **WIDE)
        st.download_button("Daily rates, Excel", ex["vfm_xlsx"], "rizzml_vfm_daily_rates.xlsx", **WIDE)
    with c[1]:
        st.markdown("**Well tests (PTA)**")
        st.download_button("PTA results, CSV", ex["pta_csv"], "rizzml_pta_results.csv", "text/csv", **WIDE)
        st.download_button("PTA results, Excel", ex["pta_xlsx"], "rizzml_pta_results.xlsx", **WIDE)
    st.markdown("**Full report**")
    c = st.columns(2)
    c[0].download_button("Everything in one Excel workbook", ex["all_xlsx"], "rizzml_results.xlsx", **WIDE)
    c[1].download_button("Report with all charts (HTML)", ex["html"], "rizzml_report.html", "text/html", **WIDE)

# ---------------------------------------------------------------------------------------- convert
with tab_convert:
    st.caption("Side tool: convert any table between CSV and Excel.")
    f = st.file_uploader("CSV or Excel file", type=["csv", "xlsx", "xls"], key="convert")
    if f:
        data = f.getvalue()
        excel = f.name.lower().endswith((".xlsx", ".xls"))
        sheet = st.selectbox("Sheet", pd.ExcelFile(f).sheet_names) if excel else 0
        df = P.read_table(f.name, data, sheet)
        st.caption(f"{len(df):,} rows, {df.shape[1]} columns. First rows:")
        st.dataframe(df.head(200), hide_index=True, **WIDE)
        stem = Path(f.name).stem
        if excel:
            st.download_button("Download as CSV", P.to_csv(df), f"{stem}.csv", "text/csv", type="primary")
        elif len(df) > 1_048_575:
            st.error("Too many rows for Excel (its limit is 1,048,576). Keep this one as CSV.")
        else:
            st.download_button("Download as Excel", P.to_excel({stem[:31] or "data": df}), f"{stem}.xlsx", type="primary")
