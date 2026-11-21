# Project state

Last updated: 2026-11-21

Scoring: VFM 50 (methodology 20 / accuracy 30) · Auto-PTA 30 (plots 10 /
parameters 20) · UI 10 · Presentation 10.

## Status

| Phase | Deliverable | State |
|---|---|---|
| 0 | Data cleaning | **done** |
| 0 | EDA | **done** |
| 1 | Feature engineering | **done** |
| 1 | Trained VFM model | not started |
| 1 | Excel: daily oil/water/gas predictions | not started |
| 2 | Build-up detection | **done** (6 events identified) |
| 2 | Horner analysis → k, skin, ΔP_skin | not started |
| 2 | PTA plots per shut-in event | not started |
| 3 | Streamlit UI | not started |
| — | Presentation | not started |

## Done

**Cleaning** (`ml/src/clean.py`) — repairs are logged and verified, not assumed.

- High-frequency: 7,410 `-999.25` sentinels → NaN, 2,513 duplicate keys dropped,
  449 spikes removed (0.011%, Hampel filter with noise-calibrated floors),
  short gaps ≤5 min interpolated, longer outages left visible. 3,914,560 rows out.
- Well tests: 5 sign flips repaired; GL-06's 9 gas rows converted from m³/d to
  Mscf/d. All five physical identities now close to ≤0.11 (1-decimal rounding).
- `reservoir_pvt.csv` and `well_completion.csv` audited — clean, no repairs needed.

**EDA** (`ml/eda/run_eda.py`) — 7 figures + `ml/outputs/eda_summary.md`.

**Features** (`ml/src/features.py`) — window aggregation, per-well robust
z-scores, static capacity properties, physics interactions. Validated in
`ml/outputs/feature_report.md`: time-forward oil MAPE drops 27.0% → 5.1%.
Leave-one-out per target: oil 3.99%, water 3.85%, gas 7.41%.

Artefacts (regenerate — `data/processed/` is gitignored):
`high_freq_clean.parquet`, `well_tests_clean.parquet`,
`train_table.parquet` (85 × 147), `daily_table.parquet` (2,729 well-days × 143).

## Next

1. **VFM model.** Train on `train_table.parquet`, score with the time-forward
   scheme only. Start from regularised linear / small LightGBM — 85 rows against
   136 features punishes capacity. Predict onto `daily_table.parquet`, export
   `date, well_name, oil_rate_stbd, water_rate_stbd, gas_rate_mscfd`.
2. **PTA.** Horner analysis on the 6 build-ups, using predicted daily Qo as the
   rate term. Needs the depth correction below.
3. **UI.** Streamlit: upload → visualise → predict → PTA plots → export.

## Decisions and constraints

- **Only 6 of 10 wells admit PTA.** GL-03, GL-05, GL-07, GL-09 never close their
  choke. GL-02 (5.7 h) and GL-06 (8.0 h) are short — radial flow may not develop,
  so expect an uncertain Horner slope there.

  | well | start | duration | build-up |
  |---|---|--:|--:|
  | GL-01 | 2025-04-15 08:00 | 72.0 h | +271 psi |
  | GL-02 | 2025-03-08 14:23 | 5.7 h | +281 psi |
  | GL-04 | 2025-06-03 08:00 | 48.0 h | +837 psi |
  | GL-06 | 2025-07-22 03:11 | 8.0 h | +119 psi |
  | GL-08 | 2025-08-19 09:00 | 72.0 h | +522 psi |
  | GL-10 | 2025-05-27 21:04 | 9.0 h | +228 psi |

- **Gauge is 150–420 ft shallower than the pressure datum on every well.** Correct
  gauge readings to datum with a hydrostatic gradient before Horner analysis or
  permeability and skin will be biased. `datum_minus_gauge_ft` is in
  `features.static_table()`.
- **Single-phase oil PTA is justified** — every well's minimum downhole pressure
  sits well above its bubble point (e.g. GL-04: 2,269 vs 1,265 psia).
- **A random-split CV score is meaningless here** and will be ~4% MAPE regardless.
  See `ml/outputs/feature_report.md`.

## Open risks

- **Unseen-well generalisation fails.** Every feature set scores at or worse than
  predicting the global mean under GroupKFold by well. With 10 wells there is not
  enough between-well data. Only matters if the organisers score on a held-out
  *well* rather than held-out days — worth confirming with them.
- **85 labels, 136 features.** Overfitting is the main threat to the 30 accuracy
  points.
- `data/high_freq_data.csv` is in Git LFS and draws on the repo owner's quota
  (1 GB free storage/bandwidth). Each clone pulls 257 MB. Teammates need
  `git lfs install` or they get a 130-byte pointer instead of the CSV.
