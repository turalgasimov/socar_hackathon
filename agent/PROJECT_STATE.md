# Project state

Last updated: 2026-11-21

Scoring: VFM 50 (methodology 20 / accuracy 30) · Auto-PTA 30 (plots 10 /
parameters 20) · UI 10 · Presentation 10.

> **Keep this file current.** Anyone — person or agent — who writes or changes
> code updates this file **in the same commit**: move the Status row, add a line
> under Done with the number that proves it works, prune Next, and record any
> risk or decision the team must not silently reverse. A stale state file sends
> the next session to redo finished work. The plan and task ownership live in
> [`NEXT_STEPS.md`](NEXT_STEPS.md).

## Status

| Phase | Deliverable | State |
|---|---|---|
| 0 | Data cleaning | **done** |
| 0 | EDA | **done** |
| 1 | Feature engineering | **done** |
| 1 | VFM baselines benchmarked | **done** (physics wins time-forward: 2.67–3.10% vs Ridge 5.11%) |
| 1 | Chosen VFM model, fitted and persisted | not started |
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

**VFM baselines** (`ml/eda/benchmark_vfm.py`) — physics beats ML on 85 labels,
which is the expected outcome at this sample size. Liquid rate, leave-one-test-out:

| model | MAPE |
|---|--:|
| Choke physics, `q ∝ S²·√ΔPc·√WHP·GLR⁻⁰·⁶` | **1.82%** |
| IPR per-well (`Pwf`, `t`) | 2.10% |
| Ridge (raw + well one-hot) | 2.93% |
| HistGradientBoosting (raw + static) | 3.80% |
| RandomForest (raw + well one-hot) | 5.19% |
| *leave-one-WELL-out, HGB* | *69.7%* |

Phase split from the choke model: oil 2.35%, water 3.25%, gas 5.33%. The fitted
exponents (`S^2.05`, `dPc^0.47`) reproduce the subcritical choke law, so the
model is recovering real physics rather than curve-fitting.

**Time-forward scores** (`ml/eda/timeforward_vfm.py`) — the honest number for
the deliverable. Predicting well *w* at time *T*, training sees the other nine
wells plus *w*'s own earlier tests only; the water-cut trend is extrapolated
from past tests. 55 of 85 tests scored (a well needs 3 prior tests).

| target | MAPE | bias |
|---|--:|--:|
| liquid | **2.04%** | +0.26% |
| oil | **3.07%** | +0.53% |
| water | **3.99%** | −0.03% |
| gas | **5.90%** | +2.31% |

Worth noting: LOO (1.82%) is only mildly optimistic here, 2.04% time-forward.
A constrained physical form cannot memorise a well's level the way a free ML
model can — the same comparison on the Ridge feature stack degrades 3.99% →
6.44%. **LOO is still the wrong number to report**, but the choke model is not
leaning on leakage. Gas carries a +2.31% bias from the `gas = oil × Rs` split;
worth revisiting if gas accuracy matters to scoring.

**Physics variants vs ML, time-forward** (`python ml/eda/benchmark_vfm.py --tf-only`,
~15 s, needs `train_table.parquet`). Same 55 folds as `validate_features.time_forward()`,
oil rate, features taken from `train_table` so Ridge-58 is scored on identical rows.
(The choke × WC-trend row reads 3.10% here vs 3.07% in `timeforward_vfm.py` only because
the inputs come from cleaned-HF window means rather than the `well_tests.csv` columns.)

| model | TF MAPE | p90 |
|---|--:|--:|
| Persistence (copy the well's previous test) | 6.00% | 12.6% |
| Per-well linear trend | 6.04% | 13.3% |
| Ridge, 58 features (`validate_features`) | 5.11% | 10.1% |
| IPR per-well (`t`, `Pwf`) | 8.45% | 9.5% |
| Choke × water-cut trend | 3.10% | 6.1% |
| Thermal per-well, `qo = a + b·T_gauge` (Joule-Thomson) | 3.08% | 5.4% |
| ½ choke + ½ thermal (weights fixed in advance) | 2.93% | 5.1% |
| **Choke × WC(t, `dp_tubing`, GL), variant chosen by nested TF** | **2.67%** | 5.5% |

Well-cluster bootstrap (5000 resamples, 95% CI of the MAPE gap):
- Ridge − (choke+thermal) = **+2.17 pp [+1.07, +3.42]** → the physics lead is real.
- Persistence − Ridge = +0.89 pp [−1.54, +3.34] → Ridge-58 is **not** distinguishable
  from copying the previous test.
- choke_trend − (choke+thermal) = +0.17 pp [−0.26, +0.56] → the ensemble gain is
  **not** established.
- choke_trend − choke_vlp = +0.54 pp [+0.16, +1.04] → using the tubing pressure drop
  (`dp_tubing`) as a water-cut sensor is a real gain: of the choke model's oil error,
  the water-cut estimate is the part that improves most.

Error vs number of earlier tests of the same well (3 → 6–8): Ridge 4.00 → 6.18%,
choke 3.97 → 2.73%, thermal 5.53 → 2.32% — the physics models improve as history
accumulates, Ridge does not. **Per-well IPR with free `t` and `Pwf` terms is not
usable time-forward** (8.45%): it extrapolates the reservoir-pressure decline from
3–8 points. All rows are still test-routed labels — the train–serve skew under
Open risks applies to every number in this table.

Artefacts (regenerate — `data/processed/` is gitignored):
`high_freq_clean.parquet`, `well_tests_clean.parquet`,
`train_table.parquet` (85 × 147), `daily_table.parquet` (2,729 well-days × 143).

## Next

**The plan, with owners and estimates, lives in [`NEXT_STEPS.md`](NEXT_STEPS.md).**
It is kept in one place so the two cannot drift apart — this file records what
*is*, that file records what is *planned*.

In short: settle the test-mode correction (blocks everything), fit and persist
the model, export the daily Excel, then PTA, UI, presentation.

Open question for the organisers, worth asking early: **is the daily ground
truth measured under test-separator routing or normal production?** The answer
decides the first item.

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

- **Train–serve skew on `whp_downstream_psia` — the strongest single feature.**
  During a well test the well is routed to the test separator (129.7–134.5 psia)
  rather than the production manifold, so downstream wellhead pressure runs
  **19–29 psi lower during tests than in normal production, on all ten wells**.
  That is **−2.6σ** in test-time units; no other sensor shifts more than 0.20σ.

  Concretely, GL-04: its 9 tests all sit between 149.3 and 156.9 psia, while the
  273 days to predict run 159.4–189.7. **The lowest normal day is above the
  highest test — zero overlap.** The model has never seen a value like the ones
  it must predict on.

  It reaches the choke model through `dPc`: 129.6 psi on test windows vs 119.2
  on normal days. Through `dPc^0.47` that alone biases predictions **−3.8%**.
  Against the honest time-forward errors that is ~1.9× the liquid error (2.04%)
  and ~1.2× the oil error (3.07%) — comparable to the model's accuracy, not
  dwarfed by it, and *systematic*, so unlike random error it does not average
  out over 2,729 well-days. Independently confirmed in
  `docs/DATA_REPORT_TASK1_TASK2.md` §1.5, which estimates test rates 1–4% high.

  **This is a correction to apply, not a reason to discard the model.** Decide
  before submitting: de-bias the daily predictions, or restrict to the
  routing-invariant sensors (`whp`, `dh_pressure`, `annulus`, `gas_lift`,
  `dh_temperature`, all ≤0.20σ).

- **Unseen-well generalisation fails.** Every feature set scores at or worse than
  predicting the global mean under GroupKFold by well. With 10 wells there is not
  enough between-well data. Only matters if the organisers score on a held-out
  *well* rather than held-out days — worth confirming with them.
- **85 labels, 136 features.** Overfitting is the main threat to the 30 accuracy
  points.
- `data/high_freq_data.csv` is in Git LFS and draws on the repo owner's quota
  (1 GB free storage/bandwidth). Each clone pulls 257 MB. Teammates need
  `git lfs install` or they get a 130-byte pointer instead of the CSV.
