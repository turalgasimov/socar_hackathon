"""PTA exploration: theory atlas, the six build-ups, and two Horner window choices.

This is the exploratory / hand-calculation reference for Phase 2. It is not the
deliverable pipeline: it writes figures and reference tables to
ml/outputs/figures/pta/ (described in that folder's README.md).

Inputs
  pressure  data/processed/high_freq_clean.parquet  (gauge depth; the cleaning step
            leaves every build-up window untouched, verified minute by minute)
  shut-ins  data/choke_events.csv                    (choke = 0)
  rate      ml/outputs/vfm_S1_routing.csv            (leaderboard champion, oil)
            ml/outputs/vfm_submission.csv            (S0, rate-sensitivity only)
  rock/PVT  data/reservoir_pvt.csv, data/well_completion.csv

Conventions
  q      VFM oil rate of the last FULL flowing day before the shut-in
  Np     cum_oil_at_2025_01_01 + VFM daily oil up to the shut-in time
  tp     24 * Np / q   (Horner pseudo-producing time, hours)
  pwf    last flowing gauge reading at the shut-in minute
  dP'    Bourdet derivative w.r.t. ln of Agarwal time tp*dt/(tp+dt), L = 0.10
  Window A  longest run after the storage hump where the derivative's log-slope
            is within +-0.10 (the IARF plateau)
  Window B  "late points": the last 0.3 log-cycle of the IARF plateau found by A.
            With no boundary these are the last points of the build-up; where a
            closed boundary bends the derivative down (p-bar regime), the window
            stops where the plateau stops. No 0.3-cycle plateau -> B = A, flagged.

Run:  python ml/eda/pta_explore.py      (~40 s)
"""
from __future__ import annotations

import sys
from math import factorial, log
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import ive, kve

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import viz  # noqa: E402
from config import F_CHOKE, F_COMPLETION, F_HF_CLEAN, F_PVT, FIGS, OUT  # noqa: E402

PTA_DIR = FIGS / "pta"
PTA_DIR.mkdir(parents=True, exist_ok=True)
EPOCH = pd.Timestamp("2025-01-01")


# =============================================================================
# 1. Theory: analytical type curves (Laplace solutions + Stehfest inversion)
# =============================================================================
def _stehfest(N=12):
    v = np.zeros(N)
    for i in range(1, N + 1):
        s = 0.0
        for k in range((i + 1) // 2, min(i, N // 2) + 1):
            s += k ** (N // 2) * factorial(2 * k) / (factorial(N // 2 - k) * factorial(k) * factorial(k - 1)
                                                      * factorial(i - k) * factorial(2 * k - i))
        v[i - 1] = (-1) ** (N // 2 + i) * s
    return v


_V = _stehfest()


def _invert(F, t):
    return np.array([log(2) / tt * sum(_V[i] * F((i + 1) * log(2) / tt) for i in range(len(_V))) for tt in t])


def _infinite(s):
    b = np.sqrt(s)
    return kve(0, b) / (s * b * kve(1, b))


def _closed(reD):
    def f(s):
        b = np.sqrt(s); a = b * reD
        R = kve(1, a) / ive(1, a) * np.exp(-2 * (a - b))
        return (kve(0, b) + R * ive(0, b)) / (s * b * (kve(1, b) - R * ive(1, b)))
    return f


def _const_p(reD):
    def f(s):
        b = np.sqrt(s); a = b * reD
        R = kve(0, a) / ive(0, a) * np.exp(-2 * (a - b))
        return (kve(0, b) - R * ive(0, b)) / (s * b * (kve(1, b) + R * ive(1, b)))
    return f


def _fault(LD):
    return lambda s: _infinite(s) + kve(0, 2 * LD * np.sqrt(s)) * np.exp(-2 * LD * np.sqrt(s)) / s


def _channel(WD, n=60):
    def f(s):
        b = np.sqrt(s)
        return _infinite(s) + 2 * sum(kve(0, k * WD * b) * np.exp(-k * WD * b) for k in range(1, n + 1)) / s
    return f


def _dual_porosity(omega, lam):
    def f(s):
        fs = (omega * (1 - omega) * s + lam) / ((1 - omega) * s + lam)
        b = np.sqrt(s * fs)
        return kve(0, b) / (s * b * kve(1, b))
    return f


def _storage_skin(pD0, CD, S):
    return lambda s: (s * pD0(s) + S) / (s * (1 + CD * s * (s * pD0(s) + S)))


def bourdet(x, p, L=0.10):
    """Bourdet derivative dp/dx with a +-L window in x (x = ln time)."""
    d = np.full(len(p), np.nan)
    for i in range(len(p)):
        l = np.where(x <= x[i] - L)[0]; r = np.where(x >= x[i] + L)[0]
        if len(l) and len(r):
            j, k = l[-1], r[0]
            d1 = (p[i] - p[j]) / (x[i] - x[j]); d2 = (p[k] - p[i]) / (x[k] - x[i])
            d[i] = (d1 * (x[k] - x[i]) + d2 * (x[i] - x[j])) / (x[k] - x[j])
    return d


def theory_figures():
    CD, S = 1000.0, 3.0
    tD = np.logspace(-1, 8.3, 260)
    x = tD / CD

    def drawdown(model):
        p = _invert(_storage_skin(model, CD, S), tD)
        return bourdet(np.log(tD), p, 0.12)

    def buildup(model, tpD):
        F = _storage_skin(model, CD, S)
        p_tp = _invert(F, np.array([tpD]))[0]
        p = _invert(F, tD) - (_invert(F, tpD + tD) - p_tp)
        return bourdet(np.log(tpD * tD / (tpD + tD)), p, 0.12)

    p_inf = _invert(_storage_skin(_infinite, CD, S), tD)
    d_inf = bourdet(np.log(tD), p_inf, 0.12)
    reD = 3000.0
    panels = [
        ("1. Homogeneous, infinite-acting", [("Δp", p_inf, viz.BLUE, "-"), ("Δp′", d_inf, viz.ORANGE, "-")],
         ["WBS: Δp and Δp′ on one unit-slope line", "hump: skin × storage", "IARF: Δp′ flat (= 0.5 here) → m, k"]),
        ("2. Closed circle: drawdown vs build-up", [("Δp′ drawdown", drawdown(_closed(reD)), viz.ORANGE, "-"),
                                                    ("Δp′ build-up", buildup(_closed(reD), 5e8), viz.BLUE, "-")],
         ["drawdown: PSS → Δp′ unit slope", "build-up: Δp′ falls → p̄ reached", "same reservoir, opposite late shape"]),
        ("3. Constant-pressure boundary", [("Δp′", drawdown(_const_p(reD)), viz.ORANGE, "-"),
                                           ("Δp′ infinite", d_inf, viz.BLUE, ":")],
         ["Δp′ drops sharply, also in drawdown", "pressure stabilises at the boundary value"]),
        ("4. One sealing fault", [("Δp′", drawdown(_fault(800.0)), viz.ORANGE, "-"), ("Δp′ infinite", d_inf, viz.BLUE, ":")],
         ["Δp′ doubles: second IARF level = 2 × first", "fault distance from the time of the step"]),
        ("5. Channel (two parallel faults)", [("Δp′", drawdown(_channel(1500.0)), viz.ORANGE, "-"),
                                              ("Δp′ infinite", d_inf, viz.BLUE, ":")],
         ["late linear flow: Δp′ slope ½", "channel width from the ½-slope level"]),
        ("6. Dual porosity (fissures + matrix)", [("Δp′", drawdown(_dual_porosity(0.05, 2e-6)), viz.ORANGE, "-"),
                                                  ("Δp′ homogeneous", d_inf, viz.BLUE, ":")],
         ["valley between two IARF levels", "ω: valley depth · λ: valley time"]),
    ]
    fig, axs = plt.subplots(2, 3, figsize=(14, 8.6))
    for ax, (title, series, notes) in zip(axs.ravel(), panels):
        for lab, y, col, ls in series:
            m = np.isfinite(y) & (y > 1e-3)
            ax.loglog(x[m], y[m], ls, color=col, lw=1.8, label=lab)
        ax.loglog(x, x, color=viz.INK_MUTED, lw=0.8, ls="--")
        ax.axhline(0.5, color=viz.INK_MUTED, lw=0.8, ls="--")
        ax.set_xlim(1e-2, 1e5); ax.set_ylim(5e-2, 60)
        ax.set_title(title); ax.set_xlabel("t_D / C_D"); ax.set_ylabel("p_D ,  t_D · dp_D/dt_D")
        ax.legend(loc="lower right")
        ax.text(0.02, 0.98, "\n".join("• " + n for n in notes), transform=ax.transAxes, va="top", ha="left",
                fontsize=7.6, color=viz.INK_2)
    viz.titled(fig, "Flow-regime atlas: what each reservoir does to the log-log derivative",
               f"Analytical solutions (Laplace + Stehfest), C_D = {CD:.0f}, skin = {S:.0f}. "
               "Dashed: unit slope (WBS) and the IARF level 0.5.")
    viz.save(fig, PTA_DIR / "pta_00_theory_flow_regime_atlas.png")

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for Sk, col in zip([-2, 0, 5, 12], [viz.SEQ[2], viz.SEQ[4], viz.SEQ[6], viz.SEQ[7]]):
        # negative skin through the effective wellbore radius: C_D -> C_D e^(2S), S -> 0
        model = _storage_skin(_infinite, CD * np.exp(2 * Sk), 0.0) if Sk < 0 else _storage_skin(_infinite, CD, Sk)
        tDk = tD * np.exp(2 * Sk) if Sk < 0 else tD
        p = _invert(model, tDk)
        ax.loglog(x, bourdet(np.log(tDk), p, 0.12), color=col, lw=1.8, label=f"S = {Sk}")
        ax.loglog(x, p, color=col, lw=0.9, ls=":")
    ax.loglog(x, x, color=viz.INK_MUTED, lw=0.8, ls="--"); ax.axhline(0.5, color=viz.INK_MUTED, lw=0.8, ls="--")
    ax.set_xlim(1e-2, 1e4); ax.set_ylim(5e-2, 60)
    ax.set_xlabel("t_D / C_D"); ax.set_ylabel("p_D (dotted) ,  derivative (solid)")
    ax.legend(title="skin", loc="lower right")
    viz.titled(fig, "Skin sets the height of the storage hump",
               "Same storage, different skin: the hump grows with C_D·e^(2S); the IARF level (0.5) does not move, so k is skin-free.")
    viz.save(fig, PTA_DIR / "pta_01_theory_skin_storage_hump.png")


# =============================================================================
# 2. Data
# =============================================================================
HF = pd.read_parquet(F_HF_CLEAN, columns=["timestamp", "well_name", "dh_pressure_psia"])
CHOKE = pd.read_csv(F_CHOKE, parse_dates=["timestamp"])
PVT = pd.read_csv(F_PVT).set_index("well_name")
COMP = pd.read_csv(F_COMPLETION).set_index("well_name")
PRED = {name: pd.read_csv(OUT / f, parse_dates=["timestamp"])
        for name, f in [("S1", "vfm_S1_routing.csv"), ("S0", "vfm_submission.csv")]}
TESTS = pd.read_csv(Path(F_PVT).parent / "well_tests.csv")


def shut_in_events() -> pd.DataFrame:
    ev = []
    for w, c in CHOKE.groupby("well_name"):
        c = c.sort_values("timestamp").reset_index(drop=True)
        for i, r in c.iterrows():
            if r.choke_opening_pct == 0:
                prev = c[(c.timestamp < r.timestamp) & (c.choke_opening_pct > 0)]
                ev.append(dict(well=w, start=r.timestamp, end=c.timestamp[i + 1], last_change=prev.timestamp.iloc[-1]))
    return pd.DataFrame(ev)


def rate_and_np(w, start, pred="S1"):
    d = PRED[pred][PRED[pred].well_name == w].set_index("timestamp").oil_rate_stbd
    day = start.normalize()
    q = float(d.loc[day - pd.Timedelta("1D")])
    np_2025 = float(d.loc[:day - pd.Timedelta("1D")].sum() + q * (start - day).total_seconds() / 86400)
    return q, COMP.loc[w, "cum_oil_at_2025_01_01_stb"] + np_2025


def fluid_gradient(w):
    """Liquid gradient below the gauge, psi/ft, from test-average oil API, Rs, salinity and water cut."""
    t = TESTS[TESTS.well_name == w][["oil_gravity_api", "gas_sg", "water_salinity_ppm", "water_cut_pct"]].mean()
    go = 141.5 / (131.5 + t.oil_gravity_api)
    rho_o = (62.4 * go + 0.0136 * COMP.loc[w, "solution_gor_at_pb_scf_stb"] * t.gas_sg) / PVT.loc[w, "oil_fvf_rb_stb"]
    rho_w = 62.4 * (1 + 0.695e-6 * t.water_salinity_ppm)
    wc = t.water_cut_pct / 100
    return ((1 - wc) * rho_o + wc * rho_w) / 144


# =============================================================================
# 3. Build-up interpretation
# =============================================================================
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
            runs.append(cur); cur = []
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
    """Late IARF points: the last 0.3 log-cycle of the IARF plateau (window A's run).

    Where the plateau reaches the end of the data (no boundary) these are simply the
    last points of the build-up. Where a boundary bends the derivative down at late
    time, the last points are p-bar regime, not IARF, so the window stops where the
    plateau stops. If no plateau of 0.3 cycles exists, B falls back to A and is flagged.
    """
    t0, t1, developed = window_A(t, der, s, tol, cycles)
    if not developed:
        return t0, t1, False, True
    start = max(t0, t1 / 10 ** cycles)
    boundary_after = t1 < t[-1] * 0.999 and np.nanmin(s[t > t1]) < -tol if (t > t1).any() else False
    return start, t1, bool(boundary_after), False


def interpret(ev, pred="S1", window="A"):
    P = PVT.loc[ev.well]
    g = HF[(HF.well_name == ev.well) & (HF.timestamp >= ev.start - pd.Timedelta("2h")) &
           (HF.timestamp <= ev.end)].set_index("timestamp").dh_pressure_psia
    pwf = g.loc[:ev.start].dropna().iloc[-1]
    b = g.loc[ev.start + pd.Timedelta("1min"): ev.end - pd.Timedelta("1min")].dropna()
    dt = (b.index - ev.start).total_seconds().to_numpy() / 3600
    p = b.to_numpy()
    q, Np = rate_and_np(ev.well, ev.start, pred)
    tp = 24 * Np / q
    h, phi, ct, rw, B, mu = (P.net_pay_thickness_ft, P.porosity_frac, P.total_compressibility_1_psi,
                             P.wellbore_radius_ft, P.oil_fvf_rb_stb, P.oil_viscosity_cp)
    tg, pg = _log_grid(dt, p)
    der = bourdet(np.log(tp * tg / (tp + tg)), pg - pwf)
    s = _deriv_log_slope(tg, der)
    if window == "A":
        t0, t1, flag = window_A(tg, der, s)
        note = "IARF plateau" if flag else "IARF not clearly developed (flattest 0.3 cycle used)"
    else:
        t0, t1, boundary_after, fallback = window_B(tg, der, s)
        note = ("no 0.3-cycle IARF plateau: same window as A" if fallback else
                "last 0.3 log-cycle of the IARF plateau" + ("; later boundary points excluded" if boundary_after else
                                                             " (= last points of the build-up)"))
    win = (dt >= t0) & (dt <= t1)
    hx = np.log10((tp + dt) / dt)
    c1, c0 = np.polyfit(hx[win], p[win], 1)
    m = -c1
    p1hr = c0 + c1 * np.log10(tp + 1.0)
    k = 162.6 * q * B * mu / (m * h)
    S = 1.151 * ((p1hr - pwf) / m - np.log10(k / (phi * mu * ct * rw ** 2)) + 3.2275)
    dps = 0.869 * m * S
    G = fluid_gradient(ev.well)
    dz = P.datum_tvd_ft - COMP.loc[ev.well, "gauge_tvd_ft"]
    early = dt <= 3 / 60 + 1e-9
    C = float(np.median(q * B * dt[early] / (24 * (p[early] - pwf))))
    res = dict(well_name=ev.well, shut_in_start=ev.start, shut_in_end=ev.end, duration_h=round(dt.max(), 2),
               window=window, window_start_h=round(t0, 3), window_end_h=round(t1, 3), note=note,
               rate_source=pred, qo_stbd=round(q, 1), np_stb=round(Np), tp_h=round(tp, 1), pwf_gauge_psia=round(pwf, 2),
               horner_slope_psi_per_cycle=round(m, 3), permeability_md=round(k, 2), skin=round(S, 3),
               delta_p_skin_psi=round(dps, 2), p1hr_gauge_psia=round(p1hr, 2), p_star_gauge_psia=round(c0, 2),
               p_end_gauge_psia=round(p[-1], 2), datum_offset_psi=round(G * dz, 1),
               p_star_datum_psia=round(c0 + G * dz, 2), m_from_derivative=round(2.303 * np.nanmedian(der[(tg >= t0) & (tg <= t1)]), 3),
               storage_bbl_per_psi=round(C, 4), flow_efficiency=round((c0 - pwf - dps) / (c0 - pwf), 3),
               r_inv_ft=round(0.0325 * np.sqrt(k * dt.max() / (phi * mu * ct))))
    plot = dict(dt=dt, p=p, tg=tg, dpg=pg - pwf, der=der, hx=hx, win=win, c0=c0, c1=c1)
    return res, plot


def event_figure(ev, rA, pA, rB):
    fig, ax = plt.subplots(2, 3, figsize=(15.5, 8.8))
    w = ev.well
    g = HF[(HF.well_name == w) & (HF.timestamp >= ev.start - pd.Timedelta("24h")) &
           (HF.timestamp <= ev.end + pd.Timedelta("6h"))]
    a = ax[0, 0]
    a.plot(g.timestamp, g.dh_pressure_psia, color=viz.BLUE, lw=1.2)
    a.axvspan(ev.start, ev.end, color=viz.GRID, alpha=0.8, lw=0)
    a.set_title("A. Pressure history (gauge depth)"); a.set_ylabel("p, psia"); a.tick_params(axis="x", labelrotation=25)
    a.text(0.02, 0.96, f"shaded = shut-in ({rA['duration_h']:.1f} h)\nq before shut-in (VFM S1) = {rA['qo_stbd']:.0f} stb/d",
           transform=a.transAxes, va="top", fontsize=8, color=viz.INK_2)
    a = ax[0, 1]
    a.plot(pA["dt"], pA["p"], color=viz.BLUE, lw=1.4)
    a.axhline(rA["p_star_gauge_psia"], color=viz.INK_MUTED, ls="--", lw=0.9)
    a.text(pA["dt"].max(), rA["p_star_gauge_psia"], " p* (Horner, window A)", va="bottom", ha="right", fontsize=8, color=viz.INK_2)
    a.set_title("B. Cartesian build-up"); a.set_xlabel("Δt, h"); a.set_ylabel("p_ws, psia")
    a = ax[0, 2]
    ok = np.isfinite(pA["der"]) & (pA["der"] > 0)
    a.loglog(pA["tg"], pA["dpg"], "o", ms=3, color=viz.BLUE, label="Δp")
    a.loglog(pA["tg"][ok], pA["der"][ok], "o", ms=3, color=viz.ORANGE, label="Δp′ (Bourdet)")
    a.axvspan(rA["window_start_h"], rA["window_end_h"], color=viz.GRID, alpha=0.9, lw=0)
    a.axvspan(rB["window_start_h"], rB["window_end_h"], facecolor="none", edgecolor=viz.INK_2, hatch="///", lw=0.6)
    a.axhline(rA["horner_slope_psi_per_cycle"] / 2.303, color=viz.INK_MUTED, ls="--", lw=0.9)
    xs = np.array([pA["tg"].min(), pA["tg"].min() * 30])
    a.loglog(xs, pA["dpg"][0] * xs / pA["tg"][0], color=viz.INK_MUTED, ls=":", lw=1)
    a.set_title("C. Log-log diagnostic"); a.set_xlabel("Δt, h"); a.set_ylabel("Δp, Δp′ (psi)")
    a.legend(loc="lower center")
    a.text(0.02, 0.96, f"grey = window A {rA['window_start_h']:g}–{rA['window_end_h']:g} h\n"
                       f"hatched = window B {rB['window_start_h']:g}–{rB['window_end_h']:g} h\n"
                       f"- - IARF level m/2.303 · ··· unit slope (WBS)",
           transform=a.transAxes, va="top", fontsize=8, color=viz.INK_2)
    a = ax[1, 0]
    hx, win = pA["hx"], pA["win"]
    a.semilogx(10 ** hx, pA["p"], "o", ms=2, color=viz.SEQ[2])
    a.semilogx(10 ** hx[win], pA["p"][win], "o", ms=2.5, color=viz.BLUE)
    xx = np.linspace(0, hx.max(), 50)
    a.semilogx(10 ** xx, pA["c0"] + pA["c1"] * xx, color=viz.ORANGE, lw=1.4)
    a.invert_xaxis()
    a.set_title("D. Horner plot (window A line)"); a.set_xlabel("(t_p + Δt) / Δt"); a.set_ylabel("p_ws, psia")
    a.text(0.02, 0.96, f"m = {rA['horner_slope_psi_per_cycle']:.2f} psi/cycle\np* = {rA['p_star_gauge_psia']:.1f} psia\n"
                       f"P1hr = {rA['p1hr_gauge_psia']:.1f} psia", transform=a.transAxes, va="top", fontsize=8, color=viz.INK_2)
    a = ax[1, 1]
    a.semilogx(pA["dt"], pA["p"], "o", ms=2, color=viz.SEQ[2])
    a.semilogx(pA["dt"][win], pA["p"][win], "o", ms=2.5, color=viz.BLUE)
    m_mdh = np.polyfit(np.log10(pA["dt"][win]), pA["p"][win], 1)[0]
    a.set_title("E. MDH plot"); a.set_xlabel("Δt, h"); a.set_ylabel("p_ws, psia")
    a.text(0.02, 0.96, f"MDH slope = {m_mdh:.2f} psi/cycle\n(t_p ≫ Δt, so MDH ≈ Horner)", transform=a.transAxes,
           va="top", fontsize=8, color=viz.INK_2)
    a = ax[1, 2]; a.axis("off")
    rows = [("", "window A", "window B"),
            ("window, h", f"{rA['window_start_h']:g}–{rA['window_end_h']:g}", f"{rB['window_start_h']:g}–{rB['window_end_h']:g}"),
            ("Horner slope m, psi/cycle", f"{rA['horner_slope_psi_per_cycle']:.2f}", f"{rB['horner_slope_psi_per_cycle']:.2f}"),
            ("k, md", f"{rA['permeability_md']:.1f}", f"{rB['permeability_md']:.1f}"),
            ("skin S", f"{rA['skin']:.2f}", f"{rB['skin']:.2f}"),
            ("ΔP_skin, psi", f"{rA['delta_p_skin_psi']:.1f}", f"{rB['delta_p_skin_psi']:.1f}"),
            ("p* gauge, psia", f"{rA['p_star_gauge_psia']:.1f}", f"{rB['p_star_gauge_psia']:.1f}"),
            ("q_o (VFM S1), stb/d", f"{rA['qo_stbd']:.0f}", ""), ("t_p = 24·N_p/q, h", f"{rA['tp_h']:,.0f}", ""),
            ("p_wf(Δt=0), psia", f"{rA['pwf_gauge_psia']:.1f}", ""), ("C (unit slope), bbl/psi", f"{rA['storage_bbl_per_psi']:.4f}", "")]
    a.table(cellText=rows, colWidths=[0.5, 0.25, 0.25], loc="upper left", edges="horizontal")
    a.set_title("F. Results")
    a.text(0.0, 0.02, f"A: {rA['note']}\nB: {rB['note']}", transform=a.transAxes, fontsize=7.5, color=viz.INK_2, va="bottom")
    viz.titled(fig, f"{w} build-up, shut-in {ev.start:%Y-%m-%d %H:%M} ({rA['duration_h']:.1f} h)",
               f"Window A: m {rA['horner_slope_psi_per_cycle']:.1f} psi/cycle → k {rA['permeability_md']:.0f} md, "
               f"S {rA['skin']:.2f}.  Window B: m {rB['horner_slope_psi_per_cycle']:.1f} → k {rB['permeability_md']:.0f} md, "
               f"S {rB['skin']:.2f}.  Rate: VFM S1.")
    viz.save(fig, PTA_DIR / f"pta_10_{w}_{ev.start:%Y-%m-%d}_buildup_all_plots.png")


def overview_figure(ev_tab, plots, resA):
    verdict = {"GL-08": "infinite-acting · clean IARF", "GL-02": "short (5.6 h)", "GL-06": "short (8 h)",
               "GL-04": "long storage hump", "GL-01": "closed boundary · Δp′ falls → p̄", "GL-10": "short + boundary"}
    fig, axs = plt.subplots(2, 3, figsize=(14, 8))
    for ax, w in zip(axs.ravel(), ["GL-08", "GL-02", "GL-06", "GL-04", "GL-01", "GL-10"]):
        pp, rr = plots[w], resA[w]
        ok = np.isfinite(pp["der"]) & (pp["der"] > 0)
        ax.loglog(pp["tg"], pp["dpg"], "o", ms=2.6, color=viz.BLUE, label="Δp")
        ax.loglog(pp["tg"][ok], pp["der"][ok], "o", ms=2.6, color=viz.ORANGE, label="Δp′")
        ax.axvspan(rr["window_start_h"], rr["window_end_h"], color=viz.GRID, alpha=0.8, lw=0)
        ax.axhline(rr["horner_slope_psi_per_cycle"] / 2.303, color=viz.INK_MUTED, ls="--", lw=0.8)
        ax.set_xlim(1e-2, 1e2); ax.set_ylim(0.5, 2e3)
        ax.set_title(f"{w}: {verdict[w]}"); ax.set_xlabel("Δt, h"); ax.set_ylabel("Δp, Δp′ (psi)")
        ax.text(0.98, 0.96, f"m {rr['horner_slope_psi_per_cycle']:.1f} · k {rr['permeability_md']:.0f} md · S {rr['skin']:.2f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=8, color=viz.INK_2)
        if w == "GL-08":
            ax.legend(loc="lower left")
    viz.titled(fig, "Six build-ups, one diagnostic: which flow regimes each shut-in reaches",
               "Shaded: window A (IARF plateau) used for the Horner line. Dashed: IARF derivative level m/2.303. Rate = VFM S1.")
    viz.save(fig, PTA_DIR / "pta_02_overview_six_buildups_loglog.png")


def main():
    viz.apply_style()
    theory_figures()
    ev = shut_in_events()
    A, B, A0, plots, resA = [], [], [], {}, {}
    for e in ev.itertuples():
        rA, pA = interpret(e, "S1", "A")
        rB, _ = interpret(e, "S1", "B")
        r0, _ = interpret(e, "S0", "A")
        event_figure(e, rA, pA, rB)
        A.append(rA); B.append(rB); A0.append(r0); plots[e.well] = pA; resA[e.well] = rA
    overview_figure(ev, plots, resA)
    tA, tB, t0 = pd.DataFrame(A), pd.DataFrame(B), pd.DataFrame(A0)
    tA.to_csv(PTA_DIR / "pta_reference_window_A.csv", index=False)
    tB.to_csv(PTA_DIR / "pta_reference_window_B.csv", index=False)
    show = ["well_name", "window_start_h", "window_end_h", "horner_slope_psi_per_cycle", "permeability_md", "skin",
            "delta_p_skin_psi", "p_star_gauge_psia", "note"]
    pd.set_option("display.width", 220)
    print("\nWindow A (IARF plateau), rate S1:\n" + tA[show].to_string(index=False))
    print("\nWindow B (late IARF points), rate S1:\n" + tB[show].to_string(index=False))
    sens = pd.DataFrame({"well": tA.well_name, "k_S1": tA.permeability_md, "k_S0": t0.permeability_md,
                         "dk_pct": (tA.permeability_md / t0.permeability_md - 1) * 100, "dS": tA.skin - t0.skin})
    print("\nRate sensitivity, window A (S1 vs S0):\n" + sens.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
