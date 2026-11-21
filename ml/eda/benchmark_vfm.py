"""
VFM benchmark — physics vs ML model comparison. Results are recorded in
agent/PROJECT_STATE.md; the shipped model is ml/src/vfm.py.

Uses ONLY well_tests.csv (+ choke_events, completion, pvt). High-frequency data is not needed here,
because the sensor columns in well_tests are exactly the HF means over each test window (verified,
|diff| < 0.4 psi). Labels = 85 well tests.

Protocol
  LOO  : leave-one-test-out. For each of the 85 tests: fit on the other 84, predict the held-out one.
  LOWO : leave-one-well-out. Fit on 9 wells, predict all tests of the 10th (unseen well).
  TF   : time-forward (section 3) -- the team's REPORTING protocol, same folds as
         ml/eda/validate_features.py. Oil rate, 55 targets, with a well-cluster bootstrap.
  Metric: MAPE = mean(|pred / true - 1|), in %.

Run:  python ml/eda/benchmark_vfm.py            (LOO + LOWO + TF; data dir defaults to <repo>/data)
      python ml/eda/benchmark_vfm.py --tf-only  (time-forward section only, ~1 min)

NOTE: LOO is interpolation in time and is optimistic for every model; report TF numbers.
All labels are measured under test-separator routing -- see agent/PROJECT_STATE.md, Open risks.
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


# ----------------------------------------------------------------------------------------------
# 3. Time-forward — the team's reporting protocol (ml/eda/validate_features.py)
# ----------------------------------------------------------------------------------------------
# Same (test, train) pairs as validate_features.time_forward(): for each well, for each test
# k >= 3, train on every other well (all tests) plus THIS well's earlier tests -> 55 targets.
# Target: oil rate. Per-well models (thermal, IPR, baselines) only see this well's earlier tests.
#   ridge58      Faig's RidgeCV on the "+ physics interactions" set (58 features)
#   choke_*      pooled choke law (implicit GLR, no leakage) x water-cut estimate:
#                  trend  per-well linear WC(t)
#                  pooled common WC slope, per-well intercept
#                  vlp    wc = a_w + s*t + c1*dp_tubing + c2*GL  (tubing gradient as WC sensor)
#   thermal      per-well qo = a + b*T_gauge   (Joule-Thomson)
#   ipr3         per-well qo = a + b*t + c*Pwf
#   base_last    copy the well's previous test;  base_trend  per-well linear trend in time
# Needs data/processed/train_table.parquet (cleaning + features pipeline, agent/AGENTS.md §4).
TF_PAIRS = [("ridge58", "ens_choke_thermal"), ("base_last", "ens_choke_thermal"),
            ("base_last", "ridge58"), ("choke_trend", "ens_choke_thermal"),
            ("thermal", "choke_trend"), ("choke_trend", "choke_vlp")]


class TFModels:
    def __init__(self, tr, feature_cols):
        L = np.log
        self.tr = tr
        self.y = tr.oil_rate_stbd.to_numpy()
        self.well = tr.well_name.to_numpy()
        self.t = tr.t.to_numpy()
        self.wc = tr.wc.to_numpy()
        self.q = tr.qL.to_numpy()
        self.W = pd.get_dummies(tr.well_name).to_numpy(dtype=float)
        self.X = tr[feature_cols].to_numpy()
        glr = (tr.gl + tr.qL * (1 - tr.wc) * tr.rs / 1000) / tr.qL   # training rows: q known
        self.Xc = np.c_[self.W, L(tr.S), L(tr.dpc), L(tr.whp), L(glr)]
        self.lnq = L(self.q)

    def own(self, m, i):
        return m & (self.well == self.well[i])

    def wc_hat(self, m, i, mode):
        g = self.own(m, i)
        if mode == "trend":
            return float(np.polyval(np.polyfit(self.t[g], self.wc[g], 1), self.t[i]))
        if mode == "vlp":
            A = np.c_[self.W, self.t, self.tr.dp_tubing__mean, self.tr.gl]
            return float(A[i] @ lstsq(A[m], self.wc[m], rcond=None)[0])
        num = den = 0.0                                          # pooled slope
        for w in np.unique(self.well[m]):
            h = m & (self.well == w)
            if h.sum() < 2:
                continue
            tc = self.t[h] - self.t[h].mean()
            num += tc @ (self.wc[h] - self.wc[h].mean())
            den += tc @ tc
        s = num / den
        return float((self.wc[g] - s * self.t[g]).mean() + s * self.t[i])

    def choke(self, m, i, wc_mode):
        L = np.log
        b = lstsq(self.Xc[m], self.lnq[m], rcond=None)[0]
        r = self.tr.iloc[i]
        wc = self.wc_hat(m, i, wc_mode)
        base = self.W[i] @ b[:-4] + b[-4] * L(r.S) + b[-3] * L(r.dpc) + b[-2] * L(r.whp)
        f = lambda lq: base + b[-1] * L((r.gl + np.exp(lq) * (1 - wc) * r.rs / 1000) / np.exp(lq)) - lq
        return np.exp(brentq(f, L(10.0), L(1e6))) * (1 - wc)

    def perwell(self, m, i, cols):
        g = self.own(m, i)
        A = np.c_[np.ones(len(self.tr)), self.tr[cols].to_numpy()] if cols else np.ones((len(self.tr), 1))
        return float(A[i] @ lstsq(A[g], self.y[g], rcond=None)[0])

    def last(self, m, i):
        g = np.where(self.own(m, i))[0]
        prev = g[self.t[g] < self.t[i]]
        j = prev[np.argmax(self.t[prev])] if len(prev) else g[np.argmin(np.abs(self.t[g] - self.t[i]))]
        return float(self.y[j])

    def candidates(self, m, i):
        ct, cp, cv = (self.choke(m, i, k) for k in ("trend", "pooled", "vlp"))
        th = self.perwell(m, i, ["T"])
        return {"choke_trend": ct, "choke_pooled": cp, "choke_vlp": cv,
                "ens_trend_thermal": (ct + th) / 2, "ens_vlp_thermal": (cv + th) / 2}


def tf_folds(tr, rows=None, min_history=3):
    """(test, train-mask, n_earlier) triples; restricted to `rows` (a train mask) if given."""
    start, well = tr.start.to_numpy(), tr.well_name.to_numpy()
    base = np.ones(len(tr), bool) if rows is None else rows
    out = []
    for w in pd.unique(well[base]):
        idx = np.where(base & (well == w))[0]                    # sorted by (well, start)
        for k in range(min_history, len(idx)):
            i = idx[k]
            out.append((i, base & ((well != w) | (start < start[i])), k))
    return out


def time_forward_section(n_boot=5000, seed=42):
    import sys
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "ml" / "src"))
    sys.path.insert(0, str(root / "ml" / "eda"))
    import validate_features as VF
    from config import PROC

    f = PROC / "train_table.parquet"
    if not f.exists():
        print(f"\n[time-forward skipped] {f} not found - run the cleaning + features pipeline first.")
        return
    tr = pd.read_parquet(f).sort_values(["well_name", "start"], ignore_index=True)
    tr["t"] = ((tr.start + (tr.end - tr.start) / 2) - pd.Timestamp("2025-01-01")).dt.total_seconds() / 86400
    tr["qL"] = tr.oil_rate_stbd + tr.water_rate_stbd
    tr["wc"] = tr.water_rate_stbd / tr.qL
    tr["S"] = tr.choke_pct__mean / 100 * tr.choke_max_size_64ths
    tr["dpc"], tr["whp"] = tr.dp_choke__mean, tr.whp_psia__mean
    tr["gl"], tr["T"], tr["pwf"] = tr.gas_lift_rate_mscfd__mean, tr.dh_temperature_degf__mean, tr.dh_pressure_psia__mean
    tr["rs"] = tr.solution_gor_at_pb_scf_stb
    M = TFModels(tr, VF.feature_sets(tr)["+ physics interactions"])
    y = M.y

    folds = tf_folds(tr)
    rows = np.array([i for i, _, _ in folds])
    P = {k: np.full(len(tr), np.nan) for k in
         ["ridge58", "base_last", "base_trend", "choke_trend", "choke_vlp", "thermal", "ipr3", "nested"]}
    kk = np.full(len(tr), np.nan)
    picks = []
    for i, m, k in folds:
        kk[i] = k
        P["ridge58"][i] = VF.model().fit(M.X[m], y[m]).predict(M.X[[i]])[0]
        P["base_last"][i] = M.last(m, i)
        P["base_trend"][i] = M.perwell(m, i, ["t"])
        P["thermal"][i] = M.perwell(m, i, ["T"])
        P["ipr3"][i] = M.perwell(m, i, ["t", "pwf"])
        cand = M.candidates(m, i)
        P["choke_trend"][i], P["choke_vlp"][i] = cand["choke_trend"], cand["choke_vlp"]
        # nested selection: choose the variant on an inner time-forward run of this fold's train set
        err = {}
        for j, mj, _ in tf_folds(tr, rows=m):
            for name, p in M.candidates(mj, j).items():
                err.setdefault(name, []).append(abs(p / y[j] - 1))
        pick = min(err, key=lambda n_: np.mean(err[n_]))
        picks.append(pick)
        P["nested"][i] = cand[pick]
    P["ens_choke_thermal"] = (P["choke_trend"] + P["thermal"]) / 2
    E = {k: np.abs(v[rows] / y[rows] - 1) * 100 for k, v in P.items()}

    labels = {"base_last": "Persistence (copy previous test)", "base_trend": "Per-well linear trend",
              "ridge58": "Ridge, 58 features (validate_features)", "ipr3": "IPR per-well (t, Pwf)",
              "choke_trend": "Choke x WC trend (pre-set)", "thermal": "Thermal per-well (Joule-Thomson)",
              "ens_choke_thermal": "Ensemble 1/2 choke + 1/2 thermal (pre-set)",
              "choke_vlp": "Choke x WC(t, dp_tubing, GL) (post-hoc pick)",
              "nested": "Nested-selected choke variant (honest)"}
    print(f"\nOil rate, TIME-FORWARD, n={len(rows)} targets (min_history=3)")
    print(f"  {'model':46s} {'MAPE':>6s} {'p90':>6s} {'bias':>6s}")
    for k, lab in labels.items():
        e = E[k]
        bias = np.mean(P[k][rows] / y[rows] - 1) * 100
        print(f"  {lab:46s} {e.mean():5.2f}% {np.percentile(e, 90):5.2f}% {bias:+5.2f}%")
    print(f"  nested picks: {pd.Series(picks).value_counts().to_dict()}")

    kb = np.where(kk[rows] >= 6, 6, kk[rows]).astype(int)
    print("\n  TF oil MAPE by number of earlier tests of the same well (6 = 6..8):")
    print("  " + pd.DataFrame({"n": pd.Series(kb).value_counts().sort_index(),
                               **{k: pd.Series(E[k]).groupby(kb).mean().round(2)
                                  for k in ["ridge58", "choke_trend", "thermal"]}}).to_string().replace("\n", "\n  "))

    # paired well-cluster bootstrap of MAPE gaps (targets of one well are correlated)
    rng = np.random.default_rng(seed)
    wells = M.well[rows]
    uw = np.unique(wells)
    by_w = {w: np.where(wells == w)[0] for w in uw}
    print(f"\n  MAPE gap A - B, 95% well-cluster bootstrap CI (B = {n_boot}):")
    for a, b in TF_PAIRS:
        d = E[a] - E[b]
        bc = np.array([d[np.concatenate([by_w[w] for w in rng.choice(uw, len(uw))])].mean()
                       for _ in range(n_boot)])
        lo, hi = np.percentile(bc, [2.5, 97.5])
        print(f"  {a:12s} - {b:18s} {d.mean():+5.2f} pp  [{lo:+5.2f}, {hi:+5.2f}]")


if __name__ == "__main__":
    import sys as _sys
    if "--tf-only" not in _sys.argv:
        main()
    else:
        _sys.argv.remove("--tf-only")
    time_forward_section()
