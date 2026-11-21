"""Feature engineering and normalisation for the VFM model.

The design follows one measured fact: 98.3% of oil-rate variance sits BETWEEN
wells and only 1.7% WITHIN them. So the problem is really two problems:

  1. well scale      -> from static rock/completion properties (leakage-free;
                        cum_oil_at_2025_01_01 alone is r=+0.96 with mean oil rate)
  2. within-well drift -> from sensor deviations against that well's own baseline

Raw sensor values answer neither cleanly, which is why plain global
standardisation does not help here: it rescales columns without separating
these two signals. Per-well z-scoring does separate them.

Leakage rules observed throughout:
  * per-well baselines come from the HIGH-FREQUENCY record, never from labels.
    High-frequency data exists for every well at prediction time, so this is
    legitimate; normalising by a label-derived well mean would not be.
  * static properties are known before 2025 and are safe.
  * the StandardScaler is inside a Pipeline so it is fit on training folds only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import SENSORS

# columns aggregated over a window: raw sensors plus the engineered drops
AGG_COLS = SENSORS + ["dp_choke", "dp_tubing", "dp_annulus_tubing", "choke_pct"]

# how many of a window's minutes must be present for the row to be usable
MIN_COVERAGE = 0.80


# --------------------------------------------------------------------------- #
# per-well baselines (leakage-free: derived from unlabelled sensor data)
# --------------------------------------------------------------------------- #
def well_baselines(hf: pd.DataFrame) -> pd.DataFrame:
    """Median and IQR of each sensor per well, over the whole record.

    Used to express a window as a deviation from how that well normally runs.
    Robust statistics so a residual outage or spike cannot move the baseline.
    """
    g = hf.groupby("well_name", observed=True)[AGG_COLS]
    med = g.median().add_suffix("__wmed")
    iqr = (g.quantile(0.75) - g.quantile(0.25)).add_suffix("__wiqr")
    out = pd.concat([med, iqr], axis=1)
    # guard against a degenerate IQR (constant sensor) before dividing
    for c in AGG_COLS:
        s = out[f"{c}__wiqr"]
        out[f"{c}__wiqr"] = s.where(s > 1e-6, 1.0)
    return out.reset_index()


# --------------------------------------------------------------------------- #
# window aggregation
# --------------------------------------------------------------------------- #
def _slope_per_hour(y: np.ndarray, minutes: np.ndarray) -> float:
    """Least-squares trend in units per hour; NaN-safe."""
    m = np.isfinite(y)
    if m.sum() < 3:
        return np.nan
    return float(np.polyfit(minutes[m] / 60.0, y[m], 1)[0])


def aggregate_windows(hf: pd.DataFrame, windows: pd.DataFrame) -> pd.DataFrame:
    """Summarise the per-minute record over arbitrary [start, end] windows.

    `windows` needs columns well_name, start, end. Returns one row per window
    with mean/std/min/max/p10/p90/last/slope per sensor, plus coverage.
    """
    hf = hf.sort_values(["well_name", "timestamp"])
    by_well = {w: d.reset_index(drop=True) for w, d in hf.groupby("well_name", observed=True)}
    rows = []
    for _, win in windows.iterrows():
        d = by_well.get(win.well_name)
        if d is None:
            continue
        lo, hi = d.timestamp.searchsorted(win.start), d.timestamp.searchsorted(win.end, "right")
        d = d.iloc[lo:hi]
        expected = max(int((win.end - win.start).total_seconds() // 60) + 1, 1)
        rec = {"well_name": win.well_name, "start": win.start, "end": win.end,
               "n_minutes": len(d), "coverage": len(d) / expected}
        mins = (d.timestamp - win.start).dt.total_seconds().to_numpy() / 60.0
        for c in AGG_COLS:
            v = d[c].to_numpy(dtype="float64")
            rec[f"{c}__mean"] = np.nanmean(v) if np.isfinite(v).any() else np.nan
            rec[f"{c}__std"] = np.nanstd(v) if np.isfinite(v).sum() > 1 else np.nan
            rec[f"{c}__min"] = np.nanmin(v) if np.isfinite(v).any() else np.nan
            rec[f"{c}__max"] = np.nanmax(v) if np.isfinite(v).any() else np.nan
            rec[f"{c}__p10"] = np.nanpercentile(v, 10) if np.isfinite(v).any() else np.nan
            rec[f"{c}__p90"] = np.nanpercentile(v, 90) if np.isfinite(v).any() else np.nan
            rec[f"{c}__last"] = v[np.isfinite(v)][-1] if np.isfinite(v).any() else np.nan
            rec[f"{c}__slope"] = _slope_per_hour(v, mins)
        rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# normalisation layers
# --------------------------------------------------------------------------- #
def add_within_well(feats: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Robust per-well z-scores: (window mean - well median) / well IQR.

    This is the layer that exposes the 1.7% within-well signal. Without it a
    tree model spends its depth separating wells by absolute pressure instead
    of learning how each well responds to its own changes.
    """
    f = feats.merge(base, on="well_name", how="left")
    for c in AGG_COLS:
        f[f"{c}__z"] = (f[f"{c}__mean"] - f[f"{c}__wmed"]) / f[f"{c}__wiqr"]
        f[f"{c}__ratio"] = f[f"{c}__mean"] / f[f"{c}__wmed"].replace(0, np.nan)
    return f.drop(columns=[c for c in f.columns if c.endswith(("__wmed", "__wiqr"))])


def static_table(pvt: pd.DataFrame, comp: pd.DataFrame,
                 asof: pd.Timestamp = pd.Timestamp("2025-01-01")) -> pd.DataFrame:
    """Static per-well properties plus the capacity proxies that set well scale."""
    s = pvt.merge(comp, on="well_name")
    s["days_on_prod"] = (asof - s.first_production_date).dt.days
    s["phi_h"] = s.porosity_frac * s.net_pay_thickness_ft           # storage thickness
    s["hc_pore_volume"] = (s.phi_h * (1 - s.water_saturation_frac)
                           * s.estimated_drainage_area_acres)        # hydrocarbon pore volume
    s["tubing_area_in2"] = np.pi * (s.tubing_id_in / 2) ** 2         # flow area
    s["gl_valve_depth_frac"] = s.gl_valve_tvd_ft / s.gauge_tvd_ft    # lift-point placement
    s["datum_minus_gauge_ft"] = s.datum_tvd_ft - s.gauge_tvd_ft      # PTA depth correction
    s["cum_oil_mmstb"] = s.cum_oil_at_2025_01_01_stb / 1e6
    s["mobility"] = s.net_pay_thickness_ft / s.oil_viscosity_cp      # kh/mu proxy (k unknown)
    return s.drop(columns=["first_production_date"])


STATIC_FEATURES = [
    "net_pay_thickness_ft", "porosity_frac", "water_saturation_frac",
    "oil_viscosity_cp", "oil_fvf_rb_stb", "bubble_point_pressure_psia",
    "reservoir_temperature_degf", "estimated_drainage_area_acres",
    "total_compressibility_1_psi", "wellbore_radius_ft",
    "gauge_tvd_ft", "gl_valve_tvd_ft", "gl_valve_port_64ths", "tubing_id_in",
    "solution_gor_at_pb_scf_stb", "days_on_prod", "phi_h", "hc_pore_volume",
    "tubing_area_in2", "gl_valve_depth_frac", "cum_oil_mmstb", "mobility",
]


def add_physics(f: pd.DataFrame) -> pd.DataFrame:
    """Interactions that carry multiphase-flow meaning, not just column products."""
    eps = 1e-6
    # choke response: a choke equation is roughly q ~ Cv * f(opening) * sqrt(dP)
    f["choke_flow_proxy"] = f["choke_pct__mean"] * np.sqrt(f["dp_choke__mean"].clip(lower=0) + eps)
    # lift efficiency: injected gas per unit of available drawdown
    f["gl_per_dp"] = f["gas_lift_rate_mscfd__mean"] / (f["dp_tubing__mean"].abs() + eps)
    # how hard the well is being drawn down relative to its own normal
    f["drawdown_ratio"] = f["dp_tubing__mean"] / (f["dh_pressure_psia__mean"] + eps)
    # annulus-to-tubing differential drives injection through the valve
    f["inj_differential"] = f["annulus_pressure_psia__mean"] - f["whp_psia__mean"]
    # temperature rise above reservoir temperature tracks total throughput
    if "reservoir_temperature_degf" in f:
        f["temp_deficit"] = f["reservoir_temperature_degf"] - f["dh_temperature_degf__mean"]
    # stability of the window: a surging well tests badly
    f["whp_instability"] = f["whp_psia__std"] / (f["whp_psia__mean"].abs() + eps)
    return f


# --------------------------------------------------------------------------- #
# assembled tables
# --------------------------------------------------------------------------- #
TARGETS = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]


def build_training_table(hf, wt, pvt, comp) -> pd.DataFrame:
    """The 85 labelled rows: window features + per-well z-scores + statics."""
    windows = wt[["well_name", "test_start", "test_end"]].rename(
        columns={"test_start": "start", "test_end": "end"})
    f = aggregate_windows(hf, windows)
    f = add_within_well(f, well_baselines(hf))
    f = f.merge(static_table(pvt, comp), on="well_name", how="left")
    f = add_physics(f)
    lab = wt[["well_name", "test_start"] + TARGETS].rename(columns={"test_start": "start"})
    f = f.merge(lab, on=["well_name", "start"], how="left")
    # capacity-normalised targets: removes the between-well scale a model would
    # otherwise have to memorise, and is invertible for an unseen well
    for t in TARGETS:
        f[f"{t}__per_phih"] = f[t] / f["phi_h"]
    return f


def build_daily_table(hf, pvt, comp, min_coverage: float = MIN_COVERAGE) -> pd.DataFrame:
    """Daily features for the Excel deliverable, same transform chain as training."""
    d = hf.copy()
    d["date"] = d.timestamp.dt.normalize()
    windows = (d.groupby(["well_name", "date"], observed=True)
                 .size().reset_index(name="n"))
    windows["start"] = windows.date
    windows["end"] = windows.date + pd.Timedelta(hours=23, minutes=59)
    f = aggregate_windows(hf, windows[["well_name", "start", "end"]])
    f = add_within_well(f, well_baselines(hf))
    f = f.merge(static_table(pvt, comp), on="well_name", how="left")
    f = add_physics(f)
    f["date"] = f["start"].dt.normalize()
    f["low_coverage"] = f.coverage < min_coverage
    return f


def feature_columns(f: pd.DataFrame) -> list[str]:
    """Model inputs: everything numeric that is not a target, key, or artefact."""
    drop = set(TARGETS + [f"{t}__per_phih" for t in TARGETS]
               + ["well_name", "start", "end", "date", "n_minutes", "low_coverage"])
    return [c for c in f.columns
            if c not in drop and pd.api.types.is_numeric_dtype(f[c])]
