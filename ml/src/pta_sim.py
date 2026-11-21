"""Radial finite-difference simulator — an independent check on the Laplace model.

`ml/src/pta_model.py` solves the diffusivity equation in Laplace space and
inverts with Stehfest (N = 12). This solves the same equation in the time
domain: implicit variable-step BDF2 on a log-spaced radial grid, with
geometrically growing time steps. The two share no code and no numerical
machinery, so agreement between them tests the implementation rather than the
assumption.

Written deliberately by the agent that did NOT write pta_model.py.

Physics, oilfield units, time in hours:

    PV_i ct dp_i/dt = sum of inter-cell Darcy flow        (rb/hr per cell)
    flow_{i,i+1}    = 0.00708 k h (p_{i+1}-p_i) / (mu ln(r_{i+1}/r_i)) / 24
    wellbore         cell 0, capacity C rb/psi, production drawn from it
    outer boundary   no-flow (closed) or fixed pressure (constant-pressure)

It takes an arbitrary rate schedule, so it carries multi-rate superposition
natively and needs no superposition approximation at all — unlike the Laplace
build-up, which assumes either `0.5 ln(1+dt/tp)` or PSS.

SKIN, AND WHY THE TWO CODES ARE NOT THE SAME MODEL
--------------------------------------------------
Skin enters here as an EFFECTIVE WELLBORE RADIUS rw' = rw exp(-S), not as an
explicit pressure drop. Three of our six wells have NEGATIVE skin, and there an
explicit skin resistance in series with the first cell gives a conductance

    T = alpha k h / (mu (ln(r_1/rw) + S)) / 24

whose denominator is negative: on a log grid fine enough to resolve storage,
ln(r_1/rw) is ~0.03, so any S < -0.03 flips the sign and the system is
ill-posed. The effective radius is unconditionally well behaved.

The substitution is exact for a thin steady-state skin in the RESERVOIR, but it
is NOT exact once wellbore storage is present, because `pta_model.py` references
C_D and t_D to the true rw while this grid starts at rw'. `verify()` measures
that gap: it is 0.01-0.09 psi on five wells and 0.89 psi on GL-08 (S = -1.589),
i.e. 0.004-0.17% of the build-up. That is a property of the two formulations,
not of either solver, and it is why `verify()` reports BOTH comparisons.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_banded

SKIN_C = 141.2         # the Laplace code's dp = 141.2 q B mu pD / (k h)
ALPHA = 1.0 / SKIN_C   # Darcy constant, DERIVED from SKIN_C -- see below

# ALPHA is 1/141.2, not the 0.00708 usually quoted for 2 pi x 1.127e-3. The two
# differ by 0.030%, and that mismatch is visible: with 0.00708 the FD sat a flat
# 0.027% away from the Laplace curve on every well -- the same RELATIVE offset
# for wells with quite different k, S, C and h, which is the signature of a
# constant rather than of discretisation. Deriving ALPHA from SKIN_C makes the
# two codes share the constant by construction: steady radial flow gives
# dp = q B mu ln(r2/r1) / (ALPHA k h) here and 141.2 q B mu ln(r2/r1) / (k h)
# there, so ALPHA = 1/141.2 exactly. The diffusivity then follows as
# 5.615 / (141.2 x 48 pi) = 2.6379e-4, against the 0.0002637 in pta_model.py.


def make_grid(rw: float, re: float, n: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Log-spaced cell centres and the pore-volume factor pi(r_out^2-r_in^2)."""
    edges = np.geomspace(rw, re, n + 1)
    centres = np.sqrt(edges[:-1] * edges[1:])            # geometric, right for log flow
    area = np.pi * (edges[1:] ** 2 - edges[:-1] ** 2)
    return centres, area


def time_steps(dur: float, n: int, eps: float = 1e-9) -> np.ndarray:
    """Geometrically growing steps covering [0, dur].

    A build-up is logarithmic in time, so uniform steps spend their effort where
    nothing happens and under-resolve the storage-dominated start. Measured on
    GL-01: 400 geometric steps beat 12,000 uniform ones by 20x (0.107 vs 2.097
    psi) at a thirtieth of the cost.
    """
    return np.diff(np.concatenate([[0.0], dur * np.geomspace(eps, 1.0, n)]))


def simulate(k, S, C, rock, schedule, re=None, boundary="closed",
             n_cells=200, p_init=0.0, re_mult=12.0, steps_per_segment=800,
             eps=1e-9, order=2):
    """Run a rate schedule; return (time_h, well-pressure CHANGE from p_init).

    `schedule` is [(duration_h, q_stb_d), ...]; positive q is production, so
    the pressure change is negative while flowing. `order=2` is variable-step
    BDF2 (first step implicit Euler, which BDF2 needs to start); `order=1`
    forces implicit Euler throughout and is kept only to show the difference.

    The wellbore is cell 0 with capacity C, so storage is implicit and the
    matrix stays tridiagonal.
    """
    h, phi, ct, rw, B, mu = (rock[x] for x in ("h", "phi", "ct", "rw", "B", "mu"))
    rwe = rw * np.exp(-S)
    total_h = sum(d for d, _ in schedule)
    if re is None or boundary == "infinite":
        r_inv = 0.0325 * np.sqrt(max(k, 1e-9) * total_h / (phi * mu * ct))
        re = max(re_mult * r_inv, 50 * rw)
    r, area = make_grid(rwe, re, n_cells)
    stor = np.empty(n_cells + 1)
    stor[0] = C                                   # wellbore, rb/psi
    stor[1:] = area * h * phi / 5.615 * ct        # reservoir cells, rb/psi
    # conductances, rb/hr/psi: well<->cell1 then cell i<->i+1
    T = np.empty(n_cells)
    T[0] = ALPHA * k * h / (mu * np.log(r[0] / rwe)) / 24.0
    T[1:] = ALPHA * k * h / (mu * np.log(r[1:] / r[:-1])) / 24.0
    n = n_cells + 1

    # the Laplacian band is fixed; only the capacity term changes with dt
    lap = np.zeros((3, n))
    lap[1, :-1] += T
    lap[1, 1:] += T
    lap[0, 1:] = -T
    lap[2, :-1] = -T
    if boundary == "constant_pressure":
        lap[:, -1] = 0.0
        lap[1, -1] = 1.0
        lap[2, -2] = 0.0

    p = np.full(n, float(p_init))
    out_t, out_p = [0.0], [0.0]
    t = 0.0
    for dur, q_surf in schedule:
        p_prev = dt_prev = None                   # BDF2 restarts each segment
        src = -q_surf * B / 24.0                  # production out of the wellbore
        for dt in time_steps(dur, max(int(steps_per_segment), 2), eps):
            ab = lap.copy()
            if order == 1 or p_prev is None:      # implicit Euler
                ab[1] += stor / dt
                rhs = stor * p / dt
            else:                                 # variable-step BDF2
                w = dt / dt_prev
                c = stor / dt
                ab[1] += c * (1 + 2 * w) / (1 + w)
                rhs = c * ((1 + w) * p - w * w / (1 + w) * p_prev)
            rhs[0] += src
            if boundary == "constant_pressure":
                ab[1, -1], ab[0, -1], rhs[-1] = 1.0, 0.0, p_init
            p_new = solve_banded((1, 1), ab, rhs)
            p_prev, dt_prev, p = p, dt, p_new
            t += dt
            out_t.append(t)
            out_p.append(p[0] - p_init)
    return np.array(out_t), np.array(out_p)


def buildup(k, S, C, rock, q, tp_h, dt_h, re=None, boundary="closed", **kw):
    """Pressure RISE since shut-in, on the requested dt grid, to compare with
    pta_model.buildup_dp (which returns the same quantity)."""
    span = float(np.max(dt_h))
    t, p = simulate(k, S, C, rock, [(tp_h, q), (span, 0.0)], re=re,
                    boundary=boundary, **kw)
    mask = t >= tp_h
    t_bu, p_bu = t[mask] - tp_h, p[mask]
    return np.interp(dt_h, t_bu, p_bu - p_bu[0])
