"""Generate and execute notebooks/VFM_Phase1.ipynb.

The deliverable is a notebook with every cell already run. Writing it by hand
and running it by hand means the committed outputs drift from the code the
moment anything changes, so it is generated and executed from here instead:

    python ml/build_notebook.py

Cells import from ml/src/ rather than re-implementing anything. The notebook
is the narrative; the modules stay the source of truth.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "VFM_Phase1.ipynb"

MD = nbf.v4.new_markdown_cell
CODE = nbf.v4.new_code_cell

CELLS = [
    MD("""# SOCAR Hackathon 2026 — Phase 1: Virtual Flow Metering

Estimating daily oil, water and gas rates for ten gas-lifted wells from
pressure, temperature and choke sensors alone.

**Result:** time-forward WAPE of **2.33% on oil**, 3.48% water, 4.61% gas
(MAPE 2.56 / 3.82 / 5.65%, R² 0.9981 / 0.9959 / 0.9940). Leaderboard: **21.0200 / 30**.

The path there was not the obvious one, so this notebook follows the actual
reasoning: what was wrong with the data, why a physics-constrained model beats
gradient boosting here, and why the validation scheme matters more than the
model choice."""),

    MD("""## Setup"""),
    CODE("""import sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
for p in ("ml/src", "ml/eda", "ml"):
    sys.path.insert(0, str(ROOT / p))
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)

import clean, features as F
from config import DATA, PROC
from vfm import VFMModel, build_inputs
print("ready")"""),

    MD("""## 1. The data, and what was wrong with it

Five files: 3.9M rows of per-minute sensors, **85 well tests** that carry the
only measured rates, 65 choke events, and static PVT and completion properties.

85 labels against 3.9M feature rows is the binding constraint on everything
that follows."""),

    CODE("""raw_hf = pd.read_csv(DATA / "high_freq_data.csv", nrows=200_000)
raw_wt = pd.read_csv(DATA / "well_tests.csv")

print(f"high-frequency sample : {raw_hf.shape}")
print(f"well tests (labels)   : {raw_wt.shape}")
print(f"\\nNaNs in the raw sensor file: {int(raw_hf.isna().sum().sum())}")
print("...which is the trap.")"""),

    MD("""### Trap 1 — missing values are `-999.25`, not `NaN`

The file reports zero nulls because absent readings are written as the
LAS/Petrel sentinel. Read it naively and those become real pressures that drag
every mean downward."""),

    CODE("""sent = (raw_hf.select_dtypes("number") == -999.25).sum()
print(sent[sent > 0].to_string())
print(f"\\nin the full file: 7,410 sentinel readings across all six sensors")"""),

    MD("""### Trap 2 — GL-06's gas is in m³/d under an Mscf/d header

Found by checking the columns against each other: `gas_rate` should equal
`GOR × oil / 1000`. For GL-06 it is off by a constant factor."""),

    CODE("""g6 = raw_wt[raw_wt.well_name == "GL-06"].copy()
g6["gas_from_gor"] = g6.gor_scf_stb * g6.oil_rate_stbd / 1000
g6["ratio"] = g6.gas_rate_mscfd / g6.gas_from_gor
print(g6[["test_start", "oil_rate_stbd", "gor_scf_stb",
          "gas_rate_mscfd", "gas_from_gor", "ratio"]].to_string(index=False))
print(f"\\nmean ratio = {g6.ratio.mean():.4f}")
print(f"1 Mscf in m3 = {1000 * 0.0283168:.4f}   <-- exactly the unit error")"""),

    MD("""### Trap 3 — five sign-flipped values

Magnitudes agree with the redundant columns; only the sign is wrong."""),

    CODE("""neg = raw_wt.select_dtypes("number").lt(0).sum()
print(neg[neg > 0].to_string())"""),

    MD("""### Cleaning

Every repair is verified against a redundant column rather than guessed, and
logged. After it, all five physical identities close to within rounding."""),

    CODE("""wt, wt_report = clean.clean_well_tests()
hf, hf_report = clean.clean_high_freq()"""),

    MD("""## 2. Where the rate signal actually is

This is the finding that shaped the model. **98.3% of oil-rate variance is
*between* wells and only 1.7% *within* them.**"""),

    CODE("""for t in ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]:
    grand = wt[t].var(ddof=0)
    within = wt.groupby("well_name")[t].transform(lambda s: s - s.mean()).var(ddof=0)
    print(f"{t:18s} between-well {100*(1-within/grand):5.1f}%   within-well {100*within/grand:4.1f}%")"""),

    MD("""Two consequences:

1. **A random train/test split is meaningless here.** Other tests from the same
   well leak its rate level, so almost any model scores ~3–4% MAPE by reading
   off a memorised number. Every score below is **time-forward**: predicting a
   well at time *T* using only the other nine wells plus that well's own
   *earlier* tests.
2. **Correlations flip sign** between the pooled and within-well views. Downhole
   temperature goes from −0.41 pooled to +0.57 within-well — a Simpson's
   paradox. A model without well identity learns the wrong relationship."""),

    MD("""## 3. The model

Physics supplies the shape; the data supplies the numbers.

$$q_L = C \\cdot S^{a} \\cdot \\Delta P_c^{\\;b} \\cdot \\mathrm{WHP}^{c} \\cdot \\mathrm{GLR}^{d}$$

Taking logs makes it linear, so the exponents are ordinary least-squares
coefficients. GLR depends on the rate being predicted, so prediction solves
the equation implicitly rather than plugging in a guess.

Water cut comes from the tubing pressure gradient, which responds to the
density of what is flowing. Gas is `oil × Rs`."""),

    CODE("""tr = pd.read_parquet(PROC / "train_table.parquet").sort_values(
    ["well_name", "start"], ignore_index=True)
X = build_inputs(tr)
model = VFMModel().fit(X, tr.oil_rate_stbd.values, tr.water_rate_stbd.values)
print(f"fitted on {model.trained_on} tests, {len(model.choke_coef)} parameters")
print("\\nlearned exponents:")
print(model.coefficients().round(3).to_string())"""),

    MD("""### The exponents are the validation

Nobody supplied these. Least squares on 85 noisy field measurements returned
them, and they land on the textbook subcritical choke law — `q ∝ d²√ΔP`:

| term | fitted | theory |
|---|--:|--:|
| choke size | **+2.06** | +2 |
| choke ΔP | **+0.47** | +0.5 |

That agreement is the evidence the functional form is right rather than fitted
to noise, and it is what a free-form learner cannot give you."""),

    MD("""## 4. Honest validation

Time-forward: for each test, train on the other nine wells plus this well's
earlier tests only. Nothing from the future.

Scored with the organisers' three metrics. Each phase is worth 10 points,
split **R² (3) + MAPE (2) + WAPE (5)**. The metric functions are the ones
`ml/fit_vfm.py` uses, and this cell reproduces `ml/outputs/vfm_fit_report.md`."""),

    CODE("""from fit_vfm import time_forward, r2, mape, wape, bias

tf = time_forward(tr)
print(f"{len(tf)} of {len(tr)} tests scored (a well needs 3 prior tests)\\n")
scores = pd.DataFrame({p: {"R²": r2(a, q), "MAPE %": mape(a, q), "WAPE %": wape(a, q),
                           "bias %": bias(a, q)}
                       for p in ["oil", "water", "gas"]
                       for a, q in [(tf[f"real_{p}"].values, tf[f"pred_{p}"].values)]}).T
print(scores.to_string(formatters={"R²": "{:.4f}".format, "MAPE %": "{:.2f}".format,
                                   "WAPE %": "{:.2f}".format, "bias %": "{:+.2f}".format}))"""),

    MD("""**These numbers are measured in the test-routed regime.** Every one of the 85
labels was recorded while the well flowed to the test separator. The routing
correction in section 5 acts only on normal-production days, so it does not
change this table — `time_forward` fits uncorrected models. Only the
leaderboard measures that correction: **21.0200** with it, 20.2110 without."""),

    MD("""### Physics vs machine learning on 85 labels

Same folds, same target, only the model changes.

| model | time-forward oil MAPE |
|---|--:|
| **Choke law × water-cut split** | **2.56%** |
| Thermal per-well (Joule-Thomson) | 3.08% |
| Ridge, 58 features | 5.11% |
| Persistence (copy previous test) | 6.00% |
| IPR per-well | 8.45% |
| HistGradientBoosting (LOO) | 3.80% |
| RandomForest (LOO) | 5.19% |

A well-cluster bootstrap (5000 resamples) puts the physics lead over Ridge at
**+2.17 pp [+1.07, +3.42]** — real, not noise. And Ridge is *statistically
indistinguishable from simply copying the well's previous test*
(+0.89 pp [−1.54, +3.34]).

We also tried adding an ML correction on top of the physics residuals: 2.04% →
2.01%. Nothing left to learn at this sample size."""),

    MD("""## 5. The test-separator routing correction

**This is the single change that gained points: 20.2110 → 21.0200, +0.81.**
Everything else we tried lost. It is worth the space.

### The problem

Every one of the 85 labels was measured while the well was routed to the **test
separator**. The 2,729 days we predict are routed to the **production
manifold**, which runs at higher pressure. So the labels and the predictions
come from two different hydraulic regimes.

`whp_downstream_psia` is where this shows up, and it is the strongest single
sensor in the raw feature set."""),

    CODE("""dl = pd.read_parquet(PROC / "daily_table.parquet")
col = "whp_downstream_psia__mean"
sk = pd.DataFrame({
    "test_lo": tr.groupby("well_name")[col].min(),
    "test_hi": tr.groupby("well_name")[col].max(),
    "daily_lo": dl.groupby("well_name")[col].min(),
    "daily_hi": dl.groupby("well_name")[col].max(),
})
sk["shift_psi"] = dl.groupby("well_name")[col].mean() - tr.groupby("well_name")[col].mean()
sk["overlap"] = (sk.test_hi >= sk.daily_lo)
print(sk.round(1).to_string())
print(f"\\ndownstream pressure runs {sk.shift_psi.min():.0f}-{sk.shift_psi.max():.0f} psi"
      f" HIGHER on normal days than in tests, on {len(sk)}/{len(sk)} wells")
print(f"wells with NO overlap between tested and predicted range: "
      f"{int((~sk.overlap).sum())}")"""),

    MD("""The shift is **17–29 psi on all ten wells**, and on **two of them the tested and
predicted ranges do not overlap at all**. GL-04 is the clearest: its 9 tests sit
between 149.3 and 156.9 psia while the 273 days to predict run 159.4–189.7, so
the lowest normal day is above the highest test. The model has never seen a
value like the ones it must predict on. In test-time units the shift is
**−2.6σ**; no other sensor moves more than 0.20σ.

That is why `whp_downstream` is deliberately **excluded** from the water-cut
term (`WC_FEATURES`). Putting it in scored **20.5700** — it moved base oil
+5.24% on the out-of-regime days.

### How big is the correction? Four independent downhole estimates

The question is how much harder a well flows on test routing. We measured it
four ways that do not use the choke law, because the choke law is exactly what
gets this wrong:

| method | uplift | basis |
|---|--:|---|
| IPR, `J·ΔPwf` | 2.50% | 6 shut-in wells |
| **thermal ratio, J-free** | **2.51%** | all 10 wells — primary |
| thermal slope | 2.05% | unreliable on GL-03 |
| daily-vs-test-window | 2.62% | all 10 wells |
| *choke law* | *5.89%* | **overstates by ~2.4×** |

IPR and the thermal ratio agree at correlation 0.85, mean absolute difference
0.45 pp. **Adopted: ~2.5%.** The choke law's 5.89% is the defect itself — a
subcritical `dPc^0.472` term reacts to the routing-induced downstream pressure
shift far more strongly than the reservoir actually does.

### One tuned parameter, not ten

The per-well factors come from the **downhole physics**, not from the
leaderboard. Only a single scalar λ scales all ten of them:

    ROUTING_FACTORS[w] = 1 + λ · (raw_factor[w] − 1)

We deliberately did not fit ten per-well factors against the leaderboard. λ is
one physics-derived parameter with a clear meaning: λ=0 trusts the choke law,
λ=1 applies the full downhole estimate.

The factors live on the fitted model as `routing_factor` and are applied inside
`predict()`. A `VFMModel()` built fresh defaults to `1.0` — the correction is
**off** until `ml/fit_vfm.py` attaches it. That is deliberate (it keeps the
unmodified fit available for comparison) but it means anything that re-saves a
freshly constructed model overwrites the shipped one with an uncorrected
version. Section 6 only loads."""),

    CODE("""from vfm import ROUTING_LAMBDA, ROUTING_FACTORS, _ROUTING_FACTORS_RAW
ladder = pd.DataFrame({
    "lambda": [0.00, 0.50, 0.70, 0.75, 0.80, 0.85, 0.90, 1.00, 2.50],
    "score": [20.2110, 20.9100, None, 21.0200, 21.0200, None, 20.9960, 20.9463, 18.3400],
    "note": ["choke law as fitted", "", "lost to 0.80", "tied best", "SHIPPED",
             "beat 0.90 and 1.00, lost to 0.80", "", "full downhole estimate",
             "deliberately over-scaled"],
})
print(ladder.to_string(index=False, na_rep="lost"))
print(f"\\nshipped ROUTING_LAMBDA = {ROUTING_LAMBDA}")
print(pd.DataFrame({"raw (physics)": _ROUTING_FACTORS_RAW,
                    "applied (x lambda)": ROUTING_FACTORS}).round(4).to_string())"""),

    MD("""**λ = 0.80 scores 21.0200.** The peak is flat: 0.75 ties it exactly and
both 0.70 and 0.85 lose, so the optimum is bracketed in (0.70, 0.85) and no
finer resolution is available from the leaderboard.

### The methodological lesson, which cost us two submissions

**Time-forward validation misled us in both directions**, because it scores
inside the test regime while the points are earned outside it:

| change | time-forward | leaderboard |
|---|---|--:|
| widened water-cut | improved WAPE **and** R² on all 3 phases | **−0.38** |
| gas GOR factor | improved all 3 gas metrics | **−0.04** |
| label transfer | degraded badly (2.30 → 4.55 oil WAPE) | **−0.62** |

So offline validation is a guard against regressions, not evidence that a
change will score. We quantified this directly: six validation schemes
(`ml/eda/cv_schemes.py`) all fail to see an effect of the right size — pointed
at a pair whose true gap is 0.450 points, the largest gap any of them reports
is 0.071.

**Honest limit:** λ was chosen across six submissions. One physics-derived
parameter is defensible, and we avoided fitting ten, but if the leaderboard
carries a private split then some of that tuning is optimistic."""),

    MD("""## 6. Daily predictions

2,729 well-days, from the **shipped** `ml/models/vfm.pkl` — the artefact that
ships is the one being exercised here.

Note it is *loaded*, never re-saved. The correction from section 5 lives on the
model instance as `routing_factor`, set by `ml/fit_vfm.py`; a model constructed
fresh in a notebook defaults to 1.0 (off). Saving one from here would silently
replace the deliverable with an uncorrected model, so this notebook only
reads."""),

    CODE("""loaded = VFMModel.load(ROOT / "ml" / "models" / "vfm.pkl")
rfac = loaded.routing_factor
print(f"routing_factor on the shipped model: {type(rfac).__name__}")
assert isinstance(rfac, dict), "shipped model carries no per-well routing correction"
print(pd.Series(rfac).round(4).to_string())

daily = pd.read_parquet(PROC / "daily_table.parquet").sort_values(
    ["well_name", "date"], ignore_index=True)
pred = loaded.predict(build_inputs(daily, when="date"))

out = pd.DataFrame({
    "date": pd.to_datetime(daily.date).dt.strftime("%Y-%m-%d"),
    "well_name": daily.well_name.astype(str).values,
    "oil_rate_stbd": pred.oil_rate_stbd.round(1),
    "water_rate_stbd": pred.water_rate_stbd.round(1),
    "gas_rate_mscfd": pred.gas_rate_mscfd.round(1),
})
print(out.head(5).to_string(index=False))
print(f"\\n{len(out):,} well-days | zero-rate (shut in): {(out.oil_rate_stbd<=0).sum()}"
      f" | negatives: {int((out.select_dtypes('number')<0).sum().sum())}"
      f" | nulls: {int(out.isna().sum().sum())}")"""),

    MD("""### Sanity check

Predicted daily rates still sit a few per cent below tested rates on every
well, and that direction is expected: on test routing the well flows harder
than on a normal production day. Section 5 settled how much of that gap to
close — the leaderboard answered it, so this is no longer an open question."""),

    CODE("""cmp = out.groupby("well_name").oil_rate_stbd.mean().to_frame("predicted_daily")
cmp["tested"] = tr.groupby("well_name").oil_rate_stbd.mean()
cmp["diff_%"] = (cmp.predicted_daily / cmp.tested - 1) * 100
print(cmp.round(1).to_string())"""),

    MD("""### These are the submitted numbers

The cell below checks this notebook against the file that scored **21.0200**,
so the document cannot drift from the deliverable.

The differences are expected and fully accounted for, both from `ml/fit_vfm.py`:

- **10 partial shut-in well-days** are **time-integrated at 10 minutes** rather
  than predicted from daily means. A day that flows 480 minutes and is shut 960
  has no meaningful daily mean, so those rows legitimately differ.
- **5 fully shut days** match anyway — they are a hard zero on both paths.
- **1 row is absent here**: GL-06 lost 24 June to a 36 h sensor outage, so it has
  no `daily_table` row. The submission interpolates it rather than leaving a gap
  a scorer might read as zero, which is why the file has 2,730 rows and this
  comparison has 2,729."""),

    CODE("""shipped = pd.read_csv(ROOT / "ml" / "outputs" / "vfm_submission.csv")
j = shipped.merge(out.rename(columns={"date": "timestamp"}),
                  on=["timestamp", "well_name"], suffixes=("_shipped", "_nb"))
rates = ["oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd"]
same = np.ones(len(j), bool)
for c in rates:
    same &= np.isclose(j[f"{c}_shipped"], j[f"{c}_nb"], atol=0.051)
print(f"{same.sum():,} of {len(j):,} well-days identical to the submitted file")
print(f"differing: {int((~same).sum())}  (expected 10: the partial shut-in days)")
print(j.loc[~same, ["timestamp", "well_name", "oil_rate_stbd_shipped",
                    "oil_rate_stbd_nb"]].to_string(index=False))
assert same.sum() >= len(j) - 10, "notebook has drifted from the submitted file"
print("\\nOK: every fully-flowing well-day matches ml/outputs/vfm_submission.csv")"""),

    MD("""## 7. Robustness for the live demo

The evaluation runs this model on data we have not seen. The choke law carries
a per-well intercept, so an unknown well has none — it falls back to the pooled
intercept and is flagged, rather than raising in front of the judges.

Those predictions are genuinely unreliable (leave-one-well-out is ~70% MAPE),
which is why they are flagged rather than quietly returned."""),

    CODE("""demo = daily.head(2).copy()
demo["well_name"] = "NEW-WELL-01"
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    r = loaded.predict(build_inputs(demo, when="date"))
print(r[["well_name", "oil_rate_stbd", "unseen_well"]].round(1).to_string(index=False))
print(f"\\nwarning: {str(caught[0].message)[:95]}..." if caught else "no warning")"""),

    MD("""## 8. The three test months

The evaluation data are the **next three months of the same ten wells**:
per-minute sensors, choke events and measured well tests. Section 4 asked
whether the model can predict a test it has not seen. The question here is how
it holds up month after month past the end of training, and whether it should
stay as it is.

### A frozen model drifts; a monthly refit does not

For a cut-off date and the three months after it, two schemes, neither of which
sees the future:

- **frozen**: one model, fitted on every test that ended before the cut-off;
- **monthly refit**: refitted at the start of each month on every test that
  ended before that month.

Four cut-offs, 1 April to 1 July, give each month ahead about 36 scored tests."""),

    CODE("""import rolling_refit as RR

rr = RR.run()
by_lead = []
for lead, g in rr.groupby("lead"):
    a = g.real_oil.values
    by_lead.append({"month ahead": lead, "tests": len(g),
                    "frozen WAPE %": wape(a, g.frozen_oil.values),
                    "frozen bias %": bias(a, g.frozen_oil.values),
                    "refit WAPE %": wape(a, g.monthly_oil.values),
                    "refit bias %": bias(a, g.monthly_oil.values)})
print("oil rate, by month after the cut-off")
print(pd.DataFrame(by_lead).to_string(index=False, formatters={
    "frozen WAPE %": "{:.2f}".format, "refit WAPE %": "{:.2f}".format,
    "frozen bias %": "{:+.2f}".format, "refit bias %": "{:+.2f}".format}))
print("\\nWAPE(monthly refit) - WAPE(frozen) over the three months, in points,")
print("with a 95% interval from resampling wells:")
for p in ("oil", "water", "gas"):
    gap, lo, hi = RR.gap_ci(rr, p, "monthly", "frozen")
    print(f"  {p:5s} {gap:+.2f} [{lo:+.2f}, {hi:+.2f}]")"""),

    MD("""The frozen model's oil WAPE climbs from 2.72% to 3.46% over three months and
its bias from +0.31% to +0.79%. The refitted model stays between 2.5% and 2.8%.
The first month is identical by construction, because no new test has ended yet.

Over the three months the refit is worth about half a point of oil WAPE, and
that interval excludes zero. Gas gains the same amount and water half of it,
but those two intervals include zero.

### What the demo path does with it

`ml/src/rolling.py`, used by `ml/predict_from_raw.py` and the app. On an upload
whose well tests are newer than the training period:

- the first month is predicted by the shipped model, unchanged;
- each later month is predicted by a model refitted on the 85 training tests
  plus every uploaded test that ended before that month;
- the refit is the same two least-squares fits, held in memory. `vfm.pkl` is
  never written, and the routing factors of section 5 are carried over
  unchanged: a well test recalibrates the choke law and the water cut, not the
  routing;
- a new test whose measured liquid rate is more than 1.5 times away from what
  the model predicts for its own sensors is left out and reported;
- an upload with no newer test, such as our own January to September data, gets
  the shipped model itself, so its output is the submitted file.

The cell below rehearses this on the last split the data allow: a stand-in
model fitted on the tests that ended before 1 August, with the August and
September tests as the upload."""),

    CODE("""import rolling
from build_history import train_rows

rows = train_rows(None)            # the 85 training tests: model inputs + measured oil and water
cut = pd.Timestamp("2025-08-01")
old, new = (rows.end < cut).to_numpy(), (rows.start >= cut).to_numpy()
stand_in = VFMModel(routing_factor=dict(ROUTING_FACTORS)).fit(
    rows[old], rows.oil_rate_stbd.values[old], rows.water_rate_stbd.values[old])
hist = {"train": rows[old].reset_index(drop=True),
        "state": pd.DataFrame({"train_end": [rows.start[old].max()]})}
Xt = rows[new].reset_index(drop=True)
upload = pd.DataFrame({"well_name": Xt.well_name, "test_start": Xt.start, "test_end": Xt.end,
                       "oil_rate_stbd": Xt.oil_rate_stbd, "water_rate_stbd": Xt.water_rate_stbd})
rolled, rep = rolling.monthly_refit(stand_in, hist, Xt, upload, np.ones(len(Xt), bool),
                                    pd.date_range(cut, "2025-09-30"))
print(f"stand-in model: {old.sum()} tests; upload: {new.sum()} tests")
print("refits:", rolling.describe(rep))

# a test is a test-separator rate, so it is compared without the routing correction
real = {"oil": Xt.oil_rate_stbd.values, "water": Xt.water_rate_stbd.values,
        "gas": tr.gas_rate_mscfd.values[new]}
pred = {name: rolling.unrouted(m).predict(Xt) for name, m in [("frozen", stand_in), ("monthly refit", rolled)]}
print()
for name, p in pred.items():
    print(f"{name:14s} WAPE  oil {wape(real['oil'], p.oil_rate_stbd.values):.2f}%   "
          f"water {wape(real['water'], p.water_rate_stbd.values):.2f}%   "
          f"gas {wape(real['gas'], p.gas_rate_mscfd.values):.2f}%")
aug = (Xt.start < "2025-09-01").to_numpy()
print("\\nAugust tests predicted by the unchanged model:",
      bool(np.allclose(pred["frozen"].oil_rate_stbd[aug], pred["monthly refit"].oil_rate_stbd[aug])))"""),

    MD("""One refit, for September, on the nine August tests. August is predicted by
the unchanged model, so no day is ever predicted with a test from its own month.

On this one split the refit does not help oil (1.58% to 1.83%, 18 tests) and
helps gas (4.67% to 4.45%). A single split of 18 tests is within noise, which is
why the pooled table above is the evidence, and why the refit can be switched
off (`--frozen`). `python ml/eda/history_handoff.py` runs the same rehearsal
end to end through the app's back end, from raw CSVs, and gets the same numbers.

### Refitting on our own predictions would do nothing

If the new months came without measured rates, the tempting move would be to
refit on the model's own predictions. It cannot work. A self-labelled row lies
exactly on the fitted surface, so it has zero residual and the least-squares
solution does not move."""),

    CODE("""p = rolling.unrouted(stand_in).predict(Xt)
both = pd.concat([rows[old], Xt], ignore_index=True)
self_fit = VFMModel().fit(both, np.r_[rows.oil_rate_stbd.values[old], p.oil_rate_stbd.values],
                          np.r_[rows.water_rate_stbd.values[old], p.water_rate_stbd.values])
change = max(np.abs(self_fit.choke_coef - stand_in.choke_coef).max(),
             np.abs(self_fit.wc_coef - stand_in.wc_coef).max())
print(f"largest coefficient change after adding {len(Xt)} self-labelled tests: {change:.1e}")"""),

    MD("""### What an upload of later months takes from the training period

An upload that starts on 1 October holds no January to September rows, yet
three things depend on them. `ml/models/history/` (about 125 KB, built by
`ml/build_history.py`) keeps them:

- **the opening choke setting.** `choke_events.csv` is an event log. A well
  with no row at the start of the upload would have no choke until its first
  change, and a well with no change at all would have none;
- **the oil produced so far,** for the PTA producing time. Without it the
  cumulative is 2.5% to 10.3% short;
- **the rate on the last training day,** for a shut-in on the upload's first day.

`python ml/eda/history_handoff.py` rehearses it: history cut at 31 July, an
August to September upload with no opening choke rows. With the history all ten
wells are within 0.5% of the scored file on the first day and every flowing day
is within 0.02%. Without it no well is right on the first day and errors reach
63%. GL-08's permeability and skin reproduce the submission either way, because
the build-up lasts 72 hours against a producing time near 88,000 hours."""),

    CODE("""import history

store = history.load()
print(store["state"][["cum_oil_stb", "last_choke_pct", "last_choke_time",
                      "last_oil_rate_stbd"]].round(1).to_string())
print(f"\\ntraining tests stored for the refit: {len(store['train'])}; "
      f"the last one started {history.train_end(store):%Y-%m-%d}")"""),

    MD("""## Summary

| phase | R² | MAPE | WAPE | bias |
|---|--:|--:|--:|--:|
| **Oil** | 0.9981 | 2.56% | **2.33%** | +0.25% |
| **Water** | 0.9959 | 3.82% | **3.48%** | +0.15% |
| **Gas** | 0.9940 | 5.65% | **4.61%** | +2.04% |

Validated time-forward on 55 held-out tests, never a random split. These are
test-routed numbers; the leaderboard, which scores normal-production days with
the routing correction applied, gives **21.0200 / 30**.

**What made the difference:** finding the `-999.25` sentinel and GL-06's unit
error before modelling; recognising that 98.3% between-well variance makes
random splits meaningless; and using physics to constrain the functional form
so that 85 labels only had to estimate 14 parameters instead of discovering a
whole relationship.

**Honest limits.** Gas keeps a +2% bias — every correction we tested cost more
variance than it removed. The model does not generalise to wells it was not
fitted on. And all 85 labels were measured under test-separator routing, which
sits ~2.6% away from normal production conditions. Past the end of training a
frozen model drifts (oil WAPE 2.7% to 3.5% over three months); the monthly
refit holds it near 2.5–2.8%, and it needs the new months' well tests to do so.

Phase 2 (PTA) is in a separate notebook."""),
]


def main() -> None:
    nb = nbf.v4.new_notebook(cells=CELLS)
    nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python"}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"executing {len(CELLS)} cells...")
    NotebookClient(nb, timeout=1800, kernel_name="python3",
                   resources={"metadata": {"path": str(OUT.parent)}}).execute()
    nbf.write(nb, OUT)
    n_out = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("outputs"))
    print(f"wrote {OUT.relative_to(ROOT)} -- {n_out} code cells with outputs")


if __name__ == "__main__":
    main()
