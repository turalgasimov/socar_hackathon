"""The same model under six validation schemes. A diagnostic, not a scoreboard.

    python ml/eda/cv_schemes.py

Our docs assert that a random-split CV score here "is meaningless and will be
~4% MAPE regardless". That is an assertion we had never measured. This measures
it, and turns k-fold into evidence rather than a number we quote.

WHY RANDOM K-FOLD LEAKS HERE
----------------------------
98.3% of oil-rate variance is BETWEEN wells and 1.7% within. Each well has 7-9
tests. So a random fold almost always leaves other tests from the same well in
training, and the model only has to recall that well's rate level -- which the
per-well intercept hands it directly. The fold never asks the question we care
about: predict a rate at a time we have not seen.

THE DECISIVE TEST, NOT JUST THE SPREAD
--------------------------------------
A scheme is useful only if it RANKS candidates the way the truth does. We know
the truth for exactly one pair, because both were submitted:

    shipped water-cut set (t, dp_tubing, gl)        leaderboard 21.0200
    widened set                                     leaderboard 20.5700

An earlier version of this file scored two candidate widenings, because
AGENTS.md and PROJECT_STATE.md disagreed about which one was submitted. Rovshan
settled it in 9b54131: they were two different variants.

  - the `whp_downstream` variant moved base oil +5.24% offline and was caught
    BEFORE submission (d0ac161). It was never scored.
  - the widening that WAS submitted added only routing-safe sensors --
    `whp, dh_p, dh_t, ann` -- and scored 20.5700 (reverted in 7fefd46).

PROJECT_STATE.md and ml/evaluate.py were right; AGENTS.md was wrong. The set
below is confirmed numerically as well as documentally: under leave-one-test-out
it scores 23.4405 against the 23.441 evaluate.py records for that probe.

Changes nothing that ships.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "src"))
warnings.filterwarnings("ignore")

from config import PROC  # noqa: E402
from vfm import ROUTING_FACTORS, VFMModel, build_inputs  # noqa: E402

PH = [("oil", "oil_rate_stbd"), ("water", "water_rate_stbd"),
      ("gas", "gas_rate_mscfd")]
MIN_HISTORY = 3
# points reach zero at these error levels (ml/infer_truth.py); SHAPE only
M0 = {"oil": 12.2, "water": 14.2, "gas": 16.1}
W0 = {"oil": 10.6, "water": 12.4, "gas": 14.3}

SHIPPED_WC = ["t", "dp_tubing", "gl"]
# the widening that was actually submitted and scored 20.5700 (see 9b54131)
WIDENED = {"submitted widening (+ whp,dh_p,dh_t,ann)":
           SHIPPED_WC + ["whp", "dh_p", "dh_t", "ann"]}
TRUE_GAP = 21.0200 - 20.5700          # shipped minus widened, in points
LEAKY = ["kfold_5", "kfold_10", "stratified_by_well", "leave_one_test_out"]
SCHEMES = LEAKY + ["time_forward", "groupkfold_by_well"]


def metrics(a, p):
    return {"r2": float(1 - ((a - p) ** 2).sum() / ((a - a.mean()) ** 2).sum()),
            "mape": float(np.mean(np.abs(p / a - 1)) * 100),
            "wape": float(np.abs(a - p).sum() / a.sum() * 100)}


def points(m, phase):
    return (3 * np.clip(m["r2"], 0, 1)
            + 2 * np.clip(1 - m["mape"] / M0[phase], 0, 1)
            + 5 * np.clip(1 - m["wape"] / W0[phase], 0, 1))


def folds(tr, scheme, rng):
    """Yield (test_index_array, train_bool_mask) for each fold."""
    n = len(tr)
    well = tr.well_name.astype(str).to_numpy()
    start = tr.start.to_numpy()
    idx = np.arange(n)

    if scheme.startswith("kfold"):
        k = int(scheme.split("_")[1])
        for part in np.array_split(rng.permutation(n), k):
            m = np.ones(n, bool)
            m[part] = False
            yield part, m

    elif scheme == "stratified_by_well":
        # one random test per well per fold: still leaks, by construction
        per = {w: rng.permutation(idx[well == w]) for w in np.unique(well)}
        for j in range(max(len(v) for v in per.values())):
            part = np.array([v[j] for v in per.values() if j < len(v)])
            m = np.ones(n, bool)
            m[part] = False
            yield part, m

    elif scheme == "groupkfold_by_well":          # unseen well: the honest floor
        for w in np.unique(well):
            yield idx[well == w], well != w

    elif scheme == "leave_one_test_out":
        for i in idx:
            m = np.ones(n, bool)
            m[i] = False
            yield np.array([i]), m

    elif scheme == "time_forward":                # past of the same well only
        for w in np.unique(well):
            wi = idx[well == w]
            wi = wi[np.argsort(start[wi])]
            for j in range(MIN_HISTORY, len(wi)):
                yield np.array([wi[j]]), (well != w) | (start < start[wi[j]])


def run(tr, X, rf, wc_features, scheme, seed=0):
    rng = np.random.default_rng(seed)
    pred = {k: np.full(len(tr), np.nan) for k, _ in PH}
    for part, m in folds(tr, scheme, rng):
        mdl = VFMModel(wc_features=wc_features).fit(
            X[m], tr.oil_rate_stbd.values[m], tr.water_rate_stbd.values[m])
        p = mdl.predict(X.iloc[part])
        for k, c in PH:
            pred[k][part] = p[c].to_numpy() * rf[part]
    rows = ~np.isnan(pred["oil"])
    out, total = {}, 0.0
    for k, c in PH:
        mm = metrics(tr[c].values[rows], pred[k][rows])
        out[k] = mm
        total += points(mm, k)
    out["total"], out["n"] = total, int(rows.sum())
    return out


def main() -> None:
    tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(
        ["well_name", "start"], ignore_index=True)
    X = build_inputs(tr)
    rf = tr.well_name.astype(str).map(ROUTING_FACTORS).fillna(1.0).to_numpy()

    print(f"{len(tr)} real measured tests, {tr.well_name.nunique()} wells "
          f"(7-9 tests each)")
    print()
    print("1. THE LEAK, MEASURED. Same model, same rows, different folds.")
    print()
    print(f"  {'scheme':22s} {'n':>4s} {'oil WAPE':>9s} {'water':>8s} "
          f"{'gas':>7s} {'points':>8s}")
    rows = []
    for sc in SCHEMES:
        a = run(tr, X, rf, SHIPPED_WC, sc)
        print(f"  {sc:22s} {a['n']:4d} {a['oil']['wape']:8.2f}% "
              f"{a['water']['wape']:7.2f}% {a['gas']['wape']:6.2f}% "
              f"{a['total']:8.3f}")
        rows.append(dict(scheme=sc, n=a["n"], points_shipped=a["total"],
                         **{f"{k}_{x}": a[k][x] for k, _ in PH
                            for x in ("r2", "mape", "wape")}))
    df = pd.DataFrame(rows)
    lk = df[df.scheme.isin(LEAKY)].oil_wape
    tf = float(df.loc[df.scheme == "time_forward", "oil_wape"].iloc[0])
    gk = float(df.loc[df.scheme == "groupkfold_by_well", "oil_wape"].iloc[0])
    print()
    print(f"  Oil WAPE: leaky schemes {lk.min():.2f}-{lk.max():.2f}%, "
          f"time-forward {tf:.2f}%, unseen well {gk:.2f}%.")
    print(f"  The four leaky schemes agree to within {lk.max()-lk.min():.2f} pp "
          f"of each other: once the")
    print("  same well's other tests are in training, the fold design barely "
          "matters. The docs' claim")
    print("  that a random split lands '~3-4% regardless' is confirmed, and "
          "now measured.")

    print()
    print("2. THE TEST THAT MATTERS: do they rank the one pair we know?")
    print()
    print(f"  Truth: shipped beats widened by {TRUE_GAP:+.3f} points "
          f"(21.0200 vs 20.5700).")
    print("  The widening is the one that was actually submitted: "
          "+ whp, dh_p, dh_t, ann (9b54131).")
    print()
    for label, feats in WIDENED.items():
        print(f"  {label}")
        print(f"    {'scheme':22s} {'shipped':>8s} {'widened':>8s} "
              f"{'gap':>7s} {'verdict':>9s}")
        inv = 0
        for sc in SCHEMES:
            a = float(df.loc[df.scheme == sc, "points_shipped"].iloc[0])
            b = run(tr, X, rf, feats, sc)["total"]
            v = "CORRECT" if a - b > 0 else "INVERTED"
            inv += v == "INVERTED"
            print(f"    {sc:22s} {a:8.3f} {b:8.3f} {a-b:+7.3f} {v:>9s}")
            df.loc[df.scheme == sc, f"gap_{label[0]}"] = a - b
        print(f"    -> {inv}/{len(SCHEMES)} INVERT the known ordering")
        print()

    gcols = [c for c in df.columns if c.startswith("gap_")]
    sane = df[df.scheme != "groupkfold_by_well"][gcols].to_numpy()
    worst = float(np.nanmax(np.abs(sane)))
    print("3. THE REAL RESULT IS THE MAGNITUDE, NOT THE SIGN.")
    print()
    print(f"  The true effect is {TRUE_GAP:.3f} points. Across every scheme "
          f"except")
    print(f"  unseen-well, the largest gap any of them reports is "
          f"{worst:.3f} points -- {TRUE_GAP/worst:.0f}x too small,")
    print("  before we even ask about the sign. (Unseen-well is excluded: "
          "adding four features wrecks")
    print("  generalisation to an eleventh well for reasons that have nothing "
          "to do with the")
    print("  leaderboard.) These schemes do not merely rank wrongly: they "
          "cannot SEE an effect of")
    print("  the right size. It lives on the 2,729 out-of-regime scored days, "
          "and all 85 labels are")
    print("  in-regime. No resampling of in-regime labels recovers an "
          "out-of-regime effect.")

    print()
    print("  SEED STABILITY of random k-fold (10 seeds, 5 folds):")
    tot, g = [], []
    for sd in range(10):
        a = run(tr, X, rf, SHIPPED_WC, "kfold_5", sd)["total"]
        b = run(tr, X, rf, list(WIDENED.values())[0], "kfold_5", sd)["total"]
        tot.append(a)
        g.append(a - b)
    tot, g = np.array(tot), np.array(g)
    print(f"    points {tot.mean():.3f} +- {tot.std():.3f}    "
          f"gap {g.mean():+.3f} +- {g.std():.3f}    "
          f"sign: {int((g > 0).sum())} correct / {int((g <= 0).sum())} inverted")
    print("    The gap is smaller than its own seed noise, so even its sign is "
          "not a measurement.")

    print()
    print("  VERDICT: k-fold is useful here for quantifying the leak and "
          "catching gross regressions.")
    print("  Do not use it, or any scheme in this file, to choose between "
          "candidates.")

    out = ROOT / "ml" / "outputs" / "cv_schemes.csv"
    df.round(6).to_csv(out, index=False)
    print()
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
