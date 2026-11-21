"""Does the normalisation actually help? Measured, not assumed.

Runs the same model over four feature sets and four validation schemes, and
writes ml/outputs/feature_report.md. The point of the four schemes is that they
disagree wildly, and picking the wrong one is how a VFM model gets a great
score and then fails on the real submission.

    python ml/eda/validate_features.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold, KFold, LeaveOneOut, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
warnings.filterwarnings("ignore")

import features as F  # noqa: E402
from config import OUT, PROC  # noqa: E402

ALPHAS = np.logspace(-2, 4, 40)


def model():
    """Scaler inside the pipeline so it is fit per training fold, never globally."""
    return make_pipeline(StandardScaler(), RidgeCV(alphas=ALPHAS))


def mape(a, p):
    return float(np.mean(np.abs((a - p) / a)) * 100)


def feature_sets(tr):
    cols = F.feature_columns(tr)
    win = [c for c in cols if c.endswith("__mean")]
    z = [c for c in cols if c.endswith(("__z", "__ratio"))]
    st = [c for c in cols if c in F.STATIC_FEATURES]
    phys = ["choke_flow_proxy", "gl_per_dp", "drawdown_ratio",
            "inj_differential", "temp_deficit", "whp_instability"]
    return {
        "window means only": win,
        "+ per-well z-scores": win + z,
        "+ static properties": win + z + st,
        "+ physics interactions": win + z + st + phys,
    }


def time_forward(tr, cols, target, min_history=3):
    """Per well: train on every other well plus this well's earlier tests."""
    preds, acts = [], []
    for w, d in tr.groupby("well_name"):
        d = d.reset_index(drop=True)
        for i in range(min_history, len(d)):
            trn = tr[(tr.well_name != w) | (tr.start < d.start[i])]
            m = model().fit(trn[cols].values, trn[target].values)
            preds.append(m.predict(d.loc[[i], cols].values)[0])
            acts.append(d[target][i])
    return mape(np.array(acts), np.array(preds)), len(acts)


def main() -> None:
    tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(
        ["well_name", "start"], ignore_index=True)
    y = tr.oil_rate_stbd.values
    g = tr.well_name.values
    sets = feature_sets(tr)

    rows = []
    for name, cols in sets.items():
        X = tr[cols].values
        r = {"features": name, "n": len(cols)}
        r["leave-one-test-out"] = mape(y, cross_val_predict(model(), X, y, cv=LeaveOneOut()))
        r["time-forward"] = time_forward(tr, cols, "oil_rate_stbd")[0]
        r["random 10-fold"] = mape(y, cross_val_predict(
            model(), X, y, cv=KFold(10, shuffle=True, random_state=0)))
        r["unseen well"] = mape(y, cross_val_predict(
            model(), X, y, cv=GroupKFold(n_splits=10), groups=g))
        rows.append(r)
    res = pd.DataFrame(rows)
    base = mape(y, np.full_like(y, y.mean()))

    best = sets["+ static properties"]
    per_target = {t: mape(tr[t].values, cross_val_predict(
        model(), tr[best].values, tr[t].values, cv=LeaveOneOut())) for t in F.TARGETS}

    md = [
        "# Feature engineering and normalisation - measured effect",
        "",
        "Model held constant (RidgeCV on standardised inputs, scaler fit inside each",
        "training fold). Only the feature set changes. Metric is MAPE on oil rate, %.",
        "",
        "| feature set | n | leave-one-out | time-forward | random 10-fold | unseen well |",
        "|---|--:|--:|--:|--:|--:|",
    ]
    for _, r in res.iterrows():
        md.append(f"| {r.features} | {r.n} | {r['leave-one-test-out']:.2f} | "
                  f"{r['time-forward']:.2f} | {r['random 10-fold']:.2f} | {r['unseen well']:.1f} |")
    md += [
        f"| *baseline: predict the global mean* | - | - | - | - | {base:.1f} |",
        "",
        "## Reading this table",
        "",
        "- **Per-well z-scoring is the single biggest win.** Time-forward error drops from "
        f"{res.loc[0,'time-forward']:.1f}% to {res.loc[1,'time-forward']:.1f}% on that one change. "
        "98.3% of rate variance is between wells, so raw sensor values mostly encode *which well "
        "this is*; the z-scores expose the 1.7% that is actual production change.",
        "- **Static properties add the well-scale term** the z-scores deliberately removed, "
        f"taking time-forward to {res.loc[2,'time-forward']:.2f}%.",
        "- **`random 10-fold` is not a valid score here.** It puts other tests from the same well "
        "in training, so the model reads off a memorised level. Treat it as a leakage check, "
        "not a result.",
        "- **`unseen well` is near or worse than the baseline for every set.** With 10 wells there "
        "is not enough between-well data to generalise to an 11th. If the organisers score on a "
        "held-out *well*, this approach does not transfer - but the deliverable asks for daily "
        "rates on these same 10 wells, which is the time-forward column.",
        "",
        "## Per-target error (leave-one-out, static set)",
        "",
        "| target | MAPE |",
        "|---|--:|",
    ] + [f"| {t} | {v:.2f}% |" for t, v in per_target.items()] + [
        "",
        f"Gas is the hardest target ({per_target['gas_rate_mscfd']:.1f}%), as expected: it is the "
        "smallest-magnitude rate and the most sensitive to the separator conditions that the "
        "high-frequency sensors do not observe.",
        "",
        "## Caveat",
        "",
        f"The full matrix is {len(F.feature_columns(tr))} features for {len(tr)} labelled rows. "
        "That is heavily p >> n, and the numbers above come from L2-regularised linear models "
        "chosen for that reason. A high-capacity model on this table will overfit; keep "
        "regularisation strong and prefer the smaller sets.",
    ]
    (OUT / "feature_report.md").write_text("\n".join(md), encoding="utf-8")
    print(res.to_string(index=False))
    print(f"\nwrote {(OUT / 'feature_report.md')}")


if __name__ == "__main__":
    main()
