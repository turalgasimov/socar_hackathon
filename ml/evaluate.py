"""Offline evaluation harness. Use this now the leaderboard is closed.

    python ml/evaluate.py                       # score the shipped model
    python ml/evaluate.py --wc-features t dp_tubing gl whp
    python ml/evaluate.py --label <name>        # tag the run in the log

Appends every run to ml/outputs/eval_log.csv so candidates stay comparable.

READ THIS BEFORE TRUSTING A NUMBER FROM IT
------------------------------------------
**This harness fails its own validation.** On the single case we can check
against a real score, it inverts the ranking:

    candidate                  harness   leaderboard
    shipped (lambda 0.80)       23.385       21.0200
    routing-safe widened WC     23.441       20.5700

It calls the widened water-cut an improvement; the leaderboard called it a
0.45 loss. That is a shape change, so the comfortable rule "trust it for
shape, not level" is falsified by the one experiment available.

The reason is that in this model a shape change carries a LEVEL side-effect
on the out-of-regime days -- widening the split moved base oil +5.24% -- and
these 85 test-routed labels cannot see it.

So: use this to detect gross regressions, and for nothing finer. A candidate
that scores 2 points worse here is genuinely broken. A candidate 0.05 better
means nothing at all. There is no offline scheme that fixes this, because
every label we own sits in the wrong regime -- it is a data problem, not a
splitting or synthetic-truth problem.

WHAT THIS CAN AND CANNOT TELL YOU
---------------------------------
It scores against the **85 real measured well tests**, not a synthetic truth.
A synthetic truth built from our own predictions would carry our model's shape
by construction, mark every shape change as a loss automatically, and teach us
nothing -- `data/processed/inferred_truth.parquet` is exactly that and it
already missed a held-out axis by 0.37 points. Do not score candidates on it.

The real limitation is the regime, and no choice of split fixes it: all 85
labels are test-separator routed while the 2,729 scored days are not. The
routing difference is a **level** shift, so:

    GROSS REGRESSIONS -> detectable. A candidate 2 points worse is broken.
    FINE RANKING      -> not detectable, see above. Do not chase 0.05 here.
    LEVEL             -> invisible. The level is settled at lambda=0.80 by six
                         leaderboard probes; leave it alone.

There is deliberately no "estimated leaderboard score" option. Given the
inverted ranking above, printing one would lend the number an authority it
has not earned.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))

from config import OUT, PROC  # noqa: E402
from vfm import ROUTING_FACTORS, VFMModel, build_inputs  # noqa: E402

LOG = OUT / "eval_log.csv"
PH = [("oil", "oil_rate_stbd"), ("water", "water_rate_stbd"), ("gas", "gas_rate_mscfd")]
MIN_HISTORY = 3

# Points reach zero at these error levels, inferred by inverting nine
# leaderboard scores (ml/infer_truth.py). Only the SHAPE of the mapping is
# used here, to weight the three metrics the way the organisers do.
M0 = {"oil": 12.2, "water": 14.2, "gas": 16.1}
W0 = {"oil": 10.6, "water": 12.4, "gas": 14.3}


def metrics(a: np.ndarray, p: np.ndarray) -> dict:
    return {"r2": float(1 - ((a - p) ** 2).sum() / ((a - a.mean()) ** 2).sum()),
            "mape": float(np.mean(np.abs(p / a - 1)) * 100),
            "wape": float(np.abs(a - p).sum() / a.sum() * 100),
            "bias": float(np.mean(p / a - 1) * 100)}


def points(m: dict, phase: str) -> float:
    return (3 * np.clip(m["r2"], 0, 1)
            + 2 * np.clip(1 - m["mape"] / M0[phase], 0, 1)
            + 5 * np.clip(1 - m["wape"] / W0[phase], 0, 1))


def folds(tr: pd.DataFrame, scheme: str):
    well, start = tr.well_name.astype(str).to_numpy(), tr.start.to_numpy()
    if scheme == "loto":                       # interpolation: both sides available
        return [(i, np.arange(len(tr)) != i) for i in range(len(tr))]
    out = []                                   # time-forward: past only
    for w in pd.unique(well):
        idx = np.where(well == w)[0]
        idx = idx[np.argsort(start[idx])]
        for k in range(MIN_HISTORY, len(idx)):
            out.append((idx[k], (well != w) | (start < start[idx[k]])))
    return out


def run(wc_features=None, scheme="loto") -> dict:
    tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(
        ["well_name", "start"], ignore_index=True)
    X = build_inputs(tr)
    rf = tr.well_name.astype(str).map(ROUTING_FACTORS).fillna(1.0).to_numpy()
    pred = {k: np.full(len(tr), np.nan) for k, _ in PH}
    for i, m in folds(tr, scheme):
        kw = {"wc_features": wc_features} if wc_features else {}
        mdl = VFMModel(**kw).fit(X[m], tr.oil_rate_stbd.values[m], tr.water_rate_stbd.values[m])
        p = mdl.predict(X.iloc[[i]]).iloc[0]
        for k, c in PH:
            pred[k][i] = p[c] * rf[i]
    rows = ~np.isnan(pred["oil"])
    res, total = {}, 0.0
    for k, c in PH:
        m = metrics(tr[c].values[rows], pred[k][rows])
        res[k] = m
        total += points(m, k)
    res["total"] = total
    res["n"] = int(rows.sum())
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wc-features", nargs="+", default=None)
    ap.add_argument("--scheme", choices=["loto", "timeforward"], default="loto")
    ap.add_argument("--label", default="shipped")
    a = ap.parse_args()

    r = run(a.wc_features, a.scheme)
    print(f"{a.label}   scheme={a.scheme}   n={r['n']} real measured tests\n")
    print(f"  {'phase':6s} {'R2':>8s} {'MAPE':>8s} {'WAPE':>8s} {'bias':>8s} {'pts/10':>7s}")
    for k, _ in PH:
        m = r[k]
        print(f"  {k:6s} {m['r2']:8.4f} {m['mape']:7.2f}% {m['wape']:7.2f}% "
              f"{m['bias']:+7.2f}% {points(m,k):7.2f}")
    print(f"\n  harness total: {r['total']:.3f} / 30")
    print("  NOT a leaderboard prediction. This harness inverted the ranking on")
    print("  the one case with a real score -- see the module docstring. Treat a")
    print("  2-point drop as a real regression and anything finer as noise.")

    row = {"when": datetime.now().isoformat(timespec="seconds"), "label": a.label,
           "scheme": a.scheme, "n": r["n"], "total": round(r["total"], 4),
           **{f"{k}_{x}": round(r[k][x], 4) for k, _ in PH
              for x in ("r2", "mape", "wape", "bias")}}
    df = pd.DataFrame([row])
    df.to_csv(LOG, mode="a", header=not LOG.exists(), index=False)
    print(f"  logged to {LOG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
