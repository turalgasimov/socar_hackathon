# Working in this repo

SOCAR Hackathon 2026 — **Intelligent Well Performance Analysis**. Build a single
workflow that goes from raw field sensors → estimated production rates (VFM) →
well-test interpretation (PTA), behind a usable interface.

Scoring, out of 100: **VFM 50** (methodology 20, accuracy 30) · **Auto-PTA 30**
(plots 10, parameters 20) · **UI 10** · **Presentation 10**. Challenge brief:
`docs/README.md`.

---

## 1. The problem in one page

Ten gas-lifted wells (`GL-01`…`GL-10`), 1 Jan – 30 Sep 2025.

- **3.9 M rows** of per-minute sensors: wellhead pressure up/downstream of the
  choke, downhole pressure and temperature, annulus pressure, gas-lift rate.
- **85 well tests** — the *only* labels. Each is a 12–24 h window with measured
  oil, water and gas rates. 7–9 per well.
- 65 choke events, plus static PVT and completion properties per well.

**Phase 1 (VFM):** predict daily oil / water / gas for every well-day.
**Phase 2 (PTA):** Horner build-up analysis using the predicted daily oil rate.
**Phase 3 (UI):** both modules behind one interface, with export.

---

## 2. Environment

`python` is **not on PATH** on the original machine. Use the full path:

```
C:/Users/Faiq/AppData/Local/Programs/Python/Python313/python.exe
```

Installed: pandas 2.3.2, numpy 2.3.2, scikit-learn 1.8.0, lightgbm 4.6.0,
xgboost 3.2.0, scipy 1.17.0, matplotlib 3.10.5, seaborn, plotly,
streamlit 1.53.1, pyarrow 23.0.0, openpyxl 3.1.5.

## 3. Layout

```
agent/           AGENTS.md · CLAUDE.md · PROJECT_STATE.md · NEXT_STEPS.md
data/            raw CSVs; high_freq_data.csv (257 MB) via Git LFS
data/processed/  derived parquet — GITIGNORED, regenerate with the pipeline
docs/            brief, data dictionary, data report, physics report
ml/src/          config.py · clean.py · features.py · viz.py
ml/eda/          run_eda.py · validate_features.py · benchmark_vfm.py
ml/outputs/      figures/ + generated markdown reports
ui/              Streamlit app (Phase 3, not started)
```

`ml/src` is pushed onto `sys.path` by each script; modules import each other by
bare name (`import features`), not as a package.

## 4. Run order

```bash
PY="C:/Users/Faiq/AppData/Local/Programs/Python/Python313/python.exe"

# 1. clean -> data/processed/{high_freq_clean,well_tests_clean}.parquet  (~90 s)
"$PY" -c "import sys;sys.path.insert(0,'ml/src');import clean;from config import *; \
  wt,_=clean.clean_well_tests();wt.to_parquet(F_WT_CLEAN,index=False); \
  hf,_=clean.clean_high_freq();hf.to_parquet(F_HF_CLEAN,index=False,compression='zstd')"

# 2. EDA -> ml/outputs/figures/*.png + eda_summary.md
"$PY" ml/eda/run_eda.py

# 3. feature sets x 4 CV schemes -> ml/outputs/feature_report.md
"$PY" ml/eda/validate_features.py

# 4. physics vs ML baselines (reads raw CSVs directly, no step 1 needed)
"$PY" ml/eda/benchmark_vfm.py
```

The raw→parquet cache makes reloads near-instant. Delete
`data/processed/high_freq.parquet` to force a re-read of the 257 MB CSV.

---

## 5. Data traps — do not rediscover these the hard way

- **Missing values are `-999.25`, not NaN.** The raw high-frequency file reports
  zero nulls and 7,410 sentinel readings. A naive `read_csv` treats them as real
  pressures and silently corrupts every mean.
- **GL-06's gas columns in `well_tests.csv` are m³/d under an Mscf/d header**
  (factor 28.3168 = 1 Mscf in m³). Uncorrected, GL-06 looks like it makes 28× its
  real gas. `clean.py` rebuilds them from GOR/GLR, which are correct.
- **Five sign-flipped values** in `well_tests.csv`: `gas_lift_rate` ×2,
  `water_rate`, `gas_rate`, `total_gas_rate`.
- **2,513 duplicate `(well_name, timestamp)` rows.**
- **2025-08-09 01:09–05:40 all ten wells drop out at once** — a historian
  failure, not sensor faults. No well can impute another across it.
- **Well-test sensor columns *are* the mean of their window.** That is the
  correct VFM label join, verified to <0.4 psi.
- **Choke closed (`choke_opening_pct == 0`) ⟺ gas lift off.** Six such events,
  and they are the only PTA build-ups.
- **`choke_events.csv` is an event log, not a series** — forward-fill it.
- **The gauge sits 150–420 ft shallower than the pressure datum** on every well.
  Correct to datum before Horner or k and skin will be biased.

## 6. Modelling rules

- **Never report a random-split or plain leave-one-out score.** Other tests from
  the same well leak a memorised rate level; anything scores ~3–4% MAPE and it
  means nothing. Use the time-forward scheme in `ml/eda/validate_features.py`.
- **98.3% of oil-rate variance is between wells, 1.7% within.** Features must
  carry well identity (per-well z-scores + static properties) or a model learns
  the between-well trend and inverts the within-well one — downhole temperature
  flips sign, −0.41 pooled to +0.57 within-well.
- **Physics beats ML at n=85.** Choke model 1.82% vs Ridge 2.93%, GBM 3.80%,
  RF 5.19%. Reach for a physical relation before a bigger learner.
- **Unseen-well generalisation does not work** (69.7% MAPE, worse than the
  global mean). Ten wells is not enough to generalise to an eleventh.
- **136 features, 85 labelled rows.** Keep regularisation strong, prefer the
  smaller feature sets, fit scalers **inside** a `Pipeline`.
- **Watch the test-mode skew.** During a test the well is routed to the test
  separator, so `whp_downstream_psia` runs 19–29 psi low (−2.6σ). See
  `PROJECT_STATE.md` → Open risks before trusting any LOO number.

## 7. Conventions

- Figures go through `ml/src/viz.py` — call `viz.apply_style()` first, then
  `viz.titled()` / `viz.save()`. Validated CVD-safe palette; past 3 series use
  small multiples, not more hues.
- **A chart subtitle states the takeaway and must match the numbers actually
  plotted.** Verify before writing one.
- Cleaning functions return `(frame, report_dict)` — keep every repair logged.
- Code, comments, docs and commit messages in English.
- Numbers quoted in any document must be reproducible by a script in this repo.

## 8. Workflow — required

**Every time you write or change code, update `PROJECT_STATE.md` in the same
commit.** It is the only shared record of where the project stands; a stale one
sends the next session to redo finished work or re-litigate a settled decision.

Update, as applicable:

- the **Status** table — move the row you just advanced
- **Done** — one line on what now exists and the number that proves it works
- **Next** — remove what you finished, add what your change exposed
- **Open risks** — anything you found and did not fix
- **Decisions and constraints** — any choice the team must not silently reverse

Also:

- Check `NEXT_STEPS.md` before starting, so two agents do not take the same task.
- Do not commit anything to `data/processed/` — it is derived and gitignored.
- Before committing, re-run the scripts you touched and confirm they still pass.
