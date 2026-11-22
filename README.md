# SOCAR Hackathon 2026 — Intelligent Well Performance Analysis

Virtual Flow Metering (VFM) and Pressure Transient Analysis (PTA) for ten
gas-lifted wells, delivered through a single interactive workflow.

- Challenge brief: [`docs/README.md`](docs/README.md)
- Current status and next steps: [`agent/PROJECT_STATE.md`](agent/PROJECT_STATE.md)
- Conventions and gotchas for contributors: [`agent/AGENTS.md`](agent/AGENTS.md)
- Current plan and task ownership: [`agent/NEXT_STEPS.md`](agent/NEXT_STEPS.md)
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
`agent/AGENTS.md` for the interpreter path.

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
CLAUDE.md        loader — imports the agent/ docs for Claude Code
agent/           AGENTS.md · CLAUDE.md · PROJECT_STATE.md · NEXT_STEPS.md
data/            raw CSVs (high_freq_data.csv via Git LFS)
data/processed/  derived parquet, gitignored — regenerate with the commands above
docs/            challenge brief, data dictionary, data & physics reports
ml/src/          config · clean · features · vfm · daily_predict · history · rolling · viz · pta_*
ml/eda/          run_eda.py · validate_features.py · benchmark_vfm.py · validation and rehearsal scripts
ml/models/       vfm.pkl · vfm.joblib · history/ (training-period store for uploads of later months)
ml/outputs/      figures, generated reports, submission files
notebooks/       VFM_Phase1.ipynb · PTA_Phase2.ipynb
ui/              Streamlit app (see ui/README.md)
pitch/           deck, notes and speech
```

## Baselines

```bash
python ml/eda/benchmark_vfm.py        # physics vs ML, leave-one-test-out
python ml/eda/validate_features.py    # feature sets x 4 CV schemes, time-forward
```

**Phase 1 is closed: leaderboard 21.0200 / 30.**

The model is a physics-constrained choke law, 14 fitted parameters, no ML —
its exponents come out at `S^2.057` and `dPc^0.472` against textbook 2 and
0.5, which is the evidence the form is right rather than curve-fitted. Honest
time-forward scores: oil 2.56% MAPE / 2.33% WAPE, water 3.82 / 3.48, gas
5.65 / 4.61.

Rebuild and submit with one command:

```bash
python ml/fit_vfm.py        # writes ml/outputs/vfm_submission.csv
```

Load the trained model (`ml/models/vfm.pkl`). The pickle holds a `VFMModel`,
whose class lives in `ml/src/vfm.py`, so that folder must be on the path first:

```python
import sys; sys.path.insert(0, "ml/src")
from vfm import VFMModel, build_inputs
model = VFMModel.load("ml/models/vfm.pkl")      # predict with model.predict(build_inputs(table))
```

The evaluation data are the next three months of the same wells. The demo path
(`ml/predict_from_raw.py`, the app) runs on such an upload alone: the stored
training history supplies the opening choke setting and the PTA producing time,
and well tests newer than the training period refit the model month by month,
in memory only. Rehearse with `python ml/eda/history_handoff.py`.

**Before trusting any local score, read the methodological lesson in
[`agent/PROJECT_STATE.md`](agent/PROJECT_STATE.md).** All 85 labels are
test-separator routed and the scored days are not, so time-forward
improvements have twice turned into leaderboard losses.
