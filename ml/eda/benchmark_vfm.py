"""
VFM benchmark — reproduces the model-comparison table in docs/DATA_REPORT_TASK1_TASK2.md (§2.2).

Uses ONLY well_tests.csv (+ choke_events, completion, pvt). High-frequency data is not needed here,
because the sensor columns in well_tests are exactly the HF means over each test window (verified,
|diff| < 0.4 psi). Labels = 85 well tests.

Protocol
  LOO  : leave-one-test-out. For each of the 85 tests: fit on the other 84, predict the held-out one.
  LOWO : leave-one-well-out. Fit on 9 wells, predict all tests of the 10th (unseen well).
  Metric: MAPE = mean(|pred / true - 1|) on liquid rate (oil + water), in %.

Run:  python ml/eda/benchmark_vfm.py            (data dir defaults to <repo>/data)
      python ml/eda/benchmark_vfm.py --data PATH

NOTE: LOO here is leave-one-TEST-out with well intercepts (interpolation in time). AGENTS.md argues
random/LOO splits leak the well level; compare against the time-forward scheme in
ml/eda/validate_features.py before drawing conclusions.
"""
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.linalg import lstsq
from scipy.optimize import brentq
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import RidgeCV

warnings.filterwarnings("ignore")
M3_PER_MSCF = 28.3168


# ----------------------------------------------------------------------------------------------
# 1. Load + repair labels
# ----------------------------------------------------------------------------------------------
def load_tests(d: Path) -> pd.DataFrame:
    t = pd.read_csv(d / "well_tests.csv", parse_dates=["test_start", "test_end"])
    ch = pd.read_csv(d / "choke_events.csv", parse_dates=["timestamp"])
    cp = pd.read_csv(d / "well_completion.csv")
    pvt = pd.read_csv(d / "reservoir_pvt.csv")

    # label repair (found via redundancy: liquid=oil+water, GOR=gas/oil, total_gas=gas+GL)
    for c in ["water_rate_stbd", "gas_rate_mscfd", "gas_lift_rate_mscfd", "total_gas_rate_mscfd"]:
        t[c] = t[c].abs()                                    # 5 sign flips
    m6 = t.well_name == "GL-06"                               # GL-06 gas reported in m3/d
    t.loc[m6, ["gas_rate_mscfd", "total_gas_rate_mscfd"]] /= M3_PER_MSCF

    t = t.merge(cp, on="well_name").merge(pvt, on="well_name")
    t["mid"] = t.test_start + (t.test_end - t.test_start) / 2
    t["t_days"] = (t.mid - pd.Timestamp("2025-01-01")).dt.total_seconds() / 86400

    def choke_at(well, ts):  # choke is a step function: last event at or before ts
        c = ch[(ch.well_name == well) & (ch.timestamp <= ts)]
        return c.choke_opening_pct.iloc[-1]

    t["choke"] = [choke_at(r.well_name, r.mid) for r in t.itertuples()]
    t = t.sort_values(["well_name", "mid"]).reset_index(drop=True)

    # physics features
    t["S"] = t.choke / 100 * t.choke_max_size_64ths           # bean size, 1/64 in
    t["dpc"] = t.whp_psia - t.whp_downstream_psia             # pressure drop across choke
    t["wc"] = t.water_rate_stbd / t.liquid_rate_stbd
    return t


# ----------------------------------------------------------------------------------------------
# 2. Models (each returns LOO predictions of liquid rate)
# ----------------------------------------------------------------------------------------------
RAW = ["whp_psia", "whp_downstream_psia", "dh_pressure_psia", "dh_temperature_degf",
       "annulus_pressure_psia", "gas_lift_rate_mscfd", "choke", "t_days"]
STATIC = ["net_pay_thickness_ft", "porosity_frac", "oil_viscosity_cp", "tubing_id_in",
          "gauge_tvd_ft", "gl_valve_tvd_ft", "datum_tvd_ft"]


def loo(n, fn):
    p = np.zeros(n)
    for i in range(n):
        m = np.arange(n) != i
        p[i] = fn(m, i)
    return p


def wc_loo(t):
    """Water cut of the held-out test: linear trend in time, fit on the other tests of the same well."""
    out = []
    for i in range(len(t)):
        g = t[(t.well_name == t.well_name[i]) & (t.index != i)]
        out.append(np.polyval(np.polyfit(g.t_days, g.wc, 1), t.t_days[i]))
    return np.array(out)


def choke_model(t, W, y):
    """ln qL = a_well + b1 ln S + b2 ln dPc + b3 ln WHP + b4 ln GLR(qL)
    GLR = (GL + qL*(1-WC)*Rs/1000) / qL contains the target -> solve implicitly (no leakage)."""
    L = np.log
    t = t.copy()
    t["wc_hat"] = wc_loo(t)

    def feats(df, q, wc):
        glr = (df.gas_lift_rate_mscfd.values + q * (1 - wc) * df.solution_gor_at_pb_scf_stb.values / 1000) / q
        return np.c_[L(df.S), L(df.dpc), L(df.whp_psia), L(glr)]

    pred = np.zeros(len(t))
    for i in range(len(t)):
        m = np.arange(len(t)) != i
        tr = t[m]
        X = np.c_[W[m], feats(tr, tr.liquid_rate_stbd.values, tr.wc.values)]  # train: true q is known
        b = lstsq(X, y[m], rcond=None)[0]
        te = t.iloc[[i]]
        f = lambda lq: np.r_[W[i], feats(te, np.array([np.exp(lq)]), te.wc_hat.values)[0]] @ b - lq
        pred[i] = np.exp(brentq(f, np.log(50), np.log(50000)))
    return pred, b, t.wc_hat.values


def ipr_model(t, y):
    """Per-well: qL = a + b*t + c*Pwf  (c = -J, a + b*t = J*Pr(t) with linear depletion)."""
    n = len(t)
    X = np.c_[np.ones(n), t.t_days, t.dh_pressure_psia]

    def fn(m, i):
        g = m & (t.well_name == t.well_name[i]).values
        return X[i] @ lstsq(X[g], y[g], rcond=None)[0]
    return loo(n, fn)


def thermal_oil_model(t):
    """Per-well: qo = a + b*T_gauge   (Joule-Thomson: T - T_res = eta*(Pr-Pwf) = eta*qo/J)."""
    n = len(t)
    X = np.c_[np.ones(n), t.dh_temperature_degf]
    y = t.oil_rate_stbd.values

    def fn(m, i):
        g = m & (t.well_name == t.well_name[i]).values
        return X[i] @ lstsq(X[g], y[g], rcond=None)[0]
    return loo(n, fn)


# ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path(__file__).resolve().parents[2] / "data")
    d = ap.parse_args().data
    t = load_tests(d)
    n = len(t)
    y = t.liquid_rate_stbd.values
    wells = sorted(t.well_name.unique())
    W = pd.get_dummies(t.well_name)[wells].values.astype(float)
    mape = lambda p, yy=y: np.abs(p / yy - 1).mean() * 100

    R = {}
    X = np.c_[W, t[RAW].values]
    R["RandomForest (raw + well one-hot)"] = loo(n, lambda m, i: RandomForestRegressor(
        500, random_state=0, min_samples_leaf=2).fit(X[m], y[m]).predict(X[[i]])[0])
    X2 = t[RAW + STATIC].values
    hgb = lambda: HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=5)
    R["HistGradientBoosting (raw + static)"] = loo(n, lambda m, i: hgb().fit(X2[m], y[m]).predict(X2[[i]])[0])
    Z = np.c_[W, ((t[RAW] - t[RAW].mean()) / t[RAW].std()).values]
    R["Ridge (raw + well one-hot)"] = loo(n, lambda m, i: RidgeCV(alphas=np.logspace(-3, 3, 20)).fit(
        Z[m], y[m]).predict(Z[[i]])[0])
    R["IPR per-well (Pwf, t)"] = ipr_model(t, y)
    choke_pred, coefs, wc_hat = choke_model(t, W, np.log(y))
    R["Choke physics (pooled, implicit GLR)"] = choke_pred
    R["Ensemble 0.5 choke + 0.5 IPR (pre-set)"] = 0.5 * choke_pred + 0.5 * R["IPR per-well (Pwf, t)"]
    R["Ensemble 0.7 choke + 0.3 IPR (post-hoc!)"] = 0.7 * choke_pred + 0.3 * R["IPR per-well (Pwf, t)"]

    print(f"\nLiquid rate, leave-one-test-out, n={n}")
    for k, v in R.items():
        print(f"  {k:42s} MAPE {mape(v):5.2f}%")
    print(f"  choke exponents (full fit, last fold): S^{coefs[10]:.2f}  dPc^{coefs[11]:.2f}  "
          f"WHP^{coefs[12]:.2f}  GLR^{coefs[13]:.2f}")

    # leakage demo: GLR computed with the TRUE held-out rate
    L = np.log
    glr_true = (t.gas_lift_rate_mscfd + t.oil_rate_stbd * t.solution_gor_at_pb_scf_stb / 1000) / y
    XL = np.c_[W, L(t.S), L(t.dpc), L(t.whp_psia), L(glr_true)]
    leak = loo(n, lambda m, i: np.exp(XL[i] @ lstsq(XL[m], L(y)[m], rcond=None)[0]))
    print(f"  {'(LEAKAGE) choke with true-q GLR':42s} MAPE {mape(leak):5.2f}%   <- not a real result")

    # phase split from the choke model
    oil = choke_pred * (1 - wc_hat)
    wat = choke_pred * wc_hat
    gas = oil * t.solution_gor_at_pb_scf_stb / 1000
    print("\nPhase split (choke liquid x WC trend; gas = oil x Rs):")
    for name, p, yy in [("oil", oil, t.oil_rate_stbd), ("water", wat, t.water_rate_stbd), ("gas", gas, t.gas_rate_mscfd)]:
        r2 = 1 - ((p - yy) ** 2).sum() / ((yy - yy.mean()) ** 2).sum()
        print(f"  {name:6s} MAPE {mape(p, yy.values):5.2f}%   R2 {r2:.4f}")
    print(f"  oil, thermal-only per-well (qo = a + b*T)  MAPE {mape(thermal_oil_model(t), t.oil_rate_stbd.values):5.2f}%")

    # unseen well
    p = np.zeros(n)
    for w in wells:
        te = (t.well_name == w).values
        p[te] = hgb().fit(X2[~te], y[~te]).predict(X2[te])
    print(f"\nLeave-one-WELL-out, HistGradientBoosting (raw + static): MAPE {mape(p):.1f}%")


if __name__ == "__main__":
    main()
