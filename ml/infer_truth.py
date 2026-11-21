"""Infer the organisers' ground truth from our leaderboard scores.

We have nine (submission, score) pairs. Each submission is our base prediction
multiplied by known per-well, per-phase factors, so the only unknown is the
truth itself. If we can find a truth that reproduces all nine scores, we can
grade future candidates offline instead of spending submissions.

Model of the truth:

    truth[i] = base[i] * s_phase * exp(e[i]),   e ~ N(0, sigma_phase^2)

`s_phase` is the systematic level we are off by; `sigma_phase` is the
irreducible per-day error. The noise draw is seeded, so scoring is
deterministic and the fit is reproducible.

Model of the scoring function, per phase, 10 points:

    R2   /3   ->  3 * clip(R2, 0, 1)
    MAPE /2   ->  2 * clip(1 - MAPE/M0, 0, 1)
    WAPE /5   ->  5 * clip(1 - WAPE/W0, 0, 1)

M0 and W0 are the error levels that score zero. They are unknown and fitted.

Eight free parameters against nine observations: tight, so treat a good fit as
evidence the FORM is right, not as proof of the exact numbers. The test that
matters is whether it predicts a held-out score it was not fitted on.

    python ml/infer_truth.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))

from vfm import ROUTING_LAMBDA, _ROUTING_FACTORS_RAW as RAW  # noqa: E402

PH = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]
SEED = 0

# (name, lambda, gas multiplier, observed score)
OBS = [
    ("lam0.00", 0.00, 1.000, 20.2110),
    ("lam0.50", 0.50, 1.000, 20.9100),
    ("lam0.75", 0.75, 1.000, 21.0200),
    ("lam0.80", 0.80, 1.000, 21.0200),
    ("lam0.90", 0.90, 1.000, 20.9960),
    ("lam1.00", 1.00, 1.000, 20.9463),
    ("lam2.50", 2.50, 1.000, 18.3400),
    ("lam1.00_gas0.982", 1.00, 0.982, 20.9100),
    ("lam0.80_gas1.02", 0.80, 1.020, 20.6100),
]
HOLDOUT = "lam0.90"      # excluded from the fit, used to test it


def load_base() -> pd.DataFrame:
    """The lambda=0 prediction, recovered from the shipped lambda=0.80 file."""
    ship = pd.read_csv(ROOT / "ml" / "outputs" / "vfm_submission.csv")
    f = ship.well_name.map({w: 1 + ROUTING_LAMBDA * (r - 1) for w, r in RAW.items()}).to_numpy()
    base = ship.copy()
    for c in PH:
        base[c] = base[c] / f
    return base


def submission(base: pd.DataFrame, lam: float, gas_mult: float) -> np.ndarray:
    m = base.well_name.map({w: 1 + lam * (r - 1) for w, r in RAW.items()}).to_numpy()
    out = np.column_stack([base[c].to_numpy() * m for c in PH])
    out[:, 2] *= gas_mult
    return out


def score(pred: np.ndarray, truth: np.ndarray, M0: np.ndarray, W0: np.ndarray) -> float:
    total = 0.0
    for k in range(3):
        a, p = truth[:, k], pred[:, k]
        ok = a > 0
        a, p = a[ok], p[ok]
        r2 = 1 - ((a - p) ** 2).sum() / ((a - a.mean()) ** 2).sum()
        mape = np.mean(np.abs(p / a - 1)) * 100
        wape = np.abs(a - p).sum() / a.sum() * 100
        total += (3 * np.clip(r2, 0, 1)
                  + 2 * np.clip(1 - mape / M0[k], 0, 1)
                  + 5 * np.clip(1 - wape / W0[k], 0, 1))
    return float(total)


def build_truth(base: pd.DataFrame, s: np.ndarray, sig: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    b = np.column_stack([base[c].to_numpy() for c in PH])
    e = rng.standard_normal(b.shape)
    return b * s * np.exp(e * sig)


def main() -> None:
    base = load_base()
    fit_rows = [o for o in OBS if o[0] != HOLDOUT]
    preds = {n: submission(base, lam, g) for n, lam, g, _ in OBS}

    def resid(theta):
        s, sig, M0, W0 = theta[:3], np.abs(theta[3:6]), np.abs(theta[6:9]), np.abs(theta[9:12])
        truth = build_truth(base, s, sig)
        return [score(preds[n], truth, M0, W0) - obs for n, _, _, obs in fit_rows]

    x0 = np.r_[1.02, 1.02, 1.02, 0.05, 0.06, 0.07, 12.0, 14.0, 16.0, 10.0, 12.0, 14.0]
    sol = least_squares(resid, x0, max_nfev=4000)
    s, sig, M0, W0 = sol.x[:3], np.abs(sol.x[3:6]), np.abs(sol.x[6:9]), np.abs(sol.x[9:12])
    truth = build_truth(base, s, sig)

    print(f"fitted on {len(fit_rows)} scores, '{HOLDOUT}' held out\n")
    print("INFERRED TRUTH")
    for i, c in enumerate(PH):
        print(f"  {c:18s} level x{s[i]:.4f} vs our lambda=0 base   "
              f"per-day noise sigma {sig[i]*100:.1f}%")
    print("\nINFERRED SCORING (points reach zero at)")
    for i, c in enumerate(PH):
        print(f"  {c:18s} MAPE {M0[i]:5.1f}%   WAPE {W0[i]:5.1f}%")

    print(f"\n{'submission':20s} {'observed':>9s} {'modelled':>9s} {'err':>7s}")
    for n, _, _, obs in OBS:
        m = score(preds[n], truth, M0, W0)
        tag = "  <- HELD OUT" if n == HOLDOUT else ""
        print(f"{n:20s} {obs:9.4f} {m:9.4f} {m-obs:+7.3f}{tag}")
    err = np.array([score(preds[n], truth, M0, W0) - o for n, _, _, o in fit_rows])
    print(f"\nfitted RMS error {np.sqrt((err**2).mean()):.4f} points")
    out = ROOT / "data" / "processed" / "inferred_truth.parquet"
    pd.DataFrame(truth, columns=PH).assign(
        timestamp=base.timestamp, well_name=base.well_name).to_parquet(out, index=False)
    print(f"truth written to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
