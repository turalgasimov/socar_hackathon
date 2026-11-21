# Pitch — SOCAR Hackathon 2026

What we have, what we say, and what is still missing. Status as of 21 Nov
2026, ~17:30 (GitHub `master` at `6e00f4a`).

- The spoken script is [`speech.txt`](speech.txt).
- The research behind every claim is in [`../research/`](../research/).

Markers:
- `TODO(you)`: only you can fill it.
- `TODO(peers)`: waits on the ML/PTA work.
- `TODO(us)`: UI or pitch work we still have to build.

---

## 1. Format and scoring

| | |
|---|---|
| Slot | **7:00 total, including the live demo**, then 3 min Q&A |
| Demo | We run the app live on the **organisers' test data**, raw CSVs in and results out (`docs/Deliverables.pdf`) |
| Deadline | Code, `.pkl` model, results, notebook, PTA plots and slides on GitHub by **22 Nov 13:00** |
| Jury | SOCAR engineers + Caspian AI Institute: technical, not "product people" |
| Language | TODO(you): Azerbaijani or English? `speech.txt` is in English for now |
| Speakers | TODO(you): who says which part (marked `[SPEAKER ?]` in `speech.txt`) |
| Product name | **RizzML** |

**Scoring (100 points):**
- VFM 50: methodology 20 · accuracy 30
- PTA 30: plots 10 · parameters 20
- UI 10: functionality 4 · workflow 6
- Presentation 10

VFM accuracy is 10 points per phase, split R² /3 + MAPE /2 + WAPE /5. WAPE
weights by volume, so GL-07 (34% of field oil) dominates.

---

## 2. What we have right now

### VFM: done
- **Model:** a choke-flow physics model for liquid rate, water cut estimated
  from the tubing pressure drop, gas from the static solution GOR (Rs). Saved
  as `ml/models/vfm.pkl` (plus `.joblib`). It refuses to save itself if oil
  MAPE is above 4%.
- **Scores, time-forward** (55 of 85 tests; each predicted only from the past):

  | phase | R² | MAPE | WAPE | bias |
  |---|--:|--:|--:|--:|
  | oil | 0.9981 | **2.56%** | **2.33%** | +0.25% |
  | water | 0.9959 | **3.82%** | **3.48%** | +0.15% |
  | gas | 0.9940 | **5.65%** | **4.61%** | +2.04% |

- **Physics vs machine learning** (time-forward oil MAPE, same folds):

  | model | MAPE |
  |---|--:|
  | Copy the well's previous test | 6.00% |
  | Ridge regression, 58 features | 5.11% |
  | **Choke physics (best variant)** | **2.67%** |

  - The physics lead is real: **+2.17 pp, 95% CI [1.07, 3.42]**
    (well-cluster bootstrap, 5,000 resamples).
  - Ridge is **statistically no better than copying the last test**:
    +0.89 pp [−1.54, 3.34].
  - As a well collects more tests, physics improves (3.97 → 2.73%) and
    Ridge gets worse (4.00 → 6.18%).
- **The model rediscovered the choke law:** fitted exponents S^2.057 and
  ΔP^0.472, against the textbook 2 and 0.5. Nobody told it those values.
- **Deliverables done:**
  - `ml/outputs/vfm_submission.csv`: 2,730 rows in the template's exact
    format
  - `ml/outputs/vfm_daily_predictions.xlsx`: 2,729 well-days, with the 14
    low-coverage days flagged
  - `notebooks/VFM_Phase1.ipynb`: all cells run
- **Ready for the live demo:**
  - `ml/predict_from_raw.py` takes the raw CSVs and produces predictions in
    **61.6 s** on the full dataset, bit-identical to the submission.
  - A hostile test (renamed wells, two months of data) finishes in 11.8 s.
    It **flags unseen wells instead of crashing**: unseen-well error is about
    70%, so those numbers are marked, not trusted.

### Data quality: done (our strongest story)
- **Hidden missing values:** 7,410 readings coded as `-999.25` in a file that
  reports zero missing values.
- **Wrong units:** GL-06 gas rates were in m³/d under an Mscf/d header, so off
  by 28×.
- **Other repairs:**
  - 5 sign flips
  - 2,513 duplicate rows
  - 449 spikes removed (0.011%)
  - 3,914,560 clean rows out
- **A night when every well went silent:** on 2025-08-09, 01:09–05:40, all
  10 wells dropped out at once. That's a data-recording system failure, not
  10 broken sensors.
- **The test-mode trap:** during a well test, flow goes to the test
  separator, so downstream wellhead pressure reads 19–29 psi lower than on
  normal days, on all 10 wells. On GL-04 the test range and the normal-day
  range don't even overlap.
  - Measured effect: **2.5%**, agreed by four independent methods (IPR
    2.50%, thermal ratio 2.51%, thermal slope 2.05%, daily vs test window
    2.62%).
  - Whether the correction is applied in the submission: TODO(peers).
- **Partial shut-in days:** on the 10 days where a well was shut in part of
  the day, using the daily average differs by 30% on average (up to 68%)
  from integrating only the flowing minutes. Fixed by integrating; field oil
  total moves −0.023%.

### PTA: in progress (peers)
- **6 build-ups found automatically.** GL-03, GL-05, GL-07 and GL-09 never
  shut in, so PTA isn't possible on those wells, and we say so.

  | well | start | duration | build-up |
  |---|---|--:|--:|
  | GL-01 | 2025-04-15 08:00 | 72.0 h | +271 psi |
  | GL-02 | 2025-03-08 14:23 | 5.7 h | +281 psi |
  | GL-04 | 2025-06-03 08:00 | 48.0 h | +837 psi |
  | GL-06 | 2025-07-22 03:11 | 8.0 h | +119 psi |
  | GL-08 | 2025-08-19 09:00 | 72.0 h | +522 psi |
  | GL-10 | 2025-05-27 21:04 | 9.0 h | +228 psi |

- The gauge sits 150–420 ft above datum, so it needs a hydrostatic
  correction before Horner analysis.
- Single-phase oil is justified: downhole pressure stays above bubble point
  (e.g. GL-04: 2,269 vs 1,265 psia).
- GL-02 and GL-06 are short build-ups, so their slopes are flagged as
  uncertain.
- **Horner results (m, k, skin, ΔP skin) and plots:** TODO(peers). The demo,
  the value slide and the speech all need them.

### UI: built (us), in `ui/`
- **Run:** `pip install -r ui/requirements.txt`, then `cd ui && streamlit run app.py`
  (add `--server.address 0.0.0.0` to serve other PCs). Check before a demo:
  `python ui/check_pipeline.py <folder with the raw CSVs>`.
- **Flow:** upload the raw files (CSV or Excel) → Run analysis (~30 s) → tabs: 1 Field data,
  2 Production rates (VFM), 3 Well tests (PTA) with interpretation, 4 Export, plus a CSV/Excel
  converter. Exports: VFM and PTA as CSV and Excel, one combined workbook, an HTML report.
- Uses the ML team's code unchanged (`ml/src`, `ml/predict_from_raw.py`, `ml/models/vfm.pkl`); the
  PTA mirrors `ml/eda/pta_explore.py` and matches its reference to within 1% on k.

### Research: done (`research/`)
- **Nobody combines gas-lift VFM and PTA.** About 30 products checked.
  KAPPA-Automate comes closest, but its rates come from a reservoir model
  and it needs an expert to set up.
- **SOCAR already uses three KAPPA products** (Report.az, Nov 2025). We are
  complementary, never against KAPPA.
- **The literature agrees:** with only well tests, physics-based models beat
  ML, and copying the last test beats most models (Hotvedt et al., 2022, 10
  wells).
- **Problem numbers:**
  - Canada's regulator (AER Directive 017) requires at least 3 tests per
    month for oil wells above 30 m³/d. Ours average about 1,450 bbl/d (about
    230 m³/d) and get about 1. (The average SOCAR well, about 4 m³/d, would
    need only 1 a month there.)
  - A multiphase meter costs about US$100–250k, plus up to 25% to install
    (Shell/PDO, 2002);
    smart-well hardware about US$2–5M per well (Ma et al., 2020).
  - PETRONAS skin screening: 28 jobs, +6,500 bopd, screening time from 2
    weeks to 1 day.

### What the problem costs (from `research/COMPETITORS.md` §12)
- **SOCAR is a gas-lift company:** 52.4% of its oil is gas-lifted, 64.6% at
  Azneft (SOCAR Annual Report 2024).
- **One percent of that oil going unseen = about US$26M a year** (about 78,800
  bbl/d at Brent $91.98 on 20 Nov 2026, gross). 1% is the top-quartile
  deferment benchmark (PDO, SPE-214005); a mature field there ran at 3.7%.
- **Our 10 wells:** 1% lost = **$4.9M a year**, 5% = $24.3M. A single unseen
  20% drop on one well for 15 days (half a monthly test interval) = about
  $0.4M.
- **Allocation:** testing weekly instead of monthly is worth $27–80M a year in
  a 36-well field (Sadri & Shariatipour, ASME JERT 2020, simulation). A 1%
  metering error on 20,000 bbl/d is about $18k a day at $92 (NEL 2014,
  rescaled).
- **Upside documented elsewhere:** skin screening +6,500 bopd from 28 jobs
  (PETRONAS); gas-lift optimisation +7% on 200+ wells (ExxonMobil, 2024).
- **Caution:** SOCAR wells average about 26 bbl/d; ours about 1,450. Value
  scales with total volume, and software costs almost nothing per extra well
  *(inference)*.

---

## 3. What the jury must remember

1. **A rate for every well, every day, from sensors SOCAR already has.** No
   new hardware.
2. **Physics beat machine learning, and the model rediscovered the choke law
   by itself.**
3. **The only workflow that connects rates to reservoir diagnosis (VFM →
   PTA) for gas-lifted wells**, and it complements the KAPPA tools SOCAR
   already uses.

## 4. Where we break the template

- **Added a live demo and a methodology section.** They carry about 60 of the
  points.
- **Target audience, business model and competition squeezed into about 45
  s,** because the demo takes a third of the slot.
- **The roadmap is one line inside the ask.** "What we already did" is the
  methodology section.
- **Jargon only in the methodology section.**

## 5. Run sheet (7:00)

| Time | Section | Slides |
|---|---|---|
| 0:00–0:45 | Hook + problem | 1–2 |
| 0:45–1:05 | Solution | 3 |
| 1:05–3:35 | **Live demo** (the ~60 s processing wait is narrated with the data-quality story) | 4 (app embedded) |
| 3:35–4:55 | Methodology and results | 5–6 |
| 4:55–5:40 | Competition, value, deployment | 7–8 |
| 5:40–6:00 | Team | 9 |
| 6:00–6:30 | The cost cut: SOCAR today vs RizzML (counter stops) | 10 |
| 6:20–7:00 | **Buffer** for live-demo hiccups | — |

## 6. Slides

The deck is built: `pitch/deck/` (HTML: reveal.js + three.js, works offline).
Run `python3 -m http.server 8000 -d pitch/deck` from the repo root and open
http://localhost:8000. Keys: F fullscreen, S speaker view with timer, Esc overview.
PDF for the upload: open `/?print-pdf` and print. The demo slide loads the app
from http://localhost:8501 only when it is running. A live counter (bottom right) starts when you
leave slide 1: daily well rates RizzML could compute on one PC (44/s, from our measured 61.6 s for
2,730 well-days) next to the well tests SOCAR runs in the same time (5,715 wells tested monthly):
about 18,600 vs 1 after 7 minutes. It stops on the cost slide (10): today vs RizzML on time per rate
(12–24 h vs 0.02 s), rates per well (monthly vs daily), error between tests (6.0% vs 2.6%) and hardware
per well ($100–250k vs $0). Press R to reset it before you start. The pilot ask is no longer in the deck;
team photos go in pitch/deck/team/ as rovshan.jpg, faig.jpg, tural.jpg (initials show until then).
Press R to reset it before you start. Slide 10 is a references backup.

| # | Slide | Content | Status |
|--:|---|---|---|
| 1 | Hook | One well, 9 months: a dense sensor line and ~9 dots for the tests. Question: "How much did GL-04 produce yesterday?" | TODO(us): build the figure |
| 2 | Problem | 3.9 M readings vs 85 rates · ~1 test per month; Canada requires 3 for wells above 30 m³/d · **52% of SOCAR oil is gas-lifted; 1% unseen ≈ US$26M/yr** · meters US$100–250k each · separate, disconnected tools | text ready |
| 3 | Solution | One-liner + 3 points: one connected flow · physics first · no hardware, on SOCAR's server | text ready |
| 4 | Demo | Streamlit app embedded (`?embed=true`); QR code to open it on a phone | TODO(us) |
| 5 | Physics vs ML | Three bars: copy last test 6.00 · Ridge 5.11 · physics 2.67. Exponents 2.06 / 0.47 vs 2 / 0.5 | TODO(us): chart |
| 6 | Results + limits | Scores table (R², MAPE, WAPE) · routing gap 2.5% by 4 methods · unseen wells flagged · PTA results table | TODO(peers): PTA numbers |
| 7 | Competition | The five-row table in §8 | text ready |
| 8 | Value + deployment | Daily rates · skin → lost barrels → stimulation list · on-prem, browser only, one model version | TODO(peers): $ figure |
| 9 | Team | TODO(you): one line per person | TODO(you) |
| 10 | Cost cut | Centre: SOCAR today vs RizzML on time per rate, rates per well, error, hardware, the frozen compute counter, and money saved ($125–312k of meters per well; up to $1.8B if every SOCAR well were metered) | built |
| 11 | References | 10 sources | built |
| — | Backup | Q&A slides: validation scheme, routing gap, unseen wells, KAPPA | TODO(us) |

## 7. Demo plan

1. **Open** the app from a second laptop or a phone (QR code): "it runs on a
   server, I'm only a browser".
2. **Upload** the organisers' raw CSVs and press Run. About 60 s; narrate the
   data-quality story meanwhile.
3. **VFM:** daily oil, water and gas per well, with the test dots on top.
   Download the CSV.
4. **PTA:** list of shut-ins → Horner plot → k, skin, ΔP skin →
   interpretation. TODO(peers) numbers.
5. **Export:** Excel and the report.

Fallbacks:
- **Test data has a new well:** the app flags it as unseen; say so openly.
- **Upload fails:** switch to our bundled dataset.
- **App fails:** play the backup video. TODO(us): record it.
- **Venue Wi-Fi blocks laptop-to-laptop:** use a phone hotspot. Test it early
  on 22 Nov.

## 8. Competition

From `research/COMPETITORS.md` and `research/FINDING.md`: about 30 products
checked, and **none combines gas-lift VFM and PTA in one workflow**. **SOCAR
already uses three KAPPA products** (Report.az, 26 Nov 2025), so we position as
*complementary* to KAPPA, never against it.

| Alternative | Examples | What's missing for gas-lifted wells | Our edge |
|---|---|---|---|
| Physical multiphase meters | SLB Vx, Emerson Roxar | ~US$100–250k per meter, plus up to 25% to install (Shell/PDO, 2002) | **US$0 hardware**: uses the sensors already on the well |
| "Smart well" hardware | SLB intelligent completions, Baker Hughes fibre and downhole flowmeters | New downhole hardware, US$2–5M per well (Ma et al., 2020) | Runs on standard wellhead sensors |
| VFM software | Weatherford MetaFlow, SLB + Dataiku, Olga Online, Solution Seeker | Rates only, no PTA; heavy simulators or ML black boxes; mostly cloud | Physics choke model calibrated on your well tests; explainable; on your own server |
| PTA software | KAPPA Saphir and KAPPA-Automate, SLB WellTest, Petex IVM | Expert tools; rates come from a reservoir model or from somewhere else | Automatic shut-ins + Horner on our own daily rates, same well, one view |
| Reservoir simulation suites | tNavigator (Rock Flow Dynamics) | Model-centric: they *consume* rates and well-test results for history matching; no VFM, no automatic build-up analysis | Supplies the daily rates and k/skin their models need |
| Status quo | Periodic well tests + spreadsheets | ~1 test per well per month; separate, disconnected tools | A rate every day; one workflow; an audit trail |

**Rules:**
- Never pitch against KAPPA. We supply the daily rate history its PTA needs.
- No promises. Say what the prototype already does.
- Use public facts only, and don't quote vendors' accuracy claims.
- Don't raise vendor ownership or sanctions on stage; compare capabilities only.

**If the jury asks**
- *"We already use tNavigator."* "Good, then we feed it. tNavigator builds
  and history-matches reservoir models, and it needs measured rates and
  well-test results as inputs. It doesn't estimate rates from sensors or
  interpret build-ups automatically. Our daily rates and k/skin go straight
  into its history matching and material balance."
- *"KAPPA already does this."* See §11: we supply the daily rate history
  KAPPA's PTA needs.

## 9. Users, value and the ask

- **Users:**
  - the production engineer for a cluster of gas-lifted wells
  - the reservoir engineer who interprets build-ups
  - TODO(you): which SOCAR fields or production units, how many engineers,
    how many gas-lift wells; the decision maker
- **Value:**
  1. A rate every day instead of about once a month.
  2. Every shut-in turned into skin, then lost barrels, then a stimulation
     candidate list. PETRONAS benchmark: +6,500 bopd from 28 jobs.
     TODO(peers): our own lost-barrels figure.
  3. No meter hardware.
  4. One model version and an audit trail.
  5. Money: 1% of SOCAR's gas-lifted oil ≈ US$26M a year; 1% of our 10
     wells ≈ $4.9M a year (see §2, "What the problem costs").
  6. Skin → dollars: lost rate = q × ΔP_skin / (p̄ − p_wf − ΔP_skin), so the
     app can turn every shut-in into lost bbl/d and $/yr *(inference, standard
     inflow equation)*. Real-world anchor: PETRONAS got about 232 bopd per
     acid job, which is about $7.8M a year gross per job at $92.
- **Deployment:** one server inside SOCAR's network; engineers use a browser;
  the data never leaves. The roadmap later adds company login and a live
  data feed.
- **Ask (draft):** a 3-month pilot on TODO(you) N gas-lift wells: read access
  to the sensor data, one server inside SOCAR's network, and one production
  engineer as our counterpart.

## 10. Team

| Name | Connection to oil, gas, wells | What they built here |
|---|---|---|
| Rovshan Agayev | Physics Olympiad Champion; has a paper on reservoir engineering | Physics benchmarks, routing gap, partial shut-in fix |
| Faig Tayibov | 2× ICPC Champion; has integrated ML and computer vision into LMS systems | Data cleaning, VFM model, submission, notebook |
| Tural Gasimov | CanSat Global Finalist; has engineered military-grade simulations and software | UI, pitch, competitor research |

## 11. Q&A backup (3 min)

| Likely question | Short answer |
|---|---|
| Why not a random train/test split? | It leaks each well's rate level; any model scores ~4%. We validate time-forward only. |
| 85 labels: isn't that overfitting? | That's why physics wins. Few parameters, and ML was no better than copying the last test. |
| Does it work on a new well? | Not reliably (~70% error). The app flags unseen wells instead of guessing quietly; a new well needs a few tests to calibrate. |
| Is the data synthetic? Then the choke law is built in. | Possibly. We present it as a physics-consistency check, not proof that physics always wins. |
| What about well-test vs normal-day conditions? | Measured at 2.5% by four independent methods. TODO(peers): whether it is corrected in the submission. |
| Why PTA on daily rates? | The brief asks for it. A 2.6% rate error moves skin by only ~0.013; permeability inherits the error one-to-one. |
| Is single-phase valid? | Yes: pressure stays above bubble point on every well. |
| GL-02 and GL-06 build-ups are short. | 5.7 h and 8 h; radial flow may not develop, so we flag them. |
| KAPPA already does this. | KAPPA-Automate gets rates from a reservoir model. Ours come from choke physics calibrated on well tests, for gas lift, and can feed KAPPA. Complementary. |
| Deployment and security? | On-premises server, browser access; the data never leaves SOCAR. |
| Where does the $26M come from? | SOCAR Annual Report 2024: 52.4% of oil is gas-lifted (3.92 Mt ≈ 78,800 bbl/d). 1% of that at Brent $92 is ≈ $26M a year gross. 1% is the top-quartile deferment benchmark (PDO, SPE-214005). |
| SOCAR wells make ~26 bbl/d, yours ~1,450. | True; the hackathon wells aren't typical. Value scales with total volume, and software costs almost nothing per extra well. |

## 12. Open before 13:00 tomorrow

- [ ] TODO(peers): Horner results and plots; whether the routing correction is applied
- [ ] TODO(you): product name, language, speakers, team rows, pilot size, SOCAR user details
- [ ] TODO(us): UI end to end on raw CSVs
- [x] Deck v1 in `pitch/deck/` (hook chart, physics-vs-ML bars, 3D field)
- [ ] TODO(us): QR code for the demo; fill RizzML, team and PTA numbers in the deck
- [ ] TODO(us): backup video
- [ ] Ask the organisers: is the test data new days or new wells? Is the daily truth test-routed?
- [ ] Rehearse twice with a stopwatch; cut the speech if it runs past 6:20

## Slide rules

- One idea per slide, with the number big.
- Slide titles use the rubric's own words ("VFM methodology", "PTA results").
- No product mention before the Solution slide.
- Every number on a slide matches the final results files.
