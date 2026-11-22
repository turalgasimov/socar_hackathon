# Pitch — SOCAR Hackathon 2026

What we have, what we say, and what is still missing. Status as of 22 Nov
2026 (GitHub `master` at `ed1bd26`).

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
weights by volume, so GL-07 (31% of field oil) dominates.

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
  separator, so downstream wellhead pressure reads 17–29 psi lower than on
  normal days, on all 10 wells. On GL-02 and GL-04 the test range and the
  normal-day range don't even overlap.
  - Measured effect: **2.5%**, agreed by four independent methods (IPR
    2.50%, thermal ratio 2.51%, thermal slope 2.05%, daily vs test window
    2.62%).
  - Applied in the submission: daily rates are scaled up by 80% of each well's measured
    routing factor, the setting that scored best on the leaderboard.
- **Partial shut-in days:** on the 10 days where a well was shut in part of
  the day, using the daily average differs by 36% on average (up to 104%)
  from integrating only the flowing minutes. Fixed by integrating; field oil
  total moves −0.023%.

### PTA: done (peers): 8.3840 / 20, best of five PTA submissions
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

- **Method: an exact model match, not a hand-picked straight line.**
  - The diffusivity equation (wellbore storage + skin + radial flow + boundary) is solved in
    Laplace space and fitted to every point of each build-up.
  - It is the model family KAPPA Saphir and SLB regress on.
  - Fit error 0.03–0.08 psi RMS, against gauge noise of about 0.03 psi.

  | well | boundary | k (md) | skin | ΔP skin (psi) | m (psi/cycle) |
  |---|---|--:|--:|--:|--:|
  | GL-01 | closed, r_e 1,367 ft | 105.25 | 5.741 | 116.78 | 23.41 |
  | GL-02 | infinite | 61.34 | −0.264 | −11.49 | 50.14 |
  | GL-04 | infinite | 57.35 | −0.904 | −108.13 | 137.57 |
  | GL-06 | infinite | 295.48 | 2.307 | 29.04 | 14.48 |
  | GL-08 | infinite | 43.07 | −1.589 | −127.44 | 92.27 |
  | GL-10 | closed, r_e 1,048 ft | 176.40 | 2.195 | 54.41 | 28.52 |

- **Validated on data the fit never saw.**
  - Fitted on the first 24 h of GL-01, the model forecasts the next 48 h at noise level (0.04 psi).
  - The aquifer / constant-pressure boundary is rejected: it fits 7–9× worse.
  - Two independent solvers (Laplace/Stehfest and time-domain finite differences) agree within
    ~0.02–0.03 psi, and the inversion error is ≤ 0.03 psi.
- **Better than the textbook Horner line where it should be.**
  - On GL-08 (clean 72 h) the two agree within 0.3%.
  - On the short or storage-dominated tests (GL-02/04/06) the derivative is still 3–5% above the
    radial-flow level when the test ends, so the Horner line is too steep and the model's k is
    3–4% higher.
  - Leaderboard: Horner 7.25 / 7.38, model 8.38.
- **Datum:** the gauge sits 150–420 ft above datum. The offset is constant through a build-up, so it
  cancels in k, skin, m and ΔP skin (verified per well). Only p* and p̄ need it.
- **Single-phase oil is justified:** pressure stays above bubble point (GL-04: 2,269 vs 1,265 psia).
- **Where to see it:** `ml/outputs/figures/pta/` (9 figures) and `notebooks/PTA_Phase2.ipynb`. The
  app shows the same results, and `ui/check_pipeline.py` checks it against the submission.

### UI: built (us), in `ui/`
- **Run:** `pip install -r ui/requirements.txt`, then `cd ui && streamlit run app.py`
  (add `--server.address 0.0.0.0` to serve other PCs). Check before a demo:
  `python ui/check_pipeline.py <folder with the raw CSVs>`.
- **Flow:** sign in (demo account `rizzman@socar.az` / `guessme`, no real authentication yet) → a
  tile menu in SOCAR colours: Load Data → Production Rates (VFM) → Well Tests (PTA) → Generate Graph →
  Export, plus Sample Data, Field Data, Data Quality, History and a CSV/Excel converter. Settings
  (dark/light, AZ/EN/RU) sit in the account bar. History keeps each user's uploads, analyses and
  downloaded files, and reopens them. Exports: VFM and PTA as CSV and Excel, one workbook, an HTML report.
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
  - Well testing follows API MPMS Chapter 20.5 (2017), the recommended practice for production
    well testing in measurement and allocation: separator, multiphase-meter and tank tests. It
    treats test duration as a flow-stability question (Annex C). We found no fixed test frequency
    in its public description; the text is paywalled, so we do not claim one either way.
  - Between tests, every rate is allocated, not measured. Sadri & Shariatipour (J. Energy Resour.
    Technol. 142(4), 2020): allocation error falls as tests get more frequent, most going from one
    to two tests a month; monthly to weekly testing cut allocation-error costs by $27–80M in their
    three cases. Our wells get about 1 a month.
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
| 0:00–0:50 | Hook + problem (click off the blank slide 1 to start) | 2–3 |
| 0:50–1:05 | Solution | 4 |
| 1:05–3:30 | **Live demo** (the analysis wait is narrated with the data-quality story) | 5 (app embedded) |
| 3:30–5:20 | Methodology, results, and the well tests (PTA) | 6–8 |
| 5:20–5:55 | Competition, value, deployment | 9–10 |
| 5:55–6:15 | Team | 11 |
| 6:15–6:50 | The cost cut: SOCAR today vs RizzML (counter stops) | 12 |
| 6:50–7:00 | **Buffer**; the demo's data-quality story has one optional line to drop | — |

## 6. Slides

The deck is built: `pitch/deck/` (HTML: reveal.js, 2D SVG and CSS motion, no WebGL).
To present or upload, use `pitch/RizzML_pitch.html`: the whole deck in one file, opened by
double-click, no server (rebuild with `python3 pitch/deck/build.py` after editing `pitch/deck/`).
Only the live demo needs something running: the app on port 8501. Before the talk, open the demo
slide once and sign in inside it; it stays signed in for the whole talk. Keys: F fullscreen,
S speaker view with timer, Esc overview. For uploading there is also the PDF,
`pitch/RizzML_pitch.pdf` (11 pages; remake by opening the file with `?print-pdf` and printing). The demo slide loads the app
from http://localhost:8501 only when it is running. A live counter (bottom right) starts when you
leave the blank first slide: daily well rates RizzML could compute on one PC (44/s, from our measured 61.6 s for
2,730 well-days) next to the well tests SOCAR runs in the same time (5,715 wells tested monthly):
about 18,600 vs 1 after 7 minutes. It stops on the cost slide (12): today vs RizzML on time per rate
(12–24 h vs 0.02 s), rates per well (monthly vs daily), error between tests (6.0% vs 2.6%) and hardware
per well ($100–250k vs $0). Press R to reset it before you start. The pilot ask is no longer in the deck;
team photos go in pitch/deck/team/ as rovshan.jpg, faig.jpg, tural.jpg (initials show until then).
Press R to reset it before you start. Slide 1 is blank on purpose (stand there while introduced); slide 13 is a references backup.

| # | Slide | Content | Status |
|--:|---|---|---|
| 1 | Blank | Empty on purpose: stand there while introduced. The live counter starts on the next click | built |
| 2 | Hook | Question: "How much oil did GL-04 produce yesterday?" · 2D map of the ten wells · GL-04's nine measured tests as dots with "?" between them | built |
| 3 | Problem | 1 test a month; allocation error drops most going to 2 (API MPMS 20.5, Sadri & Shariatipour 2020) · 52% of SOCAR oil is gas-lifted · separator $0.8–1.5M, meter $100–250k · GL-04's April as a calendar: 1 measured day, 29 unknown | built |
| 4 | Solution | RizzML one-liner · no hardware, on SOCAR's server · the daily estimate drawn through the test dots · animated well cross-section (choke, gas-lift valves, gauge, reservoir) | built |
| 5 | Demo | The app embedded live (sign in once on this slide before the talk) | built; TODO(us): QR code to open it on a phone |
| 6 | Physics vs ML | Three bars: copy last test 6.0% · ML, 58 features 5.1% · physics 2.7%. Exponents 2.06 / 0.47 vs 2 / 0.5 | built |
| 7 | Results + limits | VFM per phase (MAPE, WAPE, R²) · routing gap 2.5% by 4 methods · unseen wells flagged | built |
| 8 | Well tests (PTA) | The six build-ups on the log-log diagnostic with the model match (the team's figure) · k / skin / boundary table: k 43–295 md, skin −1.6 to +5.7, three stimulated, three damaged, GL-01 and GL-10 closed · fit 0.03–0.08 psi · hold-out on GL-01 | built |
| 9 | Competition | Rates camp vs reservoir-diagnosis camp, RizzML bridging them; SOCAR already runs KAPPA (table in §8) | built |
| 10 | Value + deployment | Daily rates · skin → lost barrels → stimulation list (up to ~1,470 stb/d of oil on the three damaged wells, ≈ $135k a day gross at $92; an upper bound) · PETRONAS 2 weeks → 1 day · one PC, data never leaves · the shut-in well, pressure building | built |
| 11 | Team | Photos, education, one achievement and one line each; "Our team trying to understand the provided data" | built |
| 12 | Cost cut | Centre: SOCAR today vs RizzML on time per rate, rates per well, error, hardware, the frozen compute counter, and money saved ($125–312k of meters per well; up to $1.8B if every SOCAR well were metered) | built |
| 13 | References | 12 sources | built |
| — | Backup | Q&A slides: validation scheme, routing gap, unseen wells, KAPPA | TODO(us) |

## 7. Demo plan

1. **Open** the app from a second laptop or a phone (QR code): "it runs on a
   server, I'm only a browser".
2. **Upload** the organisers' raw CSVs and press Run. About 60 s; narrate the
   data-quality story meanwhile.
3. **VFM:** daily oil, water and gas per well, with the test dots on top.
   Download the CSV. On the test data, "Oil error vs tests" is a true forecast
   check: every test is scored by a model that had not seen it. Data Quality
   lists the months the model was refitted on the new tests.
4. **PTA:** list of shut-ins → Horner plot → k, skin, ΔP skin →
   interpretation. Show GL-01: k 105 md, skin +5.7, ΔP skin 117 psi, flow
   efficiency 57%, up to ~750 stb/d recoverable (upper bound).
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
     Ours: up to ~1,470 stb/d of oil lost to skin on the three damaged wells
     (GL-01 ~750, flow efficiency 57%; GL-10 ~520; GL-06 ~190), at today's drawdown.
     Say it as an **upper bound**: it assumes the skin is removable damage and the
     lift system can take the extra rate. At $92 that is ≈ $135k a day gross.
  3. No meter hardware.
  4. One model version and an audit trail.
  5. Money: 1% of SOCAR's gas-lifted oil ≈ US$26M a year; 1% of our 10
     wells ≈ $4.9M a year (see §2, "What the problem costs").
  6. Skin → dollars: lost rate = q × ΔP_skin / (p̄ − p_wf − ΔP_skin), with
     p̄ − p_wf from the fitted build-up model (`ml/src/pta_rate.py`). The app now
     shows it for every damaged well. Real-world anchor: PETRONAS got about 232 bopd per
     acid job, which is about $7.8M a year gross per job at $92.
- **Deployment:** one server inside SOCAR's network; engineers use a browser;
  the data never leaves. The roadmap later adds company login and a live
  data feed.
- **Ask (draft):** a 3-month pilot on TODO(you) N gas-lift wells: read access
  to the sensor data, one server inside SOCAR's network, and one production
  engineer as our counterpart.

## 10. Team

| Name | Education | Connection to oil, gas, wells | What they built here |
|---|---|---|---|
| Rovshan Agabeyov | ASOIU, Petroleum Engineering | Physics Olympiad Champion; author of "PI-ML and Physical Type Curves for Water-Injection Wells" | Physics benchmarks, routing gap, partial shut-in fix |
| Tural Gasimov | ASOIU, Robotics Engineering; ADA, BSc Computer Science | CanSat Global Finalist; has engineered military-grade simulations and software | UI, pitch, competitor research |
| Faig Tayibov | ADA, BSc Computer Science | 2× ICPC Champion; has integrated ML and computer vision into LMS systems | Data cleaning, VFM model, submission, notebook |

## 11. Q&A backup (3 min)

| Likely question | Short answer |
|---|---|
| Why not a random train/test split? | It leaks each well's rate level; any model scores ~4%. We validate time-forward only. |
| 85 labels: isn't that overfitting? | That's why physics wins. Few parameters, and ML was no better than copying the last test. |
| Does it work on a new well? | Not reliably (~70% error). The app flags unseen wells instead of guessing quietly; a new well needs a few tests to calibrate. |
| Is the data synthetic? Then the choke law is built in. | Possibly. We present it as a physics-consistency check, not proof that physics always wins. |
| What about well-test vs normal-day conditions? | Measured at 2.5% by four independent methods, and corrected in the submission (80% of each well's routing factor scored best). |
| Why PTA on daily rates? | The brief asks for it. A 2.6% rate error moves skin by only ~0.013; permeability inherits the error one-to-one. |
| Is single-phase valid? | Yes: pressure stays above bubble point on every well. |
| GL-02 and GL-06 build-ups are short. | 5.7 h and 8 h. The model fits through the storage transition, so no straight-line window is needed. A Horner line on the last points reads k 3–4% low. |
| How do you know the model is right, not just flexible? | Tests on data it never saw: it forecasts the late build-up from the early part at noise level, the competing boundary is rejected 7–9×, and two independent solvers agree within ~0.02–0.03 psi. |
| KAPPA already does this. | KAPPA-Automate gets rates from a reservoir model. Ours come from choke physics calibrated on well tests, for gas lift, and can feed KAPPA. Complementary. |
| Is this KAPPA? | Same physics family (analytical diffusivity solutions + regression). What we add: automatic shut-in detection, and the rates come from our own VFM on the same well. |
| Deployment and security? | On-premises server, browser access; the data never leaves SOCAR. |
| Where does the $26M come from? | SOCAR Annual Report 2024: 52.4% of oil is gas-lifted (3.92 Mt ≈ 78,800 bbl/d). 1% of that at Brent $92 is ≈ $26M a year gross. 1% is the top-quartile deferment benchmark (PDO, SPE-214005). |
| SOCAR wells make ~26 bbl/d, yours ~1,450. | True; the hackathon wells aren't typical. Value scales with total volume, and software costs almost nothing per extra well. |

## 12. Open before 13:00 tomorrow

- [x] PTA results and plots (exact model match, 8.3840 / 20); routing correction applied in the submission
- [ ] TODO(you): product name, language, speakers, team rows, pilot size, SOCAR user details
- [x] UI end to end on raw CSVs (`ui/check_pipeline.py` passes)
- [x] Deck in `pitch/deck/` (hook chart, physics-vs-ML bars, 2D field map, month calendar, well cross-section); single file and PDF in `pitch/`
- [ ] TODO(us): QR code for the demo (PTA and lost-oil lines are on slides 7 and 9)
- [ ] TODO(us): backup video
- [x] Test data: the next three months of the same ten wells, with measured well tests (organisers). The app runs on that upload alone and refits monthly on the new tests (`python ml/eda/history_handoff.py`)
- [ ] Ask the organisers: on the test data, are daily rates scored or the well-test rates? Is the daily truth test-routed?
- [ ] Rehearse twice with a stopwatch; the speech runs about 6:50 by word count, so drop the optional demo line if it runs over

## Slide rules

- One idea per slide, with the number big.
- Slide titles use the rubric's own words ("VFM methodology", "PTA results").
- No product mention before the Solution slide.
- Every number on a slide matches the final results files.
