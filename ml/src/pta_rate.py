"""Oil rate at a shut-in from the MEASURED well tests, through the inflow relation (IPR).

    q_IPR = q_test(t) * (pbar - pwf_day) / (pbar - pwf_test(t))

q_test(t), pwf_test(t)  linear-in-time interpolation of the two tests that bracket t
pwf_day                 daily-mean gauge pressure of the day the rate is wanted for (flowing minutes)
pbar - pwf              drawdown from the build-up model (see drawdown())

The tests are the only measured rates, and the inflow relation is the same whether the well flows to
the test separator or to the production manifold, so this rate needs neither the VFM choke law nor the
routing correction. The test and the build-up use the same gauge, so the gauge->sandface offset cancels.
Validated by leave-one-out over the interior tests (loo_errors): MAE 1.85 %, bias -0.15 % on the six
PTA wells (python ml/eda/pta_probes.py).

Unscored as of 2026-11-22: it feeds the PTA probes in ml/outputs/candidates/, not the shipped file.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def interp_tests(t: pd.Timestamp, tests: pd.DataFrame):
    """Oil rate and gauge pwf at time t, interpolated linearly between the bracketing tests.
    `tests`: one well, columns test_mid, oil_rate_stbd, dh_pressure_psia."""
    tests = tests.sort_values("test_mid")
    prev, nxt = tests[tests.test_mid <= t].tail(1), tests[tests.test_mid > t].head(1)
    if prev.empty or nxt.empty:
        r = (nxt if prev.empty else prev).iloc[0]
        return float(r.oil_rate_stbd), float(r.dh_pressure_psia), "nearest test only"
    p, n = prev.iloc[0], nxt.iloc[0]
    f = (t - p.test_mid) / (n.test_mid - p.test_mid)
    return (float(p.oil_rate_stbd + f * (n.oil_rate_stbd - p.oil_rate_stbd)),
            float(p.dh_pressure_psia + f * (n.dh_pressure_psia - p.dh_pressure_psia)),
            f"{p.test_mid:%Y-%m-%d} .. {n.test_mid:%Y-%m-%d} (f = {f:.2f})")


def drawdown(m: float, skin: float, boundary: str, r_e: float, rw: float, area_acres: float) -> float:
    """pbar - pwf, psi, from the build-up model: (m / 1.1516) = 141.2 q B mu / (k h) times
    closed:    ln(r_e / rw) - 0.75 + S                (pseudo-steady state, fitted r_e)
    otherwise: ln(r_area / rw) - 0.5 + S             (steady state on the drainage-area radius)"""
    a = m / 1.1516
    if boundary == "closed":
        return a * (np.log(r_e / rw) - 0.75 + skin)
    r_area = np.sqrt(area_acres * 43560 / np.pi)
    return a * (np.log(r_area / rw) - 0.5 + skin)


def ipr_rate(t: pd.Timestamp, pwf_day: float, tests: pd.DataFrame, dd: float):
    """IPR oil rate at time t and flowing gauge pressure pwf_day; dd = pbar - pwf_day."""
    q_t, pwf_t, how = interp_tests(t, tests)
    return q_t * dd / (dd + (pwf_day - pwf_t)), q_t, pwf_t, how


def loo_errors(tests: pd.DataFrame, dd: float) -> pd.DataFrame:
    """Leave-one-out over the interior tests: each predicted from its two neighbours, IPR-adjusted."""
    tests = tests.sort_values("test_mid").reset_index(drop=True)
    rows = []
    for i in range(1, len(tests) - 1):
        t = tests.iloc[i]
        q_hat, q_n, _, _ = ipr_rate(t.test_mid, t.dh_pressure_psia, tests.drop(index=i), dd)
        rows.append(dict(test=t.test_mid, q_measured=t.oil_rate_stbd, q_ipr=q_hat,
                         err_ipr_pct=100 * (q_hat / t.oil_rate_stbd - 1),
                         err_interp_only_pct=100 * (q_n / t.oil_rate_stbd - 1)))
    return pd.DataFrame(rows)
