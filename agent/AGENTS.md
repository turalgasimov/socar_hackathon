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
CLAUDE.md        loader — imports the four agent/ docs at session start
agent/           AGENTS.md · CLAUDE.md · PROJECT_STATE.md · NEXT_STEPS.md
data/            raw CSVs; high_freq_data.csv (257 MB) via Git LFS
data/processed/  derived parquet — GITIGNORED, regenerate with the pipeline
docs/            brief, data dictionary, data report, physics report
ml/src/          config · clean · features · vfm · daily_predict · viz ·
                 history (what an upload of later months takes from Jan–Sep) ·
                 rolling (monthly refit on uploaded tests, in memory only) ·
                 pta_model (diffusivity equation, Laplace + Stehfest) ·
                 pta_rate (oil rate at a shut-in from the well tests via the IPR; unscored)
                 (label_transfer.py is built but NOT shipped — see rejected)
ml/              fit_vfm.py · predict_from_raw.py · build_notebook.py · make_pta.py ·
                 build_pta_notebook.py
ml/eda/          run_eda · validate_features · benchmark_vfm ·
                 timeforward_vfm · routing_checks · pta_explore · pta_probes ·
                 history_handoff · rolling_refit · self_training · lambda_split · vfm_probes
ml/models/       vfm.pkl (required format) + vfm.joblib · history/ (Jan–Sep
                 rates + per-well state for uploads of later months, ml/src/history.py)
ml/outputs/      figures/ · submitted/ · reports · vfm_submission.csv
notebooks/       VFM_Phase1.ipynb · PTA_Phase2.ipynb (all cells executed)
ui/              Streamlit app (Tural): app.py · pipeline.py (back end) · check_pipeline.py
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

# 5. FIT + SHIP -> ml/models/vfm.pkl and ml/outputs/vfm_submission.csv
#    This is the one that produces the deliverable. It verifies time-forward
#    BEFORE persisting and refuses to save above 4% oil MAPE.
"$PY" ml/fit_vfm.py

# 6. the demo path: raw CSVs in, predictions out, nothing from data/processed/
#    The test data are only the NEXT three months; ml/models/history/ supplies the
#    opening choke setting and the PTA producing time from Jan-Sep. Rebuild it only
#    if the scored rates change; rehearse the hand-off with history_handoff.py.
"$PY" ml/predict_from_raw.py --data <dir> --out <file.csv>
"$PY" ml/build_history.py          # -> ml/models/history/ (from the lam0.80 record)
"$PY" ml/eda/history_handoff.py    # history to 31 Jul + Aug-Sep upload, ~2 min

# 7. PTA (needs step 1). Figures -> ml/outputs/figures/pta/ (~60 s), then the
#    result file -> ml/outputs/pta_submission.csv + pta_results.xlsx (~25 s).
#    make_pta.py refuses to write unless the output is identical to the scored file.
"$PY" ml/eda/pta_explore.py
"$PY" ml/make_pta.py
"$PY" ml/build_pta_notebook.py   # notebooks/PTA_Phase2.ipynb (~90 s; nbformat, nbclient, ipykernel)
"$PY" ml/eda/pta_probes.py       # unscored PTA probes -> ml/outputs/candidates/pta_*.csv
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
  The offset is constant through a build-up, so it cancels in k, S, m and
  ΔP_skin (asserted per event in `ml/make_pta.py`). Correct only reported
  absolute pressures (p*, p̄) to datum.
- **PTA `horner_slope` must be ≥ 0** — the platform rejects a negative slope,
  so report m as a positive psi/cycle. And use the **oil** rate: k from the
  total liquid rate scored 4.8375 against 8.3840.

## 6. Modelling rules

- **Never report a random-split or plain leave-one-out score.** Other tests from
  the same well leak a memorised rate level; anything scores ~3–4% MAPE and it
  means nothing. Use the time-forward scheme in `ml/eda/validate_features.py`.
- **98.3% of oil-rate variance is between wells, 1.7% within.** Features must
  carry well identity (per-well z-scores + static properties) or a model learns
  the between-well trend and inverts the within-well one — downhole temperature
  flips sign, −0.41 pooled to +0.57 within-well.
- **Physics beats ML at n=85.** Time-forward oil: choke 2.56% vs Ridge-58
  5.11%, GBM 3.80% (LOO), RF 5.19% (LOO), persistence 6.00%. A well-cluster
  bootstrap puts Ridge-58 *statistically level with copying the previous
  test*. Reach for a physical relation before a bigger learner.
- **Unseen-well generalisation does not work** (69.7% MAPE, worse than the
  global mean). Ten wells is not enough to generalise to an eleventh.
- **136 features, 85 labelled rows.** Keep regularisation strong, prefer the
  smaller feature sets, fit scalers **inside** a `Pipeline`.
- **Watch the test-mode skew.** During a test the well is routed to the test
  separator, so `whp_downstream_psia` runs 19–29 psi low (−2.6σ) and 99% of
  daily values fall outside the tested range. Keep it out of any model term:
  putting it in the water-cut split moved base oil +5.24% offline and was caught
  before submission (d0ac161). The widening that was submitted instead used only
  routing-safe sensors (whp, dh_p, dh_t, ann) and still scored 20.57 against
  20.9463, so it was reverted (7fefd46).
- **Time-forward does not predict the leaderboard.** All 85 labels are
  test-routed, the 2,729 scored days are not, so it measures fit inside the
  wrong regime. Two changes that improved every time-forward metric *lost*
  points. Use it as a regression guard; let the leaderboard settle level and
  bias. See `PROJECT_STATE.md` → the methodological lesson.
- **The test data are the next three months of the same wells, with measured
  well tests.** The demo path refits the model at the start of each month on
  the tests that ended before it (`ml/src/rolling.py`): in memory only, routing
  factors unchanged, and the shipped model untouched when an upload has no test
  after the training period. Refitting on our own predictions does nothing
  (`ml/eda/self_training.py`); do not retry it.
- **A well-test rate is compared without the routing correction.** Tests are
  test-separator rates; with the correction the check reads +2.8% high on oil.
  `rolling.unrouted()` is the one place that switches it off.
- **The routing correction is settled at λ=0.80** (`ROUTING_LAMBDA` in
  `ml/src/vfm.py`), worth +0.81 and the only change that ever gained points.
  Do not re-tune it; 0.75 and 0.80 tie and both neighbours lose.

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
- Do not delete the root `CLAUDE.md` or put content in it. It only imports the
  `agent/` docs, and that import is what makes them load automatically.
- Before committing, re-run the scripts you touched and confirm they still pass.
