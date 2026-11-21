"""Was lambda overfitted to the leaderboard? A public/private split test.

We tuned ROUTING_LAMBDA by submitting. If the leaderboard scores one subset of
the 2,730 well-days (public) and the final ranking uses another (private), the
lambda that is best on public may not be best on private. Two tests:

A. SIMULATED SPLITS (ml/infer_truth.py scorer) -- ASSUMPTION-DEPENDENT
   A rough guide, not a measurement: it runs a scorer model fitted to nine
   leaderboard points, under three assumptions about the water level. Part B
   comes from real sensor data and is the stronger result.

   Fit the inferred truth to the nine leaderboard scores, then split the days
   into public/private many times, find the best lambda on each half, and
   measure what using the public optimum (and the shipped 0.80) costs on the
   private half. Run in three worlds: the free fit, and s_water pinned low and
   high (the board does not identify water; see ml/eda/vfm_probes.py --profile).

   Limitation: the simulated truth is base x level x iid daily noise, so it has
   NO drift over time by construction. A time split there measures noise only.
   That is what test B is for.

B. REAL-DATA TIME CHECK (sensors, no model) -- the stronger of the two
   The routing correction exists because normal-production days run at higher
   downstream wellhead pressure than test windows. If that offset drifts over
   the year, a lambda tuned on one period would not fit another. Measure the
   offset per well per month: normal-day whp_downstream minus the well's mean
   test-window whp_downstream, and express each month as a ratio to the well's
   all-year offset. Proxy assumption: the needed correction scales with the
   pressure offset, so a month at ratio x would want lambda ~ 0.80 * x.

    python ml/eda/lambda_split.py      (~1 min)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "src"))
sys.path.insert(0, str(ROOT / "ml"))

import infer_truth as it  # noqa: E402
from config import PROC  # noqa: E402
from vfm import ROUTING_LAMBDA  # noqa: E402

GRID = np.round(np.arange(0.40, 1.2001, 0.01), 2)
REPS = 200
SEED = 1


# ------------------------------------------------------------ A. simulated
def fit_world(base, preds, s_water=None):
    """Fit the scorer to all nine scores; s_water free or pinned."""
    def unpack(th):
        if s_water is None:
            s, rest = th[:3], th[3:]
        else:
            s, rest = np.array([th[0], s_water, th[1]]), th[2:]
        return s, np.abs(rest[:3]), np.abs(rest[3:6]), np.abs(rest[6:9])

    def resid(th):
        s, sig, M0, W0 = unpack(th)
        t = it.build_truth(base, s, sig)
        return [it.score(preds[n], t, M0, W0) - o for n, _, _, o in it.OBS]

    tail = [[.08, .09, .02, 12, 14, 16, 11, 12, 14], [.05, .06, .04, 15, 15, 15, 12, 12, 12]]
    heads = ([[1.025, 1.03, 1.02], [1.03, 1.05, 1.00]] if s_water is None
             else [[1.025, 1.02], [1.03, 1.00]])
    best = min((least_squares(resid, h + t, max_nfev=3000) for h, t in zip(heads, tail)),
               key=lambda r: r.cost)
    s, sig, M0, W0 = unpack(best.x)
    rms = float(np.sqrt(np.mean(np.square(resid(best.x)))))
    return it.build_truth(base, s, sig), M0, W0, s, rms


def best_lam(curves: np.ndarray) -> float:
    return float(GRID[int(np.argmax(curves))])


def run_splits(base, truth, M0, W0) -> pd.DataFrame:
    subs = [it.submission(base, lam, 1.0) for lam in GRID]
    i80 = int(np.where(GRID == ROUTING_LAMBDA)[0][0])
    n = len(base)
    t = pd.to_datetime(base.timestamp).to_numpy()
    wells = base.well_name.to_numpy()
    rng = np.random.default_rng(SEED)

    def curve(mask):
        return np.array([it.score(s[mask], truth[mask], M0, W0) for s in subs])

    full = curve(np.ones(n, bool))
    schemes: dict[str, list[np.ndarray]] = {
        "random 50/50": [rng.random(n) < 0.5 for _ in range(REPS)],
        "random 30% public": [rng.random(n) < 0.3 for _ in range(REPS)],
        "by well, 5 public": [np.isin(wells, rng.choice(np.unique(wells), 5, replace=False))
                              for _ in range(REPS // 4)],
        "time: Jan-Jun public": [t < np.datetime64("2025-07-01")],
        "time: Jan-Apr public": [t < np.datetime64("2025-05-01")],
    }
    rows = []
    for name, masks in schemes.items():
        lp, lq, regret_pub, regret_80 = [], [], [], []
        for m in masks:
            cp, cq = curve(m), curve(~m)
            jp, jq = int(np.argmax(cp)), int(np.argmax(cq))
            lp.append(GRID[jp]); lq.append(GRID[jq])
            regret_pub.append(cq[jq] - cq[jp])     # private loss from tuning on public
            regret_80.append(cq[jq] - cq[i80])     # private loss of shipping 0.80
        lp, lq, rp, r8 = map(np.asarray, (lp, lq, regret_pub, regret_80))
        rows.append({"split": name, "n": len(masks),
                     "lam* public": f"{np.median(lp):.2f} [{np.percentile(lp, 5):.2f}, {np.percentile(lp, 95):.2f}]",
                     "lam* private": f"{np.median(lq):.2f} [{np.percentile(lq, 5):.2f}, {np.percentile(lq, 95):.2f}]",
                     "private loss, public lam*: mean / p95": f"{rp.mean():.4f} / {np.percentile(rp, 95):.4f}",
                     "private loss of 0.80: mean / p95": f"{r8.mean():.4f} / {np.percentile(r8, 95):.4f}"})
    print(f"  full-data lam* = {best_lam(full):.2f}; score(0.80) = {full[i80]:.4f}, "
          f"score(1.00) = {full[np.where(GRID == 1.0)[0][0]]:.4f}, "
          f"score(lam*) = {full.max():.4f}")
    return pd.DataFrame(rows)


# ------------------------------------------------------------ B. real data
def time_drift() -> None:
    d = pd.read_parquet(PROC / "daily_table.parquet")
    tr = pd.read_parquet(PROC / "train_table.parquet")
    test_days = set()
    for r in tr.itertuples():
        for day in pd.date_range(pd.Timestamp(r.start).normalize(), pd.Timestamp(r.end).normalize()):
            test_days.add((r.well_name, day))
    d["date"] = pd.to_datetime(d.date)
    normal = d[(d.choke_pct__mean > 1)
               & ~pd.Series(list(zip(d.well_name, d.date))).isin(test_days).to_numpy()].copy()
    test_level = tr.groupby("well_name").whp_downstream_psia__mean.mean()
    normal["offset"] = normal.whp_downstream_psia__mean - normal.well_name.map(test_level)
    normal["month"] = normal.date.dt.to_period("M")
    m = normal.groupby(["well_name", "month"]).offset.mean().unstack()
    ratio = m.div(normal.groupby("well_name").offset.mean(), axis=0)

    print("\nB. ROUTING OFFSET BY MONTH (real sensors, the stronger result): normal-day whp_downstream minus the")
    print("   well's mean test-window whp_downstream, psi")
    print(m.round(1).to_string())
    field = ratio.mean(axis=0)            # equal weight per well
    print("\n   field mean of monthly offset / all-year offset, and the lambda it implies:")
    print(pd.DataFrame({"offset ratio": field.round(3),
                        "implied lambda": (ROUTING_LAMBDA * field).round(2)}).T.to_string())
    print(f"\n   per-well monthly ratio: min {ratio.min().min():.2f}, max {ratio.max().max():.2f}; "
          f"field monthly ratio {field.min():.3f} to {field.max():.3f}")
    print(f"   all-year offset per well, psi: {normal.groupby('well_name').offset.mean().round(1).to_dict()}")


def main() -> None:
    base = it.load_base()
    preds = {n: it.submission(base, lam, g) for n, lam, g, _ in it.OBS}
    print("A. SIMULATED PUBLIC/PRIVATE SPLITS (infer_truth scorer) -- ASSUMPTION-DEPENDENT")
    print("   A scorer model fitted to 9 leaderboard points, in 3 water-level worlds: a rough")
    print("   guide, not a measurement. Part B (real sensors) is the stronger result.")
    print("   lam* = best lambda on that half, median [5%, 95%]; loss in points out of 30\n")
    for label, sw in [("free fit", None), ("s_water = 0.99", 0.99), ("s_water = 1.07", 1.07)]:
        truth, M0, W0, s, rms = fit_world(base, preds, sw)
        print(f"-- world: {label}  (s = {np.round(s, 4).tolist()}, fit RMS {rms:.4f} on 9 scores)")
        print(run_splits(base, truth, M0, W0).to_string(index=False))
        print()
    time_drift()


if __name__ == "__main__":
    main()
