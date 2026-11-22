"""Monthly refit: the model of each month has seen every well test that ended before that month.

The test data are the three months after training and carry measured well tests. A frozen model
drifts over those months (oil WAPE 2.72 -> 3.26 -> 3.46% by month, ml/eda/rolling_refit.py); a
model refitted as tests arrive stays flat. So for an upload with tests after the training period:

    first month     the shipped model, unchanged (no new test has ended yet)
    each later one  refitted on the training tests (ml/models/history/train_tests.csv) plus every
                    uploaded test that ended before the first day of that month

Nothing is looked up from the future: a day in November is predicted without any November test.
The refit is the same two least-squares fits as ml/fit_vfm.py, held in memory only -- vfm.pkl is
never written. The routing factors are carried over unchanged: tests are test-separator rates, so
they recalibrate the choke law and the water cut, not the routing correction.

Monthly, not after every test: on our data the two are tied (oil WAPE gap -0.02 [-0.15, +0.21]),
and a monthly model gives a daily series with at most one step per month.

An upload with no test after the training period (our own Jan-Sep data) gets the shipped model
object itself, so its predictions are identical to the submitted file.
"""
from __future__ import annotations

import copy
import warnings

import numpy as np
import pandas as pd

from vfm import EPOCH, VFMModel

# A new test whose measured liquid rate is this far from what the shipped model predicts for its
# own sensors is left out of the refit (a unit or logging error, not a rate change). The model's
# worst time-forward miss on a real test is far inside this.
MAX_LABEL_RATIO = 1.5


class MonthlyModel:
    """Routes each row to the model of its calendar month (`t` is days since vfm.EPOCH)."""

    def __init__(self, base: VFMModel, by_month: dict[pd.Period, VFMModel]):
        self.base, self.by_month = base, dict(by_month)
        self.wells = base.wells

    def predict(self, X: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
        if not len(X) or not self.by_month:
            return self.base.predict(X, strict=strict)
        month = (EPOCH + pd.to_timedelta(X.t.to_numpy(float), unit="D")).to_period("M")
        parts = []
        for per in month.unique():
            idx = np.flatnonzero(month == per)
            p = self.by_month.get(per, self.base).predict(X.iloc[idx], strict=strict)
            p.index = idx
            parts.append(p)
        return pd.concat(parts).sort_index().reset_index(drop=True)


def unrouted(model):
    """The same model without the routing correction: what a test-separator rate is compared to."""
    if isinstance(model, MonthlyModel):
        return MonthlyModel(unrouted(model.base), {k: unrouted(m) for k, m in model.by_month.items()})
    m = copy.copy(model)
    m.routing_factor = 1.0
    if hasattr(m, "water_scale"):   # a leaderboard water level, if one is ever baked in (RUNBOOK, Case W):
        m.water_scale = 1.0         # also a normal-day correction, so also off for a test window
    return m


def monthly_refit(base: VFMModel, hist: dict | None, Xt: pd.DataFrame | None, wt: pd.DataFrame | None,
                  ok: np.ndarray | None, days: pd.Series) -> tuple[VFMModel | MonthlyModel, dict]:
    """Build the month-by-month model for an upload.

    Xt, wt, ok: model inputs, cleaned labels and a usable-window mask for the uploaded tests (row
    for row). days: the dates being predicted. Returns (model, report); the model is `base` itself
    whenever there is nothing to refit on.
    """
    rep = {"refits": [], "tests_after_training": 0, "tests_left_out": [], "note": ""}
    if hist is None or hist.get("train") is None:
        rep["note"] = "no training tests stored (ml/models/history/train_tests.csv); shipped model used"
        return base, rep
    if Xt is None or wt is None or not len(wt):
        rep["note"] = "no well tests in the upload; shipped model used"
        return base, rep

    cut = pd.Timestamp(hist["state"].train_end.max())
    new = ok & (wt.test_start > cut).to_numpy()
    oil, wat = wt.oil_rate_stbd.to_numpy(float), wt.water_rate_stbd.to_numpy(float)
    need = ["S", "dpc", "whp", "gl", "rs", "t", *base.wc_features]
    new &= np.isfinite(Xt[need].to_numpy(float)).all(axis=1) & (Xt.S.to_numpy(float) > 0)
    new &= np.isfinite(oil) & np.isfinite(wat) & (oil > 0) & (wat >= 0)
    rep["tests_after_training"] = int(new.sum())
    if not new.any():
        rep["note"] = "no usable well test after the training period; shipped model used"
        return base, rep

    # labels that contradict their own sensors stay out
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = unrouted(base).predict(Xt)
    ratio = (oil + wat) / (p.oil_rate_stbd + p.water_rate_stbd).to_numpy(float)
    known = np.isin(Xt.well_name.to_numpy(), base.wells)
    wild = new & known & ~((ratio > 1 / MAX_LABEL_RATIO) & (ratio < MAX_LABEL_RATIO))
    for i in np.flatnonzero(wild):
        rep["tests_left_out"].append(f"{wt.well_name.iloc[i]} {wt.test_start.iloc[i]:%Y-%m-%d} "
                                     f"(measured/predicted liquid {ratio[i]:.2f})")
    new &= ~wild

    train = hist["train"]
    end = wt.test_end.to_numpy()
    by_month = {}
    for per in pd.PeriodIndex(pd.to_datetime(days), freq="M").unique().sort_values():
        sel = new & (end < np.datetime64(per.start_time))
        if not sel.any():
            continue
        cols = [c for c in train.columns if c in Xt.columns]
        X = pd.concat([train[cols], Xt.loc[sel, cols]], ignore_index=True)
        try:
            m = copy.copy(base).fit(X, np.r_[train.oil_rate_stbd.to_numpy(float), oil[sel]],
                                    np.r_[train.water_rate_stbd.to_numpy(float), wat[sel]])
            if not (np.isfinite(m.choke_coef).all() and np.isfinite(m.wc_coef).all()):
                raise ValueError("non-finite coefficients")
        except Exception as e:  # a failed refit must not take the run down: that month keeps the shipped model
            rep["tests_left_out"].append(f"refit for {per} failed ({e}); shipped model used")
            continue
        by_month[per] = m
        rep["refits"].append({"month": str(per), "tests_added": int(sel.sum()),
                              "wells": int(wt.well_name[sel].nunique()), "trained_on": m.trained_on})
    if not by_month:
        rep["note"] = "no new test ended before a later month began; shipped model used"
        return base, rep
    return MonthlyModel(base, by_month), rep


def describe(rep: dict) -> str:
    """One line for the data-quality table."""
    if rep["refits"]:
        return ", ".join(f"{r['month']} (+{r['tests_added']} tests)" for r in rep["refits"])
    return "none: " + rep["note"]
