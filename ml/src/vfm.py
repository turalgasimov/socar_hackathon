"""The VFM model: sensors -> oil, water and gas rate.

Structure, chosen by the benchmark in ml/eda/benchmark_vfm.py:

  liquid   ln qL = a_well + b1 ln S + b2 ln dPc + b3 ln WHP + b4 ln GLR(qL)
           A subcritical choke law. GLR depends on qL, so prediction solves it
           implicitly rather than plugging in a guess.
  split    wc = a_well + s*t + c1*dp_tubing + c2*GL
           Water cut from the tubing pressure gradient, which responds to the
           density of what is flowing. Beats a plain per-well time trend by
           0.54 pp [+0.16, +1.04], well-cluster bootstrapped.
  gas      oil * Rs / 1000, Rs static per well. Carries a +2.3% bias; every
           history-based GOR estimate tested costs more variance than it
           removes (see agent/NEXT_STEPS.md, tried and rejected).

Time-forward oil MAPE 2.67% (nested-selected, honest). The same nested run
picks this variant in 54 of 55 folds, which is why it is hard-coded here.

Fitted parameters are plain arrays, so joblib round-trips cleanly and the UI
can load the model without importing a training stack.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.linalg import lstsq
from scipy.optimize import brentq

EPOCH = pd.Timestamp("2025-01-01")

# columns the model needs, and where they come from in a window-aggregate table
SOURCE = {
    "whp": "whp_psia__mean",
    "dpc": "dp_choke__mean",
    "dp_tubing": "dp_tubing__mean",
    "gl": "gas_lift_rate_mscfd__mean",
    "choke_pct": "choke_pct__mean",
}


def build_inputs(df: pd.DataFrame, when: str = "start") -> pd.DataFrame:
    """Map a window-aggregate table (train_table / daily_table) to model inputs."""
    out = pd.DataFrame({"well_name": df.well_name.astype(str).values})
    for k, col in SOURCE.items():
        out[k] = df[col].values
    out["S"] = out.choke_pct / 100 * df.choke_max_size_64ths.values   # bean size, 1/64 in
    out["rs"] = df.solution_gor_at_pb_scf_stb.values
    out["t"] = (pd.to_datetime(df[when]) - EPOCH).dt.total_seconds().values / 86400
    return out


@dataclass
class VFMModel:
    """Fitted choke-law VFM. Call fit(), then predict()."""

    wells: list[str] = field(default_factory=list)
    choke_coef: np.ndarray | None = None   # [n_wells intercepts, lnS, lnDPc, lnWHP, lnGLR]
    wc_coef: np.ndarray | None = None      # [n_wells intercepts, t, dp_tubing, gl]
    routing_factor: float = 1.0            # see note in predict()
    trained_on: int = 0

    # ---------------------------------------------------------------- fitting
    def _dummies(self, well: np.ndarray) -> np.ndarray:
        return np.stack([(well == w).astype(float) for w in self.wells], axis=1)

    def fit(self, X: pd.DataFrame, oil: np.ndarray, water: np.ndarray) -> "VFMModel":
        qL = oil + water
        wc = water / qL
        self.wells = sorted(pd.unique(X.well_name))
        W = self._dummies(X.well_name.values)

        # water cut: tubing gradient + gas-lift rate + time, per-well intercept
        A = np.c_[W, X.t.values, X.dp_tubing.values, X.gl.values]
        self.wc_coef = lstsq(A, wc, rcond=None)[0]

        # choke law. On training rows qL is known, so GLR is computed directly.
        glr = (X.gl.values + qL * (1 - wc) * X.rs.values / 1000) / qL
        C = np.c_[W, np.log(X.S.values), np.log(X.dpc.values),
                  np.log(X.whp.values), np.log(glr)]
        self.choke_coef = lstsq(C, np.log(qL), rcond=None)[0]
        self.trained_on = len(X)
        return self

    # ------------------------------------------------------------- prediction
    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Return oil / water / gas rates.

        `routing_factor` multiplies the liquid rate and defaults to 1.0 (off).
        The model already responds to the lower choke drop of a normal
        production day through the dPc term, so no correction is applied
        unless the organisers confirm the ground truth is defined differently.
        See agent/PROJECT_STATE.md, Open risks.
        """
        if self.choke_coef is None:
            raise RuntimeError("model is not fitted")
        unknown = set(X.well_name) - set(self.wells)
        if unknown:
            raise ValueError(f"model has no intercept for {sorted(unknown)}; "
                             "it does not generalise to unseen wells")
        W = self._dummies(X.well_name.values)
        b, n = self.choke_coef, len(self.wells)

        wc = np.c_[W, X.t.values, X.dp_tubing.values, X.gl.values] @ self.wc_coef
        wc = np.clip(wc, 0.0, 0.95)

        # A fully closed choke means the well is shut in and produces nothing.
        # That is a hard zero, not something to extrapolate a log-law onto --
        # ln(S) is undefined at S=0. Affects the middle days of the multi-day
        # build-ups; partial days are modelled normally from the day's mean.
        shut = X.S.values <= 0

        S = np.where(shut, 1.0, X.S.values)  # placeholder, masked out below
        base = (W @ b[:n] + b[n] * np.log(S)
                + b[n + 1] * np.log(X.dpc.values) + b[n + 2] * np.log(X.whp.values))
        b_glr = b[n + 3]
        gl, rs = X.gl.values, X.rs.values

        qL = np.zeros(len(X))
        for i in np.flatnonzero(~shut):
            def f(lq: float, i: int = i) -> float:
                q = np.exp(lq)
                glr = (gl[i] + q * (1 - wc[i]) * rs[i] / 1000) / q
                return base[i] + b_glr * np.log(glr) - lq
            qL[i] = np.exp(brentq(f, np.log(10.0), np.log(1e6)))

        qL *= self.routing_factor
        wc = np.where(shut, 0.0, wc)
        oil = qL * (1 - wc)
        return pd.DataFrame({
            "well_name": X.well_name.values,
            "oil_rate_stbd": oil,
            "water_rate_stbd": qL * wc,
            "gas_rate_mscfd": oil * rs / 1000,
            "water_cut_frac": wc,
        })

    # ----------------------------------------------------------- persistence
    def save(self, path: str | Path) -> Path:
        import joblib
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @staticmethod
    def load(path: str | Path) -> "VFMModel":
        import joblib
        return joblib.load(Path(path))

    # ------------------------------------------------------------- reporting
    def coefficients(self) -> pd.Series:
        n = len(self.wells)
        return pd.Series(
            {"exp_choke_size_S": self.choke_coef[n],
             "exp_choke_dP": self.choke_coef[n + 1],
             "exp_WHP": self.choke_coef[n + 2],
             "exp_GLR": self.choke_coef[n + 3]})
