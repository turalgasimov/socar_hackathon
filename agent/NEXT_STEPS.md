# Next steps

Last updated: 2026-11-21. Ordered by points at risk, not by difficulty.

Points still unclaimed: **VFM accuracy 30** · **PTA parameters 20** · **PTA
plots 10** · **UI 10** · **Presentation 10** · **VFM methodology 20** (partly
earned — the cleaning and validation work is the evidence for it).

Claim a task by putting your name in the Owner column and committing that
change before you start.

| # | Task | Owner | Blocks | Est. |
|---|---|---|---|---|
| 0 | Ask organisers: is daily ground truth test-routed or normal production? | — | 1 | 5 min |
| 1 | Settle the test-mode correction | — | 2, 3 | 1–2 h |
| 2 | Fit + persist the VFM model | — | 3, 5 | 2–3 h |
| 3 | Excel: daily rate predictions | — | 4 | 1 h |
| 4 | PTA: Horner on 6 build-ups | — | 5 | 3–4 h |
| 5 | Streamlit UI | — | — | 4–6 h |
| 6 | Presentation | — | — | 2 h |

---

## 0. Ask the organisers (do this first, it is free)

**Is the daily ground truth measured under test-separator routing or normal
production?** The answer decides task 1 and could be worth several points of
accuracy. Everything below assumes we do not get an answer and have to hedge

## 1. Settle the test-mode correction — **blocks everything**

The choke model scores 2.04% MAPE time-forward on liquid (3.07% oil), but that
is measured under test-separator routing. On normal production days `dPc` is
119.2 psi against 129.6 during tests, and through `dPc^0.47` that is a
systematic **−3.8%** on every daily prediction — comparable to the model's own
error, and systematic rather than random, so it does not average out across
2,729 well-days.

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

## 2. Fit and persist the VFM model

Start from what already wins: **choke physics + per-well IPR**, phase split via
the water-cut trend (`benchmark_vfm.py` already has all three).

- Score **time-forward**, not LOO — `ml/eda/timeforward_vfm.py` already does
  this for the choke model (liquid 2.04%, oil 3.07%, water 3.99%, gas 5.90%).
  Those are the numbers to beat and to quote.
- **Gas has a +2.31% bias** from the `gas = oil × Rs` split, while oil and
  water are unbiased. If gas is scored equally, a better gas path than
  multiplying by solution GOR is the cheapest accuracy left on the table.
- Fit on all 85 tests once the scheme is settled, then **persist the fitted
  object** (`ml/models/vfm.joblib`) so the UI loads it instead of refitting.
- Write a thin `predict(features_df) -> DataFrame` wrapper — the UI and the
  Excel export should share one code path, not two.
- Keep the physics exponents in the saved artefact; they are presentation
  material (`S^2.05`, `dPc^0.47` reproducing the subcritical choke law).

Done when: `ml/models/vfm.joblib` exists, a time-forward score is recorded in
`PROJECT_STATE.md`, and `predict()` runs on `daily_table.parquet`.

## 3. Excel: daily predictions

Columns exactly as the brief asks: `date`, `well_name`, `oil_rate_stbd`,
`water_rate_stbd`, `gas_rate_mscfd`. 2,729 well-days.

- **Flag the 14 low-coverage well-days, do not silently drop them.** Add a
  `coverage` or `flag` column — judges will look for how missing data was
  handled, and this is cheap methodology credit.
- GL-06 has no 24 Jun at all (36 h outage). Decide: omit the row, or emit it
  with a null and a flag. Omitting silently is the one wrong answer.
- Sanity-check the output before shipping: per-well mean predicted oil against
  per-well mean tested oil. A >10% gap means the correction from task 1 is
  wrong.

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

## Known traps, so nobody rediscovers them

- Random/LOO CV scores ~3–4% for anything and means nothing. Time-forward only.
- 136 features against 85 rows. Strong regularisation; a deep GBM will overfit.
- Unseen-well CV is 69.7% MAPE — worse than predicting the global mean.
- `data/processed/` is gitignored; a fresh clone must run the cleaning step.
- `git lfs install` before cloning, or `high_freq_data.csv` is a 130-byte stub.
- Root `CLAUDE.md` is a loader that imports the `agent/` docs. Claude Code only
  auto-reads a root `CLAUDE.md`, so deleting it silently stops the agent docs
  from loading. Edit the files in `agent/`, never the loader.
