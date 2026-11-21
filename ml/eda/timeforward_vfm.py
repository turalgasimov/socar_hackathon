"""Time-forward validation of the choke physics model.

benchmark_vfm.py scores leave-one-test-out: when predicting a test, the model
has already seen *later* tests from the same well. That is optimistic — it is
not the situation the daily submission is in.

Here, predicting well w at time T, the training set is:
    every test from the other nine wells  +  w's own tests strictly before T
and the water-cut trend is extrapolated from w's past tests only. Nothing from
the future of that well is used.

This is the number to quote for the VFM deliverable.

    python ml/eda/timeforward_vfm.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.linalg import lstsq
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")

from benchmark_vfm import load_tests  # noqa: E402

MIN_HISTORY = 3  # tests needed before a well can be predicted


def _feats(df: pd.DataFrame, q: np.ndarray, wc: np.ndarray) -> np.ndarray:
    """ln of the four choke-law terms. GLR depends on q, hence passed in."""
    glr = (df.gas_lift_rate_mscfd.values
           + q * (1 - wc) * df.solution_gor_at_pb_scf_stb.values / 1000) / q
    return np.c_[np.log(df.S), np.log(df.dpc), np.log(df.whp_psia), np.log(glr)]


def _wc_from_past(t: pd.DataFrame, i: int) -> float:
    """Water cut at test i, extrapolated from that well's earlier tests only."""
    past = t[(t.well_name == t.well_name[i]) & (t.mid < t.mid[i])]
    if len(past) >= 2:
        return float(np.polyval(np.polyfit(past.t_days, past.wc, 1), t.t_days[i]))
    return float(past.wc.mean())


def time_forward(t: pd.DataFrame) -> pd.DataFrame:
    wells = sorted(t.well_name.unique())
    W = pd.get_dummies(t.well_name)[wells].values.astype(float)
    y = t.liquid_rate_stbd.values
    ly = np.log(y)
    rows = []
    for i in range(len(t)):
        w, ti = t.well_name[i], t.mid[i]
        past_same = (t.well_name == w) & (t.mid < ti)
        if past_same.sum() < MIN_HISTORY:
            continue
        trn = (t.well_name != w) | past_same          # no future of this well
        tr = t[trn]
        X = np.c_[W[trn.values], _feats(tr, tr.liquid_rate_stbd.values, tr.wc.values)]
        b = lstsq(X, ly[trn.values], rcond=None)[0]

        wc_hat = _wc_from_past(t, i)
        te = t.iloc[[i]]

        def resid(lq: float) -> float:
            f = _feats(te, np.array([np.exp(lq)]), np.array([wc_hat]))[0]
            return float(np.r_[W[i], f] @ b) - lq

        q = float(np.exp(brentq(resid, np.log(50), np.log(50000))))
        rows.append({"well": w, "date": ti, "n_train": int(trn.sum()),
                     "real_liquid": y[i], "pred_liquid": q, "wc_hat": wc_hat,
                     "real_oil": t.oil_rate_stbd[i], "real_water": t.water_rate_stbd[i],
                     "real_gas": t.gas_rate_mscfd[i],
                     "rs": t.solution_gor_at_pb_scf_stb[i]})
    r = pd.DataFrame(rows)
    r["pred_oil"] = r.pred_liquid * (1 - r.wc_hat)
    r["pred_water"] = r.pred_liquid * r.wc_hat
    r["pred_gas"] = r.pred_oil * r.rs / 1000
    return r


def main() -> None:
    t = load_tests(Path(__file__).resolve().parents[2] / "data")
    r = time_forward(t)
    mape = lambda a, p: float(np.mean(np.abs(p / a - 1)) * 100)
    bias = lambda a, p: float(np.mean(p / a - 1) * 100)

    print(f"Time-forward: {len(r)} of {len(t)} tests scored "
          f"(a well needs {MIN_HISTORY} prior tests before it can be predicted)\n")
    print(f"{'target':8s} {'MAPE':>8s} {'bias':>8s}")
    for name in ["liquid", "oil", "water", "gas"]:
        a, p = r[f"real_{name}"].values, r[f"pred_{name}"].values
        print(f"{name:8s} {mape(a,p):7.2f}% {bias(a,p):+7.2f}%")

    print("\nFor comparison, leave-one-test-out on the same model: liquid 1.82%")
    print("(LOO lets the model see later tests from the same well.)")

    print("\nPer well, liquid:")
    g = r.groupby("well").apply(
        lambda d: pd.Series({"n": len(d),
                             "MAPE_%": mape(d.real_liquid.values, d.pred_liquid.values),
                             "bias_%": bias(d.real_liquid.values, d.pred_liquid.values)}))
    print(g.round(2).to_string())


if __name__ == "__main__":
    main()
