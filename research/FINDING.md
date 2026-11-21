# Findings from the research links

Every link in [`REF.md`](REF.md) was read on 2026-11-21. How much of each was
read is marked:

- **Full:** the whole page or paper was read.
- **Abstract:** paywalled; only the abstract was available.
- **Unverified:** the page is gone; described from search-engine snippets.

Quotes are verbatim. Anything marked *(inference)* is our reading, not the
source's.

---

## Takeaways for the pitch

1. **Nobody combines VFM and PTA on standard sensors.** Only SLB's
   intelligent-completion workflows estimate rates *and* run a "quicklook
   pressure transient analysis" for permeability and skin. That product
   requires SLB intelligent completions and downhole gauges. No source mentions
   virtual flow metering by name, Horner analysis, build-ups, automatic shut-in
   detection, ΔP skin, or gas-lift rate estimation.
2. **Every vendor that estimates rates needs new downhole hardware:** SLB
   intelligent completions, Baker Hughes fibre (SureVISION), or downhole
   flowmeters (SureFLO/SureSENS). That hardware costs **US$2–5 million per
   well** ("Most production wells in China cannot afford such a high cost";
   Ma et al., 2020). *(inference)* Our approach uses sensors already on the
   well, so the hardware cost is zero.
3. **A peer-reviewed source states our problem in its own words:** raw
   downhole-gauge data "cannot be directly used for reservoir modeling or
   interpretation with existing well test interpretation theory", so data
   processing is "indispensable" (Ma et al., 2020). This backs our
   data-cleaning story.
4. **Fragmentation is documented:** "Logging and control in traditional
   technology are two independent projects… leading to the inaccuracy" (Ma et
   al., 2020).
5. **Benchmark numbers vendors use (to match or beat on stage):**
   - SLB: analysis and decision time cut "by a factor of 10"; action in "a few
     days instead of months"
   - iFactory: "45-90 min" to build a well picture by hand vs "Under 2
     minutes"; "150-300" wells per engineer; "2-5 days" detection delay
   - QRI: "90%+" less time to value
   - Intelie: "35%" fewer field-engineering resources
6. **Nobody states on-premises deployment.** iFactory gives no model, IPT says
   cloud, SureVISION says edge-to-cloud, OFM says desktop or a cloud
   subscription. "Runs inside SOCAR's network" is a differentiator.
7. **AI claims are vague everywhere**, and the closest rival (SLB) makes none.
   A "physics-based and explainable" position stands out. H&P also markets
   "physics-based modeling … and machine learning", so the framing is credible
   in the industry.
8. **Even a vendor questioned whether the hardware pays off:** Baker Hughes
   authors titled a 2009 SPE paper "Intelligent Well Systems—Providing Value or
   Just Another Completion?". Ma et al. add: "we still can't guarantee that any
   intelligent well system can improve production stably and safely", and some
   wells have "an input-output ratio of less than 1".
9. **There is a direct precedent for our VFM idea:** SPE-115135-MS (2008)
   estimates split flow rates from downhole gauge data plus control-valve
   settings, the same principle as our choke-physics model (title only, not
   read).

10. **tNavigator, a teammate's reservoir-simulation suite, is a partner, not a
    rival.** It has no virtual flow metering and no automatic build-up/Horner
    analysis. It *uses* rates and well-test results to calibrate its models,
    which is exactly what we produce (see the tNavigator section below).
---

## Closest to our product: production analysis software

### SLB: production optimisation workflows for intelligent completions (Full) — closest competitor
- **What it is:** software workflows for wells with intelligent completions
  (downhole flow-control valves plus permanent gauges). Published 29 Jun 2023.
- **Does:**
  - consolidates "hundreds of channels of high-frequency data"
  - uses a proprietary simulator plus automated engines to estimate "zonal flow
    rates, fluid phases, drawdowns, productivity index"
  - back-allocation and water cut
  - downhole valve setting optimiser, gas-breakthrough detection
  - "Evaluate permeability and skin" with "quicklook pressure transient
    analysis for full history of production data"
- **Numbers:**
  - decision time cut "by a factor of 10 compared with conventional
    techniques"
  - action in "a few days instead of months"
  - case studies: Saudi Aramco in-lateral cleanup, "40% Incremental Oil"
    (Manara), "+15%" oil (Ecuador), a Caspian offshore paper (SPE-176648)
- **VFM:** yes (zonal rates, though never called VFM). **PTA:** yes,
  "quicklook" k and skin; no Horner, build-up or shut-in detection mentioned.
  **Gas lift:** no. **AI:** none claimed. **Deployment and price:** not
  stated; the data sheet requires an SLB login.
- *(inference)* Locked to SLB completion hardware. We work on any gas-lifted
  well's surface sensors, with automatic shut-ins, Horner k, skin and ΔP skin,
  and Excel and report export.

### SLB OFM: well and reservoir analysis software (Full, including product sheet)
- **What it is:** desktop and enterprise production-surveillance software.
- **Does:**
  - dashboards, GIS maps, exception reports
  - decline curves (Arps, Duong, power law, stretched exponential), P10/P50/P90
    type wells, waterflood voidage ratios
  - workflow catalogue (e.g. liquid-loading detection, workover candidates)
  - API; integrates with Avocet and Petrel
- **Customers:** PEMEX and AQP case-study titles; Bayerngas Norge managed
  services.
- **Deployment:** "local desktop and corporate repositories", "at the well
  site or in the office", or a subscription on Delfi.
- **VFM:** no. **PTA:** no. **Gas lift:** no. **AI:** none claimed.
- *(inference)* The closest match to our "surveillance app" framing, but it
  analyses rates it is given and doesn't estimate them. Our output could feed
  it.

### iFactory: AI-powered well performance dashboard (Full)
- **What it is:** marketing article for an analytics dashboard, Aug 2026.
- **Does:**
  - one view per well: rates against forecast and decline band, water cut
    against offset wells, GOR flags
  - ESP health score, rod-pump card analysis, chemical-dosing checks
  - connects to existing SCADA and manual well tests "without requiring new
    field hardware"
- **Numbers:**
  - "45-90 min" to assemble a well picture by hand vs "Under 2 minutes"
  - "4-7" systems checked per diagnosis; "150-300" wells per engineer
  - detection delay "2-5 days", or "four to six days" vs "within hours"
  - rollout "one to two weeks" (SCADA) to "four to six weeks" (full)
  - "over 1000+ clients"; no named customers
- **AI:** per-well baselines, automatic correlation, priority ranking, reads
  pump cards.
- **VFM:** no (it displays rates). **PTA:** no. **Gas lift:** no (ESP and rod
  pump only).
- *(inference)* It monitors the rates it is given; we compute them and
  interpret the reservoir.

### QRI SpeedWise Galaxy (Full)
- **What it is:** suite of AI apps for reservoir management and field
  planning: opportunity finder, unconventional forecasting, waterflood model,
  AutoML, automated decline curves, reservoir diagnostics,
  drilling/completion benchmarking, artificial-lift KPIs.
- **Numbers:**
  - "Saves 20% to 50% annually in CapEx/OpEx"
  - "90%+ reduction in the time spent to value creation"
  - waterflood surveillance for "over 500 MBBL/D"; "100+" reservoirs since 2013
  - 4 patents; no named customers
- **AI:** ML and deep-learning forecasts, AutoML "for anyone", "Augmented AI"
  (AI plus expert review).
- **VFM:** no. **PTA:** no. **Gas lift:** no (artificial lift names only ESP).
- *(inference)* Portfolio-level forecasting that consumes the per-well daily
  rates and test results we produce.

---

## Smart-completion hardware ("intelligent well" in the industry sense)

### Baker Hughes: well monitoring and analytics (Full, plus SureVISION, SureFLO, SureSENS pages)
- **What it is:** mostly downhole hardware: fibre optics, electronic gauges,
  downhole flowmeters, wet-mate connectors. One software product: SureVISION.
- **SureVISION:** turns fibre data into "physics-based flow allocation
  combined with AI-enhanced analytics", three-phase profiling, leak and
  crossflow detection; "edge-to-cloud", "no vendor lock-in".
- **SureFLO:** venturi and quartz downhole flowmeters, "accuracy of up to
  98%"; claims to eliminate production logs and surface well testing. Case
  study: "slashed costs by $65 million".
- **SureSENS:** quartz gauges, "a run life of more than 20 years"; its software
  "calculates flow based on the differential pressure measurements".
- **VFM:** partly, but only with fibre or downhole flowmeters. **PTA:** no.
  **Gas lift:** no (generic artificial lift).
- *(inference)* They get rates by installing hardware; we get them from
  existing surface sensors at near-zero capex, and add PTA.

### Halliburton: intelligent completions (Full, plus Clariti View)
- **What it is:** hardware and service: SmartWell completions, DataSphere
  permanent gauges, downhole valves, hydraulic and electric control systems.
  Clariti View is real-time gauge monitoring with alerts.
- **Claims (case-study titles):** triple-zone "10,000-psi" injection; a 12-zone
  SmartWell "doubles number of zones"; "Integrated solution doubles reservoir
  contact"; an offshore CCS project.
- **VFM:** no. **PTA:** no. **Gas lift:** no. **AI:** none.
- *(inference)* Hardware that produces data; we are the analysis layer on top
  of ordinary sensors.

### SLB: well completions software, category page (Full; "Load More" not expanded)
- **What it is:** SLB's completion software line: surface acquisition and
  control for intelligent completions, Petrel completion optimisation (with
  the Intersect simulator), the production workflows above, and liner
  installation planning.
- **Customers in case studies:** Saudi Aramco, Eni (Ivory Coast), XCL
  Resources (Uinta), a Peru ICD case; paper SPE-223842 (cloud optimisation of
  electric downhole valves).
- **VFM, PTA, gas lift on this page:** no. "Gas Lift", "Well Test Design and
  Interpretation" and "Surface Multiphase Flowmetering" appear only as SLB
  menu items. *(inference)* SLB sells these as separate products.
- *(inference)* Design and control software tied to SLB hardware; we are
  vendor-neutral.

---

## Off-target (a different problem)

### IPT Global: AI analytics for well integrity (Full; article, 29 Oct 2025)
- Promotes the SureTec well-integrity platform: digital schematics, barrier
  management, pressure testing, equipment health.
- AI claims: anomaly detection in pressure and temperature "faster and more
  accurately than manual analysis", auto-flagging across tests, predicting
  defective cement and corrosion before plug and abandonment. Cloud-based. No
  numbers or customers.
- **Not reservoir PTA.** "Pressure testing" here means barrier and integrity
  tests. No VFM, no gas lift.

### Geoactive Interactive Petrophysics (Full)
- Well-log interpretation software in modules: formation evaluation, borehole
  imaging, cased hole, geomechanics, geophysics, ML (curve repair, rock
  typing). A Petrosa petrophysicist calls it "the most user-friendly
  Petrophysical Interpretation package".
- No VFM, PTA or gas lift. "Formation testing" means formation-tester data,
  not well tests. No direct competition.

### H&P (Helmerich & Payne): Advanced Well Engineering / DrillScan (Full)
- Drilling engineering service (a team of "40+" engineers) using DrillScan
  software (torque and drag, bit, live advisory via REST APIs), plus a 24/7
  remote operations centre.
- **Numbers:**
  - "up to 50%" less RPM fluctuation; "~$25.4K per well" saved
  - customers with 10 wells "save an average of 24 days and over $1.5 million"
  - the FAQ contradicts some of these figures
- No VFM, PTA or gas lift. *(inference)* The useful parallel is its "physics +
  ML" marketing.

### Intelie 4.0: rigs and wells performance (Full)
- An "operational AI platform" (an Omni AI company) for drilling and frac:
  rig-state detection, KPI benchmarking, digital twin, frac-pump monitoring.
- **Numbers:**
  - "3,000+" Permian wells; "55M+ ft" drilled; "55" offshore rigs; "450+"
    frac pumps
  - "35%" fewer field-engineering resources
- Nothing on production. *(inference)* Its automatic rig-state detection is
  similar in spirit to our automatic shut-in detection.

### WellPro Software (Unverified: domain dead, no Web Archive copy)
- The domain no longer exists, and the Web Archive has zero captures. Search
  engines still index it as "WELLPRO - Advanced Software Solutions for the Oil
  Industry". Their snippets describe:
  - reservoir and production optimisation and real-time monitoring
  - classic inflow-performance and pipe-flow models (Darcy, Vogel, Joshi,
    Beggs & Brill)
  - PVT, sensitivity analysis, Venezuelan-fiscal NPV/IRR economics
  - "500+ active wells"
- Not confirmed. Unrelated companies share the name (UK, Nigeria, North Dakota).
- *(inference, if the snippets are right)* Nodal analysis plus economics; no
  rate estimation from live sensors and no automated PTA.

---

## Papers

### Review of intelligent well technology — Ma Huiyun et al., *Petroleum* 6(3), 2020, pp. 226–233 (Full)
Three links in REF.md point to **this one paper**: both ResearchGate entries
(337264934, 344783954) and the ScienceDirect article. Crossref lists the
ScienceDirect ID as an alias of DOI 10.1016/j.petlm.2019.11.003. Open access
(CC BY-NC-ND 4.0); authors from PetroChina Southwest and Southwest Petroleum
University.

- **Covers:**
  - the architecture of intelligent wells: downhole sensing, flow control,
    data transmission, surface data analysis
  - advantages and limits, foreign products, China's R&D, recommendations
- **Cost:**
  - imported systems "priced between US$2 million and US$5 million"
  - "nearly RMB 8 million" for a ~4,000 m well
  - break-even needs at least "68 t" of oil per day
  - some wells have "an input-output ratio of less than 1"
- **Adoption:**
  - first electro-hydraulic system, SCRAMS, in 1997
  - "27% per year" growth over the first 10 years
  - "more than 300" wells with complete systems
  - "tens of thousands" with partial technology (downhole monitoring or flow
    control)
  - permanent downhole gauges in use since the "1960s"
- **Reliability:** Shell targets a "10 years" life and "more than 95%"
  reliability. "We still can't guarantee that any intelligent well system can
  improve production stably and safely."
- **On PTA:** raw gauge data contain "abnormal points and noise, multiple
  stages of pressure rise and fall. Such data cannot be directly used for
  reservoir modeling or interpretation with existing well test interpretation
  theory." Prior methods: multi-step gauge-data processing, wavelet filtering,
  deconvolution, kernel ridge regression, Kalman-filter monitoring.
- **On rate estimation:** cites work that uses wavelets "to calculate unknown
  flow through downhole instantaneous pressure data", and Liu & Horne's
  kernel methods for interpreting pressure and flow together. These are
  academic precedents for VFM.
- **On workflow:** "Logging and control in traditional technology are two
  independent projects"; surface software must "summarize and screen" raw
  data "to help the user to clearly understand the downhole occurrence".
  Intelligent wells suit "gas lift wells".
- *(inference)* The strongest source for our problem slide: hardware costs
  millions, raw data can't be interpreted directly, and the tools are
  disconnected.

### Smart Well Completions: A Comprehensive Review of Technologies, Applications and Challenges — Khan et al., SPE-219507-MS, 2023 (Abstract)
- Ten authors from Mari Petroleum (Pakistan), SPE/PAPG PATS symposium,
  Islamabad, Nov 2023. DOI 10.2118/219507-MS. Paywalled everywhere tried
  (ResearchGate, OnePetro, SPE, CORE, arXiv).
- **Covers:**
  - how smart completions evolved; when to choose them (multilayered or
    compartmentalised reservoirs)
  - design and deployment challenges
  - applications: "auto gas lift, production optimization … remote
    operations"
  - fibre (acoustic and temperature) as a replacement for production logs
- No numbers in the abstract, and no mention of VFM or PTA.
- *(inference)* A recent operator view that names gas lift and real-time
  analysis as core uses, but frames the answer as hardware. That leaves room
  for a software layer.

### Intelligent Well Systems—Providing Value or Just Another Completion? — Sun, Constantine, Tirado, Eriksen, Costa (Baker Hughes), SPE-124916-MS, ATCE 2009 (Abstract)
- DOI 10.2118/124916-MS. Paywalled (OnePetro, CORE); no open copy found.
- **Covers:** five installed systems (gas producer, oil producer, auto-gas-lift
  oil producer, multilateral, horizontal multi-isolation). For each:
  - wellbore modelling, choking strategy, estimated performance
  - design-stage models compared against real-time data
  - lessons on flow modelling, erosion, tool selection
- **The question it asks:** "Was value realized by using an IWS?" Value comes
  from faster production, "managing production allocations", water control,
  recovery, and lower capex or intervention cost.
- **Related papers by the same group (titles only, not read):**
  - SPE-115135-MS (2008): estimating split flow rate from downhole real-time
    gauge data plus control-valve settings. A precedent for our choke-based
    VFM.
  - SPE-113416-MS (2008): downhole choking's effect on flow performance and
    production allocation.
- *(inference)* The value of downhole data depends on turning it into
  allocated rates, which is what our VFM does.

---

## Added later: tNavigator (Rock Flow Dynamics)

Sources: the screenshot [`tnavigator.jpeg`](tnavigator.jpeg) (a teammate's
install) plus vendor pages and public records, read on 2026-11-21. Every claim
below has a link in the research notes; the main ones are inline.

### What the screenshot shows (our own install)
- **Modules on the launcher:**
  - Geology Designer (static modelling)
  - Model Designer (pre/post-processing, dynamic and integrated modelling,
    field development planning)
  - Network Designer (surface facilities)
  - Simulation (black-oil, compositional, thermal, integrated)
  - AHM & Uncertainty (assisted history matching, uncertainty, optimisation)
  - Seismic, MBA (material balance), PVT Designer, Geosteering, RP Designer
    (relative permeability)
  - Well Designer (well modelling), Simulation Results, Fracture Simulator
- **Utilities:** Adviser, Manuals, Licenses, Batch Jobs, Remote GUI (cluster
  access). The toolbar is set to 16 threads, with a "Use GPU" option.
- **No well-test/PTA tile and no virtual-flow-metering tile.** The newer
  Reservoir Performance, Production Designer and Digital Asset modules are
  also missing. *(inference)* Either an older version or unlicensed modules;
  Help → About shows which.

### Company and product
- **Rock Flow Dynamics:** "Established in 2005"
  ([about](https://rfdyn.com/about/)); started in Moscow with Skolkovo grant
  support ([sk.ru 2017](https://sk.ru/news/fond-skolkovo-provel-biznesmissiyu-v-azerbaydzhanskoy-kompanii-socar/)).
  - Today it lists 33 offices, none in Russia; Budapest is marked "HQ"
    ([contact](https://rfdyn.com/contact/)).
  - Claims "330+ commercial clients across 47 countries" and 4 releases a
    year; the latest is 26.3, from 8 Oct 2026
    ([release](https://rfdyn.com/tnavigator-26-3-key-feautures/)).
- **What tNavigator is:** an "all-in-one solution for reservoir management…
  from seismic interpretation to surface network optimisation".
- **Licensing:**
  - "Rent, own, enterprise or SaaS cloud"
    ([rfdyn.com](https://rfdyn.com/)).
  - Local/network licence server, cloud licence server, or dongle; CPU and
    GPU; Linux and Windows
    ([licence brochure 2023](https://rfdyn.com/wp-content/uploads/2023/06/2023-tNavigator-License-Modules-web.pdf)).
  - Cloud runs on Azure or AWS, or on on-prem clusters.
- **Pricing:** none public. University donations were valued at US$320k for 2
  licences (KTU, 2022) and US$26.8M for WVU (2025, seat count not stated).
  These are valuations, not prices.

### Compared with our two halves
- **Build-up PTA (Horner, k and skin from build-ups):** no dedicated module
  found.
  - The closest is Reservoir Performance (decline curves and rate-transient
    analysis, Bourdet derivative, flowing material balance;
    [module](https://rfdyn.com/module/reservoir-performance/)).
  - Well-test data is only *consumed*: as an IPR input, and displayed on a
    cross-section tab.
  - In RFD's own Corrib case study, the transient analysis was done in a
    separate tool and kh and skin were then matched in tNavigator
    ([case](https://rfdyn.com/casestudies/opc-nephin-energy)).
- **Virtual flow metering:** not offered. Adjacent features:
  - Digital Asset, a real-time web dashboard over AVEVA PI
    ([25.3](https://rfdyn.com/tnavigator-25-3-key-updates-now-available/),
    [25.4](https://rfdyn.com/tnavigator-25-4-key-updates-now-available/))
  - Well Designer's choke pressure-drop correlation, with correlation
    selection "based on actual measurements" (26.3)
  - *(inference)* That's a building block for choke-based VFM, but it isn't
    sold as rate estimation.
- **Gas lift:** Well Designer offers "Gas lift design and optimisation" and
  VFP tables ([module](https://rfdyn.com/module/well-designer/)). Network
  Designer covers wells, pipes, chokes and compressors, with production
  optimisation.
- **ML:** neural-net and LSTM proxy models in AHM & Uncertainty, an LLM
  assistant, native Python.

### Azerbaijan
- **2017:** RFD presented tNavigator to SOCAR during a Skolkovo business
  mission in Baku. No contract or pilot was reported
  ([sk.ru](https://sk.ru/news/fond-skolkovo-provel-biznesmissiyu-v-azerbaydzhanskoy-kompanii-socar/)).
- **Baku job ads list tNavigator as a skill**, e.g. a Production Engineer
  role (Sep 2026: "Prosper, OFM, MBAL, tNavigator";
  [Airswift](https://www.airswift.com/jobs/production-engineer-sme-1280697)).
- **Not found:** any public SOCAR, Azneft or institute licence, or any use
  at a Baku university. Absence in search doesn't mean absence in practice.

### Procurement facts (sourced, neutral)
- **Ownership:** control of the UK entity moved from Russian nationals to a
  Cyprus holding in Apr 2023
  ([Companies House](https://find-and-update.company-information.service.gov.uk/company/08971422/persons-with-significant-control)).
  Russian sales run through a separate Russian company.
- **Sanctions:** no match on OpenSanctions for the company names (checked 21
  Nov 2026). This is not a legal screening.
- **Western and Gulf deals continue** (Adura unlimited licence; availability
  on AIQ's Genesis platform, ADIPEC 2026).

### What it means for us *(inference)*
Complementary. tNavigator is model-centric. Our daily oil, gas and water rates
feed its history matching, MBA, rate-transient analysis and network
calibration, and our k, skin and ΔP skin feed its well connections, the same
handoff as in the Corrib case. It would become a direct competitor only if RFD
added VFM to Digital Asset. On stage, stick to the capability comparison; don't
raise ownership.

---

## Search used

### Brave Search: "intelligent well performance analysis software and solutions"
The results lean toward smart-completion hardware, because in industry usage
"intelligent well" means downhole valves and gauges. Better terms for our
competitors: "virtual flow metering software" and "pressure transient analysis
software". The follow-up competitor search covers those.

---

## Coverage

| # | Link | Read |
|--:|---|---|
| 1 | SLB intelligent-completion workflows | Full |
| 2 | SLB OFM | Full, plus product sheet |
| 3 | iFactory dashboard | Full |
| 4 | QRI SpeedWise | Full |
| 5 | Baker Hughes monitoring and analytics | Full, plus 3 product pages |
| 6 | Halliburton intelligent completions | Full, plus Clariti View |
| 7 | SLB completions software | Full ("Load More" not expanded) |
| 8 | IPT Global article | Full |
| 9 | Geoactive IP | Full |
| 10 | H&P DrillScan | Full |
| 11 | Intelie | Full |
| 12 | WellPro | Unverified (dead, no archive) |
| 13–15 | Ma et al. 2020 (2× ResearchGate + ScienceDirect) | Full (one paper) |
| 16 | Khan et al. 2023, SPE-219507 | Abstract (paywalled) |
| 17 | Sun et al. 2009, SPE-124916 | Abstract (paywalled) |
| 18 | Brave search | Reviewed |
| 19 | tNavigator (teammate's screenshot + vendor pages) | Screenshot + web |
