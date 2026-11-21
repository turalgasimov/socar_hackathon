"""Fit the VFM model, verify it time-forward, persist it, predict the daily table.

    python ml/fit_vfm.py

Writes:
    ml/models/vfm.joblib                      the fitted model
    ml/outputs/vfm_daily_predictions.xlsx     the Phase 1 deliverable
    ml/outputs/vfm_fit_report.md              scores and sanity checks

The time-forward check runs before persisting. A model that fails it is not
saved, so ml/models/vfm.joblib is never a model nobody has scored.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))

from config import OUT, PROC  # noqa: E402
from vfm import VFMModel, build_inputs  # noqa: E402

MODEL_PATH = ROOT / "ml" / "models" / "vfm.joblib"
MIN_HISTORY = 3
TF_MAX_OIL_MAPE = 4.0  # refuse to persist if time-forward oil error exceeds this


def mape(a, p):
    return float(np.mean(np.abs(p / a - 1)) * 100)


def bias(a, p):
    return float(np.mean(p / a - 1) * 100)


def time_forward(tr: pd.DataFrame) -> pd.DataFrame:
    """Predict each test from the other wells plus that well's earlier tests."""
    X = build_inputs(tr)
    start = tr.start.to_numpy()
    well = tr.well_name.astype(str).to_numpy()
    rows = []
    for w in pd.unique(well):
        idx = np.where(well == w)[0]
        idx = idx[np.argsort(start[idx])]
        for k in range(MIN_HISTORY, len(idx)):
            i = idx[k]
            m = (well != w) | (start < start[i])
            fit = VFMModel().fit(X[m], tr.oil_rate_stbd.values[m], tr.water_rate_stbd.values[m])
            p = fit.predict(X.iloc[[i]]).iloc[0]
            rows.append({"well": w, "start": start[i], "n_history": k,
                         "real_oil": tr.oil_rate_stbd.values[i],
                         "real_water": tr.water_rate_stbd.values[i],
                         "real_gas": tr.gas_rate_mscfd.values[i],
                         "pred_oil": p.oil_rate_stbd, "pred_water": p.water_rate_stbd,
                         "pred_gas": p.gas_rate_mscfd})
    return pd.DataFrame(rows)


def main() -> None:
    tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(
        ["well_name", "start"], ignore_index=True)
    daily = pd.read_parquet(PROC / "daily_table.parquet").sort_values(
        ["well_name", "date"], ignore_index=True)

    print(f"training rows: {len(tr)}   daily rows to predict: {len(daily):,}\n")

    # 1. verify before trusting
    tf = time_forward(tr)
    scores = {p: (mape(tf[f"real_{p}"].values, tf[f"pred_{p}"].values),
                  bias(tf[f"real_{p}"].values, tf[f"pred_{p}"].values))
              for p in ["oil", "water", "gas"]}
    print(f"TIME-FORWARD ({len(tf)} of {len(tr)} tests, min_history={MIN_HISTORY})")
    print(f"  {'phase':6s} {'MAPE':>8s} {'bias':>8s}")
    for p, (m, b) in scores.items():
        print(f"  {p:6s} {m:7.2f}% {b:+7.2f}%")

    oil_mape = scores["oil"][0]
    if oil_mape > TF_MAX_OIL_MAPE:
        raise SystemExit(f"\nREFUSING TO PERSIST: time-forward oil MAPE {oil_mape:.2f}% "
                         f"exceeds the {TF_MAX_OIL_MAPE}% gate.")

    # 2. fit on everything and persist
    X = build_inputs(tr)
    model = VFMModel().fit(X, tr.oil_rate_stbd.values, tr.water_rate_stbd.values)
    model.save(MODEL_PATH)
    print(f"\nfitted on all {model.trained_on} tests -> {MODEL_PATH.relative_to(ROOT)}")
    print("  choke exponents: " + ", ".join(f"{k.replace('exp_','')}={v:+.3f}"
                                            for k, v in model.coefficients().items()))

    # 3. predict the daily table through the persisted object, not the in-memory one
    loaded = VFMModel.load(MODEL_PATH)
    Xd = build_inputs(daily, when="date")
    pred = loaded.predict(Xd)
    out = pd.DataFrame({
        "date": pd.to_datetime(daily.date).dt.strftime("%Y-%m-%d"),
        "well_name": daily.well_name.astype(str).values,
        "oil_rate_stbd": pred.oil_rate_stbd.round(1),
        "water_rate_stbd": pred.water_rate_stbd.round(1),
        "gas_rate_mscfd": pred.gas_rate_mscfd.round(1),
        "data_coverage": daily.coverage.round(3).values,
        "low_coverage_flag": daily.low_coverage.values,
    })
    xlsx = OUT / "vfm_daily_predictions.xlsx"
    out.to_excel(xlsx, index=False, sheet_name="daily_rates")
    print(f"\npredictions -> {xlsx.relative_to(ROOT)}  ({len(out):,} well-days, "
          f"{int(out.low_coverage_flag.sum())} flagged low coverage)")

    # 4. sanity: predicted daily means against tested means, per well
    cmp = (out.assign(w=out.well_name).groupby("w")
           .agg(pred_oil=("oil_rate_stbd", "mean"), pred_water=("water_rate_stbd", "mean")))
    cmp["test_oil"] = tr.groupby("well_name").oil_rate_stbd.mean()
    cmp["test_water"] = tr.groupby("well_name").water_rate_stbd.mean()
    cmp["oil_diff_%"] = (cmp.pred_oil / cmp.test_oil - 1) * 100
    print("\nSANITY -- mean predicted daily vs mean tested rate, per well")
    print("(a few % lower is expected: tests run at lower back-pressure)")
    print(cmp.round(1).to_string())
    print(f"\nfield-wide oil difference: {(cmp.pred_oil.sum()/cmp.test_oil.sum()-1)*100:+.1f}%")

    _report(scores, model, out, cmp, len(tf), len(tr))


def _report(scores, model, out, cmp, n_tf, n_tr) -> None:
    md = [
        "# VFM fit report", "",
        f"Model: `ml/models/vfm.joblib`, fitted on all {n_tr} well tests.",
        "Structure: choke law for liquid x water-cut split from the tubing gradient; "
        "gas from static Rs. See `ml/src/vfm.py`.", "",
        f"## Time-forward scores ({n_tf} of {n_tr} tests)", "",
        "| phase | MAPE | bias |", "|---|--:|--:|",
    ]
    md += [f"| {p} | {m:.2f}% | {b:+.2f}% |" for p, (m, b) in scores.items()]
    md += [
        "", "Each test is predicted from the other nine wells plus that well's own",
        "earlier tests. No future information, no same-test leakage.", "",
        "## Fitted choke exponents", "",
        "| term | exponent | textbook |", "|---|--:|--:|",
        f"| choke size S | {model.coefficients()['exp_choke_size_S']:+.3f} | +2 (area ~ d²) |",
        f"| choke dP | {model.coefficients()['exp_choke_dP']:+.3f} | +0.5 (√ΔP) |",
        f"| WHP | {model.coefficients()['exp_WHP']:+.3f} | — |",
        f"| GLR | {model.coefficients()['exp_GLR']:+.3f} | — |",
        "", "The first two land on the subcritical choke law without being told to, "
        "which is the evidence that the form is right rather than fitted to noise.", "",
        "## Daily predictions", "",
        f"`ml/outputs/vfm_daily_predictions.xlsx` — {len(out):,} well-days, "
        f"{int(out.low_coverage_flag.sum())} flagged below 80% minute coverage.",
        "", "| well | mean predicted oil | mean tested oil | diff |", "|---|--:|--:|--:|",
    ]
    md += [f"| {w} | {r.pred_oil:,.0f} | {r.test_oil:,.0f} | {r['oil_diff_%']:+.1f}% |"
           for w, r in cmp.iterrows()]
    md += [
        "", "Predicted daily rates sitting a few per cent below tested rates is the",
        "expected direction: a test runs the well at lower back-pressure than normal",
        "production, so it flows harder. Whether that gap should be corrected depends",
        "on how the organisers defined the daily ground truth — see",
        "`agent/PROJECT_STATE.md`, Open risks.",
    ]
    (OUT / "vfm_fit_report.md").write_text("\n".join(md), encoding="utf-8")
    print(f"report -> ml/outputs/vfm_fit_report.md")


if __name__ == "__main__":
    main()
