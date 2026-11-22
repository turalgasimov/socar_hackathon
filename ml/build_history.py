"""Write ml/models/history/: what the app keeps from the training period (see ml/src/history.py).

    python ml/build_history.py                       # the shipped history, to 2025-09-30
    python ml/build_history.py --end 2025-07-31 --out <dir>   # a truncated one, for testing

daily_rates.csv  every well-day from 1 Jan to --end, from the scored Task 1 file
                 (lam0.80_21.0200_SHIPPED.csv -- the rates PTA already uses)
well_state.csv   per well, as of the day after --end: cumulative oil, last choke setting,
                 last daily rates, fluid averages of the last three well tests, and the start
                 of the last test the model was trained on
train_tests.csv  model inputs and measured oil/water of every test the model was trained on,
                 for the monthly refit (ml/src/rolling.py). Needs data/processed/train_table.parquet.

The model's training set is every test in the data (what vfm.pkl saw), whatever --end is. A
rehearsal with a model fitted on fewer tests passes `trained_to` to build(): only tests that
ended before that date are then stored and counted as training.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))

import clean  # noqa: E402
import history  # noqa: E402
from config import DATA, PROC  # noqa: E402
from vfm import VFMModel, build_inputs  # noqa: E402

RECORD = ROOT / "ml" / "outputs" / "submitted" / "lam0.80_21.0200_SHIPPED.csv"


def train_rows(trained_to: pd.Timestamp | None) -> pd.DataFrame:
    """Model inputs + labels of the training tests, exactly the rows ml/fit_vfm.py fits on."""
    tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(["well_name", "start"], ignore_index=True)
    rows = build_inputs(tr).assign(oil_rate_stbd=tr.oil_rate_stbd.to_numpy(float),
                                   water_rate_stbd=tr.water_rate_stbd.to_numpy(float),
                                   start=pd.to_datetime(tr.start).to_numpy(), end=pd.to_datetime(tr.end).to_numpy())
    if trained_to is not None:
        rows = rows[rows.end < trained_to].reset_index(drop=True)
    return rows


def build(end: pd.Timestamp, out: Path, data_dir: Path = DATA,
          trained_to: pd.Timestamp | None = None) -> pd.DataFrame:
    rates = pd.read_csv(RECORD, parse_dates=["timestamp"])
    rates = rates[rates.timestamp <= end].sort_values(["well_name", "timestamp"], ignore_index=True)
    comp = pd.read_csv(data_dir / "well_completion.csv").set_index("well_name")
    anchor, col = history.cum_anchor(comp)

    # the cumulative is only right if no day between the anchor and --end is missing
    days = pd.date_range(anchor, end)
    for w, g in rates[rates.timestamp >= anchor].groupby("well_name"):
        assert len(g) == len(days) and g[history.RATES].notna().all().all(), f"{w}: gaps in {RECORD.name}"

    ck = pd.read_csv(data_dir / "choke_events.csv", parse_dates=["timestamp"])
    ck = ck[ck.timestamp < end + pd.Timedelta(days=1)].sort_values("timestamp")
    last_ck = ck.groupby("well_name").last()

    wt, _ = clean.clean_well_tests(verbose=False, data_dir=data_dir)
    train = train_rows(trained_to)
    train_end = train.start.max()                       # start of the last test the model saw
    if trained_to is None:   # the stored rows must be the shipped model's own training set
        shipped = VFMModel.load(ROOT / "ml" / "models" / "vfm.pkl")
        refit = VFMModel().fit(train, train.oil_rate_stbd.to_numpy(), train.water_rate_stbd.to_numpy())
        assert refit.wells == shipped.wells and len(train) == shipped.trained_on, "not the shipped training set"
        assert abs(refit.choke_coef - shipped.choke_coef).max() < 1e-6, "choke law differs from vfm.pkl"
        assert abs(refit.wc_coef - shipped.wc_coef).max() < 1e-6, "water-cut fit differs from vfm.pkl"
    wt = wt[wt.test_start <= end].sort_values("test_start")
    fluid = wt.groupby("well_name").tail(3).groupby("well_name")[history.FLUID].mean()

    last_day = rates.groupby("well_name").last()
    state = pd.DataFrame({
        "as_of": end + pd.Timedelta(days=1),
        "cum_oil_stb": comp[col] + rates[rates.timestamp >= anchor].groupby("well_name").oil_rate_stbd.sum(),
        "cum_source": f"{col} + daily oil {anchor:%Y-%m-%d}..{end:%Y-%m-%d}",
        "last_day": last_day.timestamp.dt.strftime("%Y-%m-%d"),
        **{f"last_{c}": last_day[c] for c in history.RATES},
        "last_choke_pct": last_ck.choke_opening_pct,
        "last_choke_time": last_ck.timestamp,
        **{c: fluid[c].round(4) for c in history.FLUID},
        "last_test_start": wt.groupby("well_name").test_start.max(),
        "train_end": train_end,
    }).rename_axis("well_name").reset_index()

    out.mkdir(parents=True, exist_ok=True)
    rates.assign(timestamp=rates.timestamp.dt.strftime("%Y-%m-%d"))[
        ["timestamp", "well_name", *history.RATES]].to_csv(out / "daily_rates.csv", index=False)
    state.to_csv(out / "well_state.csv", index=False)
    train.to_csv(out / "train_tests.csv", index=False)
    return state


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--end", default="2025-09-30")
    ap.add_argument("--out", type=Path, default=history.HIST_DIR)
    a = ap.parse_args()
    state = build(pd.Timestamp(a.end), a.out)
    print(f"history to {a.end} -> {a.out}  (train_tests.csv reproduces vfm.pkl: checked)")
    print(state[["well_name", "cum_oil_stb", "last_oil_rate_stbd", "last_choke_pct",
                 "last_choke_time", "water_cut_pct"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
