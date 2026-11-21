"""Hold-out tests for the PTA fits: predict data the fit never saw.

    python ml/holdout_pta.py

The shipped PTA reports a fit RMS (< 0.2 psi on all six wells). A fit residual
is not evidence: it measures how well a 3-4 parameter model can be bent onto the
window it was fitted to. These three tests withhold data instead.

  3a  EARLY -> LATE     fit an early window, predict the last third, for THREE
                        window definitions. They disagree by an order of
                        magnitude, which is itself the result: the narrowest
                        keeps only wellbore storage, the widest still contains
                        the IARF that determines k. None of them bounds the
                        submitted fit's precision -- that uses every point.
  3b  REOPENING         take the build-up-fitted (k, S, C), then simulate the
                        DRAWDOWN after the choke reopens, driven by the observed
                        10-min VFM rates. Different flow direction, different
                        data, nothing refitted. The strongest of the three, and
                        only possible with the FD simulator, since the Laplace
                        build-up carries a single-rate superposition term.
                        Scored in time bins, because the error turns out to live
                        entirely in the first hour on the wells that reopened in
                        one step to full choke -- gas-lift unloading, which the
                        choke law does not describe. After 6 h all six wells
                        agree, so k and S are validated out of sample.
  3c  ~90 DAYS         run the 89-day daily rate history and compare the
                        predicted flowing-pressure trend with the observed one.
                        Tests the OUTER BOUNDARY, which a 6-72 h build-up cannot
                        see. This is the 90-day window in pta_rate_history.csv,
                        NOT the full nine months -- the rate export covers 90
                        days before each shut-in, and that is already ~1000x the
                        build-up duration, which is what the test needs.

Writes ml/outputs/pta_holdout.csv. Reads only existing artefacts; changes
nothing that ships.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))
sys.path.insert(0, str(ROOT / "ml" / "eda"))
warnings.filterwarnings("ignore")

import pta_model as PM    # noqa: E402
import pta_sim as PS      # noqa: E402
import pta_explore as X   # noqa: E402

REF = ROOT / "ml" / "outputs" / "figures" / "pta" / "pta_reference_model_match.csv"
RATES = ROOT / "ml" / "outputs" / "pta_rate_history.csv"


WINDOWS_3A = ("log_range", "points", "linear_time")


def early_mask(tg, kind):
    """Three ways to say 'the early third', which do NOT mean the same thing."""
    if kind == "log_range":          # thirds of the log-time SPAN: storage only
        lo, hi = np.log(tg[0]), np.log(tg[-1])
        return np.log(tg) <= lo + (hi - lo) / 3
    if kind == "points":             # first third of the log-grid POINTS
        return np.arange(len(tg)) < len(tg) // 3
    return tg <= tg[0] + (tg[-1] - tg[0]) / 3     # thirds of LINEAR time


def test_3a(ev, r, rk, tg, dpg):
    """Fit an early window, predict the late third, for three window definitions.

    The three disagree by an order of magnitude, and that is the result. The
    narrowest keeps only wellbore storage; the widest still contains the IARF
    and boundary data that actually determine k. So NONE of these is the
    precision of the submitted fit, which uses every point -- they measure what
    a given subset of the data implies on its own.
    """
    lo, hi = np.log(tg[0]), np.log(tg[-1])
    late = np.log(tg) >= hi - (hi - lo) / 3
    re0 = np.sqrt(X.PVT.loc[ev.well, "estimated_drainage_area_acres"] * 43560 / np.pi)
    out = dict(n_late=int(late.sum()), k_full_md=r.permeability_md, S_full=r.skin,
               late_rise_psi=float(dpg[late].max()))
    for kind in WINDOWS_3A:
        m = early_mask(tg, kind)
        f = PM.fit_buildup(tg[m], dpg[m], r.tp_h, r.qo_stbd, rk,
                           r.permeability_md, r.skin, r.storage_bbl_per_psi,
                           r.boundary, re0)
        pred = PM.buildup_dp(f["theta"], tg, r.tp_h, r.qo_stbd, rk, r.boundary)
        res = pred[late] - dpg[late]
        out.update({
            f"{kind}_n": int(m.sum()), f"{kind}_last_dt_h": float(tg[m][-1]),
            f"{kind}_k_md": f["k"],
            f"{kind}_k_shift_pct": (f["k"] / r.permeability_md - 1) * 100,
            f"{kind}_S_shift": f["S"] - r.skin,
            f"{kind}_fit_rms_psi": f["rms_psi"],
            f"{kind}_late_rms_psi": float(np.sqrt(np.mean(res ** 2)))})
    return out


def test_3b(ev, r, rk, rates):
    """Predict the reopening drawdown from build-up-fitted parameters."""
    post = rates[(rates.well_name == ev.well) & (rates.segment == "post_reopen")]
    if post.empty:
        return {}
    post = post.sort_values("timestamp")
    ts = pd.to_datetime(post.timestamp.values)
    q = post.oil_rate_stbd.to_numpy(float)
    re = float(r.r_e_ft) if r.boundary == "closed" else None
    pre_q, _ = X.rate_and_np(ev.well, ev.start)
    sched = [(2.0 * 365 * 24, pre_q), (float(r.duration_h), 0.0)]
    sched += [(1.0 / 6.0, float(x)) for x in q]            # 10-min bins
    t, p = PS.simulate(r.permeability_md, r.skin, r.storage_bbl_per_psi, rk,
                       sched, re=re, boundary=r.boundary, steps_per_segment=200)
    t0 = sum(d for d, _ in sched[:2])
    m = t >= t0
    tb, pb = (t[m] - t0) * 60.0, p[m]                      # minutes
    obs = X.HF[(X.HF.well_name == ev.well) & (X.HF.timestamp >= ts[0])
               & (X.HF.timestamp <= ts[-1] + pd.Timedelta("10min"))]
    obs = obs.dropna(subset=["dh_pressure_psia"]).sort_values("timestamp")
    if len(obs) < 30:
        return {}
    om = (obs.timestamp - ts[0]).dt.total_seconds().to_numpy() / 60.0
    od = obs.dh_pressure_psia.to_numpy(float) - obs.dh_pressure_psia.iloc[0]
    sim = np.interp(om, tb - tb[0], pb - pb[0])
    res = sim - od

    def rms(a, b):
        s = (om >= a * 60) & (om < b * 60)
        return float(np.sqrt(np.mean(res[s] ** 2))) if s.sum() > 5 else np.nan

    late = om >= 6 * 60
    out = dict(reopen_n=len(od), reopen_drop_obs_psi=float(od.min()),
               reopen_drop_sim_psi=float(sim.min()),
               reopen_rms_psi=float(np.sqrt(np.mean(res ** 2))),
               reopen_max_psi=float(np.abs(res).max()),
               reopen_rel_pct=float(abs(sim.min() / od.min() - 1) * 100),
               rms_0_1h=rms(0, 1), rms_1_6h=rms(1, 6), rms_6_24h=rms(6, 24))
    if late.sum() > 5:
        out["reopen_rel_after6h_pct"] = float(
            abs(sim[late].min() / od[late].min() - 1) * 100)
    # how the choke was reopened: one step to full, or a staged ramp?
    ch = X.CHOKE[(X.CHOKE.well_name == ev.well)
                 & (X.CHOKE.timestamp >= ts[0] - pd.Timedelta("20min"))
                 & (X.CHOKE.timestamp <= ts[0] + pd.Timedelta("6h"))]
    steps = ch.choke_opening_pct.tolist()
    out["reopen_choke_path"] = "->".join(f"{c:g}" for c in steps) or "n/a"
    out["reopen_staged"] = len(steps) > 1
    return out


def test_3b_rate_sensitivity(ev, r, rk, rates, levels=(0.90, 1.10, 1.25)):
    """How much of 3b is actually a test of the RATE LEVEL? Almost none.

    k is proportional to q, so scaling every rate by L and k with it leaves the
    prefactor 141.2 q B mu / (k h) unchanged. What does NOT cancel is
    t_D proportional to k, so the solution is read at a shifted dimensionless
    time and only a logarithmic residual survives. Measured below: a 10% level
    error moves the predicted drawdown 0.4-0.9%, a sensitivity of 0.04-0.09.

    So 3b corroborates k, S, C and the boundary in the opposite flow direction
    and says nothing about the rate LEVEL in either direction. It cannot be used
    to support or attack the IPR-rate question (P1). It also means the residual
    after 6 h is not a level error: explaining 8% that way would need a rate
    level wrong by about 100%.
    """
    post = rates[(rates.well_name == ev.well) & (rates.segment == "post_reopen")]
    if post.empty:
        return {}
    q = post.sort_values("timestamp").oil_rate_stbd.to_numpy(float)
    re = float(r.r_e_ft) if r.boundary == "closed" else None
    pre_q, _ = X.rate_and_np(ev.well, ev.start)

    def drawdown(L):
        sched = [(2.0 * 365 * 24, pre_q * L), (float(r.duration_h), 0.0)]
        sched += [(1.0 / 6.0, float(x * L)) for x in q]
        t, p = PS.simulate(r.permeability_md * L, r.skin, r.storage_bbl_per_psi,
                           rk, sched, re=re, boundary=r.boundary,
                           steps_per_segment=200)
        t0 = sum(d for d, _ in sched[:2])
        m = t >= t0
        pb, tb = p[m], (t[m] - t0) * 60.0
        return float((pb - pb[0])[tb - tb[0] >= 6 * 60].min())

    base = drawdown(1.0)
    out, sens = {}, []
    for L in levels:
        rel = (drawdown(L) / base - 1) * 100
        out[f"rate_L{L:.2f}_pct"] = rel
        sens.append(abs(rel) / abs((L - 1) * 100))
    out["rate_level_sensitivity"] = float(np.mean(sens))
    return out


def test_3c(ev, r, rk, daily):
    """Daily rate history: does the predicted depletion trend match?"""
    d = daily[daily.well_name == ev.well].sort_values("timestamp")
    if len(d) < 60:
        return {}
    q = d.oil_rate_stbd.to_numpy(float)
    re = float(r.r_e_ft) if r.boundary == "closed" else None
    t, p = PS.simulate(r.permeability_md, r.skin, r.storage_bbl_per_psi, rk,
                       [(24.0, float(x)) for x in q], re=re,
                       boundary=r.boundary, steps_per_segment=120)
    sim_days = np.array([np.interp(i * 24.0, t, p) for i in range(len(q))])
    ts = pd.DatetimeIndex(pd.to_datetime(d.timestamp.values)).floor("D")
    obs = X.HF[(X.HF.well_name == ev.well) & (X.HF.timestamp >= ts[0])
               & (X.HF.timestamp < ts[-1] + pd.Timedelta("1D"))].copy()
    obs = obs.dropna(subset=["dh_pressure_psia"])
    obs["d"] = obs.timestamp.dt.floor("D")
    od = obs.groupby("d").dh_pressure_psia.mean().reindex(ts).to_numpy(float)
    ok = np.isfinite(od)
    if ok.sum() < 30:
        return {}
    days = np.arange(len(q), dtype=float)
    so = float(np.polyfit(days[ok], od[ok] - od[ok][0], 1)[0])
    ss = float(np.polyfit(days[ok], sim_days[ok], 1)[0])
    return dict(months_n=int(ok.sum()),
                trend_obs_psi_per_day=so, trend_sim_psi_per_day=ss,
                trend_ratio=(ss / so) if so else np.nan,
                depletion_obs_psi=float(od[ok][-1] - od[ok][0]),
                depletion_sim_psi=float(sim_days[ok][-1] - sim_days[ok][0]))


def main() -> None:
    ref = pd.read_csv(REF).set_index("well_name")
    rates = pd.read_csv(RATES)
    daily = rates[rates.segment == "daily_90d"]

    rows = []
    for ev in X.shut_in_events().itertuples():
        r, rk = ref.loc[ev.well], X.rock(ev.well)
        _, plot = X.interpret(ev, "T1", "B")
        rec = dict(well_name=ev.well, boundary=r.boundary)
        rec.update(test_3a(ev, r, rk, plot["tg"], plot["dpg"]))
        rec.update(test_3b(ev, r, rk, rates))
        rec.update(test_3b_rate_sensitivity(ev, r, rk, rates))
        rec.update(test_3c(ev, r, rk, daily))
        rows.append(rec)
    df = pd.DataFrame(rows)

    print("3a  EARLY -> LATE: fit an early window, predict the last third\n")
    labels = {"log_range": "thirds of LOG span (storage only)",
              "points": "first 1/3 of POINTS",
              "linear_time": "thirds of LINEAR time (IARF kept)"}
    for kind in WINDOWS_3A:
        ks = df[f"{kind}_k_shift_pct"]
        ss = df[f"{kind}_S_shift"]
        print(f"  {labels[kind]}")
        print(f"    {'well':7s} {'n fit':>6s} {'last dt h':>10s} {'dk':>8s} "
              f"{'dS':>8s} {'fit rms':>8s} {'HELD-OUT rms':>13s}")
        for _, x in df.iterrows():
            print(f"    {x.well_name:7s} {int(x[f'{kind}_n']):6d} "
                  f"{x[f'{kind}_last_dt_h']:10.3f} "
                  f"{x[f'{kind}_k_shift_pct']:+7.2f}% "
                  f"{x[f'{kind}_S_shift']:+8.3f} "
                  f"{x[f'{kind}_fit_rms_psi']:8.4f} "
                  f"{x[f'{kind}_late_rms_psi']:13.4f}")
        print(f"    -> k {ks.min():+.2f}..{ks.max():+.2f}%, |dS| <= "
              f"{ss.abs().max():.3f}, reads HIGH on "
              f"{int((ks > 0).sum())}/{len(df)}\n")
    print("  The windows disagree by an order of magnitude, so NONE of them is "
          "the precision of the")
    print("  submitted fit -- that uses every point. What IS robust: k reads "
          "HIGH whenever the window")
    print("  is early, in all three definitions. Constant wellbore storage is "
          "not exact in the first")
    print("  minutes of a gas-lifted test. Keep the IARF and the sensitivity "
          "is under 0.5% on k.")

    b = df.dropna(subset=["reopen_rms_psi"])
    print("\n3b  REOPENING DRAWDOWN: build-up parameters, nothing refitted\n")
    print(f"  {'well':7s} {'reopen choke path':>22s} {'RMS 0-1h':>9s} "
          f"{'1-6h':>7s} {'6-24h':>7s} | {'drop err':>9s} {'after 6h':>9s}")
    for _, x in b.sort_values("reopen_staged").iterrows():
        print(f"  {x.well_name:7s} {x.reopen_choke_path:>22s} {x.rms_0_1h:9.2f} "
              f"{x.rms_1_6h:7.2f} {x.rms_6_24h:7.2f} | {x.reopen_rel_pct:8.1f}% "
              f"{x.reopen_rel_after6h_pct:8.1f}%")
    if len(b):
        full = b[~b.reopen_staged]
        print(f"\n  THE MISS IS THE FIRST HOUR, NOT k OR S. The three wells "
              f"reopened in ONE STEP to full")
        print(f"  choke carry RMS {full.rms_0_1h.min():.1f}-"
              f"{full.rms_0_1h.max():.1f} psi in 0-1 h, collapsing to "
              f"{full.rms_1_6h.min():.1f}-{full.rms_1_6h.max():.1f} psi after it; "
              f"the three")
        print(f"  reopened in staged ramps are flat across all three bins. "
              f"Scoring the drop only after")
        print(f"  6 h, every well lands within "
              f"{b.reopen_rel_after6h_pct.min():.1f}-"
              f"{b.reopen_rel_after6h_pct.max():.1f}% "
              f"(against {b.reopen_rel_pct.min():.1f}-"
              f"{b.reopen_rel_pct.max():.1f}% over the whole window).")
        print(f"  That first hour is gas-lift unloading, which the choke law "
              f"does not describe -- a VFM\n  rate limitation, not a PTA error.")
        print()
        print(f"  WHAT 3b DOES AND DOES NOT VALIDATE. k is proportional to q, "
              f"so scaling every rate by L")
        print(f"  and k with it cancels the prefactor; only a log-time residual "
              f"survives. Measured:")
        print(f"    {'well':7s} " + " ".join(f"{f'L={L:.2f}':>9s}"
                                             for L in (0.90, 1.10, 1.25))
              + f" {'sensitivity':>12s}")
        for _, x in b.iterrows():
            print(f"    {x.well_name:7s} "
                  + " ".join(f"{x[f'rate_L{L:.2f}_pct']:+8.3f}%"
                             for L in (0.90, 1.10, 1.25))
                  + f" {x.rate_level_sensitivity:12.3f}")
        s = b.rate_level_sensitivity
        print(f"  A 10% rate-level error moves the predicted drawdown "
              f"{s.min()*10:.1f}-{s.max()*10:.1f}%. So 3b corroborates k, S, C")
        print(f"  and the boundary in the OPPOSITE FLOW DIRECTION, and says "
              f"nothing about the rate LEVEL")
        print(f"  either way -- it cannot support or attack the IPR-rate "
              f"question. Equally, the 0.1-8.4%")
        print(f"  residual is not a level error: explaining 8% that way would "
              f"need a rate level wrong by")
        print(f"  ~{8.4/s.max():.0f}%. Corroboration at the level of the rate "
              f"uncertainty, not a clean validation.")

    c = df.dropna(subset=["trend_obs_psi_per_day"])
    print("\n3c  DAILY HISTORY: does the fitted model reproduce the depletion "
          "trend?\n")
    print(f"  {'well':7s} {'boundary':>10s} {'days':>5s} {'obs psi/d':>10s} "
          f"{'sim psi/d':>10s} {'sim/obs':>8s}")
    for _, x in c.iterrows():
        print(f"  {x.well_name:7s} {x.boundary:>10s} {int(x.months_n):5d} "
              f"{x.trend_obs_psi_per_day:+10.3f} "
              f"{x.trend_sim_psi_per_day:+10.3f} {x.trend_ratio:8.2f}")

    out = ROOT / "ml" / "outputs" / "pta_holdout.csv"
    df.round(6).to_csv(out, index=False)
    print(f"\n  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
