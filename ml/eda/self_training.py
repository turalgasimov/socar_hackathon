"""Can the model be refitted on its own predictions when the new months carry no labels?

The test data give inputs only. Faig's idea: treat our own predictions for the new months as
synthetic labels and refit on them (self-training). Rehearsed on what we have: 7 months to train,
2 months held out.

    train   every real well test that ended before 1 Aug   (Jan-Jul)
    score   the real well tests of Aug-Sep, whose rates the schemes below never see

    frozen                  the Jan-Jul model, unchanged
    synthetic, test windows refit on Jan-Jul + its own predictions for the Aug-Sep test windows
    synthetic, monthly      predict Aug, refit on Jan-Jul + synthetic Aug, then predict Sep
    synthetic, daily        refit on Jan-Jul + its own predictions for every flowing Aug-Sep day
    synthetic, daily x rf   the same, synthetic rates scaled by the routing factors (as shipped)
    real labels, monthly    refit on Jan-Jul + the REAL Aug tests, then predict Sep (needs labels;
                            the reference for what real measurements would add)

Why the first three synthetic schemes cannot move: the model is two least-squares fits. A
synthetic row is the model's own prediction, so it lies exactly on the fitted surface and has
zero residual. The old coefficients already minimise the error on the real rows and make it zero
on the synthetic ones, so they minimise the sum: the refit returns the same model. A synthetic
row only moves the fit if its label differs from the model's own prediction, and then it moves
the fit toward whatever was added (here the routing factor), not toward the truth.

    python ml/eda/self_training.py      (~5 s, needs data/processed/{train,daily}_table.parquet)
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "src"))
sys.path.insert(0, str(ROOT / "ml"))

from config import PROC  # noqa: E402
from fit_vfm import bias, wape  # noqa: E402
from vfm import ROUTING_FACTORS, VFMModel, build_inputs  # noqa: E402

CUT = pd.Timestamp("2025-08-01")
MID = pd.Timestamp("2025-09-01")
PHASES = {"oil": "oil_rate_stbd", "water": "water_rate_stbd", "gas": "gas_rate_mscfd"}


def predict(model, X):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return model.predict(X)


def main() -> None:
    tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(["well_name", "start"], ignore_index=True)
    X = build_inputs(tr)
    oil, wat = tr.oil_rate_stbd.to_numpy(), tr.water_rate_stbd.to_numpy()
    start, end = pd.to_datetime(tr.start), pd.to_datetime(tr.end)
    real = (end < CUT).to_numpy()
    te = np.where((start >= CUT).to_numpy())[0]
    aug, sep = te[(start[te] < MID).to_numpy()], te[(start[te] >= MID).to_numpy()]

    def fit(extra_X=None, extra_oil=None, extra_wat=None) -> VFMModel:
        if extra_X is None:
            return VFMModel().fit(X[real], oil[real], wat[real])
        return VFMModel().fit(pd.concat([X[real], extra_X], ignore_index=True),
                              np.r_[oil[real], extra_oil], np.r_[wat[real], extra_wat])

    M0 = fit()
    out: dict[str, tuple[pd.DataFrame, int]] = {"frozen": (predict(M0, X.iloc[te]), 0)}

    # synthetic labels on the held-out test windows themselves
    p = predict(M0, X.iloc[te])
    M = fit(X.iloc[te], p.oil_rate_stbd.to_numpy(), p.water_rate_stbd.to_numpy())
    out["synthetic, test windows"] = (predict(M, X.iloc[te]), len(te))

    # month by month: synthetic August, refit, then September
    pa = predict(M0, X.iloc[aug])
    M = fit(X.iloc[aug], pa.oil_rate_stbd.to_numpy(), pa.water_rate_stbd.to_numpy())
    out["synthetic, monthly"] = (pd.concat([pa, predict(M, X.iloc[sep])]).set_axis(np.r_[aug, sep]).loc[te], len(aug))

    # synthetic labels on every flowing day of the two months (normal-production routing)
    daily = pd.read_parquet(PROC / "daily_table.parquet")
    dd = daily[pd.to_datetime(daily.date) >= CUT].reset_index(drop=True)
    Xd = build_inputs(dd, when="date")
    pdly = predict(M0, Xd)
    ok = (np.isfinite(pdly[list(PHASES.values())]).all(axis=1) & (pdly.oil_rate_stbd > 0)).to_numpy()
    Xd, pdly = Xd[ok].reset_index(drop=True), pdly[ok].reset_index(drop=True)
    M = fit(Xd, pdly.oil_rate_stbd.to_numpy(), pdly.water_rate_stbd.to_numpy())
    out["synthetic, daily"] = (predict(M, X.iloc[te]), len(Xd))
    rf = Xd.well_name.map(ROUTING_FACTORS).to_numpy()
    M = fit(Xd, pdly.oil_rate_stbd.to_numpy() * rf, pdly.water_rate_stbd.to_numpy() * rf)
    out["synthetic, daily x rf"] = (predict(M, X.iloc[te]), len(Xd))

    # the reference that needs labels: real August tests, then September
    M = fit(X.iloc[aug], oil[aug], wat[aug])
    out["real labels, monthly"] = (pd.concat([pa, predict(M, X.iloc[sep])]).set_axis(np.r_[aug, sep]).loc[te], len(aug))

    print(f"train: {real.sum()} real tests that ended before {CUT:%d %b}; scored: {len(te)} real tests of "
          f"Aug-Sep ({len(aug)} Aug, {len(sep)} Sep), {tr.well_name.iloc[te].nunique()} wells\n")
    frozen = out["frozen"][0]
    rows = []
    for name, (pr, n) in out.items():
        r = {"scheme": name, "added rows": n}
        for ph, c in PHASES.items():
            a = tr[c].to_numpy()[te]
            r[f"{ph} WAPE %"] = wape(a, pr[c].to_numpy())
        r["oil bias %"] = bias(oil[te], pr.oil_rate_stbd.to_numpy())
        r["max |change| vs frozen, stb/d"] = float(np.abs(pr.oil_rate_stbd.to_numpy() - frozen.oil_rate_stbd.to_numpy()).max())
        rows.append(r)
    fmt = {c: "{:.2f}".format for c in rows[0] if "WAPE" in c}
    fmt |= {"oil bias %": "{:+.2f}".format, "max |change| vs frozen, stb/d": "{:.6f}".format}
    print(pd.DataFrame(rows).to_string(index=False, formatters=fmt))

    s = out["real labels, monthly"][0].oil_rate_stbd.to_numpy()
    k = np.isin(te, sep)
    print(f"\nSeptember only ({k.sum()} tests), oil WAPE: frozen {wape(oil[sep], frozen.oil_rate_stbd.to_numpy()[k]):.2f}%, "
          f"synthetic monthly {wape(oil[sep], out['synthetic, monthly'][0].oil_rate_stbd.to_numpy()[k]):.2f}%, "
          f"real labels monthly {wape(oil[sep], s[k]):.2f}%")


if __name__ == "__main__":
    main()
