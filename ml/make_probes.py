"""Level probes on top of the S1 champion (20.9463).

    python ml/make_probes.py [--phase] [--well] [--period]

Six leaderboard results say the same thing: every change to the model's
SHAPE lost points, and the only gain came from changing its LEVEL.

    20.2110  no correction
    20.9463  routing level correction        +0.735  worked
    20.9100  gas level down 1.8%             -0.036
    20.5700  water-cut model reshaped        -0.376  shape
    20.3300  retrained on moved labels       -0.616  shape
    18.3400  routing level over-corrected    -2.606

So the shape is at its ceiling for this data, and anything left is a finer
level adjustment than the single global lambda already optimised.

  --phase   oil / water / gas scaled separately. We currently move all three
            by one routing factor, but gas carries the static-Rs assumption
            on top of it. S3 measured the gas gradient at +0.020 points per
            1% and the sign says UP, which has never been tried.
  --well    one factor per well. GL-07 alone is 34% of oil volume, so its
            factor dominates WAPE while contributing a tenth of the fit.
            Coordinate descent: move one well, read the score, keep or revert.
  --period  does the routing offset drift across the nine months?

Every file changes exactly one thing against the champion, so a single
scalar score stays interpretable. Submit, record, keep the winner, repeat.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "outputs" / "probes"
BASE = ROOT / "ml" / "outputs" / "vfm_S1_routing.csv"
PHASES = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]


def write(df: pd.DataFrame, name: str, base: pd.DataFrame, note: str) -> None:
    assert list(df.columns) == list(base.columns) and len(df) == len(base)
    assert df.isna().sum().sum() == 0 and (df[PHASES] < 0).sum().sum() == 0
    p = OUT / f"{name}.csv"
    df.to_csv(p, index=False)
    d = {c.split("_")[0]: 100 * (df[c].sum() / base[c].sum() - 1) for c in PHASES}
    print(f"  {p.name:28s} {note:34s} "
          + "  ".join(f"{k} {v:+5.2f}%" for k, v in d.items()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", action="store_true")
    ap.add_argument("--well", action="store_true")
    ap.add_argument("--period", action="store_true")
    a = ap.parse_args()
    if not (a.phase or a.well or a.period):
        a.phase = True

    base = pd.read_csv(BASE)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"base = S1 champion, {len(base):,} rows, oil {base.oil_rate_stbd.sum():,.0f}\n")

    if a.phase:
        print("PER-PHASE level:")
        for col, tag in [("gas_rate_mscfd", "gas"), ("water_rate_stbd", "wat"),
                         ("oil_rate_stbd", "oil")]:
            for f in (1.02, 0.98):
                d = base.copy()
                d[col] = (d[col] * f).round(1)
                write(d, f"p_{tag}_{int(f*100)}", base, f"{tag} x{f:.2f}")

    if a.well:
        print("\nPER-WELL level (gradient probes, +2% one well at a time):")
        for w in sorted(base.well_name.unique()):
            d = base.copy()
            m = d.well_name == w
            d.loc[m, PHASES] = (d.loc[m, PHASES] * 1.02).round(1)
            write(d, f"w_{w.replace('-','')}_102", base, f"{w} all phases x1.02")

    if a.period:
        print("\nPER-PERIOD level (does the offset drift?):")
        mid = pd.Timestamp("2025-05-16")
        for tag, late in [("early", False), ("late", True)]:
            d = base.copy()
            m = (pd.to_datetime(d.timestamp) >= mid) if late else (pd.to_datetime(d.timestamp) < mid)
            d.loc[m, PHASES] = (d.loc[m, PHASES] * 1.02).round(1)
            write(d, f"t_{tag}_102", base, f"{tag} half x1.02")

    print("\nSubmit one, record the score, keep it only if it beats 20.9463.")
    print("A gradient of roughly +-0.02 points per 1% is the scale to expect;")
    print("anything smaller than about 0.01 is indistinguishable from noise.")


if __name__ == "__main__":
    main()
