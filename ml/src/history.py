"""What the app keeps from the training period, so an upload of later months still gets it.

The test data are the next three months of the same ten wells, delivered as high_freq_data.csv,
choke_events.csv and well_tests.csv (PVT and completion unchanged). Predicting their rates needs
nothing from the past: ml/models/vfm.pkl carries every fitted coefficient, including each well's
intercept and water-cut trend. Four things do need the past, and this module supplies them:

1. **PTA producing time.** N_p = cum_oil_at_2025_01_01 (well_completion.csv) + oil produced since.
   An upload that starts on 1 Oct has no Jan-Sep days, so N_p would miss 2.5-10.3% of the well's
   cumulative oil (GL-03 10.3%, GL-08 7.3%).
2. **The rate before a shut-in on the upload's first day.** PTA takes q from the previous full
   day, which then lies in the history.
3. **The choke setting before the upload's first choke event.** choke_events.csv is an event
   log. If the upload has no opening row per well, the minutes before the first change have no
   choke, and those days cannot be predicted. The last known setting fills them -- only when the
   upload starts after the history ends, because a 30 Sep setting says nothing about January.
4. **Fluid properties and the training cut-off.** Per-well averages of the last well tests are a
   fallback for the gauge-to-datum correction, and the date of the last training test labels an
   accuracy check on uploaded tests as held-out or in-sample.
5. **The training tests themselves.** train_tests.csv holds the model inputs and measured rates
   of every test the shipped model was fitted on, so the model can be refitted month by month as
   the upload brings new tests (ml/src/rolling.py).

Built by `python ml/build_history.py` -> ml/models/history/{daily_rates,well_state,train_tests}.csv.
The rates are the scored Task 1 file (lam0.80_21.0200_SHIPPED.csv), the same rates PTA uses.
Uploaded days always take precedence over history days.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

HIST_DIR = Path(__file__).resolve().parents[1] / "models" / "history"
RATES = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]
FLUID = ["oil_gravity_api", "gas_sg", "water_salinity_ppm", "water_cut_pct"]
_CUM = re.compile(r"cum_oil_at_(\d{4})_(\d{2})_(\d{2})_stb")


def load(hist_dir: Path | None = None) -> dict | None:
    """The stored history, or None if it was never built (callers then behave as before)."""
    d = Path(hist_dir) if hist_dir else HIST_DIR
    if not (d / "well_state.csv").exists() or not (d / "daily_rates.csv").exists():
        return None
    rates = pd.read_csv(d / "daily_rates.csv", parse_dates=["timestamp"])
    state = pd.read_csv(d / "well_state.csv",
                        parse_dates=["as_of", "last_choke_time", "last_test_start", "train_end"])
    train = None
    if (d / "train_tests.csv").exists():
        train = pd.read_csv(d / "train_tests.csv", parse_dates=["start", "end"])
    return dict(rates=rates, state=state.set_index("well_name"), train=train, dir=str(d))


def cum_anchor(comp: pd.DataFrame) -> tuple[pd.Timestamp, str]:
    """(date, column) of the cumulative-oil figure in well_completion.csv.

    Read from the column name, so a completion file that carries the cumulative to a later date
    (e.g. cum_oil_at_2025_10_01_stb) is handled without a code change.
    """
    for c in comp.columns:
        m = _CUM.fullmatch(c)
        if m:
            return pd.Timestamp("-".join(m.groups())), c
    raise KeyError("well_completion.csv has no cum_oil_at_YYYY_MM_DD_stb column")


def extend_rates(rates: pd.DataFrame, hist: dict | None) -> tuple[pd.DataFrame, list[str]]:
    """Uploaded daily rates, preceded per well by the history days before the upload's first day.

    For PTA only (N_p and the pre-shut-in rate). Exports and charts keep the uploaded period alone.
    """
    if hist is None:
        return rates, ["no training history found; PTA uses the uploaded days only"]
    r = rates.copy()
    first = pd.to_datetime(r.timestamp).groupby(r.well_name).min()
    h = hist["rates"]
    h = h[h.well_name.isin(first.index)]
    h = h[h.timestamp < h.well_name.map(first)]
    notes = []
    if len(h):
        last = h.groupby("well_name").timestamp.max()
        gap = ((first.reindex(last.index) - last).dt.days - 1).clip(lower=0)
        notes.append(f"{len(h):,} well-days of training history used for PTA producing time "
                     f"({h.timestamp.min():%Y-%m-%d} to {h.timestamp.max():%Y-%m-%d})")
        for w, g in gap[gap > 0].items():
            notes.append(f"{w}: {g} day(s) between the history and the upload are not covered; "
                         "N_p misses that production")
    h = h.assign(timestamp=h.timestamp.dt.strftime("%Y-%m-%d"))[rates.columns]
    out = pd.concat([h, rates], ignore_index=True).sort_values(["well_name", "timestamp"],
                                                               ignore_index=True)
    return out, notes


def complete_choke(ck: pd.DataFrame, first_ts: pd.Series, hist: dict | None) -> tuple[pd.DataFrame, dict]:
    """Give every well a choke setting from its first sensor minute.

    `first_ts`: first timestamp per well in the uploaded sensors. A well with no choke event at or
    before that minute gets its last known setting from the history, placed at that minute -- but
    only if the upload starts after the history ends. Otherwise it is reported as unknown.
    """
    rep = {"choke_initial_from_history": [], "choke_initial_unknown": []}
    add = []
    state = None if hist is None else hist["state"]
    for w, t0 in first_ts.items():
        if ((ck.well_name == w) & (ck.timestamp <= t0)).any():
            continue
        if state is not None and w in state.index and t0 >= state.loc[w, "as_of"]:
            add.append({"timestamp": t0, "well_name": w,
                        "choke_opening_pct": float(state.loc[w, "last_choke_pct"])})
            rep["choke_initial_from_history"].append(w)
        else:
            rep["choke_initial_unknown"].append(w)
    if add:
        ck = pd.concat([pd.DataFrame(add), ck], ignore_index=True).sort_values("timestamp",
                                                                              ignore_index=True)
    return ck, rep


def fluid_props(well: str, tests_raw: pd.DataFrame | None, hist: dict | None) -> pd.Series | None:
    """Test-average API, gas SG, salinity and water cut: from the upload, else from the history."""
    if tests_raw is not None and (tests_raw.well_name == well).any():
        return tests_raw.loc[tests_raw.well_name == well, FLUID].mean()
    if hist is not None and well in hist["state"].index:
        return hist["state"].loc[well, FLUID].astype(float)
    return None


def train_end(hist: dict | None) -> pd.Timestamp | None:
    """Start of the last well test the shipped model was fitted on."""
    return None if hist is None else pd.Timestamp(hist["state"].train_end.max())
