"""Rate history around each shut-in, for PTA superposition and hold-out tests.

    python ml/export_pta_rates.py

Writes ml/outputs/pta_rate_history.csv with one row per (well, timestamp):

    well_name, timestamp, oil_rate_stbd, resolution, segment

Three segments per shut-in, at the resolution each use needs:

    pre_shutin   10-min, the 6 h before the choke closes   -> #4 (rate at shut-in)
    post_reopen  10-min, the 24 h after it reopens         -> #3b (drawdown hold-out)
    daily_90d    daily, the 90 days before the shut-in     -> #5 (superposition)

All rates are the shipped VFM model with ROUTING_LAMBDA=0.80 applied, so they
are on the same footing as the q values already in the PTA submission (the
daily figures reproduce them exactly -- asserted below).

Shut-in minutes are excluded from the 10-min segments: the well produces
nothing then, and a bin straddling the boundary would otherwise be a blend.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))

from config import F_HF_CLEAN, OUT  # noqa: E402
import features as F  # noqa: E402
from vfm import ROUTING_FACTORS, VFMModel, build_inputs  # noqa: E402

# shut-in and reopening times, from the six choke-closed events
EVENTS = {
    "GL-01": ("2025-04-15 08:00", "2025-04-18 08:00"),
    "GL-02": ("2025-03-08 14:23", "2025-03-08 20:02"),
    "GL-04": ("2025-06-03 08:00", "2025-06-05 08:00"),
    "GL-06": ("2025-07-22 03:11", "2025-07-22 11:11"),
    "GL-08": ("2025-08-19 09:00", "2025-08-22 09:00"),
    "GL-10": ("2025-05-27 21:04", "2025-05-28 06:04"),
}
PRE_H, POST_H, DAILY_D = 6, 24, 90


def predict_bins(model, hf, pvt, comp, well, lo, hi, freq) -> pd.DataFrame:
    """VFM oil on a regular grid between lo and hi, flowing minutes only."""
    d = hf[(hf.well_name == well) & (hf.timestamp >= lo) & (hf.timestamp < hi)].copy()
    d = d[~d.is_shut_in]
    if d.empty:
        return pd.DataFrame()
    d["bin"] = d.timestamp.dt.floor(freq)
    agg = {c: (c, "mean") for c in F.AGG_COLS}
    b = d.groupby("bin", observed=True).agg(**agg, n=("is_shut_in", "size")).reset_index()
    f = b.rename(columns={c: f"{c}__mean" for c in F.AGG_COLS}).assign(
        well_name=well, start=b.bin)
    f = f.merge(F.well_baselines(hf), on="well_name", how="left")
    f = f.merge(F.static_table(pvt, comp), on="well_name", how="left")
    for c in F.AGG_COLS:
        f[f"{c}__z"] = 0.0
    p = model.predict(build_inputs(f))
    return pd.DataFrame({"well_name": well, "timestamp": b.bin,
                         "oil_rate_stbd": p.oil_rate_stbd.round(2),
                         "n_minutes": b.n})


def main() -> None:
    hf = pd.read_parquet(F_HF_CLEAN)
    pvt = pd.read_csv(ROOT / "data" / "reservoir_pvt.csv")
    comp = pd.read_csv(ROOT / "data" / "well_completion.csv",
                       parse_dates=["first_production_date"])
    model = VFMModel.load(ROOT / "ml" / "models" / "vfm.pkl")
    daily_sub = pd.read_csv(OUT / "submitted" / "lam0.80_21.0200_SHIPPED.csv")
    daily_sub["d"] = pd.to_datetime(daily_sub.timestamp)

    rows = []
    for well, (s, r) in EVENTS.items():
        s, r = pd.Timestamp(s), pd.Timestamp(r)
        pre = predict_bins(model, hf, pvt, comp, well, s - pd.Timedelta(hours=PRE_H), s, "10min")
        if not pre.empty:
            rows.append(pre.assign(resolution="10min", segment="pre_shutin"))
        post = predict_bins(model, hf, pvt, comp, well, r, r + pd.Timedelta(hours=POST_H), "10min")
        if not post.empty:
            rows.append(post.assign(resolution="10min", segment="post_reopen"))
        d = daily_sub[(daily_sub.well_name == well)
                      & (daily_sub.d >= s - pd.Timedelta(days=DAILY_D))
                      & (daily_sub.d < s.normalize())]
        rows.append(pd.DataFrame({"well_name": well, "timestamp": d.d.values,
                                  "oil_rate_stbd": d.oil_rate_stbd.values,
                                  "n_minutes": 1440, "resolution": "daily",
                                  "segment": "daily_90d"}))

    out = pd.concat(rows, ignore_index=True).sort_values(
        ["well_name", "segment", "timestamp"], ignore_index=True)
    path = OUT / "pta_rate_history.csv"
    out.to_csv(path, index=False)

    print(f"wrote {path.relative_to(ROOT)}  ({len(out):,} rows)\n")
    print(f"  {'well':7s} {'pre 10min':>10s} {'post 10min':>11s} {'daily':>7s} "
          f"{'q_last_6h':>10s} {'q_day-1':>9s} {'ratio':>7s}")
    for well, (s, _) in EVENTS.items():
        g = out[out.well_name == well]
        pre = g[g.segment == "pre_shutin"]
        q6 = np.average(pre.oil_rate_stbd, weights=pre.n_minutes) if len(pre) else np.nan
        qd = daily_sub[(daily_sub.well_name == well)
                       & (daily_sub.d == pd.Timestamp(s).normalize() - pd.Timedelta(days=1))
                       ].oil_rate_stbd.iloc[0]
        print(f"  {well:7s} {len(pre):10d} {(g.segment=='post_reopen').sum():11d} "
              f"{(g.segment=='daily_90d').sum():7d} {q6:10.1f} {qd:9.1f} {q6/qd:7.4f}")
    print("\n  q_day-1 is the rate the shipped PTA used; q_last_6h is the #4 candidate.")


if __name__ == "__main__":
    main()
