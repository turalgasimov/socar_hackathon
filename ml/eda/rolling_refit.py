"""Frozen model or a model refitted as new well tests arrive? A calendar rehearsal.

The test data are the next three months of the same wells and include a well_tests.csv for those
months. If those tests may be used as input, the model can be refitted during the period instead
of staying as it was on the last training day. This measures what that is worth, inside the data
we have. For a cut-off date C and the three months after it:

    frozen    one model, fitted on every test that ended before C; used for all three months
    monthly   refitted at the start of each month, on every test that ended before that month
    per-test  refitted for each scored test, on every test that ended before that test started

All three see no future information. All wells' tests are used, the scored well's included, as
long as they ended in time. A well is scored only if it has 3 tests before C (as time-forward).
The per-test prediction of a test does not depend on C; the frozen one does, so several cut-offs
give the frozen model's error by lead time against the same refitted predictions.

Every label is a test-separator rate and the fits carry no routing correction, exactly as in the
time-forward table of ml/fit_vfm.py. So this compares the two schemes; it does not predict a score.

    python ml/eda/rolling_refit.py      (~10 s, needs data/processed/train_table.parquet)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "src"))
sys.path.insert(0, str(ROOT / "ml"))

from config import PROC  # noqa: E402
from fit_vfm import MIN_HISTORY, bias, mape, r2, wape  # noqa: E402
from vfm import VFMModel, build_inputs  # noqa: E402

CUTOFFS = ["2025-04-01", "2025-05-01", "2025-06-01", "2025-07-01"]
HEADLINE = "2025-07-01"          # the longest training period that leaves three months to score
SCHEMES = ["frozen", "monthly", "per-test"]
PHASES = {"oil": "oil_rate_stbd", "water": "water_rate_stbd", "gas": "gas_rate_mscfd"}
BOOT, SEED = 5000, 1


def run() -> pd.DataFrame:
    tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(["well_name", "start"], ignore_index=True)
    X = build_inputs(tr)
    y = {p: tr[c].to_numpy() for p, c in PHASES.items()}
    start, end = pd.to_datetime(tr.start).to_numpy(), pd.to_datetime(tr.end).to_numpy()
    well = tr.well_name.astype(str).to_numpy()
    cache: dict[np.datetime64, VFMModel] = {}

    def model(before) -> tuple[VFMModel, np.ndarray]:
        """Fitted on every test that ended before `before`."""
        before = np.datetime64(before)
        m = end < before
        if before not in cache:
            cache[before] = VFMModel().fit(X[m], y["oil"][m], y["water"][m])
        return cache[before], m

    rows = []
    for c in map(pd.Timestamp, CUTOFFS):
        _, m0 = model(c)
        for i in np.where((start >= c) & (start < c + pd.DateOffset(months=3)))[0]:
            if (m0 & (well == well[i])).sum() < MIN_HISTORY:
                continue
            s = pd.Timestamp(start[i])
            cuts = {"frozen": c, "monthly": max(c, s.to_period("M").start_time), "per-test": s}
            row = {"cutoff": c, "well": well[i], "start": s,
                   "lead": (s.year - c.year) * 12 + s.month - c.month + 1,
                   **{f"real_{p}": y[p][i] for p in PHASES}}
            for name, cut in cuts.items():
                fit, m = model(cut)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    pred = fit.predict(X.iloc[[i]]).iloc[0]
                row[f"n_{name}"] = int(m.sum())
                row[f"own_{name}"] = int((m & (well == well[i])).sum())
                for p, col in PHASES.items():
                    row[f"{name}_{p}"] = pred[col]
            rows.append(row)
    return pd.DataFrame(rows)


def table(d: pd.DataFrame) -> pd.DataFrame:
    out = []
    for s in SCHEMES:
        for p in PHASES:
            a, q = d[f"real_{p}"].to_numpy(), d[f"{s}_{p}"].to_numpy()
            out.append({"scheme": s, "phase": p, "R2": r2(a, q), "MAPE %": mape(a, q),
                        "WAPE %": wape(a, q), "bias %": bias(a, q)})
    return pd.DataFrame(out)


def gap_ci(d: pd.DataFrame, phase: str, a: str = "per-test", b: str = "frozen") -> tuple[float, float, float]:
    """WAPE(a) - WAPE(b) in points, with a well-cluster bootstrap 95% interval."""
    rng = np.random.default_rng(SEED)
    groups = [g for _, g in d.groupby("well")]
    def gap(x):
        r = x[f"real_{phase}"].to_numpy()
        return wape(r, x[f"{a}_{phase}"].to_numpy()) - wape(r, x[f"{b}_{phase}"].to_numpy())
    boots = [gap(pd.concat([groups[j] for j in rng.integers(0, len(groups), len(groups))]))
             for _ in range(BOOT)]
    return gap(d), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def main() -> None:
    d = run()
    fmt = {"R2": "{:.4f}".format, "MAPE %": "{:.2f}".format, "WAPE %": "{:.2f}".format, "bias %": "{:+.2f}".format}

    h = d[d.cutoff == HEADLINE]
    print(f"A. CUT-OFF {HEADLINE}: fitted on Jan-Jun, scored on the {len(h)} tests of Jul-Sep "
          f"({h.well.nunique()} wells)")
    print(f"   tests in the fit: frozen {h.n_frozen.iloc[0]}; per-test {h['n_per-test'].min()}-{h['n_per-test'].max()}"
          f" (the scored well's own: {h.own_frozen.min()}-{h.own_frozen.max()} frozen, "
          f"{h['own_per-test'].min()}-{h['own_per-test'].max()} per-test)\n")
    print(table(h).to_string(index=False, formatters=fmt))

    print("\n   by month after the cut-off (oil WAPE %, oil bias %):")
    for lead, g in h.groupby("lead"):
        print(f"   month {lead} (n={len(g)}): " + "; ".join(
            f"{s} {wape(g.real_oil.values, g[f'{s}_oil'].values):.2f} / {bias(g.real_oil.values, g[f'{s}_oil'].values):+.2f}"
            for s in SCHEMES))

    print(f"\nB. ALL CUT-OFFS {', '.join(CUTOFFS)}, three months each ({len(d)} cut-off/test pairs)")
    print("   WAPE % (bias %) by month after the cut-off: frozen -> per-test")
    for lead, g in d.groupby("lead"):
        cells = []
        for p in PHASES:
            a = g[f"real_{p}"].values
            cells.append(f"{p} {wape(a, g[f'frozen_{p}'].values):.2f} ({bias(a, g[f'frozen_{p}'].values):+.2f})"
                         f" -> {wape(a, g[f'per-test_{p}'].values):.2f} ({bias(a, g[f'per-test_{p}'].values):+.2f})")
        print(f"   month {lead} (n={len(g)}): " + "; ".join(cells))
    print("\n   all three months together:")
    print(table(d).to_string(index=False, formatters=fmt))
    print("\n   by cut-off (does a longer training period shrink the gain?), oil WAPE % frozen -> per-test:")
    for c, g in d.groupby("cutoff"):
        a = g.real_oil.values
        print(f"   {c:%Y-%m-%d} (n={len(g)}, {g.n_frozen.iloc[0]} tests in the frozen fit): "
              f"{wape(a, g.frozen_oil.values):.2f} -> {wape(a, g['per-test_oil'].values):.2f}"
              f"  ({wape(a, g['per-test_oil'].values) - wape(a, g.frozen_oil.values):+.2f})")

    print(f"\nC. IS THE GAP REAL? WAPE(per-test) - WAPE(frozen), points; well-cluster bootstrap, {BOOT} resamples")
    for label, x in [(f"cut-off {HEADLINE}", h), ("all cut-offs", d)]:
        for p in PHASES:
            g, lo, hi = gap_ci(x, p)
            print(f"   {label:19s} {p:5s} {g:+.2f} [{lo:+.2f}, {hi:+.2f}]"
                  + ("" if lo <= 0 <= hi else "   <- interval excludes 0"))
    print("\n   monthly against per-test (all cut-offs):")
    for p in PHASES:
        g, lo, hi = gap_ci(d, p, "monthly", "per-test")
        print(f"   WAPE(monthly) - WAPE(per-test) {p:5s} {g:+.2f} [{lo:+.2f}, {hi:+.2f}]")


if __name__ == "__main__":
    main()
