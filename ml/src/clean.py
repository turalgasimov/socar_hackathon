"""Cleaning pipeline for the SOCAR 2026 well-performance dataset.

Two entry points:
    clean_high_freq()  -> per-minute sensor frame, despiked, choke-joined, shut-ins flagged
    clean_well_tests() -> 85 well tests with recoverable label errors repaired

Every repair is logged to stdout and returned in a report dict so the
decisions stay auditable.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from config import (
    F_CHOKE, F_HF_PARQUET, F_HIGH_FREQ, F_WELL_TESTS, MAX_INTERP_GAP_MIN,
    MSCF_TO_M3, NULL_SENTINEL, SENSORS, SPIKE_FLOOR,
)

DTYPES = {c: "float32" for c in SENSORS}


# --------------------------------------------------------------------------- #
# high-frequency sensor data
# --------------------------------------------------------------------------- #
def load_high_freq(use_cache: bool = True, data_dir: Path | None = None) -> pd.DataFrame:
    """Read the per-minute file, caching it as parquet (257MB -> 62MB).

    `data_dir` points the whole pipeline at a different copy of the raw CSVs,
    which is what the app does with an upload. The parquet cache is bypassed
    entirely in that case -- otherwise a run against new data would silently
    return the cached rows from *our* dataset, which is the worst possible
    failure in a live demo because it looks like it worked.
    """
    if data_dir is not None:
        return pd.read_csv(
            Path(data_dir) / "high_freq_data.csv",
            dtype={**DTYPES, "well_name": "category"}, parse_dates=["timestamp"],
        ).sort_values(["well_name", "timestamp"], ignore_index=True)
    if use_cache and F_HF_PARQUET.exists():
        return pd.read_parquet(F_HF_PARQUET)
    hf = pd.read_csv(
        F_HIGH_FREQ, dtype={**DTYPES, "well_name": "category"}, parse_dates=["timestamp"]
    ).sort_values(["well_name", "timestamp"], ignore_index=True)
    hf.to_parquet(F_HF_PARQUET, index=False, compression="zstd")
    return hf


def _despike(s: pd.Series, floor: float, n_sigma: float = 6.0,
             win: int = 15, scale_win: int = 241, max_run: int = 3) -> pd.Series:
    """Hampel-style filter. Returns a boolean mask of points to reject.

    A point is a spike when it sits more than `n_sigma` robust sigmas *and*
    more than `floor` away from the local median. Runs longer than `max_run`
    minutes are spared: a sustained offset is a real process change (choke
    move, shut-in), not an instrument glitch.
    """
    med = s.rolling(win, center=True, min_periods=5).median()
    resid = s - med
    sigma = 1.4826 * resid.abs().rolling(scale_win, center=True, min_periods=30).median()
    mask = (resid.abs() > np.maximum(n_sigma * sigma, floor)) & resid.notna()
    if mask.any():
        grp = (mask != mask.shift()).cumsum()
        run_len = mask.groupby(grp).transform("size")
        mask &= run_len <= max_run
    return mask.fillna(False)


def clean_high_freq(use_cache: bool = True, verbose: bool = True,
                    data_dir: Path | None = None,
                    hist: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """`hist` (ml/src/history.py) supplies each well's last known choke setting when an upload
    of later months has no opening choke row for it. Without it, behaviour is unchanged."""
    hf = load_high_freq(use_cache, data_dir)
    rep: dict = {"rows_in": len(hf)}

    # 1. duplicate (well, timestamp) keys -- byte-identical repeated records
    dup = hf.duplicated(["well_name", "timestamp"]).sum()
    hf = hf.drop_duplicates(["well_name", "timestamp"]).sort_values(
        ["well_name", "timestamp"], ignore_index=True)
    rep["duplicate_rows_dropped"] = int(dup)

    # 2. the -999.25 absent-value code masquerades as a real reading
    sent = {}
    for c in SENSORS:
        n = int((hf[c] == NULL_SENTINEL).sum())
        hf.loc[hf[c] == NULL_SENTINEL, c] = np.nan
        sent[c] = n
    rep["sentinel_to_nan"] = sent

    # 3. isolated instrument spikes
    spikes = {}
    for c in SENSORS:
        mask = hf.groupby("well_name", observed=True)[c].transform(
            lambda s: _despike(s, SPIKE_FLOOR[c])).astype(bool)
        spikes[c] = int(mask.sum())
        hf.loc[mask, c] = np.nan
    rep["spikes_removed"] = spikes

    # 4. physical-consistency screens (evaluated after despiking)
    rep["physical_violations"] = {
        "whp_downstream_gt_whp": int((hf.whp_downstream_psia > hf.whp_psia).sum()),
        "dh_pressure_le_whp": int((hf.dh_pressure_psia <= hf.whp_psia).sum()),
        "negative_gas_lift": int((hf.gas_lift_rate_mscfd < 0).sum()),
    }
    bad = (hf.whp_downstream_psia > hf.whp_psia) | (hf.dh_pressure_psia <= hf.whp_psia)
    hf.loc[bad, ["whp_psia", "whp_downstream_psia", "dh_pressure_psia"]] = np.nan
    hf.loc[hf.gas_lift_rate_mscfd < 0, "gas_lift_rate_mscfd"] = np.nan

    # 5. bridge short outages only; long gaps stay visible to the aggregator
    filled = {}
    for c in SENSORS:
        before = int(hf[c].isna().sum())
        hf[c] = hf.groupby("well_name", observed=True)[c].transform(
            lambda s: s.interpolate(method="linear", limit=MAX_INTERP_GAP_MIN,
                                    limit_area="inside"))
        filled[c] = before - int(hf[c].isna().sum())
    rep["short_gaps_interpolated"] = filled
    rep["residual_nan"] = {c: int(hf[c].isna().sum()) for c in SENSORS}

    # 6. choke position: an event log, so hold each setting until the next change
    # merge_asof requires both frames sorted by the `on` key alone
    choke_path = (Path(data_dir) / "choke_events.csv") if data_dir else F_CHOKE
    ck = pd.read_csv(choke_path, parse_dates=["timestamp"]).sort_values("timestamp")
    hf["well_name"] = hf.well_name.astype(str)  # and matching key dtypes
    # a well with no event at or before its first minute would have no choke until its first
    # change; an upload of later months may lack the opening rows, so take the last known setting
    import history
    ck, ck_rep = history.complete_choke(ck, hf.groupby("well_name").timestamp.min(), hist)
    rep.update(ck_rep)
    hf = pd.merge_asof(
        hf.sort_values("timestamp"),
        ck.rename(columns={"choke_opening_pct": "choke_pct"}),
        on="timestamp", by="well_name", direction="backward",
    ).sort_values(["well_name", "timestamp"], ignore_index=True)
    hf["well_name"] = hf.well_name.astype("category")
    rep["choke_events"] = len(ck) - len(rep["choke_initial_from_history"])

    # 7. shut-in flag -- choke fully closed. These are the PTA build-up windows.
    hf["is_shut_in"] = hf.choke_pct.eq(0.0)
    rep["shut_in_minutes"] = int(hf.is_shut_in.sum())

    # 8. engineered pressure drops used by both VFM and PTA
    hf["dp_choke"] = hf.whp_psia - hf.whp_downstream_psia      # across the choke
    hf["dp_tubing"] = hf.dh_pressure_psia - hf.whp_psia        # gauge -> wellhead
    hf["dp_annulus_tubing"] = hf.annulus_pressure_psia - hf.whp_psia

    rep["rows_out"] = len(hf)
    if verbose:
        _print_report("HIGH-FREQUENCY CLEANING", rep)
    return hf, rep


# --------------------------------------------------------------------------- #
# well tests (the VFM labels)
# --------------------------------------------------------------------------- #
def clean_well_tests(verbose: bool = True,
                     data_dir: Path | None = None) -> tuple[pd.DataFrame, dict]:
    """Repair the label table.

    Two defect classes, both exactly recoverable from redundant columns:
      * sign flips on otherwise-valid magnitudes
      * GL-06 gas columns logged in m3/d under an Mscf/d header
    GOR and GLR are treated as ground truth: gas + gas_lift - total_gas closes
    to 0.11 mscfd when gas is rebuilt from them.
    """
    wt_path = (Path(data_dir) / "well_tests.csv") if data_dir else F_WELL_TESTS
    wt = pd.read_csv(wt_path, parse_dates=["test_start", "test_end"])
    rep: dict = {"rows": len(wt)}

    # 1. sign flips -- magnitude agrees with redundant columns, only sign is wrong
    flips = {}
    for c in ["gas_lift_rate_mscfd", "water_rate_stbd", "gas_rate_mscfd",
              "total_gas_rate_mscfd", "oil_rate_stbd"]:
        neg = wt[c] < 0
        if neg.any():
            flips[c] = [
                f"{r.well_name} {r.test_start:%Y-%m-%d} {r[c]:+.1f}"
                for _, r in wt.loc[neg].iterrows()
            ]
            wt.loc[neg, c] = wt.loc[neg, c].abs()
    rep["sign_flips_fixed"] = flips

    # 2. unit error: stated gas vs GOR-implied gas differs by exactly 1 Mscf in m3
    gas_implied = wt.gor_scf_stb * wt.oil_rate_stbd / 1000.0
    unit_bad = ((wt.gas_rate_mscfd / gas_implied) - MSCF_TO_M3).abs() < 0.5
    rep["unit_error_gas_rows"] = int(unit_bad.sum())
    rep["unit_error_wells"] = sorted(wt.loc[unit_bad, "well_name"].unique().tolist())
    wt.loc[unit_bad, "gas_rate_mscfd"] = gas_implied[unit_bad]

    tot_implied = wt.glr_scf_stb * wt.liquid_rate_stbd / 1000.0
    tot_bad = ((wt.total_gas_rate_mscfd / tot_implied) - MSCF_TO_M3).abs() < 0.5
    wt.loc[tot_bad, "total_gas_rate_mscfd"] = tot_implied[tot_bad]
    rep["unit_error_total_gas_rows"] = int(tot_bad.sum())

    # 3. post-repair identity residuals -- all should now be ~0
    rep["identity_residuals_max_abs"] = {
        "liquid-(oil+water)": float((wt.liquid_rate_stbd
                                     - (wt.oil_rate_stbd + wt.water_rate_stbd)).abs().max()),
        "watercut-wat/liq": float((wt.water_cut_pct
                                   - wt.water_rate_stbd / wt.liquid_rate_stbd * 100).abs().max()),
        "gor-gas/oil": float((wt.gor_scf_stb
                              - wt.gas_rate_mscfd * 1000 / wt.oil_rate_stbd).abs().max()),
        "totgas-(gas+gl)": float((wt.total_gas_rate_mscfd
                                  - (wt.gas_rate_mscfd + wt.gas_lift_rate_mscfd)).abs().max()),
        "glr-totgas/liq": float((wt.glr_scf_stb
                                 - wt.total_gas_rate_mscfd * 1000 / wt.liquid_rate_stbd).abs().max()),
    }
    wt["test_hours"] = (wt.test_end - wt.test_start).dt.total_seconds() / 3600
    wt["test_mid"] = wt.test_start + (wt.test_end - wt.test_start) / 2
    if verbose:
        _print_report("WELL-TEST LABEL CLEANING", rep)
    return wt, rep


def _print_report(title: str, rep: dict) -> None:
    bar = "=" * 74
    print(f"\n{bar}\n{title}\n{bar}")
    for k, v in rep.items():
        if isinstance(v, dict) and not v:
            print(f"{k}: none")
        elif isinstance(v, dict) and all(isinstance(x, (int, float)) for x in v.values()):
            print(f"{k}: " + ", ".join(f"{kk}={vv:.4g}" if isinstance(vv, float)
                                       else f"{kk}={vv}" for kk, vv in v.items()))
        elif isinstance(v, dict):
            print(f"{k}:")
            for kk, vv in v.items():
                print(f"    {kk}: {vv}")
        else:
            print(f"{k}: {v}")
