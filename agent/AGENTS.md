# Working in this repo

SOCAR Hackathon 2026 — Intelligent Well Performance Analysis. Challenge brief is
`docs/README.md`; read it before changing anything in `ml/`.

## Environment

`python` is **not on PATH** on this machine. Use the full interpreter path:

```
C:/Users/Faiq/AppData/Local/Programs/Python/Python313/python.exe
```

Installed: pandas 2.3.2, numpy 2.3.2, scikit-learn 1.8.0, lightgbm 4.6.0,
xgboost 3.2.0, scipy, matplotlib, seaborn, plotly, streamlit 1.53.1,
pyarrow 23.0.0, openpyxl 3.1.5.

## Layout

```
data/           raw CSVs (high_freq_data.csv is 257 MB, tracked via Git LFS)
data/processed/ derived parquet — GITIGNORED, regenerate with the pipeline
docs/           challenge brief and rules
ml/src/         config.py, clean.py, features.py, viz.py
ml/eda/         run_eda.py, validate_features.py
ml/outputs/     figures + generated markdown reports
ui/             UI (Phase 3, not started)
```

`ml/src` is added to `sys.path` by the scripts; modules import each other by
bare name (`import features`), not as a package.

## Run order

```bash
PY="C:/Users/Faiq/AppData/Local/Programs/Python/Python313/python.exe"
# 1. clean  -> data/processed/{high_freq_clean,well_tests_clean}.parquet
"$PY" -c "import sys;sys.path.insert(0,'ml/src');import clean;from config import *; \
  wt,_=clean.clean_well_tests();wt.to_parquet(F_WT_CLEAN,index=False); \
  hf,_=clean.clean_high_freq();hf.to_parquet(F_HF_CLEAN,index=False,compression='zstd')"
# 2. EDA    -> ml/outputs/figures/*.png + eda_summary.md
"$PY" ml/eda/run_eda.py
# 3. validate feature sets -> ml/outputs/feature_report.md
"$PY" ml/eda/validate_features.py
```

Cleaning the 3.9M-row file takes ~90 s. The raw→parquet cache makes reloads
near-instant; delete `data/processed/high_freq.parquet` to force a re-read.

## Data facts you must not rediscover the hard way

- **Missing values are `-999.25`, not NaN.** The raw high-frequency file has
  zero NaNs and 7,410 sentinel readings. Never `read_csv` it without masking.
- **GL-06's gas columns in `well_tests.csv` are in m³/d under an Mscf/d header**
  (factor 28.3168 = 1 Mscf in m³). `clean.py` rebuilds them from GOR/GLR.
- Five sign-flipped values in `well_tests.csv` (gas_lift ×2, water_rate,
  gas_rate, total_gas). All repaired by magnitude agreement with other columns.
- 2,513 duplicate `(well_name, timestamp)` rows.
- **2025-08-09 01:09–05:40 all ten wells drop out at once** (historian failure).
  No well can impute another across it.
- Well-test sensor columns **are** the mean of their window — that is the
  correct VFM label join.
- Choke closed (`choke_opening_pct == 0`) ⟺ gas lift off. Six such events.

## Modelling rules

- **Never validate with a random split.** Other tests from the same well leak a
  memorised rate level; it scores ~4% MAPE and means nothing. Use the
  time-forward scheme in `ml/eda/validate_features.py`.
- 98.3% of oil-rate variance is *between* wells, 1.7% *within*. Features must
  carry well identity (per-well z-scores + static properties) or a model will
  learn the between-well trend and invert the within-well one — downhole
  temperature flips sign, −0.41 pooled to +0.57 within-well.
- 136 features for 85 labelled rows. Keep regularisation strong; prefer the
  smaller feature sets. High-capacity models overfit this table.
- Fit scalers **inside** a `Pipeline` so they see training folds only.

## Conventions

- Figures use `ml/src/viz.py` (validated CVD-safe palette, small multiples past
  3 series). Call `viz.apply_style()` before plotting, `viz.titled()` /
  `viz.save()` for the title block.
- Chart subtitles state the takeaway and must match the numbers actually
  plotted — verify before writing one.
- Cleaning functions return `(frame, report_dict)`; keep every repair logged.
