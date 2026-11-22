"""Daily rates by time-integration, not by predicting on daily-mean sensors.

A daily rate is the time average of the instantaneous rate. On a day the well
flowed for only part of the time, predicting from the day's *mean* sensors is
not that: the mean mixes shut-in minutes (choke 0, high WHP) with flowing
ones, and the choke law is nonlinear, so f(mean) != mean(f).

It matters. On the ten partial shut-in days in this dataset the two differ by
30% on average and up to 68%, in both directions. Fully-flowing days are
unaffected (0.02% mean difference), so this is a correctness fix for the
shut-in days rather than a change in behaviour everywhere -- and those are
precisely the days a reviewer will look at.

Method: bin the day into 10-minute windows, predict on the flowing bins only,
count shut-in minutes as zero rate, and average over the minutes actually
observed. Gaps therefore average over what exists rather than assuming zero.

**Applied to partial shut-in days only, by default.** The model is a
window-mean model: it was fitted on 12-24 h test windows (721-1441 minutes),
and every one of those windows was a flowing well. Running it on 10-minute
bins applies the fitted relation at a timescale 100x shorter than anything it
was calibrated on.

For a partial shut-in day that is still clearly the right thing to do, because
the day's mean is the thing outside the calibrated regime -- no training
window ever contained shut-in minutes. For a fully flowing day the 24 h mean
*is* the calibrated use case, and integrating instead "corrects" a Jensen gap
that the fitted exponent may already absorb. On GL-03 2025-09-02, where
dp_choke swings 5.7-29.6 psi within the day, blanket integration moves the
rate 33% with nothing to validate it against. Pass `only_partial=False` to
integrate everything, but treat that as an experiment.

    daily_rates(model, hf, pvt, comp) -> one row per well-day
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

import features as F
from vfm import build_inputs

BIN = "10min"
PHASES = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]


def daily_rates(model, hf: pd.DataFrame, pvt: pd.DataFrame, comp: pd.DataFrame,
                bin_size: str = BIN, only_partial: bool = True) -> pd.DataFrame:
    """Time-integrated daily rates.

    With `only_partial` (the default) the returned frame carries rates for the
    partial shut-in days alone and NaN elsewhere, so the caller keeps its
    daily-mean predictions for fully flowing days. See the module docstring
    for why that line is drawn there.
    """
    hf = hf.copy()
    hf["date"] = hf.timestamp.dt.normalize()
    hf["bin"] = hf.timestamp.dt.floor(bin_size)

    agg = {c: (c, "mean") for c in F.AGG_COLS}
    b = (hf.groupby(["well_name", "date", "bin"], observed=True)
           .agg(**agg, shut=("is_shut_in", "mean"), n_min=("is_shut_in", "size"))
           .reset_index())

    # minutes per day actually recorded -- the denominator of the time average
    per_day = b.groupby(["well_name", "date"], observed=True).n_min.sum().rename("day_minutes")

    flow = b[b.shut < 0.5].copy()
    feats = flow.rename(columns={c: f"{c}__mean" for c in F.AGG_COLS}).assign(
        well_name=flow.well_name.astype(str), start=flow.bin)
    feats = feats.merge(F.well_baselines(hf), on="well_name", how="left")
    feats = feats.merge(F.static_table(pvt, comp), on="well_name", how="left")
    for c in F.AGG_COLS:          # z-scores are unused by the model; keep the schema
        feats[f"{c}__z"] = 0.0

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pred = model.predict(build_inputs(feats))
    unseen = sorted(set(pred.loc[pred.unseen_well, "well_name"])) if len(pred) else []

    # Weight each bin by its own minutes. Shut-in minutes contribute zero
    # rate, which is correct -- the well really produced nothing.
    #
    # A bin whose SENSORS are missing is different: predict() returns NaN for
    # it, and we must not let those minutes sit in the denominator. Doing so
    # silently scales the day down by the missing fraction -- GL-03 on
    # 2025-09-02 lost 23.6% of its flowing minutes to gas-lift gaps and came
    # out 33% low, which first looked like a Jensen effect and was really this
    # bug. Caught by Rovshan. Fifteen well-days in this dataset hit it; the
    # shipped partial shut-in days happen not to, but an upload with sensor
    # gaps would be biased low, so the live demo was exposed.
    flow = flow.reset_index(drop=True)
    usable = np.isfinite(pred[PHASES].to_numpy()).all(axis=1)
    for p in PHASES:
        flow[p] = pred[p].to_numpy() * flow.n_min.to_numpy()
    flow["priced_min"] = np.where(usable, flow.n_min.to_numpy(), 0)

    shut_min = (b.loc[b.shut >= 0.5]
                 .groupby(["well_name", "date"], observed=True).n_min.sum()
                 .rename("shut_min"))
    agg = flow.groupby(["well_name", "date"], observed=True)[PHASES + ["priced_min"]].sum()
    out = agg.join(per_day, how="right").join(shut_min, how="left").reset_index()
    out[PHASES + ["priced_min"]] = out[PHASES + ["priced_min"]].fillna(0.0)
    out["shut_min"] = out.shut_min.fillna(0.0)

    # denominator: minutes we could actually price, plus genuinely shut minutes
    denom = (out.priced_min + out.shut_min).replace(0, np.nan)
    out["unpriced_min"] = out.day_minutes - denom.fillna(0)
    for p in PHASES:
        out[p] = out[p] / denom

    cov = (hf.groupby(["well_name", "date"], observed=True)
             .agg(shut_minutes=("is_shut_in", "sum"), minutes=("is_shut_in", "size"))
             .reset_index())
    out = out.merge(cov, on=["well_name", "date"], how="left")
    out["uptime"] = 1 - out.shut_minutes / out.minutes
    out["coverage"] = out.minutes / 1440
    out["partial_shutin"] = out.shut_minutes.between(1, out.minutes - 1)
    out["fully_shut"] = out.shut_minutes == out.minutes
    if only_partial:
        keep = out.partial_shutin | out.fully_shut
        out.loc[~keep, PHASES] = np.nan
    out.attrs["unseen_wells"] = unseen
    out.attrs["warnings"] = [str(w.message) for w in caught]
    return out.sort_values(["well_name", "date"], ignore_index=True)


def integrate_shut_in_days(pred: pd.DataFrame, daily: pd.DataFrame, model, hf: pd.DataFrame,
                           pvt: pd.DataFrame, comp: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Replace daily-mean predictions on shut-in-affected days with the time-integrated rates.

    The same swap ml/fit_vfm.py makes for the scored file, for the paths that run on uploaded
    data (ml/predict_from_raw.py, ui/pipeline.py). `pred` rows align with `daily` rows; `hf` is
    the cleaned sensor frame (it needs `is_shut_in`). Returns (pred, number of days swapped).
    """
    integ = daily_rates(model, hf, pvt, comp).set_index(["well_name", "date"])
    key = pd.MultiIndex.from_arrays([daily.well_name.astype(str).to_numpy(),
                                     pd.to_datetime(daily.date).to_numpy()])
    pred = pred.copy()
    n = 0
    for col in PHASES:
        repl = integ[col].reindex(key).to_numpy()
        take = np.isfinite(repl)
        pred.loc[take, col] = repl[take]
        n = max(n, int(take.sum()))
    return pred, n


def to_submission(out: pd.DataFrame, template_cols: list[str]) -> pd.DataFrame:
    """Rectangular grid in the template's column order, gaps interpolated."""
    sub = pd.DataFrame({
        "timestamp": pd.to_datetime(out.date).dt.strftime("%Y-%m-%d"),
        "well_name": out.well_name.astype(str).values,
        **{p: out[p].round(1) for p in PHASES},
    })
    grid = pd.MultiIndex.from_product(
        [sorted(sub.well_name.unique()),
         pd.date_range(sub.timestamp.min(), sub.timestamp.max()).strftime("%Y-%m-%d")],
        names=["well_name", "timestamp"])
    s = sub.set_index(["well_name", "timestamp"]).reindex(grid)
    s[PHASES] = (s.groupby(level=0)[PHASES]
                  .transform(lambda c: c.interpolate(limit_direction="both")).round(1))
    return s.reset_index()[template_cols].sort_values(
        ["well_name", "timestamp"], ignore_index=True)
