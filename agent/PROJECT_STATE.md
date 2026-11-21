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
| S0 | shipped model, uncorrected | ×1.000 | 20.2110 |
| S1 | per-well routing factor, all phases | ×1.028 | **20.9463** |
| λ=2.5 | routing over-scaled | ×1.071 | 18.3400 |
| S3 | S1 + global GOR factor, gas only | gas ×0.982 | 20.9100 |

**S3 rejected.** −0.036 against S1, on Rovshan's own pre-set condition
("reject if the leaderboard gets worse"). It improved all three *time-forward*
gas metrics and still lost, and the reason is instructive: the +2.04% gas bias
was measured against **test-routed** labels, which are themselves ~2.5% high
relative to normal production. Much of that "gas bias" was the routing offset
appearing in the gas column. S1 already scales gas up 2.78%, so ×0.982 on top
corrected the same error twice, in opposite directions.

This is exactly why S3 had to be layered on S1. Built on S0 it would have
landed between the two and isolated neither change.

**S1 remains the champion at 20.9463.**

| probe | change vs S1 | score |
|---|---|--:|
| widened water-cut split | routing-safe sensors added to WC | 20.5700 |
| label transfer, a=1.0 | trained on 85 real + 170 transferred | 20.3300 |
| gas level ×1.02 | gas only, up | 20.6100 |

**Gas is at its optimum too.** Three points — ×0.982 → 20.9100, ×1.000 →
20.9463, ×1.020 → 20.6100 — put the V vertex at +0.00%. Both directions lose.

Note the asymmetry: the slope above the optimum is **8× steeper** than below
(0.168 vs 0.020 points per 1%). Over-predicting gas is punished far harder
than under-predicting it. If anything ever nudges gas again, **err low**.

**Label transfer is closed.** Tested three ways and it loses every time:
unweighted time-forward (oil WAPE 2.30 → 4.55), with Rovshan's 1/σ² weighting
at every α from 0.05 to 1.0 (monotonically worse), and on the leaderboard
(20.33 against 20.9463). An isolation run showed the transferred rows
themselves do the damage, not the `whp_downstream` feature they were meant to
unlock: at α=0.05, 2.30 → 3.88 with the same water-cut set, → 3.84 with
`whp_downstream` added.

The idea was sound and the diagnosis behind it was right — the transferred
rows really do land where the predictions live (`whp_downstream` 168.8–204.7
against 158.0–205.3). It simply does not pay. Those 170 rows are not
measurements; they are 85 labels moved by a physics assumption, and
correlated error in two-thirds of the training set costs more than the
feature coverage is worth. The same correction applied as a post-hoc scale
is worth +0.735 and leaves the exponents alone.

**Time-forward is a poor guide to leaderboard performance, in both directions.** The
widened water-cut split improved WAPE *and* R² on all three phases
time-forward and lost 0.38 on the leaderboard. S3's gas factor improved all
three gas metrics and lost 0.04. Both are reverted.

The common cause is the regime gap. All 85 labels are test-routed; the 2,729
days we are scored on are not. Time-forward measures fit quality *inside* the
test regime, and a change that fits that regime better can fit the prediction
regime worse. **Treat time-forward as a guard against obvious regressions,
not as evidence a change will score.** Only the leaderboard decides, so
changes should go up one at a time.

**The routing lever is exhausted. λ=1.0 is the optimum.** Three points fix
the V: ascending slope +0.735/λ below it, −1.738/λ above. The arms intersect
at **λ = 1.000**, which is exactly where S1 sits. The downhole physics
estimate of ~2.5% was right, and the leaderboard independently confirms it.

The asymmetry (descent 2.4× steeper than the ascent) is expected: R² degrades
quadratically with a scale error, so the far point at λ=2.5 is pulled down by
more than a linear arm predicts. That biases the vertex estimate slightly
left, so the true optimum is at or just below λ=1 — fine probes at λ=0.85–0.95
are built in `ml/outputs/ladder/` if worth confirming, but the V says they all
score below 20.9463.

**Do not fit a parabola to this.** A parabola through (0, 20.211), (1, 20.946),
(2.5, 18.34) places its maximum near λ=0.86 and misses the kink entirely.

**S1 settled the routing question: the ground truth is normal-production
routed.** Scaling up by the per-well factor gained **+0.735 points**, about
0.26 points per 1% of upward scaling on that segment. Rovshan's downhole
estimate was right and the choke law was overstating the response, exactly as
he argued.

Still open: whether 2.8% is the optimum or we are still short. WAPE against a
systematically-offset truth is **V-shaped, not quadratic** — it falls linearly
until the bias reaches zero, then rises — so three points bracket the minimum
rather than needing a curve fit. S2 at ×1.053 does that: still descending puts
it near 21.6; past the minimum it scores below 20.95 and the optimum lies
between ×1.028 and ×1.053.

Built by `python ml/make_variants.py`. One hypothesis per submission.

**What S0 and S1 together establish.** S0 at 67% was well below what our
validation implied. The two candidate explanations were a systematic routing
offset or a merely strict metric-to-points mapping. S1 separated them: the
score moved, so the offset is real. Both effects are probably present — the
remaining gap after correction is consistent with a strict mapping on top.

**Validation cannot see this.** Every one of the 85 labels is test-routed, so
a correction whose value lives on normal-production days scores identically
in time-forward and only shows on the leaderboard. That is why the probes are
worth their submissions.

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
