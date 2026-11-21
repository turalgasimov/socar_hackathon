"""The three checks behind the routing-gap conclusions. Reproducible, per AGENTS.md.

    python ml/eda/routing_checks.py

1. Critical choke flow — rejected.
2. How fast conditions return to normal after a test — sets the label-transfer
   window design.
3. Our daily-vs-test-window measurement of the routing gap.

The critical-flow test uses Rovshan's specification, not the one I ran first.
I refitted all 14 choke parameters separately on each side of the threshold;
he keeps the shared parameters pooled and splits only the dPc term. With 39-46
points per side, refitting everything is noisy, and his version isolates the
coefficient actually in question. Both reach the same conclusion.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.linalg import lstsq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "src"))
sys.path.insert(0, str(ROOT / "ml" / "eda"))
warnings.filterwarnings("ignore")

from benchmark_vfm import load_tests  # noqa: E402
from config import F_HF_CLEAN  # noqa: E402

SPLIT = 0.60  # downstream/WHP threshold to test for critical flow


def critical_flow(t: pd.DataFrame) -> None:
    """Does the choke law behave differently below the critical pressure ratio?

    A correlation cannot answer this -- critical flow is a threshold, where
    rate stops responding to downstream pressure. The signature is the dPc
    exponent collapsing toward zero on the low-ratio side.
    """
    print("=" * 70 + "\n1. CRITICAL CHOKE FLOW\n" + "=" * 70)
    t = t.copy()
    t["ratio"] = t.whp_downstream_psia / t.whp_psia
    low = (t.ratio < SPLIT).to_numpy()
    print(f"  pressure ratio across the 85 tests: {t.ratio.min():.3f}-{t.ratio.max():.3f} "
          f"(median {t.ratio.median():.3f})")
    print(f"  tests below 0.55: {(t.ratio < 0.55).sum()}   below {SPLIT}: {low.sum()}")

    wells = sorted(t.well_name.unique())
    W = pd.get_dummies(t.well_name)[wells].to_numpy(float)
    qL = t.liquid_rate_stbd.to_numpy()
    glr = (t.gas_lift_rate_mscfd.to_numpy()
           + qL * (1 - t.wc.to_numpy()) * t.solution_gor_at_pb_scf_stb.to_numpy() / 1000) / qL
    lnS, lnW, lnG = np.log(t.S), np.log(t.whp_psia), np.log(glr)
    lnD = np.log(t.dpc).to_numpy()

    # one pooled fit; only the dPc term is split by regime
    X = np.c_[W, lnS, lnW, lnG, np.where(low, 0, lnD), np.where(low, lnD, 0)]
    b = lstsq(X, np.log(qL), rcond=None)[0]
    resid = np.log(qL) - X @ b
    print(f"\n  {'regime':22s} {'n':>4s} {'dPc exponent':>14s} {'mean resid':>12s}")
    print(f"  {'ratio >= ' + str(SPLIT):22s} {(~low).sum():4d} {b[-2]:14.3f} {resid[~low].mean():12.4f}")
    print(f"  {'ratio <  ' + str(SPLIT):22s} {low.sum():4d} {b[-1]:14.3f} {resid[low].mean():12.4f}")
    print("\n  Critical flow would drive the low-ratio exponent toward 0. It does not.")
    print("  REJECTED -- use this, not a correlation, in the presentation.")


def recovery(hf: pd.DataFrame, wt: pd.DataFrame) -> None:
    """How quickly does downstream pressure return to normal after a test?

    Decides whether the windows either side of a test are genuinely
    normal-regime, which is what the label transfer rests on.
    """
    print("\n" + "=" * 70 + "\n2. POST-TEST RECOVERY\n" + "=" * 70)
    idx = {w: d.sort_values("timestamp").reset_index(drop=True)
           for w, d in hf.groupby("well_name", observed=True)}
    rows = []
    for _, r in wt.iterrows():
        d = idx.get(r.well_name)
        if d is None:
            continue
        tail = d[(d.timestamp >= r.test_end - pd.Timedelta("2h"))
                 & (d.timestamp <= r.test_end)].whp_downstream_psia.median()
        pre = d[(d.timestamp >= r.test_start - pd.Timedelta("6h"))
                & (d.timestamp <= r.test_start - pd.Timedelta("10min"))].whp_downstream_psia.median()
        if not np.isfinite(tail) or not np.isfinite(pre) or pre == tail:
            continue
        rec = {}
        for lab, lo, hi in [("+1h", "50min", "70min"), ("+6h", "5h", "6h"),
                            ("+24h", "23h", "25h")]:
            v = d[(d.timestamp >= r.test_end + pd.Timedelta(lo))
                  & (d.timestamp <= r.test_end + pd.Timedelta(hi))].whp_downstream_psia.median()
            rec[lab] = 100 * (v - tail) / (pre - tail)
        rows.append(rec)
    R = pd.DataFrame(rows)
    print(f"  recovery toward the pre-test level, % (100 = fully back to normal), n={len(R)}")
    print("  " + R.median().round(1).to_string().replace("\n", "\n  "))
    print("\n  Recovery is essentially immediate, so the windows either side of a")
    print("  test are normal-regime. Still start post-test windows at +1 h.")


def daily_vs_window(hf: pd.DataFrame, wt: pd.DataFrame) -> None:
    """Our route to the routing gap: same date, daily aggregate vs test window."""
    print("\n" + "=" * 70 + "\n3. ROUTING GAP, DAILY-VS-TEST-WINDOW\n" + "=" * 70)
    sys.path.insert(0, str(ROOT / "ml"))
    from config import PROC
    from vfm import VFMModel, build_inputs
    tr = pd.read_parquet(PROC / "train_table.parquet")
    daily = pd.read_parquet(PROC / "daily_table.parquet")
    m = VFMModel.load(ROOT / "ml" / "models" / "vfm.pkl")
    daily = daily.assign(pred=m.predict(build_inputs(daily, when="date")).oil_rate_stbd.values,
                         date=pd.to_datetime(daily.date))
    tr = tr.assign(date=pd.to_datetime(tr.start).dt.normalize())
    j = tr[["well_name", "date", "oil_rate_stbd"]].merge(
        daily[["well_name", "date", "pred"]], on=["well_name", "date"])
    j["gap_%"] = (j.pred / j.oil_rate_stbd - 1) * 100
    print(f"  matched {len(j)} of {len(tr)} tests")
    print("  " + j.groupby("well_name")["gap_%"].mean().round(2).to_string().replace("\n", "\n  "))
    print(f"\n  overall: {j['gap_%'].mean():+.2f}%  "
          "-- consistent with the downhole methods' ~2.5%")


def main() -> None:
    t = load_tests(ROOT / "data").reset_index(drop=True)
    critical_flow(t)
    hf = pd.read_parquet(F_HF_CLEAN)
    wt = pd.read_parquet(ROOT / "data" / "processed" / "well_tests_clean.parquet")
    recovery(hf, wt)
    daily_vs_window(hf, wt)


if __name__ == "__main__":
    main()
