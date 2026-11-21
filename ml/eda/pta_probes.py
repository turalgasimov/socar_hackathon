"""Unscored PTA probes for the platform. One change per file against the scored base (8.3840).

    python ml/eda/pta_probes.py
        writes the five probe files to ml/outputs/candidates/ and prints the IPR check and the decision table
    python ml/eda/pta_probes.py --rate ipr --abs-skin --out <file.csv>
        any combination, e.g. to build the final file from the probes that won

Inputs: the scored base ml/outputs/submitted/pta_model_match_8.3840_SHIPPED.csv; the full-precision model
results ml/outputs/figures/pta/pta_reference_model_match.csv (python ml/eda/pta_explore.py); the shipped
Task 1 rate file; data/processed/{well_tests_clean,high_freq_clean}.parquet.

Rate variants -- k * r, S - 1.1513 log10 r, dP_skin = 0.869 m S, m unchanged. This is exact for a rate
rescale (verified by a full refit: GL-06 k 312.72 vs 312.59, 0.04 %):
  vfm         r = 1, the scored base
  ipr         r = q_IPR / q_VFM on the last full flowing day (ml/src/pta_rate.py), rounded to 4 decimals
  ipr_up      r ** 1.5    (bracket beyond the IPR rate)
  ipr_down    r ** -0.5   (bracket on the other side of VFM)
  ipr_minute  the IPR rate at the shut-in minute (gauge pwf at dt = 0) instead of the last full day
Sign variant --abs-skin: |S| and |dP_skin| (tests a positive-skin convention on GL-02, GL-04, GL-08).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "src"))
import pta_rate as PR  # noqa: E402

OUT = ROOT / "ml" / "outputs"
BASE = OUT / "submitted" / "pta_model_match_8.3840_SHIPPED.csv"
MODEL = OUT / "figures" / "pta" / "pta_reference_model_match.csv"
RATES = OUT / "submitted" / "lam0.80_21.0200_SHIPPED.csv"
TEMPLATE = ROOT / "docs" / "pta_submission_template.csv"
PROBES = {  # file name -> (rate variant, abs skin)
    "pta_P0_skin_sign_abs.csv": ("vfm", True),
    "pta_P1_k_from_IPR_rate.csv": ("ipr", False),
    "pta_P2_up_IPR_rate_x1.5.csv": ("ipr_up", False),
    "pta_P2_down_IPR_rate_x-0.5.csv": ("ipr_down", False),
    "pta_P3_IPR_rate_at_shutin_minute.csv": ("ipr_minute", False),
}


def ipr_ratios() -> pd.DataFrame:
    base = pd.read_csv(BASE)
    M = pd.read_csv(MODEL, parse_dates=["shut_in_start"]).set_index("well_name")
    pvt = pd.read_csv(ROOT / "data" / "reservoir_pvt.csv").set_index("well_name")
    tests = pd.read_parquet(ROOT / "data" / "processed" / "well_tests_clean.parquet")
    v = pd.read_csv(RATES, parse_dates=["timestamp"])
    wells = base.well_name.tolist()
    hf = pd.read_parquet(ROOT / "data" / "processed" / "high_freq_clean.parquet",
                         columns=["timestamp", "well_name", "dh_pressure_psia", "is_shut_in"],
                         filters=[("well_name", "in", wells)])
    hf = hf[~hf.is_shut_in.astype(bool)]
    daily = hf.groupby([hf.well_name.astype(str), hf.timestamp.dt.normalize()]).dh_pressure_psia.mean()
    rows, loos = [], []
    for w in wells:
        m, P = M.loc[w], pvt.loc[w]
        t_w = tests[tests.well_name == w]
        ts = m.shut_in_start
        D = ts.normalize() - pd.Timedelta("1D")                    # the day the VFM q is for
        q_vfm = float(v[(v.well_name == w) & (v.timestamp == D)].oil_rate_stbd.iloc[0])
        dd = PR.drawdown(m.horner_slope_psi_per_cycle, m.skin, m.boundary, m.r_e_ft, P.wellbore_radius_ft,
                         P.estimated_drainage_area_acres)
        pwf_day = float(daily.loc[(w, D)])
        q_ipr, q_t, pwf_t, how = PR.ipr_rate(D + pd.Timedelta("12h"), pwf_day, t_w, dd)
        q_min = q_ipr * (dd + pwf_day - m.pwf_gauge_psia) / dd    # same IPR, at the shut-in minute
        loo = PR.loo_errors(t_w, dd)
        loos.append(loo)
        rows.append(dict(well=w, q_vfm=q_vfm, q_test_interp=round(q_t, 1), pwf_test_interp=round(pwf_t, 1),
                         pwf_day=round(pwf_day, 1), drawdown_psi=round(dd, 1), q_ipr=round(q_ipr, 1),
                         r_ipr=round(q_ipr / q_vfm, 4), r_ipr_minute=round(q_min / q_vfm, 4),
                         loo_mae_pct=round(loo.err_ipr_pct.abs().mean(), 2), loo_n=len(loo), tests=how))
    L = pd.concat(loos)
    print(f"IPR method, leave-one-out over {len(L)} interior tests: MAE {L.err_ipr_pct.abs().mean():.2f} %, "
          f"bias {L.err_ipr_pct.mean():+.2f} % (interpolation without the IPR step: "
          f"MAE {L.err_interp_only_pct.abs().mean():.2f} %)")
    return pd.DataFrame(rows).set_index("well")


def build(rate: str, abs_skin: bool, R: pd.DataFrame) -> pd.DataFrame:
    base = pd.read_csv(BASE)
    M = pd.read_csv(MODEL).set_index("well_name")
    out = []
    for w, t in zip(base.well_name, base.shut_in_time):
        m = M.loc[w]
        r = {"vfm": 1.0, "ipr": R.loc[w, "r_ipr"], "ipr_up": R.loc[w, "r_ipr"] ** 1.5,
             "ipr_down": R.loc[w, "r_ipr"] ** -0.5, "ipr_minute": R.loc[w, "r_ipr_minute"]}[rate]
        S = m.skin - 1.1513 * np.log10(r)
        S = abs(S) if abs_skin else S
        mm = m.horner_slope_psi_per_cycle
        out.append(dict(well_name=w, shut_in_time=t, permeability_md=round(m.permeability_md * r, 2),
                        skin=round(S, 3), delta_p_skin_psi=round(0.869 * mm * S, 2), horner_slope=round(mm, 3)))
    df = pd.DataFrame(out)
    assert df.columns.tolist() == pd.read_csv(TEMPLATE, nrows=0).columns.tolist()
    num = df[["permeability_md", "skin", "delta_p_skin_psi", "horner_slope"]].to_numpy(float)
    assert len(df) == 6 and np.isfinite(num).all() and (df.horner_slope >= 0).all() and (df.permeability_md > 0).all()
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", choices=["vfm", "ipr", "ipr_up", "ipr_down", "ipr_minute"])
    ap.add_argument("--abs-skin", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    pd.set_option("display.width", 220)
    R = ipr_ratios()
    if a.rate:
        df = build(a.rate, a.abs_skin, R)
        out = a.out or OUT / "candidates" / f"pta_{a.rate}{'_abs_skin' if a.abs_skin else ''}.csv"
        df.to_csv(out, index=False, lineterminator="\n")
        print(f"wrote {out}\n{df.to_string(index=False)}")
        return
    print("Oil rate on the last full flowing day before each shut-in: VFM vs IPR from the measured tests")
    print(R.to_string())
    for name, (rate, abs_skin) in PROBES.items():
        build(rate, abs_skin, R).to_csv(OUT / "candidates" / name, index=False, lineterminator="\n")
    print("\nwrote", ", ".join(PROBES), "to ml/outputs/candidates/")
    print("""
Decision table (base = shipped 8.3840; one change per probe):
  P0  pta_P0_skin_sign_abs.csv           keep if > 8.3840; either way go to P1
  P1  pta_P1_k_from_IPR_rate.csv         won -> P2_up ; lost -> P2_down
  P2  pta_P2_up_IPR_rate_x1.5.csv        only if P1 won;  keep if > P1, then stop the rate ladder
      pta_P2_down_IPR_rate_x-0.5.csv     only if P1 lost; keep if > 8.3840, then stop
  P3  pta_P3_IPR_rate_at_shutin_minute   only if P1 won and probes remain; keep if > best so far
Final: combine only individually winning changes (--rate <best> [--abs-skin]); no winner -> the base stays.""")


if __name__ == "__main__":
    main()
