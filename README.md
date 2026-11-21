# SOCAR Hackathon 2026 — Intelligent Well Performance Analysis

Virtual Flow Metering (VFM) and Pressure Transient Analysis (PTA) for ten
gas-lifted wells, delivered through a single interactive workflow.

- Challenge brief: [`docs/README.md`](docs/README.md)
- Current status and next steps: [`PROJECT_STATE.md`](PROJECT_STATE.md)
- Conventions and gotchas for contributors: [`AGENTS.md`](AGENTS.md)
- Findings: [`ml/outputs/eda_summary.md`](ml/outputs/eda_summary.md),
  [`ml/outputs/feature_report.md`](ml/outputs/feature_report.md)

## Getting started

This repo stores `data/high_freq_data.csv` (257 MB) in **Git LFS**. Install it
first or you will clone a 130-byte pointer file instead of the data:

```bash
git lfs install
git clone https://github.com/turalgasimov/socar_hackathon
```

Python 3.13 with pandas, scikit-learn, lightgbm, matplotlib, streamlit,
pyarrow and openpyxl. On the original machine `python` is not on PATH — see
`AGENTS.md` for the interpreter path.

Rebuild everything from the raw CSVs (`data/processed/` is gitignored):

```bash
python -c "import sys;sys.path.insert(0,'ml/src');import clean;from config import *; \
  wt,_=clean.clean_well_tests();wt.to_parquet(F_WT_CLEAN,index=False); \
  hf,_=clean.clean_high_freq();hf.to_parquet(F_HF_CLEAN,index=False,compression='zstd')"
python ml/eda/run_eda.py
python ml/eda/validate_features.py
```

## The dataset in one paragraph

Ten gas-lifted wells (GL-01…GL-10), 1 January – 30 September 2025. 3.9 M rows of
per-minute wellhead/downhole pressure, temperature, annulus pressure and
gas-lift rate; **85 well tests** carrying the measured oil/water/gas rates that
are the only labels; 65 choke events; static PVT and completion properties.

Three things to know before touching it:

1. **Missing values are encoded `-999.25`, not NaN.** The raw file reports zero
   nulls and 7,410 sentinel readings.
2. **98.3% of oil-rate variance is between wells, 1.7% within.** A random
   train/test split leaks the well's rate level and scores ~4% MAPE
   meaninglessly. Validate time-forward.
3. **Only 6 of 10 wells ever shut in**, so only those admit PTA.

Full defect list and the reasoning behind each repair:
[`ml/outputs/eda_summary.md`](ml/outputs/eda_summary.md).

## Layout

```
data/            raw CSVs (high_freq_data.csv via Git LFS)
data/processed/  derived parquet, gitignored — regenerate with the commands above
docs/            challenge brief and rules
ml/src/          config · clean · features · viz
ml/eda/          run_eda.py · validate_features.py
ml/outputs/      figures and generated reports
web/             Streamlit UI (Phase 3)
```
