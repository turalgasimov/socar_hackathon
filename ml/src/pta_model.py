"""Model-based build-up interpretation: the radial diffusivity equation solved exactly.

Instead of fitting a Horner straight line through a chosen window, the whole build-up is
matched with the analytical solution of the diffusivity equation (the same family of models
that commercial PTA packages regress on):

    wellbore storage C  +  skin S  +  radial flow (k)  +  outer boundary (infinite | closed circle r_e)

solved in Laplace space and inverted with Stehfest (N = 12). Oilfield units:

    p_D = k h dp / (141.2 q B mu)      t_D = 0.0002637 k t / (phi mu ct rw^2)      C_D = 0.8936 C / (phi ct h rw^2)
    p_wD(s) = (s p_D0 + S) / ( s [1 + C_D s (s p_D0 + S)] )        (storage and skin on any reservoir model)

Build-up after a long production period t_p at rate q (superposition):
    dp_D(dt) = p_wD(dt_D) - [p_wD(t_pD + dt_D) - p_wD(t_pD)]
    infinite:  [ ] = 0.5 ln(1 + dt/t_p)        (t_p >> dt, logarithmic regime)
    closed:    [ ] = 2 dt_D / r_eD^2           (pseudo-steady state reached during t_p)
    constant pressure at r_e: [ ] = 0          (steady state reached during t_p; comparison only)

Fitted: ln k, S, ln C (+ ln r_e for the closed circle) by least squares on the build-up.
Reported, as the brief asks: k, S, the semi-log (Horner) slope the model implies
m = 162.6 q B mu / (k h), and dP_skin = 0.869 m S.

No data access here: callers pass the build-up points, the rate and the rock/fluid set.
"""
from __future__ import annotations

from math import factorial, log

import numpy as np
from scipy.optimize import least_squares
from scipy.special import ive, kve


def stehfest_weights(N: int = 12) -> np.ndarray:
    v = np.zeros(N)
    for i in range(1, N + 1):
        s = 0.0
        for k in range((i + 1) // 2, min(i, N // 2) + 1):
            s += k ** (N // 2) * factorial(2 * k) / (factorial(N // 2 - k) * factorial(k) * factorial(k - 1)
                                                      * factorial(i - k) * factorial(2 * k - i))
        v[i - 1] = (-1) ** (N // 2 + i) * s
    return v


V = stehfest_weights()
_NV = np.arange(1, len(V) + 1)


def invert(F, t: np.ndarray) -> np.ndarray:
    """Stehfest inversion of a vectorised Laplace-space function F(s) at times t."""
    a = log(2) / t
    return a * (F(a[:, None] * _NV[None, :]) @ V)


def pd_infinite(s):
    """Finite-wellbore radial flow, infinite reservoir (Laplace space, no storage/skin)."""
    b = np.sqrt(s)
    return kve(0, b) / (s * b * kve(1, b))


def pd_closed(reD: float):
    """Finite-wellbore radial flow inside a closed circle of radius reD (scaled Bessels, stable)."""
    def f(s):
        b = np.sqrt(s); a = b * reD
        R = kve(1, a) / ive(1, a) * np.exp(-2 * (a - b))
        return (kve(0, b) + R * ive(0, b)) / (s * b * (kve(1, b) - R * ive(1, b)))
    return f


def pd_constant_pressure(reD: float):
    """Finite-wellbore radial flow with a constant-pressure circle at reD (pressure support).
    Not used by the submitted fit; kept to show that the build-ups reject it (notebooks/PTA_Phase2.ipynb)."""
    def f(s):
        b = np.sqrt(s); a = b * reD
        R = kve(0, a) / ive(0, a) * np.exp(-2 * (a - b))
        return (kve(0, b) - R * ive(0, b)) / (s * b * (kve(1, b) + R * ive(1, b)))
    return f


def with_storage_skin(pD0, CD: float, S: float):
    return lambda s: (s * pD0(s) + S) / (s * (1 + CD * s * (s * pD0(s) + S)))


def buildup_dp(theta, dt_h, tp_h, q, rock, boundary):
    """Pressure change since shut-in, psi. theta = [ln k, S, ln C(, ln r_e)]."""
    k, S, C = np.exp(theta[0]), theta[1], np.exp(theta[2])
    h, phi, ct, rw, B, mu = (rock[x] for x in ("h", "phi", "ct", "rw", "B", "mu"))
    tD = 0.0002637 * k * dt_h / (phi * mu * ct * rw ** 2)
    CD = 0.8936 * C / (phi * ct * h * rw ** 2)
    if boundary == "infinite":
        pD = invert(with_storage_skin(pd_infinite, CD, S), tD) - 0.5 * np.log(1 + dt_h / tp_h)
    elif boundary == "closed":
        reD = np.exp(theta[3]) / rw
        pD = invert(with_storage_skin(pd_closed(reD), CD, S), tD) - 2 * tD / reD ** 2
    elif boundary == "constant_pressure":     # steady state reached during t_p: no superposition term
        reD = np.exp(theta[3]) / rw
        pD = invert(with_storage_skin(pd_constant_pressure(reD), CD, S), tD)
    else:
        raise ValueError(f"unknown boundary {boundary!r}")
    return 141.2 * q * B * mu / (k * h) * pD


def horner_slope(k, q, rock):
    """Semi-log slope (psi per log cycle, positive) implied by permeability k."""
    return 162.6 * q * rock["B"] * rock["mu"] / (k * rock["h"])


def fit_buildup(dt_h, dp_psi, tp_h, q, rock, k0, S0, C0, boundary="infinite", re0=None):
    th0 = [np.log(k0), S0, np.log(max(C0, 1e-3))]
    lo, hi = [np.log(k0 / 5), -6, np.log(1e-4)], [np.log(k0 * 5), 40, np.log(2)]
    if boundary in ("closed", "constant_pressure"):
        th0.append(np.log(re0)); lo.append(np.log(150)); hi.append(np.log(30000))
    # default tolerances = the configuration that produced the scored file. k and S are correlated,
    # so the misfit valley is flat: different starts or float32 vs float64 input move k by <= ~0.05%
    # (measured by ml/make_pta.py), which is the numerical precision of the reported digits.
    r = least_squares(lambda th: buildup_dp(th, dt_h, tp_h, q, rock, boundary) - dp_psi, th0,
                      bounds=(lo, hi), x_scale="jac")
    k, S, C = np.exp(r.x[0]), r.x[1], np.exp(r.x[2])
    m = horner_slope(k, q, rock)
    return dict(boundary=boundary, k=k, S=S, C=C, re=np.exp(r.x[3]) if len(r.x) == 4 else np.nan,
                m=m, dP_skin=0.869 * m * S, rms_psi=float(np.sqrt(np.mean(r.fun ** 2))),
                max_abs_psi=float(np.max(np.abs(r.fun))), theta=r.x)


def fit_best(dt_h, dp_psi, tp_h, q, rock, k0, S0, C0, re0, closed_gain=0.7):
    """Fit infinite and closed-circle models; keep the closed one only if it cuts the
    RMS misfit by more than 30%, i.e. the boundary is actually seen in the data."""
    inf = fit_buildup(dt_h, dp_psi, tp_h, q, rock, k0, S0, C0, "infinite")
    clo = fit_buildup(dt_h, dp_psi, tp_h, q, rock, k0, S0, C0, "closed", re0)
    best = clo if clo["rms_psi"] < closed_gain * inf["rms_psi"] else inf
    return best, inf, clo
