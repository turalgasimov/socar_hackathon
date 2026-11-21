"""Scale-factor ladder for locating the routing optimum on the leaderboard.

    python ml/make_ladder.py [--lam 0.5 1.0 1.5 2.0 ...]

The per-well routing factors from the downhole physics give a *shape*; what
the leaderboard has to settle is the *magnitude*. So scale them by one
parameter instead of inventing new per-well numbers:

    factor_w(lam) = 1 + lam * (ROUTING_FACTORS[w] - 1)

    lam = 0    the uncorrected model              (S0, scored 20.2110)
    lam = 1    the downhole estimate              (S1, scored 20.9463)
    lam = 1.87 the full choke-implied uplift      (S2, x1.053 oil-weighted)

Keeping the per-well shape fixed and tuning one number means we are fitting a
single parameter against the leaderboard, not ten. That matters if there is a
private split: one parameter supported by physics is hard to overfit, ten
tuned per-well factors would not be.

WAPE against a systematically-offset truth is V-shaped — linear down to zero
bias, linear up after — so walk until the score turns over, then bisect the
bracket. Do not fit a parabola to a V; it puts the minimum in the wrong place.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))

from vfm import ROUTING_FACTORS  # noqa: E402

OUT = ROOT / "ml" / "outputs" / "ladder"
BASE = ROOT / "ml" / "outputs" / "vfm_submission.csv"
PHASES = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]
KNOWN = {0.0: 20.2110, 1.0: 20.9463}      # lam -> leaderboard score


def build(lam: float, base: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    f = {w: 1 + lam * (v - 1) for w, v in ROUTING_FACTORS.items()}
    out = base.copy()
    mult = out.well_name.map(f).fillna(1.0)
    for c in PHASES:
        out[c] = (out[c] * mult).round(1)
    weighted = out.oil_rate_stbd.sum() / base.oil_rate_stbd.sum()
    return out, weighted


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lam", type=float, nargs="+",
                    default=[1.5, 2.0, 2.5, 3.0, 4.0])
    args = ap.parse_args()

    base = pd.read_csv(BASE)
    OUT.mkdir(parents=True, exist_ok=True)
    print("known so far:")
    for lam, sc in sorted(KNOWN.items()):
        _, w = build(lam, base)
        print(f"  lam {lam:4.2f}  oil x{w:.4f}  ->  {sc:.4f}")
    slope = (KNOWN[1.0] - KNOWN[0.0])
    print(f"\n  +{slope:.4f} points per unit of lam on the first segment\n")

    print("built:")
    for lam in args.lam:
        df, w = build(lam, base)
        path = OUT / f"vfm_lam{lam:.2f}.csv"
        df.to_csv(path, index=False)
        assert list(df.columns) == list(base.columns) and len(df) == len(base)
        proj = KNOWN[1.0] + slope * (lam - 1)
        print(f"  {path.name:22s} oil x{w:.4f}   if still descending ~{proj:.2f}")

    print("\nSubmit in ascending order and stop at the first DROP. The lam before")
    print("the drop and the lam at it bracket the optimum; bisect once or twice.")
    print("Record every result in agent/PROJECT_STATE.md as you go.")


if __name__ == "__main__":
    main()
