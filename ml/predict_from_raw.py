"""Raw CSVs in, predictions out. The path the live demo takes.

    python ml/predict_from_raw.py --data <dir> --out <file.csv>

`<dir>` holds the five raw files exactly as the organisers supply them:
high_freq_data.csv, well_tests.csv, choke_events.csv, reservoir_pvt.csv,
well_completion.csv. Nothing from data/processed/ is read, and the parquet
cache is bypassed -- a demo run must never silently return rows cleaned from
*our* copy of the data.

Only `high_freq_data.csv`, `choke_events.csv`, `reservoir_pvt.csv` and
`well_completion.csv` are needed to predict. `well_tests.csv` is optional. If
present, the tests in it are scored against, and those after the training
period refit the model month by month (ml/src/rolling.py; `--frozen` turns that
off). Each test is scored by a model that has not seen it, without the routing
correction, because a test is a test-separator rate.

The Streamlit app should call `run()` rather than shelling out to this file.
"""
from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))

import clean  # noqa: E402
import daily_predict as DP  # noqa: E402
import features as F  # noqa: E402
import history  # noqa: E402
import rolling  # noqa: E402
from vfm import VFMModel, build_inputs  # noqa: E402

DEFAULT_MODEL = ROOT / "ml" / "models" / "vfm.pkl"
REQUIRED = ["high_freq_data.csv", "choke_events.csv",
            "reservoir_pvt.csv", "well_completion.csv"]


def run(data_dir: Path, model_path: Path = DEFAULT_MODEL,
        verbose: bool = True, history_dir: Path | None = None,
        refit: bool = True) -> tuple[pd.DataFrame, dict]:
    """Clean -> features -> predict. Returns (submission_frame, report).

    The training-period history (ml/src/history.py) fills a missing opening choke setting when
    the upload covers later months, and labels the self-check as held-out or in-sample. With
    `refit`, uploaded tests after the training period refit the model month by month.
    """
    data_dir = Path(data_dir)
    missing = [f for f in REQUIRED if not (data_dir / f).exists()]
    if missing:
        raise FileNotFoundError(f"{data_dir} is missing {missing}")

    rep: dict = {"data_dir": str(data_dir)}
    t0 = time.time()

    hist = history.load(history_dir)
    hf, hf_rep = clean.clean_high_freq(data_dir=data_dir, verbose=verbose, hist=hist)
    rep["clean"] = {k: hf_rep[k] for k in ("rows_in", "rows_out", "shut_in_minutes")}
    rep["choke_initial_from_history"] = hf_rep["choke_initial_from_history"]
    rep["choke_initial_unknown"] = hf_rep["choke_initial_unknown"]
    rep["sentinels_masked"] = sum(hf_rep["sentinel_to_nan"].values())
    rep["duplicates_dropped"] = hf_rep["duplicate_rows_dropped"]

    pvt = pd.read_csv(data_dir / "reservoir_pvt.csv")
    comp = pd.read_csv(data_dir / "well_completion.csv", parse_dates=["first_production_date"])
    daily = F.build_daily_table(hf, pvt, comp).sort_values(
        ["well_name", "date"], ignore_index=True)
    rep["well_days"] = len(daily)
    rep["low_coverage_days"] = int(daily.low_coverage.sum())

    model = VFMModel.load(model_path)
    tests = prepare_tests(hf, data_dir, pvt, comp)
    if refit and tests is not None:
        model, rep["refit"] = rolling.monthly_refit(model, hist, tests["X"], tests["wt"], tests["ok"], daily.date)
    else:
        rep["refit"] = {"refits": [], "tests_after_training": 0, "tests_left_out": [],
                        "note": "refit switched off" if tests is not None else "no well tests in the upload"}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pred = model.predict(build_inputs(daily, when="date"))
        # shut-in-affected days: time-integrate, as fit_vfm.py does for the scored file
        pred, rep["shut_in_days_integrated"] = DP.integrate_shut_in_days(pred, daily, model, hf, pvt, comp)
    rep["unseen_wells"] = sorted(set(pred.loc[pred.unseen_well, "well_name"]))
    rep["warnings"] = [str(w.message) for w in caught]

    sub = pd.DataFrame({
        "timestamp": pd.to_datetime(daily.date).dt.strftime("%Y-%m-%d"),
        "well_name": daily.well_name.astype(str).values,
        "oil_rate_stbd": pred.oil_rate_stbd.round(1),
        "water_rate_stbd": pred.water_rate_stbd.round(1),
        "gas_rate_mscfd": pred.gas_rate_mscfd.round(1),
    })
    sub = _complete_grid(sub)
    rep["rows_out"] = len(sub)
    rep["seconds"] = round(time.time() - t0, 1)

    # optional self-check when labels came with the data
    if tests is not None:
        rep["scored_against_tests"] = _score(model, tests, hist)
    return sub, rep


def _complete_grid(sub: pd.DataFrame) -> pd.DataFrame:
    """Fill well-days the sensors missed, so the grid is rectangular."""
    rates = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]
    grid = pd.MultiIndex.from_product(
        [sorted(sub.well_name.unique()),
         pd.date_range(sub.timestamp.min(), sub.timestamp.max()).strftime("%Y-%m-%d")],
        names=["well_name", "timestamp"])
    s = sub.set_index(["well_name", "timestamp"]).reindex(grid)
    s[rates] = (s.groupby(level=0)[rates]
                 .transform(lambda c: c.interpolate(limit_direction="both")).round(1))
    return s.reset_index()[["timestamp", "well_name", *rates]].sort_values(
        ["well_name", "timestamp"], ignore_index=True)


def prepare_tests(hf, data_dir, pvt, comp) -> dict | None:
    """Cleaned labels and model inputs for the well tests in the upload, row for row; or None."""
    if not (Path(data_dir) / "well_tests.csv").exists():
        return None
    wt, _ = clean.clean_well_tests(verbose=False, data_dir=data_dir)
    if not len(wt):
        return None
    windows = wt[["well_name", "test_start", "test_end"]].rename(
        columns={"test_start": "start", "test_end": "end"})
    f = F.aggregate_windows(hf, windows)
    f = F.add_within_well(f, F.well_baselines(hf))
    f = f.merge(F.static_table(pvt, comp), on="well_name", how="left")
    # Only use tests whose window actually has sensor data behind it. An
    # upload can carry tests that fall outside the high-frequency period.
    ok = (f.coverage >= F.MIN_COVERAGE).to_numpy()
    return {"wt": wt, "X": build_inputs(f), "ok": ok}


def _score(model, tests: dict, hist=None) -> dict:
    """If the upload carried labels, report how we did on them.

    Predictions carry no routing correction: a well test is a test-separator rate, and the
    correction is for normal-production days (with it, this check reads +2.8% high on oil).

    `basis` says whether the scored tests are after the last test the shipped model was trained
    on (held-out) or among its training tests (in-sample). A held-out test stays held-out under
    the monthly refit: the model of its month was fitted only on tests that ended before that
    month. Non-dict values only: the app reads every dict value as a phase.
    """
    wt, ok = tests["wt"], tests["ok"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = rolling.unrouted(model).predict(tests["X"])
    out = {"tests_scored": int(ok.sum()), "tests_skipped_no_data": int((~ok).sum())}
    cut = history.train_end(hist)
    if cut is not None:
        after = int((ok & (wt.test_start > cut).to_numpy()).sum())
        out["tests_after_training"] = after
        out["basis"] = ("held-out" if after == ok.sum() else "in-sample" if after == 0 else "mixed")
    for phase, col in [("oil", "oil_rate_stbd"), ("water", "water_rate_stbd"),
                       ("gas", "gas_rate_mscfd")]:
        a, q = wt[col].to_numpy()[ok], p[col].to_numpy()[ok]
        m = np.isfinite(a) & np.isfinite(q)
        a, q = a[m], q[m]
        if len(a) < 3:
            out[phase] = "too few scorable tests"
            continue
        out[phase] = {"MAPE_%": round(float(np.mean(np.abs(q / a - 1)) * 100), 2),
                      "WAPE_%": round(float(np.abs(a - q).sum() / a.sum() * 100), 2),
                      "R2": round(float(1 - ((a - q) ** 2).sum() / ((a - a.mean()) ** 2).sum()), 4)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=ROOT / "ml" / "outputs" / "predictions_from_raw.csv")
    ap.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    ap.add_argument("--frozen", action="store_true",
                    help="do not refit on uploaded tests after the training period")
    a = ap.parse_args()

    sub, rep = run(a.data, a.model, refit=not a.frozen)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sub.to_csv(a.out, index=False)

    print("\n" + "=" * 68 + f"\nRAW -> PREDICTIONS  ({rep['seconds']}s)\n" + "=" * 68)
    print(f"  source            : {rep['data_dir']}")
    print(f"  sentinels masked  : {rep['sentinels_masked']:,}")
    print(f"  duplicates dropped: {rep['duplicates_dropped']:,}")
    print(f"  well-days         : {rep['well_days']:,}  "
          f"({rep['low_coverage_days']} below 80% coverage)")
    print(f"  shut-in days      : {rep['shut_in_days_integrated']} time-integrated (10-min bins)")
    print(f"  monthly refit     : {rolling.describe(rep['refit'])}")
    for x in rep["refit"]["tests_left_out"]:
        print(f"    left out of the refit: {x}")
    print(f"  unseen wells      : {rep['unseen_wells'] or 'none'}")
    if rep["choke_initial_from_history"]:
        print(f"  opening choke from history: {', '.join(rep['choke_initial_from_history'])}")
    if rep["choke_initial_unknown"]:
        print(f"  WARNING no choke before first event: {', '.join(rep['choke_initial_unknown'])}")
    print(f"  rows written      : {rep['rows_out']:,} -> {a.out}")
    if "scored_against_tests" in rep:
        sc = rep["scored_against_tests"]
        skipped = sc["tests_skipped_no_data"]
        print(f"\n  self-check against the {sc['tests_scored']} usable well tests in this upload, no routing correction"
              + (f" ({skipped} skipped, no sensor data behind them)" if skipped else "") + ":")
        basis = sc.get("basis")
        if basis == "held-out":
            print("  held-out: every scored test is after the last test the model was trained on")
        elif basis == "mixed":
            print(f"  mixed: {sc['tests_after_training']} held-out tests, the rest in-sample")
        else:
            print("  in-sample if the model was fitted on these wells -- not a held-out score")
        for phase in ("oil", "water", "gas"):
            m = sc.get(phase)
            if isinstance(m, dict):
                print(f"    {phase:6s} R2 {m['R2']:.4f}  MAPE {m['MAPE_%']:5.2f}%  "
                      f"WAPE {m['WAPE_%']:5.2f}%")
            else:
                print(f"    {phase:6s} {m}")
    for w in rep["warnings"]:
        print(f"\n  WARNING: {w}")


if __name__ == "__main__":
    main()
