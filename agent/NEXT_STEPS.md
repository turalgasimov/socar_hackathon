# Next steps

Last updated: 2026-11-21. Ordered by points at risk, not by difficulty.

Points still unclaimed: **VFM accuracy 30** · **PTA parameters 20** · **PTA
plots 10** · **UI 10** · **Presentation 10** · **VFM methodology 20** (partly
earned — the cleaning and validation work is the evidence for it).

Claim a task by putting your name in the Owner column and committing that
change before you start.

| # | Task | Owner | Blocks | Est. |
|---|---|---|---|---|
| ~~0~~ | ~~Ask organisers about routing~~ | — | — | **answered by the leaderboard** |
| ~~1~~ | ~~Settle the test-mode correction~~ | Faig | — | **done — λ=0.80, 21.0200** |
| ~~2~~ | ~~Fit + persist the VFM model~~ | Faig | — | **done** |
| ~~3~~ | ~~Excel: daily rate predictions~~ | Faig | — | **done** |
| 4 | PTA: Horner deliverables on 6 build-ups | Rovshan | 5 | 3–4 h |  **<- active**
| 5 | Streamlit UI | — | — | 4–6 h |  **<- unclaimed, 10 pts**
| 6 | Presentation | — | — | 2 h |
| ~~7~~ | ~~Export the model as `.pkl`~~ | Faig | — | **done** |
| ~~8~~ | ~~Notebook with all cells run~~ | Faig | — | **done** |
| ~~9~~ | ~~Unseen-well fallback~~ | Faig | — | **done** |

Tasks 7–9 come from `docs/Deliverables.pdf`, which is stricter than the brief
and was only read after tasks 2–3 were built. None is hard; all are required.

---

## 0–1. Routing — **CLOSED, λ = 0.80, score 21.0200**

The question "is the ground truth test-routed or normal-production?" never
needed an answer from the organisers in the end — the leaderboard settled it.
Scaling predictions up by the per-well routing factor gained **+0.735**, which
only happens if the truth is normal-production routed.

A one-parameter ladder then found the full physics correction overshoots:

| λ | 0.0 | 0.5 | 0.70 | **0.75** | **0.80** | 0.85 | 0.90 | 1.00 | 2.5 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| score | 20.2110 | 20.9100 | lost | **21.0200** | **21.0200** | lost | 20.9960 | 20.9463 | 18.3400 |

0.75 and 0.80 tie, so the peak is flat and λ pruning is finished.
`ROUTING_LAMBDA = 0.80` lives in `ml/src/vfm.py`, so `python ml/fit_vfm.py`
writes the best-scoring submission directly.

**Net: 20.2110 → 21.0200, +0.81, entirely from this one correction.**

Two questions that remain genuinely open:

- **Is there a public/private split?** λ was tuned over six submissions.
- **What is the leader doing?** 21.22 against our 21.02, cause unidentified.
  Every structural change we tried lost, so the 0.20 is not something our own
  search was going to surface.

## 1. Settle the test-mode correction — **blocks everything**

The shipped model scores 2.56% time-forward on oil, but every label is
measured under test-separator routing.

**The size is settled: ~2.5%.** Four independent routes converge — IPR 2.50%,
J-free thermal ratio 2.51%, thermal slope 2.05%, our daily-vs-test-window
2.62%. The choke law says 5.89% and is wrong; overstating the routing response
by ~2.4x is exactly the defect. See `PROJECT_STATE.md` for the per-well table.

It is systematic, not random, so it does not average out over 2,729 well-days.
With WAPE worth 5 of each phase's 10 points, and a systematic bias passing
straight through WAPE rather than partly cancelling, **this is the largest
remaining accuracy lever in the whole project.**

### Validating the label transfer — protocol

My first proposal was wrong and is superseded. I suggested "if the fitted
choke exponents move materially, we injected our own assumption." Rovshan
pointed out that the *entire point* of the transfer is to correct the choke
model's routing sensitivity, so exponent movement is expected and desired —
the check would have flagged success as failure. Use instead:

1. **Time-forward MAPE on the 85 real tests must not degrade** when the
   transferred rows are added, versus the same model without them.
2. **On held-out tests, the refit model's implied test-vs-normal uplift must
   land near 2.5%** — leave-one-out on the transfer itself, so not circular.
3. Report exponents before and after as *information only*, not a gate.
4. **Weight transferred rows by 1/σ²**, σ from the spread between the IPR and
   thermal-ratio estimates plus a floor. GL-06 and GL-03 need the widest σ.

Never validate on transferred labels; time-forward stays on the 85 real tests.

Three options, in order of preference:

1. **De-bias explicitly.** Keep the choke model, add a routing term:
   fit the offset between test-window and normal-production `whp_downstream`
   per well (it is 19–29 psi, well-specific), and apply it when predicting.
   Best accuracy if the ground truth is normal-production.
2. **Refit on routing-invariant sensors only** (`whp`, `dh_pressure`,
   `annulus`, `gas_lift`, `dh_temperature` — all ≤0.20σ). Loses the strongest
   feature, so expect LOO to worsen, but the daily number is honest.
3. **Ship both**, pick on whatever the organisers answer in task 0.

**Write the decision into `PROJECT_STATE.md` → Decisions and constraints.**
Both workstreams must assume the same thing.

Done when: a short note in `PROJECT_STATE.md` naming the choice and the
measured size of the correction, plus whichever script implements it.

## 2–3. VFM model and daily Excel — **done**

`ml/src/vfm.py`, fitted by `python ml/fit_vfm.py`. Time-forward: oil **2.56%**,
water **3.82%**, gas **5.65%**.

- `ml/models/vfm.pkl` (+ `.joblib`) — the fitted model. `fit_vfm.py` runs the time-forward
  check *before* persisting and refuses to save above 4% oil MAPE, so the file
  is never an unscored model.
- `ml/outputs/vfm_daily_predictions.xlsx` — 2,729 well-days, with `data_coverage`
  and `low_coverage_flag` columns; the 14 thin days are flagged, not dropped.
  GL-06 has no 24 Jun row at all (36 h outage) — absent rather than zero, since
  zero would read as "shut in".
- The Excel is generated by *reloading* the saved model, so the artefact that
  ships is the one that was exercised. The UI must load it the same way and
  never retrain.
- 5 well-days have the choke shut for the full 24 h and are a hard zero, not a
  model output (`ln S` is undefined at S=0).

Still open from this block: whether to apply the routing correction (task 1).
The model does **not** apply one — `routing_factor` defaults to 1.0.

## 4. PTA — Horner on the six build-ups

Only `GL-01, GL-02, GL-04, GL-06, GL-08, GL-10` have a shut-in. `GL-03, GL-05,
GL-07, GL-09` have none, so the UI must say "no build-up available" rather than
render an empty chart.

Order of work:

1. **Correct gauge pressure to datum first** — the gauge is 150–420 ft shallower
   than datum on every well. Skipping this biases k and skin.
   `features.static_table()` carries `datum_minus_gauge_ft`.
2. Horner plot: `p_ws` vs `log((tp + Δt)/Δt)`, with `tp` from the producing
   period before shut-in and `q` the predicted daily oil rate.
3. Fit the semi-log straight line → slope `m` → `k = 162.6·q·B·μ / (m·h)`,
   then skin and `ΔP_skin`. PVT supplies `B`, `μ`, `h`, `φ`, `ct`, `rw`.
4. Also produce the log-log diagnostic (Δp and derivative) — the brief asks for
   "all relevant plots", and the derivative is what shows whether radial flow
   actually developed.
5. **GL-02 (5.7 h) and GL-06 (8.0 h) are short.** Radial flow may never develop;
   if the derivative does not flatten, report the slope as uncertain rather
   than fitting a line through wellbore storage.

Done when: an Excel of `Horner slope, k (md), skin, ΔP_skin (psi)` per event,
plus the plots saved under `ml/outputs/figures/pta/`.

## 7–9. Deliverables-PDF gaps — **done**

- **`.pkl` export.** `fit_vfm.py` writes `ml/models/vfm.pkl` (the required
  format) and `vfm.joblib` together from the same object, so they cannot
  drift. Verified identical predictions from both.
- **Notebook.** `notebooks/VFM_Phase1.ipynb`, 29 cells, all executed with
  outputs, no errors. Generated and run by `ml/build_notebook.py` so the
  committed outputs can never drift from the code — regenerate rather than
  editing cells by hand.
- **Unseen-well fallback.** `VFMModel.predict` now pools the intercept, sets
  an `unseen_well` flag and warns, instead of raising. `strict=True` restores
  the raise for batch pipelines.

Still untested: **the chain running from raw CSVs end to end.** Everything so
far starts from `data/processed/`, which will not exist for the organisers'
test data. Exercise that path before the demo.

## 5. Streamlit UI

Only 10 points, but it is the deliverable the judges actually touch, and 6 of
those 10 are for *workflow* rather than looks. Build the path end to end before
polishing any single screen.

Upload → visualise → predict (VFM) → PTA plots → export. Load the persisted
model; never train in the app. Reuse `ml/src/viz.py` so the figures match the
report.

## 6. Presentation

The strongest material is the data-quality story, because it is specific and
checkable: the `-999.25` sentinel hiding behind zero nulls, GL-06's m³/d gas
columns, the five sign flips, the field-wide 9 Aug outage, and the test-mode
routing skew. Pair it with the choke exponents coming out at the textbook
values — that shows the model found physics rather than fitting noise.

Be honest about the limits: unseen-well generalisation fails, and 85 labels is
the binding constraint. Saying so is worth more than pretending otherwise.

---

## Tried and rejected — do not redo these

- **Sub-daily integration on all days** (6 h, 3 h and 1 h bins, after the
  NaN-denominator bug was fixed). The reasoning was sound — a daily rate is
  the time-average of the instantaneous rate, so predicting once on the day's
  mean sensors is `f(mean)` where integrating blocks gives `mean(f)`, and 6 h
  bins sit inside the 12–24 h band the model was calibrated on, unlike the
  10-minute bins tried earlier.

  Measured, it changes almost nothing: field oil moves **−0.043%**, the median
  well-day moves **0.013%**, p95 is 0.05%. At roughly 0.02 points per 1% of
  level, that is ~0.001 points — three orders below what the board resolves.

  The reason is physical: these wells run at steady state. Within-day
  `dp_choke` variation has a median CV of 3.8%, so `f(mean)` and `mean(f)`
  barely diverge. It is the same finding as the per-minute dynamics features
  carrying no rate signal.

  **6 h bins are also actively worse on the partial shut-in days** — a block
  straddling the shut-in boundary gets classified wholly in or out, moving
  GL-08 19 Aug by −32.7% and GL-01 15 Apr by −25.3%. 3 h and 1 h resolve the
  edge better (6.6% and 4.4% worst case), but none of them beats the 10-minute
  treatment those days already get. Keep the current split: 10-minute
  integration where the choke closes, daily means everywhere else.

- **Label transfer** (`ml/src/label_transfer.py`, built and measured, not
  shipped). It achieves its stated goal — transferred rows sit at
  `whp_downstream` 168.8–204.7 against the 158.0–205.3 we predict on, versus
  149.3–181.6 for the raw labels — and still fails gate 1. Adding them
  time-forward: oil WAPE 2.30 → 4.55, water 3.25 → 4.16, gas 4.52 → 6.74.
  Letting the water-cut split use `whp_downstream`, the whole point, recovers
  4.55 → 4.49.

  Probable cause is a conflict, not a bug: the choke law already responds to
  the test-to-normal change through `dPc^0.47` by ~5.9%, while the
  transferred rows assert 2.8%. One set of exponents cannot serve both
  regimes, so the fit splits the difference and both get worse. Applied as a
  post-hoc scale the same 2.8% leaves the exponents alone and is worth +0.735
  points — which is the form we ship.

  Two things to try before writing it off: **1/σ² weighting**, which
  `VFMModel.fit` does not support (170 transferred rows currently outvote 85
  real ones, and pre/post windows of one test are near-duplicates); and
  refitting **only the dPc exponent** on transferred rows with the rest held
  fixed, so the transfer corrects the one coefficient it is informative about.

  Also found on the way: the thermal route's reference is the **static gauge
  temperature**, not reservoir temperature. The gauge sits 150–420 ft above
  datum in cooler rock, and on GL-01, GL-06, GL-07 and GL-10 the flowing
  gauge reads within 1 °F of T_res, so a T_res ratio silently discards those
  four wells. Measured from the six shut-ins, the geothermal gradient is
  1.17–1.45 °F/100 ft, matching Rovshan's independent 1.1–1.44. Under the
  correct reference the thermal and IPR routes agree much less well
  (corr 0.86 → 0.41), and neither reproduces the 2.5% the leaderboard proved
  — which is why the shipped magnitude comes from `ROUTING_FACTORS` rather
  than from the physics.

- **Critical choke flow as the reason the choke law overstates the routing
  effect.** Rejected. `python ml/eda/routing_checks.py` reproduces it: one
  pooled fit with only the dPc term split at a pressure ratio of 0.60 gives
  an exponent of **0.475** above and **0.478** below, with zero mean residual
  either side. Critical flow would collapse the low-ratio exponent toward 0;
  34 of 85 tests sit below 0.55 and it does not budge.

  Use this argument, not a correlation. A correlation across well averages
  (−0.16) cannot detect a threshold effect and is easy for a reviewer to
  dismiss. The same script also measures post-test recovery — 96.3% at +1 h,
  97.5% at +6 h — which is what establishes that the windows either side of a
  test are normal-regime and the label transfer is sound.

- **Replacing the static `Rs` in the gas split with the well's own GOR
  history.** The diagnosis was right — static `Rs` sits ~2.1% above each
  well's actual producing GOR, which is where the +2.31% gas bias comes from —
  but the fix is a net loss. Every history-based estimator costs more variance
  than the bias it removes, because measured GOR is noisy test to test and
  3–8 past points cannot track it. Time-forward gas MAPE:

  | GOR estimator | MAPE | bias |
  |---|--:|--:|
  | **static Rs (shipped)** | **5.90%** | +2.31% |
  | mean of past tests | 6.11% | +1.62% |
  | mean of last 3 tests | 6.66% | +1.18% |
  | half mean + half trend | 7.01% | +0.93% |
  | trend clipped to ±10% | 7.96% | +0.71% |
  | last test only | 8.67% | +1.20% |
  | linear trend from history | 8.84% | +0.25% |

  Note the pattern: every estimator that reduces the bias increases the error.
  Shrinking a per-well calibration toward `Rs` (λ=0.25) reaches 5.78%, but
  that λ was tuned on the same 55 points it is scored on, so the 0.12 pp is
  not real. Keep the static `Rs` and the bias with it. The oil error (3.07%)
  is the floor gas inherits regardless.

- **ML residual correction on top of the physics model.** Fitted Ridge and a
  regularised HistGradientBoosting to the choke model's log-residuals, using
  30 extra features (per-well z-scores, slopes, within-window std), scored
  time-forward. Result: 2.04% → 2.04% (ridge) and 2.01% (GBM). Noise. The
  physics form has already taken the available signal; there is no structure
  left in the residuals at n=85.
- **Pure ML on raw features.** Time-forward on oil: Ridge-58 scores 5.11%
  against 2.67% for the best physics variant. A well-cluster bootstrap (5000
  resamples) puts the gap at **+2.17 pp [+1.07, +3.42]** — the physics lead is
  real, not noise. Worse for ML: **Ridge-58 is statistically indistinguishable
  from persistence** (just copying the well's previous test): +0.89 pp
  [−1.54, +3.34]. And as a well accumulates history the physics models improve
  (choke 3.97 → 2.73%) while Ridge degrades (4.00 → 6.18%).
  Keep all of this in the benchmark as evidence for the methodology score —
  showing the comparison is worth more than quietly picking the winner.
- **Sub-window augmentation** (splitting each test window into quarters to get
  340 rows). Sub-windows differ by 0.08–2.1%, so they are near-duplicates: no
  new information, and a leakage trap if they land in different CV folds.
- **Per-minute dynamics features** (slugging, FFT band power, direction
  reversals, roughness). Within-well correlation with oil rate: −0.07 to
  +0.26. The wells run at steady state; minute-level variation is instrument
  noise, not flow physics.

## Known traps, so nobody rediscovers them

- Random/LOO CV scores ~3–4% for anything and means nothing. Time-forward only.
- 136 features against 85 rows. Strong regularisation; a deep GBM will overfit.
- Unseen-well CV is 69.7% MAPE — worse than predicting the global mean.
- `data/processed/` is gitignored; a fresh clone must run the cleaning step.
- `git lfs install` before cloning, or `high_freq_data.csv` is a 130-byte stub.
- Root `CLAUDE.md` is a loader that imports the `agent/` docs. Claude Code only
  auto-reads a root `CLAUDE.md`, so deleting it silently stops the agent docs
  from loading. Edit the files in `agent/`, never the loader.
