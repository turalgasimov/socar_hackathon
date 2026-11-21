"""RizzML back end: raw well data -> cleaned sensors -> daily VFM rates -> PTA for every shut-in.

Reuses the ML team's code unchanged: ml/src (clean, features, vfm) and ml/predict_from_raw.py.
PTA = the submitted method: Horner window B seeds an exact model match (ml/src/pta_model.py, imported
unchanged). The Horner steps mirror ml/eda/pta_explore.py, which loads the repo's processed data when
imported and so cannot run on an uploaded data set; the logic here is the same, line for line.
"""
from __future__ import annotations

import io
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "ml"), str(ROOT / "ml" / "src")]
import clean  # noqa: E402
import features as F  # noqa: E402
import predict_from_raw as PFR  # noqa: E402
import pta_model as PM  # noqa: E402
from config import SENSORS  # noqa: E402
from vfm import VFMModel, build_inputs  # noqa: E402

MODEL = ROOT / "ml" / "models" / "vfm.pkl"
FILES = {  # canonical name -> (required, what it holds, name keyword)
    "high_freq_data.csv": (True, "Per-minute sensors: wellhead, downhole, annulus, gas lift", "high"),
    "choke_events.csv": (True, "Choke settings over time; 0% opening = shut-in", "choke"),
    "reservoir_pvt.csv": (True, "Rock and fluid properties for the well-test analysis", "pvt"),
    "well_completion.csv": (True, "Gauge depth, tubing, cumulative oil to 1 Jan 2025", "completion"),
    "well_tests.csv": (False, "Measured rates: accuracy check and fluid gradient", "test"),
}
SENSOR_LABELS = {
    "whp_psia": "Wellhead pressure (psia)",
    "whp_downstream_psia": "Wellhead pressure, downstream of choke (psia)",
    "dh_pressure_psia": "Downhole pressure (psia)",
    "dh_temperature_degf": "Downhole temperature (°F)",
    "annulus_pressure_psia": "Annulus pressure (psia)",
    "gas_lift_rate_mscfd": "Gas-lift injection (Mscf/d)",
}
RATES = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]
PTA_COLUMNS = ["well_name", "shut_in_start", "shut_in_end", "duration_h", "horner_slope_psi_per_cycle",
               "permeability_md", "skin", "delta_p_skin_psi", "flow_efficiency", "boundary", "r_e_ft",
               "fit_rms_psi", "p_star_gauge_psia", "p_star_datum_psia", "pwf_gauge_psia", "qo_stbd", "tp_h",
               "k_horner_md", "skin_horner", "note", "r_inv_ft", "storage_bbl_per_psi"]


def canonical_name(filename: str) -> str | None:
    """Map an uploaded file name to the expected input, by keyword (case-insensitive)."""
    low = filename.lower()
    for name, (_, _, key) in FILES.items():
        if key in low:
            return name
    return None


def missing_required(data_dir: Path) -> list[str]:
    return [n for n, (req, _, _) in FILES.items() if req and not (Path(data_dir) / n).exists()]


def is_lfs_pointer(path: Path) -> bool:
    """True for a Git LFS placeholder (the real file was never downloaded)."""
    return path.exists() and path.stat().st_size < 1024 and path.read_bytes().startswith(b"version https://git-lfs")


# --------------------------------------------------------------------------------------------
# Full analysis
# --------------------------------------------------------------------------------------------
def analyse(data_dir: Path, progress=lambda msg: None) -> dict:
    """Clean -> features -> VFM -> PTA. Everything the app shows comes from this one call."""
    data_dir, t0 = Path(data_dir), time.time()
    progress("Cleaning per-minute sensor data (missing-value codes, duplicates, spikes)")
    hf, hf_rep = clean.clean_high_freq(data_dir=data_dir, verbose=False)
    pvt = pd.read_csv(data_dir / "reservoir_pvt.csv")
    comp = pd.read_csv(data_dir / "well_completion.csv", parse_dates=["first_production_date"])
    choke = pd.read_csv(data_dir / "choke_events.csv", parse_dates=["timestamp"])

    progress("Building daily inputs for every well")
    daily = F.build_daily_table(hf, pvt, comp).sort_values(["well_name", "date"], ignore_index=True)

    progress("Predicting daily oil, water and gas rates with the trained model")
    model = VFMModel.load(MODEL)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pred = model.predict(build_inputs(daily, when="date"))
    rates = PFR._complete_grid(pd.DataFrame({
        "timestamp": pd.to_datetime(daily.date).dt.strftime("%Y-%m-%d"),
        "well_name": daily.well_name.astype(str).values,
        **{c: pred[c].round(1) for c in RATES}}))

    tests = tests_raw = score = None
    if (data_dir / "well_tests.csv").exists():
        progress("Checking accuracy against the measured well tests")
        tests, _ = clean.clean_well_tests(verbose=False, data_dir=data_dir)
        tests_raw = pd.read_csv(data_dir / "well_tests.csv")
        score = PFR._score(hf, data_dir / "well_tests.csv", model, data_dir, pvt, comp)

    progress("Finding shut-ins and interpreting each build-up (PTA)")
    events = shut_in_events(choke)
    pta = []
    for ev in events.itertuples(index=False):
        try:
            pta.append(model_match(ev, hf, pvt.set_index("well_name"), comp.set_index("well_name"), rates, tests_raw))
        except Exception as e:  # one bad event must not take the whole run down
            pta.append((dict(well_name=ev.well, shut_in_start=ev.start, shut_in_end=ev.end, error=str(e)), None))

    progress("Summarising sensors for the charts")
    hourly = hf.groupby(["well_name", pd.Grouper(key="timestamp", freq="1h")], observed=True)[SENSORS].mean().reset_index()
    quality = {
        "Rows received": hf_rep.get("rows_in"), "Rows after cleaning": hf_rep.get("rows_out"),
        "Missing-value codes (-999.25) masked": sum(hf_rep.get("sentinel_to_nan", {}).values()),
        "Duplicate rows dropped": hf_rep.get("duplicate_rows_dropped"),
        "Shut-in minutes": hf_rep.get("shut_in_minutes"),
        "Well-days predicted": len(daily), "Days with low sensor coverage (<80%)": int(daily.low_coverage.sum()),
    }
    return dict(rates=rates, score=score, tests=tests, events=events, pta=pta, hourly=hourly, quality=quality,
                wells=sorted(rates.well_name.unique()),
                unseen=sorted(set(pred.loc[pred.unseen_well, "well_name"])),
                warnings=[str(w.message) for w in caught], seconds=round(time.time() - t0, 1))


def pta_table(result: dict) -> pd.DataFrame:
    rows = [r for r, _ in result["pta"] if "error" not in r]
    return pd.DataFrame(rows, columns=PTA_COLUMNS) if rows else pd.DataFrame(columns=PTA_COLUMNS)


# --------------------------------------------------------------------------------------------
# PTA: same method as ml/eda/pta_explore.py, on the data passed in
# --------------------------------------------------------------------------------------------
def shut_in_events(choke: pd.DataFrame) -> pd.DataFrame:
    ev = []
    for w, c in choke.groupby("well_name"):
        c = c.sort_values("timestamp").reset_index(drop=True)
        for i, r in c.iterrows():
            if r.choke_opening_pct == 0 and i + 1 < len(c):
                ev.append(dict(well=w, start=r.timestamp, end=c.timestamp[i + 1]))
    return pd.DataFrame(ev, columns=["well", "start", "end"])


def bourdet(x, p, L=0.10):
    """Bourdet derivative dp/dx with a +-L window in x (x = ln time)."""
    d = np.full(len(p), np.nan)
    for i in range(len(p)):
        lft = np.where(x <= x[i] - L)[0]
        rgt = np.where(x >= x[i] + L)[0]
        if len(lft) and len(rgt):
            j, k = lft[-1], rgt[0]
            d1 = (p[i] - p[j]) / (x[i] - x[j])
            d2 = (p[k] - p[i]) / (x[k] - x[i])
            d[i] = (d1 * (x[k] - x[i]) + d2 * (x[i] - x[j])) / (x[k] - x[j])
    return d


def _log_grid(dt, y, per_cycle=40):
    edges = np.logspace(np.log10(dt.min()), np.log10(dt.max()), int(np.log10(dt.max() / dt.min()) * per_cycle) + 2)
    g = pd.DataFrame({"i": np.digitize(dt, edges), "dt": dt, "y": y}).groupby("i").median()
    return g.dt.to_numpy(), g.y.to_numpy()


def _deriv_log_slope(t, der):
    lt, ld = np.log10(t), np.log10(der)
    ok = np.isfinite(ld)
    s = np.full(len(t), np.nan)
    for i in np.where(ok)[0]:
        nb = ok & (np.abs(lt - lt[i]) <= 0.15)
        if nb.sum() >= 4:
            s[i] = np.polyfit(lt[nb], ld[nb], 1)[0]
    return s


def window_A(t, der, s, tol=0.10, min_cycles=0.3):
    """Longest flat-derivative run after the hump; flagged if shorter than min_cycles."""
    lt = np.log10(t)
    after = np.arange(len(t)) > np.nanargmax(np.where(np.isfinite(der), der, -np.inf))
    flat = after & (np.abs(s) < tol)
    runs, cur = [], []
    for i in range(len(t)):
        if flat[i]:
            cur.append(i)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    best = max(runs, key=len) if runs else None
    developed = best is not None and lt[best[-1]] - lt[best[0]] >= min_cycles
    if not developed:
        cand = [(np.nanmean(np.abs(s[after & (lt >= lt[i]) & (lt <= lt[i] + min_cycles)])), i)
                for i in np.where(after & np.isfinite(s))[0] if lt[i] + min_cycles <= lt[-1]]
        i0 = min(cand)[1]
        best = list(np.where(after & (lt >= lt[i0]) & (lt <= lt[i0] + min_cycles))[0])
    return t[best[0]], t[best[-1]], developed


def window_B(t, der, s, tol=0.10, cycles=0.3):
    """Late radial-flow points: the last 0.3 log-cycle of the window-A plateau (boundary points excluded)."""
    t0, t1, developed = window_A(t, der, s, tol, cycles)
    if not developed:
        return t0, t1, False, True
    start = max(t0, t1 / 10 ** cycles)
    with warnings.catch_warnings():   # all-NaN tail slopes are expected at the very end of a build-up
        warnings.simplefilter("ignore", RuntimeWarning)
        boundary_after = t1 < t[-1] * 0.999 and np.nanmin(s[t > t1]) < -tol if (t > t1).any() else False
    return start, t1, bool(boundary_after), False


def rock(P):
    return dict(h=P.net_pay_thickness_ft, phi=P.porosity_frac, ct=P.total_compressibility_1_psi,
                rw=P.wellbore_radius_ft, B=P.oil_fvf_rb_stb, mu=P.oil_viscosity_cp)


def fluid_gradient(w, tests_raw, comp, pvt):
    """Liquid gradient below the gauge, psi/ft, from test-average API, Rs, salinity and water cut."""
    t = tests_raw[tests_raw.well_name == w][["oil_gravity_api", "gas_sg", "water_salinity_ppm", "water_cut_pct"]].mean()
    go = 141.5 / (131.5 + t.oil_gravity_api)
    rho_o = (62.4 * go + 0.0136 * comp.loc[w, "solution_gor_at_pb_scf_stb"] * t.gas_sg) / pvt.loc[w, "oil_fvf_rb_stb"]
    rho_w = 62.4 * (1 + 0.695e-6 * t.water_salinity_ppm)
    wc = t.water_cut_pct / 100
    return ((1 - wc) * rho_o + wc * rho_w) / 144


def interpret(ev, hf, pvt, comp, rates, tests_raw, window="B"):
    """Horner analysis of one build-up, using our predicted daily oil rate as q."""
    P = pvt.loc[ev.well]
    g = hf[(hf.well_name == ev.well) & (hf.timestamp >= ev.start - pd.Timedelta("12h")) &
           (hf.timestamp <= ev.end)].set_index("timestamp").dh_pressure_psia
    history = g.dropna()
    g = g.loc[ev.start - pd.Timedelta("2h"):]
    pwf = g.loc[:ev.start].dropna().iloc[-1]
    b = g.loc[ev.start + pd.Timedelta("1min"): ev.end - pd.Timedelta("1min")].dropna()
    dt = (b.index - ev.start).total_seconds().to_numpy() / 3600
    p = b.to_numpy()
    d = rates[rates.well_name == ev.well].assign(t=lambda x: pd.to_datetime(x.timestamp)).set_index("t").oil_rate_stbd
    day = ev.start.normalize()
    q = float(d.loc[day - pd.Timedelta("1D")])
    Np = comp.loc[ev.well, "cum_oil_at_2025_01_01_stb"] + float(
        d.loc[:day - pd.Timedelta("1D")].sum() + q * (ev.start - day).total_seconds() / 86400)
    tp = 24 * Np / q
    h, phi, ct, rw, B, mu = (P.net_pay_thickness_ft, P.porosity_frac, P.total_compressibility_1_psi,
                             P.wellbore_radius_ft, P.oil_fvf_rb_stb, P.oil_viscosity_cp)
    tg, pg = _log_grid(dt, p)
    der = bourdet(np.log(tp * tg / (tp + tg)), pg - pwf)
    s = _deriv_log_slope(tg, der)
    if window == "A":
        t0, t1, developed = window_A(tg, der, s)
    else:
        t0, t1, _, fallback = window_B(tg, der, s)
        developed = not fallback
    win = (dt >= t0) & (dt <= t1)
    hx = np.log10((tp + dt) / dt)
    c1, c0 = np.polyfit(hx[win], p[win], 1)
    m = -c1
    p1hr = c0 + c1 * np.log10(tp + 1.0)
    k = 162.6 * q * B * mu / (m * h)
    S = 1.151 * ((p1hr - pwf) / m - np.log10(k / (phi * mu * ct * rw ** 2)) + 3.2275)
    dps = 0.869 * m * S
    datum = None
    if tests_raw is not None and (tests_raw.well_name == ev.well).any():
        datum = fluid_gradient(ev.well, tests_raw, comp, pvt) * (P.datum_tvd_ft - comp.loc[ev.well, "gauge_tvd_ft"])
    early = dt <= 3 / 60 + 1e-9
    C = float(np.median(q * B * dt[early] / (24 * (p[early] - pwf)))) if early.any() else np.nan
    res = dict(well_name=ev.well, shut_in_start=ev.start, shut_in_end=ev.end, duration_h=round(dt.max(), 2),
               window_start_h=round(t0, 3), window_end_h=round(t1, 3),
               note="Radial flow developed" if developed else "Radial flow not clearly developed (flattest 0.3 log-cycle used)",
               qo_stbd=round(q, 1), np_stb=round(Np), tp_h=round(tp, 1), pwf_gauge_psia=round(pwf, 2),
               horner_slope_psi_per_cycle=round(m, 3), permeability_md=round(k, 2), skin=round(S, 3),
               delta_p_skin_psi=round(dps, 2), p1hr_gauge_psia=round(p1hr, 2), p_star_gauge_psia=round(c0, 2),
               p_star_datum_psia=round(c0 + datum, 2) if datum is not None else None,
               storage_bbl_per_psi=round(C, 4), flow_efficiency=round((c0 - pwf - dps) / (c0 - pwf), 3),
               r_inv_ft=round(0.0325 * np.sqrt(k * dt.max() / (phi * mu * ct))), developed=developed)
    plot = dict(dt=dt, p=p, tg=tg, dpg=pg - pwf, der=der, hx=hx, win=win, c0=c0, c1=c1, pwf=pwf, tp=tp,
                t0=t0, t1=t1, history=history, start=ev.start, end=ev.end)
    return res, plot


def model_match(ev, hf, pvt, comp, rates, tests_raw):
    """The submitted answer: exact model match (storage + skin + radial, infinite or closed circle) on the
    log-grid build-up, seeded by Horner window B with the same q and tp (as ml/eda/pta_explore.py)."""
    rB, plot = interpret(ev, hf, pvt, comp, rates, tests_raw, "B")
    rk = rock(pvt.loc[ev.well])
    re0 = np.sqrt(pvt.loc[ev.well, "estimated_drainage_area_acres"] * 43560 / np.pi)
    best, _, _ = PM.fit_best(plot["tg"], plot["dpg"], rB["tp_h"], rB["qo_stbd"], rk,
                             rB["permeability_md"], rB["skin"], rB["storage_bbl_per_psi"], re0)
    tg, tp = plot["tg"], rB["tp_h"]
    mdp = PM.buildup_dp(best["theta"], tg, tp, rB["qo_stbd"], rk, best["boundary"])
    k, S, m, dps = best["k"], best["S"], best["m"], best["dP_skin"]
    pstar, pwf = rB["p_star_gauge_psia"], rB["pwf_gauge_psia"]
    res = {**rB, "horner_slope_psi_per_cycle": round(m, 3), "permeability_md": round(k, 2), "skin": round(S, 3),
           "delta_p_skin_psi": round(dps, 2), "flow_efficiency": round((pstar - pwf - dps) / (pstar - pwf), 3),
           "boundary": best["boundary"], "r_e_ft": round(best["re"]) if best["boundary"] == "closed" else None,
           "fit_rms_psi": round(best["rms_psi"], 3), "storage_bbl_per_psi": round(best["C"], 4),
           "k_horner_md": rB["permeability_md"], "skin_horner": rB["skin"],
           "r_inv_ft": round(0.0325 * np.sqrt(k * rB["duration_h"] / (rk["phi"] * rk["mu"] * rk["ct"])))}
    plot.update(mdp=mdp, mder=bourdet(np.log(tp * tg / (tp + tg)), mdp))
    return res, plot


def explain(r: dict) -> list[str]:
    """Plain-language reading of one build-up, for engineers who are not PTA specialists."""
    out = []
    k = r["permeability_md"]
    grade = "low" if k < 10 else "moderate" if k < 100 else "high"
    out.append(f"Permeability is about **{k:.0f} md** ({grade}), from a model match of the whole build-up "
               f"(fit error {r['fit_rms_psi']:.2f} psi RMS); the implied Horner slope is {r['horner_slope_psi_per_cycle']:.1f} psi per log cycle.")
    if r.get("boundary") == "closed":
        out.append(f"The late build-up shows a **closed boundary** at about {r['r_e_ft']:,.0f} ft (drainage limit reached).")
    S, dps, fe = r["skin"], r["delta_p_skin_psi"], r["flow_efficiency"]
    if S > 0.5:
        out.append(f"Skin is **+{S:.1f}**: the near-wellbore zone is **damaged**. About {dps:.0f} psi is lost across it, "
                   f"and the well flows at roughly {fe:.0%} of its undamaged potential. **Candidate for a stimulation review.**")
    elif S < -0.5:
        out.append(f"Skin is **{S:.1f}**: the near-wellbore zone is **stimulated** (better than undamaged rock). "
                   f"No damage to remove; flow efficiency {fe:.0%}.")
    else:
        out.append(f"Skin is **{S:.1f}**, close to zero: **no significant damage**.")
    if not r["developed"]:
        out.append("Radial flow did not clearly develop (the derivative never stays flat for 0.3 log cycle). "
                   "The model match still uses every point, but treat permeability and skin as **indicative**.")
    out.append(f"Extrapolated pressure p* is {r['p_star_gauge_psia']:.0f} psia at the gauge"
               + (f" ({r['p_star_datum_psia']:.0f} psia at datum)" if r.get("p_star_datum_psia") else "")
               + f"; the test investigated about {r['r_inv_ft']:,.0f} ft into the reservoir.")
    return out


# --------------------------------------------------------------------------------------------
# Exports and conversion
# --------------------------------------------------------------------------------------------
def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            for col in ws.columns:   # readable column widths
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 48)
    return buf.getvalue()


def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def read_table(name: str, data: bytes, sheet=0) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet) if name.lower().endswith((".xlsx", ".xls")) \
        else pd.read_csv(io.BytesIO(data))
