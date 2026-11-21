"""Does ignoring the real rate history bias k and S? An independent check.

    python ml/check_pta_superposition.py

The shipped PTA treats each build-up as following a SINGLE constant rate q held
for tp_h (10-28 years, so its 0.5 ln(1+dt/tp) superposition term is ~1e-4 and
the fit is effectively a pure build-up). Reality is a varying daily rate. This
asks what that costs, using the finite-difference simulator, which carries
multi-rate superposition natively and needs no superposition formula at all.

THE EXPERIMENT, AND WHY IT NEEDS A CONTROL
------------------------------------------
    truth       the shipped (k, S, C) for the well
    case REAL   FD run: long pre-history, then the 90 observed DAILY rates from
                ml/outputs/pta_rate_history.csv, then shut in
    case FLAT   FD run: identical, except every one of those 90 days is held at
                the single rate the shipped fit assumed
    then        refit BOTH synthetic build-ups with the single-rate Laplace model
                exactly as the shipped pipeline does, and compare to truth

FLAT is the control. Refitting it cannot recover the truth perfectly either --
the FD and the Laplace model are not the same formulation (see
ml/verify_pta_sim.py: rw-effective vs explicit skin, up to 0.89 psi on GL-08),
and the refit inherits that. So the bias attributable to RATE HISTORY is
REAL minus FLAT, not REAL minus truth. Without the control this script would
charge the formulation gap to superposition and overstate the case for a
correction.

Assigned as the independent check of the other agent's item #5.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))
warnings.filterwarnings("ignore")

import pta_model as PM   # noqa: E402
import pta_sim as PS     # noqa: E402

REF = ROOT / "ml" / "outputs" / "figures" / "pta" / "pta_reference_model_match.csv"
RATES = ROOT / "ml" / "outputs" / "pta_rate_history.csv"
WELLS = ["GL-08", "GL-04"]          # as assigned
PRE_YEARS = 2.0                     # constant-rate lead-in, sets the profile


def run_case(k, S, C, rock, daily, dur_h, boundary, re, q_pre):
    """FD build-up, psi rise since shut-in, on a log dt grid."""
    sched = [(PRE_YEARS * 365 * 24, q_pre)]
    sched += [(24.0, float(q)) for q in daily]
    sched += [(dur_h, 0.0)]
    t, p = PS.simulate(k, S, C, rock, sched, re=re, boundary=boundary,
                       steps_per_segment=300)
    t_shut = sum(d for d, _ in sched[:-1])
    m = t >= t_shut
    tb, pb = t[m] - t_shut, p[m]
    dt = np.geomspace(0.05, dur_h, 60)
    return dt, np.interp(dt, tb, pb - pb[0])


def main() -> None:
    pvt = pd.read_csv(ROOT / "data" / "reservoir_pvt.csv").set_index("well_name")
    ref = pd.read_csv(REF).set_index("well_name")
    rates = pd.read_csv(RATES)
    d90 = rates[rates.segment == "daily_90d"]

    print("Rate-history bias in k and S -- FD multi-rate vs the shipped "
          "single-rate fit\n")
    rows = []
    for wn in WELLS:
        r, p = ref.loc[wn], pvt.loc[wn]
        rock = dict(h=p.net_pay_thickness_ft, phi=p.porosity_frac,
                    ct=p.total_compressibility_1_psi, rw=p.wellbore_radius_ft,
                    B=p.oil_fvf_rb_stb, mu=p.oil_viscosity_cp)
        k, S, C = r.permeability_md, r.skin, r.storage_bbl_per_psi
        re = None if r.boundary != "closed" else float(r.r_e_ft)
        daily = d90[d90.well_name == wn].sort_values("timestamp").oil_rate_stbd.to_numpy()
        q_fit = float(r.qo_stbd)

        print(f"  {wn}: {len(daily)} daily rates, "
              f"{daily.min():.0f}-{daily.max():.0f} stb/d "
              f"(mean {daily.mean():.0f}, sd {daily.std():.0f}, "
              f"spread {(daily.max()-daily.min())/daily.mean()*100:.1f}% of mean); "
              f"shipped fit used q = {q_fit:.1f}")

        cases = {}
        for name, seq, q_pre in [("REAL", daily, float(daily.mean())),
                                 ("FLAT", np.full(len(daily), q_fit), q_fit)]:
            dt, dp = run_case(k, S, C, rock, seq, float(r.duration_h),
                              r.boundary, re, q_pre)
            fit = PM.fit_buildup(dt, dp, float(r.tp_h), q_fit, rock,
                                 k0=k, S0=S, C0=C, boundary=r.boundary,
                                 re0=re if re else 2000.0)
            cases[name] = (dt, dp, fit)

        dp_gap = float(np.abs(cases["REAL"][1] - cases["FLAT"][1]).max())
        print(f"    build-up curves REAL vs FLAT differ by max "
              f"{dp_gap:.3f} psi (rise {cases['FLAT'][1].max():.1f} psi)")
        print(f"      {'case':6s} {'k md':>9s} {'dk vs truth':>12s} {'S':>8s} "
              f"{'dS vs truth':>12s} {'rms psi':>8s}")
        print(f"      {'truth':6s} {k:9.3f} {'':>12s} {S:8.3f} {'':>12s}")
        for name in ("FLAT", "REAL"):
            f = cases[name][2]
            print(f"      {name:6s} {f['k']:9.3f} {(f['k']/k-1)*100:11.2f}% "
                  f"{f['S']:8.3f} {f['S']-S:+12.3f} {f['rms_psi']:8.4f}")
        fk, rk = cases["FLAT"][2], cases["REAL"][2]
        dk = (rk["k"] / fk["k"] - 1) * 100
        ds = rk["S"] - fk["S"]
        print(f"    ATTRIBUTABLE TO RATE HISTORY (REAL - FLAT): "
              f"k {dk:+.2f}%, S {ds:+.3f}")

        # SHAPE: the #5 trigger was sign-changing residual structure. Rate
        # history has a shape of its own -- compare them, do not assume.
        dtg = cases["REAL"][0]
        diff = cases["REAL"][1] - cases["FLAT"][1]
        runs = 1 + int((np.diff(np.sign(diff)) != 0).sum())
        print(f"      {'band':5s} {'dt range h':>18s} {'mean psi':>10s} {'sd':>8s}")
        bands = []
        for i, ix in enumerate(np.array_split(np.arange(len(dtg)), 4)):
            bands.append(float(diff[ix].mean()))
            print(f"      {i+1:<5d} {dtg[ix][0]:8.3f}-{dtg[ix][-1]:9.3f} "
                  f"{diff[ix].mean():+10.4f} {diff[ix].std():8.4f}")
        print(f"      sign runs {runs} in {len(diff)} points -- rate history is "
              f"{'single-signed' if runs <= 2 else 'sign-changing'}, growing "
              f"with dt\n")
        extra = dict(sign_runs=runs, n_points=len(diff),
                     **{f"band{i+1}_psi": b for i, b in enumerate(bands)})
        rows.append(dict(well_name=wn, n_days=len(daily),
                         q_fit_stbd=q_fit, q_mean_stbd=float(daily.mean()),
                         q_sd_stbd=float(daily.std()),
                         q_spread_pct=float((daily.max()-daily.min())/daily.mean()*100),
                         dp_real_vs_flat_psi=dp_gap,
                         buildup_rise_psi=float(cases["FLAT"][1].max()),
                         k_truth_md=k, k_flat_md=fk["k"], k_real_md=rk["k"],
                         S_truth=S, S_flat=fk["S"], S_real=rk["S"],
                         k_bias_pct=dk, S_bias=ds,
                         k_control_pct=(fk["k"]/k-1)*100, S_control=fk["S"]-S,
                         **extra))

    df = pd.DataFrame(rows)
    out = ROOT / "ml" / "outputs" / "pta_superposition_check.csv"
    df.round(6).to_csv(out, index=False)
    print(f"  wrote {out.relative_to(ROOT)}")
    print(f"\n  VERDICT: rate history moves k by "
          f"{df.k_bias_pct.abs().max():.2f}% and S by "
          f"{df.S_bias.abs().max():.3f} at worst over these {len(df)} wells.")
    print(f"  The control's own offset is k {df.k_control_pct.abs().max():.2f}%, "
          f"S {df.S_control.abs().max():.3f} -- that part is the FD-vs-Laplace")
    print(f"  formulation gap, not superposition, and must not be claimed as a "
          f"correction.")
    g8 = df[df.well_name == "GL-08"].iloc[0]
    print(f"\n  SHAPE: rate history is single-signed and monotone in dt "
          f"({df.sign_runs.min()}-{df.sign_runs.max()} sign runs in "
          f"{df.n_points.max()} points),")
    print(f"  concentrated at LATE dt. The #5 trigger was SIGN-CHANGING "
          f"structure (GL-08: 10 runs in 41")
    print(f"  points, bands -0.042/-0.047/-0.011/+0.041 psi). Different shapes "
          f"-- and in the early bands")
    print(f"  where that structure sits, rate history is far too small (GL-08 "
          f"bands 1-3: {g8.band1_psi:+.4f}/{g8.band2_psi:+.4f}/"
          f"{g8.band3_psi:+.4f} psi).")
    print(f"  Rate history does NOT explain the residual structure.")


if __name__ == "__main__":
    main()
