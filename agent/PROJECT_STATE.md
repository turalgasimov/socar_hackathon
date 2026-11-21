# Project state

Last updated: 2026-11-21

Scoring: VFM 50 (methodology 20 / accuracy 30) · Auto-PTA 30 (plots 10 /
parameters 20) · UI 10 · Presentation 10.

**VFM accuracy breakdown (30):** oil, water and gas score 10 each, split
**R² /3 + MAPE /2 + WAPE /5**. WAPE is half of every phase's score, so it is
the metric to optimise — and it is volume-weighted, meaning the big wells
dominate (GL-07 alone is 34% of field oil) and a systematic bias passes
straight through instead of partly cancelling. Gas is worth exactly as much
as oil despite being the hardest phase.

> **Keep this file current.** Anyone — person or agent — who writes or changes
> code updates this file **in the same commit**: move the Status row, add a line
> under Done with the number that proves it works, prune Next, and record any
> risk or decision the team must not silently reverse. A stale state file sends
> the next session to redo finished work. The plan and task ownership live in
> [`NEXT_STEPS.md`](NEXT_STEPS.md).

## Leaderboard

| # | Submission | Change vs S0 | Score |
|---|---|---|--:|
| S0 | shipped model, uncorrected | — | **20.211 / 30** |
| S1 | per-well routing factor, all phases | oil +2.84% | *pending* |
| S2 | scaled to test-separator level | oil +5.30% | *not submitted* |
| S3 | global GOR factor, gas only | gas −1.80% | *not submitted* |

Built by `python ml/make_variants.py`. One hypothesis per submission.

**Reading S0.** 20.211/30 is 67%. Our time-forward R² is 0.994–0.998, so if R²
scores near full marks that is ~9/9, leaving 11.2 of the 21 points carried by
MAPE and WAPE — far less than oil WAPE 2.33% / water 3.48% / gas 4.61% ought
to earn. Two explanations, not mutually exclusive: a systematic offset (the
routing bias, which WAPE passes straight through), or simply a strict mapping
from metric value to points. **A single scalar cannot separate them; S1 can.**
If the gap is the routing offset, S1 moves materially. If the mapping is
strict, it barely moves.

## Deliverables checklist

From `docs/Deliverables.pdf` — the authoritative list, stricter than the brief
in `docs/README.md`. Read it before assuming a deliverable is done.

| # | Required | State |
|---|---|---|
| 1 | Result files for Phase 1 **and** Phase 2, CSV or Excel | VFM done (`ml/outputs/vfm_submission.csv`, template-exact); PTA pending |
| 2 | Trained model file(s) **in `.pkl` format** | **done** — `ml/models/vfm.pkl` (+ `.joblib`) |
| 3 | **A notebook** with all cells run, outputs showing best results | **done** — `notebooks/VFM_Phase1.ipynb` |
| 4 | A folder containing all necessary PTA plots | pending with PTA |

> "During the evaluation, we will ask you to run and demonstrate your
> application (in which your model is already placed) using the provided
> **test data**."

That sentence is the one to design against. The app must ingest *raw, unseen*
data live, run cleaning → features → predict → PTA, and not fall over.

- **Unknown wells no longer crash.** `VFMModel.predict` falls back to the
  pooled intercept, sets an `unseen_well` flag on the row and emits a
  `UserWarning`. The numbers are still unreliable (leave-one-well-out is ~70%
  MAPE), which is why they are flagged rather than quietly returned.
  `strict=True` restores the old raise, for batch pipelines where silence is
  worse than failure.
- **The whole chain must run from raw CSVs**, not from `data/processed/`.
  Nothing has been exercised that way end to end yet.

## Status

| Phase | Deliverable | State |
|---|---|---|
| 0 | Data cleaning | **done** |
| 0 | EDA | **done** |
| 1 | Feature engineering | **done** |
| 1 | VFM baselines benchmarked | **done** (physics wins time-forward: 2.67–3.10% vs Ridge 5.11%) |
| 1 | Chosen VFM model, fitted and persisted | **done** (`ml/models/vfm.pkl`, TF oil 2.56%) |
| 1 | Excel: daily oil/water/gas predictions | **done** (2,729 well-days) |
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
leaning on leakage. Gas carries a +2.31% bias from the `gas = oil × Rs` split.
Replacing the static `Rs` with the well's own GOR history was tried and loses
on MAPE (5.90% → 6.11–8.84% depending on estimator) — the bias is real but
costs less than the variance of any estimator built from 3–8 noisy past GOR
readings. The bias stays; see `NEXT_STEPS.md` → tried and rejected.

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

**The VFM model** (`ml/src/vfm.py`, fitted by `python ml/fit_vfm.py`). Choke law
for liquid × water-cut split from the tubing gradient; gas from static Rs. The
`choke_vlp` water-cut variant, which nested time-forward selection picks in 54
of 55 folds.

| phase | R² /3 | MAPE /2 | **WAPE /5** | bias |
|---|--:|--:|--:|--:|
| oil | 0.9981 | 2.56% | **2.33%** | +0.25% |
| water | 0.9959 | 3.82% | **3.48%** | +0.15% |
| gas | 0.9940 | 5.65% | **4.61%** | +2.04% |

R² is already 0.994–0.998, so those 9 points are close to maxed; the headroom
is in WAPE and MAPE. A time-forward per-well bias calibration was tested
against the real metrics: it helps gas WAPE slightly (4.61 → 4.48) but costs
more MAPE (5.65 → 6.09) and hurts oil and water outright, whose biases are
already under 0.3%. Not applied — and the trade cannot be settled properly
without knowing how metric values map to points.

Fitted exponents: `S^2.057`, `dPc^0.472`, `WHP^0.472`, `GLR^-0.612`. The first
two are the subcritical choke law (`d²`, `√ΔP`) recovered from data.

`fit_vfm.py` runs the time-forward check *before* persisting and refuses to
save a model above 4% oil MAPE, so `vfm.joblib` is never an unscored model.
Daily predictions go through the reloaded file, not the in-memory object, so
the saved artefact is what gets exercised.

Shut-in days are a hard zero, not a model output: 5 well-days have the choke
closed for the full 24 h (`ln S` is undefined there).

**Routing gap: ~2.5%, agreed.** Four independent routes now converge, so this
is settled and no longer an open range.

| method | mean uplift | notes |
|---|--:|---|
| IPR, `J·ΔPwf` | 2.50% | 6 shut-in wells only |
| Thermal ratio, J-free | 2.51% | all 10 wells — **primary** |
| Thermal slope | 2.05% | unreliable on GL-03 |
| Daily-vs-test-window (ours) | 2.62% | all 10 wells |
| *choke law* | *5.89%* | *overstates by ~2.4x — do not use* |

IPR and the J-free thermal ratio agree at correlation 0.85, mean absolute
difference 0.45 pp. **Adopt 2.5%.** The earlier −3.8% and −7% figures were both
choke-derived and are retired; the choke law is precisely what overstates the
routing response. Per-well spread is real and needs larger uncertainty on
GL-06 (IPR 2.76 vs thermal 4.29) and GL-03 (slope 1.16 vs ratio 2.75, its rate
barely moves across tests).

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

  The agreed size is **~2.5%** (see the routing-gap table above — four
  independent methods). That is comparable to the shipped model's own 2.56%
  oil error, and *systematic*, so unlike random error it does not average out
  over 2,729 well-days. With WAPE worth 5 of each phase's 10 points and a
  systematic bias passing straight through it, this is the single largest
  remaining accuracy lever.

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
