# Pitch — SOCAR Hackathon 2026

Working draft, built on `pitch_template.txt`: problem → solution → audience →
business model → competition → roadmap → team → call to action. Adapted where
our jury and rubric differ from the business hackathons the template was
written for.

- `TODO(you)` — information only you can provide.
- `TODO(peers)` — waits on the ML / PTA results.
- ⚠ — interim number from the repo; replace it with the final model's score.

## Format and audience

| | |
|---|---|
| Slot | 7 min pitch + 3 min Q&A |
| Deadline | slides are uploaded with the code by **22 Nov 13:00** |
| Scored directly | Presentation: 10 pts |
| Scored *through* the pitch | VFM methodology: 20 pts; PTA plots: 10 pts. The judges see these here and in the UI |
| Jury | SOCAR engineers + Caspian AI Institute. Technical people, not the template's "product people" |
| Language | TODO(you): Azerbaijani or English? |
| Speakers | TODO(you): who presents which section |
| Product name | TODO(you) |

## Where we break the template

- **We add a live demo and a methodology section.** The template has neither,
  and the rubric pays 20 pts for methodology, so the judges must see it.
- **"Business model" becomes "Value and deployment".** SOCAR is our only buyer.
  The rules give SOCAR a perpetual, royalty-free licence, plus exclusive use if
  we place in the top 3, so selling to other companies is off the table. We
  pitch an internal service.
- **The roadmap shrinks to one line inside the call to action.** "What we already
  did" moves into Methodology, where it scores.
- **Technical jargon is allowed in Methodology only.** Everywhere else the
  template's rule holds: the half-asleep manager with a coffee must follow.

## Run sheet

| # | Section | Time | Slides |
|---|---|--:|--:|
| 1 | Problem + hook | 0:45 | 1–2 |
| 2 | Solution | 0:30 | 1 |
| 3 | Live demo | 2:15 | — |
| 4 | Methodology and results | 1:30 | 2 |
| 5 | Who it is for | 0:20 | 1 |
| 6 | Value and deployment | 0:30 | 1 |
| 7 | Competition | 0:20 | 1 |
| 8 | Team | 0:20 | 1 |
| 9 | Call to action | 0:10 | 1 |
| | **Total** | **6:40** | 20 s buffer |

---

## 1. Problem + hook (0:45)

*Template: crystal clear for everyone, put the hook here, say nothing about the
product yet. One image, and ask the audience 1–2 questions.*

**Opening question:** "How much oil did well GL-04 produce yesterday?" Pause.
"Nobody knows. Not us, and not the engineer responsible for it."

**The fact:** over 9 months, 10 wells logged **3.9 million sensor readings** but
only **85 measured production rates**. That is about one measurement per well
per month, and roughly 46,000 sensor readings for every measured rate.

**The pain:** between tests the rates are guessed. The analysis that turns
rates into reservoir decisions is spread across "disconnected tools, scripts
and spreadsheets", which is how the challenge brief itself puts it.

- TODO(you): what a late or wrong rate costs SOCAR. One number, or a quote from a
  mentor (for example, a damaged well losing production unnoticed for weeks).
- Visual: one well over 9 months, with a dense sensor line and ~9 dots marking
  the tests. Needs a new simple figure; `fig06_rate_history.png` has 10 panels,
  which is too busy for an opener.

## 2. Solution (0:30)

*Template: simple, no jargon, and say what makes us unique. Keep that unique
point running through the whole pitch.*

**One-liner (draft):** "[NAME] turns the sensor data SOCAR already records into
daily oil, water and gas rates. From those rates it reads each well's reservoir
health at every shut-in, all in one browser app on SOCAR's own server."

What makes us unique:
1. **One connected flow:** rate estimate → well-test interpretation → report.
   Today these are separate tools.
2. **Physics first:** the model rediscovers the choke-flow law from the data,
   so engineers can check it instead of just trusting it.
3. **No new hardware, nothing to install:** it uses existing sensors and a
   browser, and the data never leaves SOCAR.

- TODO(you): pick one of the three to own. Three is a lot for 30 seconds.

## 3. Live demo (2:15)

| Step | Show | Say |
|---|---|---|
| 1 | Open the app from a second laptop, or let a judge scan a QR code | "It runs on a central server. I'm just a browser." |
| 2 | Pick a well → sensor history with the test dots | "This is everything the well tells us…" |
| 3 | VFM → daily oil, water and gas line through the test dots | "…and now every day has a rate. The dots are the real measurements." |
| 4 | PTA → shut-in list → Horner plot → k, skin, ΔP skin | "Every shut-in is found and interpreted automatically." |
| 5 | Interpretation | "Skin +X: this well is damaged and loses ~Y bbl/d." TODO(peers) |
| 6 | Export | "One click: Excel and report for both parts." |

- Demo well: TODO(peers). GL-04 has the largest build-up (+837 psi, 48 h);
  GL-01 and GL-08 have the longest (72 h). Pick the one with the cleanest Horner.
- Record a backup video by TODO(you). Test whether the venue Wi-Fi lets two
  devices reach each other; keep a phone hotspot as the fallback.
- Rehearse with a stopwatch. 2:15 means one well only, with no detours.

## 4. Methodology and results (1:30) — this is where the points are

*Not in the template. VFM methodology is worth 20 pts, and this is the only
place the judges hear it. Slide titles should use the rubric's own words.*

**Slide A: "We didn't trust the data"** (the repo itself calls this our strongest
material)
- Missing values were hidden as `-999.25`: 7,410 readings in a file that
  reported zero nulls.
- GL-06 gas rates were recorded in m³/d under an Mscf/d header, so they were
  off by 28×.
- 5 sign flips, 2,513 duplicate rows, and a 4.5-hour outage on all 10 wells at
  once (2025-08-09, a data-recording system failure).
- **The test-mode trap:** during a well test the flow is routed to the test
  separator, so downstream wellhead pressure reads 19–29 psi lower than on
  normal days, on all 10 wells. Left untreated, this biases the daily
  predictions by about −3.8%. TODO(peers): the correction you chose.

**Slide B: "Physics first, validated honestly"**
- **VFM:** at this data size, a physics model of the choke beats machine
  learning: 1.82% error on liquid rate vs 2.93% for Ridge regression and
  3.80% for gradient boosting ⚠ (these are leave-one-test-out scores;
  replace them with the final time-forward score).
- The fitted exponents (S^2.05, ΔP^0.47) match the textbook choke law (2 and
  0.5), so the model learned real physics, not a curve fit.
- Per phase: oil 2.35%, water 3.25%, gas 5.33% ⚠.
- **Validation:** time-forward, never a random split. A random split leaks each
  well's rate level and scores about 4% no matter how bad the model is.
- **PTA:** 6 shut-ins found automatically. 4 wells never shut in, so PTA is
  impossible there, and we say so. Gauges are corrected to datum (they sit
  150–420 ft above it). Single-phase oil is justified because pressure stays
  above bubble point (GL-04: 2,269 vs 1,265 psia).
- Results table: TODO(peers), with m, k, skin and ΔP skin per event.

## 5. Who it is for (0:20)

*Template: be specific to the point of absurdity, profile the early adopters,
and say where you would hang the banner.*

- **User:** the production engineer responsible for a cluster of gas-lifted
  wells. TODO(you): which SOCAR fields or production units, how many such
  engineers, how many gas-lift wells.
- **Second user:** the reservoir engineer who interprets build-ups today in
  TODO(you): which tool?
- **Decision maker:** TODO(you), e.g. head of production or digital
  transformation.
- **Early adopter:** the field with the most wells per test separator.
  TODO(you): ask a mentor.
- **Banner:** TODO(you), e.g. the office where well-test schedules are planned.

**Do this today:** ask a SOCAR mentor two questions: "How do you get rates
between tests now?" and "How long does one build-up interpretation take you?"
One real quote beats any slide, and the template counts it as validation.

## 6. Value and deployment (0:30)

*Template: "business model". Show that it is sustainable and that the value
outweighs the cost.*

- **Model:** an internal service on a central server inside SOCAR's network.
  Engineers use a browser.
- **Costs:** one server, maintenance, and retraining as new well tests arrive.
- **Value** (pick two and attach a number to each):
  1. A daily rate for every well between tests → issues caught earlier, better
     allocation.
  2. Skin → barrels lost per day → a ranked list of stimulation candidates.
     TODO(peers): the $ figure from our PTA results.
  3. Fewer test-separator hours and fewer physical meters. TODO(you): what a
     multiphase meter or a well test costs at SOCAR.
  4. Engineer time: hours → minutes per analysis. Time it during the demo.
- **Consistency:** one model version for everyone, an audit trail, nothing to
  install.

## 7. Competition (0:20)

*Template: show that you know the alternatives and say how we are better. No
promises.*

| Alternative | Its weakness for this job | Our edge |
|---|---|---|
| Physical multiphase flow meters | Hardware on every well, plus calibration and maintenance | Uses the sensors already installed |
| Periodic well tests (status quo) | About one per well per month; no rate between tests | A rate every day |
| Commercial VFM software (TODO(you): vendors SOCAR uses) | Licence cost, and it stays separate from PTA | VFM and PTA in one flow |
| Commercial PTA suites (e.g. KAPPA Saphir; TODO(you): which SOCAR uses) | Manual, expert-only, needs a rate history from elsewhere | Shut-ins detected automatically; rates come from our VFM |
| In-house spreadsheets and scripts | Disconnected and not traceable | One flow, one model version, an audit trail |

## 8. Team (0:20)

*Template: incredibly important. Don't list "frontend dev"; say what ties each
of you to oil, gas and wells, and show the passion.*

| Name | Connection to oil, gas, wells | What they built here |
|---|---|---|
| TODO(you) | TODO(you) | Data cleaning, EDA, features |
| TODO(you) | TODO(you) | VFM physics benchmark |
| TODO(you) | TODO(you) | UI and pitch |

## 9. Call to action (0:10)

*Template: ask for something specific. It also shows you mean to make it real.*

- **Ask (draft):** "A 3-month pilot on TODO(you) N gas-lift wells: read access
  to the sensor data, one server inside SOCAR's network, and one production
  engineer as our counterpart."
- **Roadmap in one line:** prototype (today) → pilot (live data feed, company
  login) → field rollout.

---

## Q&A backup (3 min)

| Likely question | Short answer |
|---|---|
| Why not a random train/test split? | It leaks each well's rate level; any model scores ~4%. We validate time-forward. |
| 85 labels and 136 features: isn't that overfitting? | That's why physics wins here. Few parameters, strong regularisation. |
| Does it work on a new well? | Not out of the box. With 10 wells there isn't enough between-well data, so a new well needs a few tests to calibrate. Say it honestly. |
| Why PTA on daily rates? | The brief asks for it. We use per-minute pressure with the predicted rate before the shut-in. |
| Is single-phase valid? | Yes. Downhole pressure stays above bubble point on every well. |
| GL-02 and GL-06 build-ups are short. | 5.7 h and 8 h; radial flow may not develop. We flag those results as uncertain. |
| Gauge depth vs datum? | Corrected hydrostatically (150–420 ft) before Horner. |
| What about the 2025-08-09 outage? | All 10 wells dropped at once; it's flagged and we don't fill it in from other wells. |
| Deployment and security? | On-premises server, browser access, company login; the data never leaves SOCAR. |
| Test-mode pressure bias? | TODO(peers): the correction you chose and its effect. |

## Slide rules

- One idea per slide, with the number big.
- Slide titles use the rubric's own words: "VFM methodology", "PTA results".
- No product mention before the Solution slide.
- Every number on a slide matches the final results. Re-check the ⚠ items
  after the model is final.
