# Competitors and similar work

Searched on 2026-11-21: vendors' own pages, trade press, SPE/OnePetro,
Semantic Scholar, arXiv and GitHub. How to read the marks:

- *(inference)*: our reading, not the source's.
- **[se]**: checked only through a search-engine excerpt of the vendor's own
  document (the vendor site blocked direct access).
- **[unverified]**: the primary source couldn't be opened.

Vendor accuracy claims are the vendors' own. No public software pricing exists
anywhere; every vendor quotes on request.

---

## Bottom line for the pitch

1. **No commercial product combines our two halves:** a choke-model VFM for
   gas-lifted wells, calibrated on well tests, *plus* automatic shut-in
   detection and Horner k, skin and ΔP skin, in one workflow. The nearest are:
   - **KAPPA-Automate:** automatic build-up detection and incremental PTA. Its
     pressure-only "Virtual Meter mode" takes rates from the reservoir model,
     with no choke or gas-lift physics and no well-test calibration, and it
     needs an expert to seed the first analysis.
   - **Petex DOF + IPM:** Horner/MDH in IVM plus online gas-lift models in IFM.
     That's three or more products to integrate.
   - **Xecta:** shows shut-in analysis and a virtual meter in an SPE webinar;
     whether they ship as product features is unverified.
   - **Weatherford and SLB:** own every piece, but as separate products.
   - **AutoWell:** an academic research workflow (SPE-218470), not a product.
2. **SOCAR already uses three KAPPA products** under a contract from about
   2023 (which three is not public). Pitch us as **complementary to KAPPA**:
   an operations-level daily workflow, with rate histories that can feed
   KAPPA. Don't pitch a replacement.
3. **Other vendors already at SOCAR:** Baker Hughes Leucipa at Azneft (about
   100 wells, pump monitoring), a Honeywell partnership and framework
   agreement, SAP UFAM "Digital Field", and SLB on Bahar/Gum Deniz. We found
   **no public record of VFM or multiphase meters at SOCAR**.
4. **The literature backs our method.** Hotvedt et al. (2022), on 10 wells
   trained on well tests only: physics-informed models do best "in the
   presence of little data", and copying the last test "outperforms nearly
   all models". That is our finding exactly. Be ready for the counterexample:
   with dense multiphase-meter data, data-driven models catch up (Hotvedt et
   al., 2022, gray-box paper).
5. **Linking VFM and PTA is defensible maths** *(inference, from the Horner
   equations)*:
   - A rate error ε passes one-to-one into permeability k.
   - Skin moves by only about −0.5ε; our 2.6% error shifts s by about 0.013.
   - ΔP skin barely moves, because the slope m comes from pressure alone.
   - So skin and ΔP skin from VFM rates are robust, and k inherits the VFM
     error.

6. **tNavigator (Rock Flow Dynamics) is complementary.** It's a reservoir
   simulation suite (a teammate has it installed). It has no VFM and no
   automatic build-up/Horner analysis; it consumes rates and well-test results
   for history matching. RFD presented it to SOCAR in 2017 (no public
   contract), and Baku job ads ask for it. Our rates and k/skin are inputs to
   it. See `FINDING.md` → tNavigator.

### Slide lines (inference)
1. "Multiphase meters: about US$100–250k each, plus up to 25% to install
   (Shell/PDO). Ours: US$0 hardware, using the sensors and well tests
   you already have."
2. "Olga Online, LedaFlow, METTE and Acuity are full simulators built for
   offshore networks. Ours is a choke model calibrated on your well tests, set
   up per well, not per project."
3. "ML VFMs (Solution Seeker, SLB with Dataiku) learn from data, without
   physics. Ours is physics-first and explainable, on your own server, with no
   cloud dependency."
4. "KAPPA-Automate automates build-ups but gets rates from the reservoir
   model. Ours links gas-lift rates and build-ups for the same well in one
   view."
5. "SLB and Weatherford own every piece, spread across 3–4 products. Ours is
   one browser workflow: sensors → daily rates → k, skin, ΔP skin → Excel."

### Numbers for the problem slide
1. **Test frequency.** Alberta's regulator (AER Directive 017, Sep 2026)
   requires at least 3 tests per month for oil wells above 30 m³/d, and even
   then allows 5–40% monthly volume uncertainty. Our wells average about
   1,450 bbl/d (about 230 m³/d, so Class 1) and get about 1 test per month
   *(inference)*. Lower classes need fewer: 6–30 m³/d needs 2 a month, and
   2–6 m³/d (the average SOCAR well, about 4 m³/d) needs 1.
2. **Meter cost.** A multiphase meter costs "between 100 and 250 kUS$" (PDO
   paid 100–150k), and implementation can "run as high as 25%" of the hardware;
   a test separator costs US$0.8–1.5M ([Scheers et al., Shell/PDO, NSFMW 2002](https://nfogm.no/wp-content/uploads/2019/02/2002-16-Multiphase-Flow-Metering-per-Well-can-it-be-justified-Scheers-Shell.pdf), 2002 dollars).
3. **Value of finding skin.** PETRONAS (SPE-199253, 2020) screened 750 well
   strings and found 101 candidates; 28 jobs added +6,500 bopd. Success rate
   rose from 55% to 73%, and screening time fell from 2 weeks to 1 day.

### Risks for Q&A
- **Dataset size.** 85 tests on 10 wells. If the hackathon data is synthetic,
  recovering the choke law may partly reflect how the data was generated.
  Frame it as a physics-consistency check, not proof that physics always wins.
- **KAPPA's relationship with SOCAR.** Never position against KAPPA.
- **Pooling.** If our physics model shares its exponents across wells, part of
  the gain may come from pooling across wells, which is what Hotvedt's best
  multi-task model also does.

---

## 1. Commercial: virtual flow metering software

| Vendor / product | What it does | PTA | Gas lift | Approach | Deployment | vs us *(inference)* |
|---|---|---|---|---|---|---|
| SLB [Olga Online](https://www.slb.com/products-and-services/delivering-digital-at-scale/software/olga-online) | Olga transient simulator on live data: virtual metering, leak detection, look-ahead. Equinor Johan Sverdrup Phase 3 award, Sep 2026 ([SLB](https://www.slb.com/newsroom/features/2026/2026-0916-slb-equinor-johan-sverdrup)) | N | not stated | First-principles transient | Web-accessible | Heavyweight offshore network twin |
| SLB + Dataiku [VFM solution](https://www.dataiku.com/solutions/catalog/virtual-flow-meter-slb/) | Rate across the choke from THP, FLP and gas-lift injection, calibrated on well tests uploaded in Excel | N | **Y** | "Empirical approach, combined with AI" | Inside Dataiku | Closest to our VFM; no PTA; needs Dataiku |
| SLB/Cameron [Modum Flow](https://www.slb.com/well-production/production-systems/metering-and-automation-systems/modum-flow) | A choke that "approximates production rates from pressure and temperature", recalibrated with well tests | N | N | not stated | Cameron choke + SCADA | Means replacing the choke; ours uses the existing one |
| SLB [OptiFlow](https://www.slb.com/products-and-services/delivering-digital-at-scale/software/optiflow) | Production assurance that integrates "virtual flow meters for minute-level intelligence" | N | not stated | Physics + AI | Cloud and edge | Enterprise platform |
| Weatherford [MetaFlow](https://intelligence.weatherford.com/metaflow-metering-platform) | Hybrid IPR/nodal physics + ML on P, T and choke. Real-time rates on Permian/Anadarko gas-lift and ESP wells ([case 2025](https://intelligence.weatherford.com/hubfs/000%20-%20Industrial%20Intelligence%20Update/Real%20Results%20PDFs/Accurate%20Real-Time%20Flow%20Rates%20Achieved%20for%20Gas%20Lift%20and%20ESP%20Wells%20with%20Virtual%20Flow%20Metering.pdf?hsLang=en)) | N | **Y** | Hybrid | not stated | **Strongest direct gas-lift VFM rival**; no PTA |
| TechnipFMC FlowManager ([poster 2025](https://nfogm.no/wp-content/uploads/2025/08/Poster-7-One-pager_-TechnipFMC_Ronnevig.pdf)) | VFM, meter surveillance and backup, flow assurance | N | not stated | First-principles | Onshore/offshore hosting | Subsea and meter-backup focus |
| Falkor (Kongsberg Digital, [rebranded 2026](https://www.kongsberg.com/news/news-archive/2026/kongsberg-digital-rebrands-as-falkor-a-kongsberg-company/)) [LedaFlow](https://falkor.com/products/ledaflow) / K-Spice | Transient multiphase simulator; lists VFM as an application | N | not stated | Physics | not stated | Simulator-grade |
| AspenTech [METTE](https://aspentech.com/ja/resources/data-sheet/aspen-mette-datasheet) (formerly Roxar) | "Web-based application" estimating oil, gas and water from real-time sensors | N | not stated | First-principles | Web | General production modelling |
| KBC (Yokogawa) Acuity VFM ([brochure](https://www.kbc.global/resources/downloads/kbc-acuity-virtual-flow-meter.pdf) [se]) | Near-real-time oil, gas and water rates; integrates with Petro-SIM and Multiflash | N | not stated | Physics | Yokogawa Cloud, SaaS ([launch](https://www.automation.com/en-us/products/october-2023/kbc-acuity-industrial-cloud-suite-digital)) | Cloud-only; may clash with NOC data rules |
| ABB + Arundo VFM ([2018](https://new.abb.com/news/detail/54064/abb-delivers-virtual-flow-meters-powered-by-arundo-analytics) [se]) | Cloud VFM on existing P, T and flow sensors | N | not stated | Analytics | Cloud | Current status unverified |
| Turbulent Flux FLUX ([NFOGM](https://nfogm.no/wp-content/uploads/2024/06/9-Self-adjusting-Real-time-Virtual-Flow-Metering-TurbulentFlux-Vanvik.pdf), [JPT](https://jpt.spe.org/hybrid-approach-to-virtual-flow-metering-combines-physics-and-machine-learning-modeling)) | Self-adjusting hybrid VFM, "<5% full-scale"; on Aker BP Valhall via [Cognite](https://www.cognite.com/en/customer-stories/dataops-oil-gas-turbulentflux-well-monitoring) | N | not stated | Hybrid | Cloud (Cognite) | North Sea offshore |
| Solution Seeker [ProductionCompass AI](https://solutionseeker.no/products-and-solutions/flow-rates/) | Neural-net VFM with "no built-in knowledge of physical laws", trained on 2,000 wells; [Reservoir Pressure](https://solutionseeker.no/products-and-solutions/reservoir-pressure/) module "Coming soon" | Planned | not stated | Pure ML | not stated | Black box; watch their reservoir-pressure module |

Older first-principles VFMs named in the Bikmukhametov & Jäschke review
(Table 1): Olga Online, K-Spice Meter, FlowManager, ABB WMS, Wood Virtuoso,
Roxar FieldWatch + METTE, Belsim ValiPerformance, and BP's in-house Rate&Phase.

## 2. Commercial: well-test and pressure-transient software

| Vendor / product | What it does | VFM | Gas lift | Deployment | vs us *(inference)* |
|---|---|---|---|---|---|
| KAPPA [Saphir](https://www.kappaeng.com/software/saphir/overview) | "Industry standard PTA": Bourdet derivative, Horner/MDH, deconvolution, analytical and numerical models | N | N | Runs inside KAPPA-Workstation | Expert tool; we give operations engineers routine Horner results |
| KAPPA [KAPPA-Server](https://www.kappaeng.com/software/ks/overview) | Permanent-gauge surveillance; "Shut-in detection is now fully automated… 24x7"; wavelet filtering; passes data to Saphir | N | N | Client-server | Overlaps our shut-in detection |
| KAPPA [KAPPA-Automate](https://www.kappaeng.com/software/ka/overview) | Automatic build-up detection, incremental PTA (skin per new shut-in), RTA. "When only pressure is available, rates will be generated in Virtual Meter mode" | Partly (rates from the reservoir model) | N | Browser client, containerised (on-prem vs cloud not stated) | **Closest competitor.** Needs an expert seed; no choke or gas-lift VFM |
| Weatherford PanSystem ([2015 brochure](https://www.weatherford.com/documents/brochure/products-and-services/formation-evaluation/well-test-design-and-analysis-services)) | Well-test analysis used by Weatherford's experts | N | N | Current status unverified | Legacy expert tool |
| SLB [WellTest](https://www.slb.com/products-and-services/delivering-digital-at-scale/subsurface/welltest-pressure-transient-analysis-software) | Drawdown, build-up and falloff PTA; test design; history matching | N | N | not stated | Expert tool |
| SLB Harmony Enterprise ([brochure](https://commodityinsights.spglobal.com/rs/325-KYL-599/images/Harmony%20Enterprise%20Brochure.pdf) [se]) | Rate-transient analysis on flowing pressure; reserves | N | N | not stated | Rate-transient only, no build-up PTA |
| Petex [IVM](https://www.petex.com/products/digital-operations-framework/ivm/) | Surveillance and automated well-test tracking; "Built-in Horner and MDH plots" trending P*, skin, k, PI; "contact Petex for a personalised quote" | Not named | not stated | "Accessible via the intranet or internet" | Second-closest (see section 5) |

Harmony and WellTest moved from S&P Global to SLB: the sale was announced in
Apr 2026 ([S&P](https://press.spglobal.com/2026-04-24-S-P-Global-Announces-New-Strategic-Direction-for-Upstream-Energy-Business))
and closed on 1 Sep 2026 ([close](https://press.spglobal.com/2026-09-01-S-P-Global-Completes-Divestiture-of-Upstream-Energy-Software-Portfolio-to-SLB)).

## 3. Commercial: production surveillance and engineering platforms

| Vendor / product | What it does | VFM | PTA | Gas lift | vs us *(inference)* |
|---|---|---|---|---|---|
| Petex [PROSPER](https://www.petex.com/products/integrated-production-modelling-suite/prosper/) / [GAP](https://www.petex.com/products/integrated-production-modelling-suite/gap/) | Nodal analysis; gas-lift design and a transient gas-lift simulator; network optimiser (an Oman case cut gas-lift use by 25%) | Indirect | N | Y | Model-building tool, not a daily workflow |
| Petex [IFM](https://www.petex.com/products/digital-operations-framework/ifm/) | Runs IPM models online; "on-line analysis and quality control of field production tests"; sends setpoints to the field | Not named | N | Case studies only | Heavy integration project |
| SLB PIPESIM ([2026.1](https://www.software.slb.com/software-news/software-top-news/pipesim/pipesim-2026-1)) | Gas-lift design and allocation; new calibration of up to 10 parameters against well tests | Indirect | N | Y | Engineering tool, not monitoring |
| SLB [Avocet](https://www.slb.com/products-and-services/delivering-digital-at-scale/software/avocet) | Production data management, well-test validation, allocation ([KOC case](https://www.slb.com/resource-library/case-study-with-navigation/so/cs-avocet-koc-kuwait)) | N | N | N | Data layer, not analytics |
| Sensia Automated Gas Lift ([brochure](https://sensiaglobal.com/Sensia/media/General/Auto-Gas-Lift-Brochure.pdf) [se]) | Three configure-to-order tiers; a virtual flowmeter feeds a PIPESIM model. An Asian NOC case lists a VFM workflow ([case](https://sensiaglobal.com/Sensia/media/General/Maximizing-Production-with-Intelligent-Gas-Lift-Optimization_338A-DS-0125-CS_Case_Study_DIGITAL.pdf) [se]) | Y | N | Y | Most complete gas-lift package; no PTA; SaaS, cloud **or on-prem**; tied to the SLB stack |
| Weatherford ForeSite / CygNet | Gas-lift optimisation: 27 of 88 wells optimised, about $1.2M opex saved ([case](https://www.weatherford.com/real-results/production/foresite-injection-rate-optimization-and-gas-lift-analysis-achieves-25-higher-production,-a-$1-2m/) [se]); CygNet 9.9 well-test module ([2025](https://weatherford.com/blog/cygnet/april-2025/announcing-cygnet-v9-9) [se]) | Via MetaFlow | N (PanSystem is separate) | Y | Has all the pieces, in separate products |
| Baker Hughes [Leucipa Lift Optimizer](https://www.bakerhughes.com/oilfield-services-and-equipment-digital/leucipa-automated-field-production-solution/leucipa-services/leucipa-lift-optimizer) | Field-wide lift optimisation including gas lift; "physics-based modeling with advanced AI" | Not stated | N | Y | **Already at Azneft** |
| Halliburton [Digital Field Solver](https://www.halliburton.com/en/software/decisionspace-365-enterprise/decisionspace-365-reservoir-and-production/digital-field-solver.html) | Real-time monitoring and diagnostics, automatic well-model calibration, physics + AI | Not stated | N | Artificial-lift design | Cloud (iEnergy) |
| Honeywell UPP Suite ([brochure](https://process.honeywell.com/content/dam/process/en/documents/document-lists/Honeywell-HPS-UPPS-Brochure.pdf) [se]) | Process control on wells, including gas-lift optimisation | Not found | N | Y | SOCAR partner; an integration target, not a rival |
| AVEVA [PI System](https://www.aveva.com/en/industries/oil-gas/upstream/) | Historian; customers build their own well-test workflows on it ([ExxonMobil 2021](https://www.aveva.com/en/perspectives/presentations/2021/simplifying-the-well-test-process-with-pi-asset-framework/)) | N | N | N | A data source for us |
| [Xecta](https://xecta.com) | "Fusion of AI & Physics", cloud-native. An SPE webinar ([deck](https://file.streaming.spe.org/wp-content/uploads/2024/02/22133737/Data-Driven-Discovery-of-Physics-for-Reservoir-Surveillance-with-Application-to-PTA.pdf)) shows automated shut-in analysis, average reservoir pressure, PI and a "Virtual meter for flow rates". BPX pilot on 441 gas-lift/ESP wells ([SWPSC 2026](https://www.swpshortcourse.org/paper/2026051-pilot-test-continuous-production-optimization-using-digital-solution-permian-basin) [se]) | Y (method; product unverified) | Partial (unverified) | Y (pilot) | Closest in concept; US unconventional, cloud |
| Rock Flow Dynamics [tNavigator](https://rfdyn.com/) | All-in-one reservoir suite: geology, simulation, history matching and uncertainty, MBA, Well Designer (gas-lift design, choke correlations calibrated on measurements), Network Designer, Reservoir Performance (DCA/RTA), Digital Asset (real-time PI dashboard). Licence: rent, own, enterprise or SaaS; CPU/GPU; on-prem or Azure/AWS | N (choke correlations only) | N (RTA only; well tests consumed) | Y (design) | **Complementary**: needs the rates and k/skin we produce; would compete only if it added VFM |

## 4. The hardware alternative: physical multiphase meters

- **Makers and products:**
  - SLB [Vx Spectra](https://www.slb.com/products-and-services/innovating-in-oil-and-gas/reservoir-characterization/reservoir-testing/surface-testing/surface-multiphase-flowmetering/vx-spectra-surface-multiphase-flowmeter) (surface) and [Vx Omni](https://www.slb.com/videos/vx-omni) (subsea)
  - Emerson [Roxar 2600](https://www.emerson.com/en-us/automation/measurement-instrumentation/flow-measurement/multiphase-meters). Emerson itself says "Fiscal metering typically still requires single-phase meters or separators".
  - TechnipFMC MPM
  - Weatherford [ForeSite Flow](https://intelligence.weatherford.com/intelligent-surveillance) (no radioactive source)
  - Pietro Fiorentini [Flowatch](https://www.fiorentini.com/en/solutions/products/products-oil-and-natural-gas-production/multiphase-flow-metering/flowatch-3i/)
  - Haimo (third-party listing)
- **Cost:**
  - "between 100 and 250 kUS$" per meter (PDO paid 100–150k); implementation
    up to +25% of hardware; test separator US$0.8–1.5M plus US$20–80k a year.
    Source: [Scheers et al., Shell/PDO, NSFMW 2002](https://nfogm.no/wp-content/uploads/2019/02/2002-16-Multiphase-Flow-Metering-per-Well-can-it-be-justified-Scheers-Shell.pdf), read in
    the primary source. 2002 dollars; no current public list prices. (The
    US$100–500k figure on Wikipedia is a looser restatement; don't use it.)
  - ARC Advisory: testing, installation, maintenance and calibration add "25
    percent, 50 percent, or more" ([ARC](https://www.arcweb.com/node/35856)
    [se]).
  - Vendor cases: up to US$550k capex saved per pad
    ([SLB Torxen](https://www.slb.com/resource-library/case-study-with-navigation/rpin/vx-spectra-torxen-canada-cs));
    US$98k per well
    ([SLB Uinta](https://www.slb.com/zh-cn/resource-library/case-study-with-navigation/rpin/surface-multiphase-flowmeter-enhances-flow-assurance-uinta-basin)).

## 5. Anything that combines VFM and PTA

**No commercial product does both for gas-lift wells.** The nearest:
1. **KAPPA-Automate:** shut-in detection, incremental PTA, and a pressure-only
   virtual meter. Its rates come from the reservoir model (no choke or gas-lift
   physics, no well-test calibration), and it needs an expert seed.
2. **Petex IVM + IFM + PROSPER/GAP:** Horner k, skin and P* plus online
   gas-lift models. "Virtual metering" isn't named; three or more products.
3. **Xecta:** both appear in an SPE webinar; packaging unverified.
4. **Weatherford** (MetaFlow, ForeSite, PanSystem) and **SLB** (PIPESIM,
   OptiFlow, WellTest, Avocet): every piece exists, but in separate products.
5. **AutoWell (research):** a published VFM → transient detection → PTA chain.
   See section 8.

**tNavigator** does neither: it has rate-transient analysis but no build-up
PTA, choke correlations but no VFM. It consumes both kinds of result.

## 6. SOCAR and Azerbaijan (public sources)

- **KAPPA:** SOCAR uses three KAPPA products under a contract from about 2023.
  KAPPA also has a preliminary PTA-focused deal with the Umid-Babek operator
  and expects BP and JOCAP contracts (Nov 2025,
  [Report.az](https://report.az/en/energy/france-s-kappa-reaches-preliminary-deal-on-software-supply-with-umid-babek-field-operator)).
  Khazar University has 25 academic KAPPA licences
  ([Khazar](https://khazar.org/en/news/7607)).
- **Baker Hughes Leucipa** at Azneft: about 100 wells initially, pump
  monitoring; gas lift not mentioned (Feb 2025,
  [Trend](https://www.trend.az/business/4004953.html)).
- **Honeywell:** a five-year partnership covering asset performance management,
  training simulators and digital twins (Mar 2026,
  [Trend](https://www.trend.az/business/4163191.html)), followed by SOCAR's
  first Global Framework Agreement, which covers software supply (Nov 2026,
  [ChemXplore](https://chemxplore.com/news/socar-honeywell-global-framework-agreement)).
- **SAP UFAM "Digital Field":** consolidated production data and a live well
  map (Apr 2020,
  [AZERTAC](https://azertag.az/en/xeber/socar_launches_digital_field_project_based_on_sap_ufam-1470517)).
- **SLB:** Bahar and Gum Deniz redevelopment (Oct 2025,
  [Caspian Post](https://caspianpost.com/energy/socar-slb-join-forces-to-accelerate-redevelopment-of-caspian-sea-oil-fields)).
- **Halliburton:** residual-oil study on Gunashli (Sep 2024,
  [Report.az](https://report.az/en/energy/socar-signs-agreement-with-us-company)).
- **Rock Flow Dynamics (tNavigator):** presented to SOCAR during a 2017
  Skolkovo business mission; no contract reported
  ([sk.ru](https://sk.ru/news/fond-skolkovo-provel-biznesmissiyu-v-azerbaydzhanskoy-kompanii-socar/)).
  Baku job ads list tNavigator as a skill (2023, 2026). No public SOCAR
  licence found.
- **Scale (SOCAR Annual Report 2024):** 52.4% of SOCAR's oil is gas-lifted
  (64.6% at Azneft); 5,715 operating wells. See section 12.
- **Not found:** any public record of VFM or multiphase-meter use at SOCAR.

---

## 7. Research: virtual flow metering

**A. Physics wins when labels are scarce (supports our result)**
- **Hotvedt, Grimstad, Imsland: "Passive learning to address nonstationarity
  in VFM"**, *Expert Systems with Applications* 2022
  ([arXiv 2202.03236](https://arxiv.org/abs/2202.03236)). Full text read.
  - 10 wells, six model types, trained on well tests only.
  - Average MAPE: linear regression 37–44%, neural net 31–41%, mechanistic
    choke model 18–22%, hybrids 12–24%, multi-task net 10–12%.
  - "VFM model types with physical considerations seem to offer the best
    performance in the presence of little data."
  - A "last observed rate" benchmark "outperforms nearly all models".
  - **This is the closest published match to our findings.**
- **Grimstad, Hotvedt, Sandnes et al.: "Bayesian neural networks for VFM"**,
  *Applied Soft Computing* 2021
  ([arXiv 2102.01391](https://arxiv.org/abs/2102.01391)).
  - 60 wells; 1–2 tests per month.
  - Median data-driven error is 4–6% on a historical hold-out but **8–13% on
    the next 3 months**. Non-stationarity is "the most concerning" challenge.
  - The same time-forward degradation we see with Ridge.
- **Hotvedt et al.: "When is gray-box modeling advantageous for VFM?"**, IFAC
  DYCOPS 2022 ([arXiv 2110.05034](https://arxiv.org/abs/2110.05034)).
  Gray-box beats data-driven with little data, and beats pure physics when
  the model is mis-specified.
- **Bikmukhametov & Jäschke: "First principles and ML VFM: a literature
  review"**, *JPSE* 2020, about 160 citations
  ([DOI](https://doi.org/10.1016/j.petrol.2019.106487),
  [preprint](https://jaschke.folk.ntnu.no/preprints/2020/Bikmukhametov_JPSE/VFM-Review.pdf)).
  - The canonical review: industry VFM is mostly first-principles, and
    choke-model VFMs are common.
  - In one field case a tubing model "showed a less accurate performance than
    the choke model".
  - BP's Rate&Phase runs at under 5% error on more than 300 wells.
- **Akhiiartdinov, Krier, Ibarra et al.: hybrid VFM**, OTC 2023
  ([DOI](https://doi.org/10.4043/32505-MS)). Six Gulf of Mexico subsea wells,
  tested about twice a year; tuned tubing and choke equations reach within 10%
  MAPE. Notes that tuning to the latest test biases predictions toward it.
- **Shekhawat et al.: data-driven choke correlation for VFM and well-test
  optimisation**, ADIPEC 2025 ([DOI](https://doi.org/10.2118/230118-MS)).
  Gilbert choke coefficients re-fitted to well tests give daily rates and rank
  wells for testing. **Nearly our method**, but no PTA and naturally flowing
  wells only.
- **Mursaliyev: VFM in the Kashagan field**, SPE Caspian 2018
  ([DOI](https://doi.org/10.2118/192592-MS)). A vertical-lift physics VFM
  within ±5% of span. **A regional (Caspian) precedent.**
- **Amin: evaluation of commercial VFMs**, OTC 2015
  ([DOI](https://doi.org/10.4043/25764-MS)). Commercial physics VFMs reach
  under 5% error on oil and under 10% on gas. Our 2.56% oil sits inside that
  band *(inference)*.

**B. Hybrid physics plus ML is best**
- **Bikmukhametov & Jäschke: "Combining ML and process engineering physics"**,
  *Computers & Chemical Engineering* 2020, about 180 citations
  ([DOI](https://doi.org/10.1016/j.compchemeng.2020.106834)). Physics features
  improve both accuracy and interpretability.
- **Challiwala et al.: physics-guided neural net through field chokes**,
  ADIPEC 2026 ([DOI](https://doi.org/10.2118/235952-MS)). Trained on lab data
  with Sachdeva, Perkins and Bernoulli choke models as features: 12.0% vs
  19.6% MAPE for Modified Sachdeva. A plain neural net "failed to generalize".
- **Bukhari et al.: self-calibrating physics-informed VFM**, ADIPEC 2026
  ([DOI](https://doi.org/10.2118/235867-MS)). Volve data; monotone XGBoost
  with choke-area and ΔP features cuts mean absolute error by 78% vs Gilbert.
- **Al-Qutami et al. (Petronas): multimodal physics + ML VFM**, IPTC 2022
  ([DOI](https://doi.org/10.2523/IPTC-22431-MS)). Two-well, 6-month pilot,
  about 50% better than any single VFM.
- **Henriksson & Yang (Turbulent Flux): hybrid VFM**, JPT 2021
  ([link](https://jpt.spe.org/hybrid-approach-to-virtual-flow-metering-combines-physics-and-machine-learning-modeling)).
  Under 5% full-scale error (vendor claim).

**C. Counter-evidence (raise it before the judges do)**
- **Hotvedt et al.: "On gray-box modeling for VFM"**, *Control Engineering
  Practice* 2022 ([arXiv 2103.12513](https://arxiv.org/abs/2103.12513)).
  - The same shape as our problem: 10 wells, a choke-only model,
    time-forward on the last 3 months. But it has **dense multiphase-meter
    labels**.
  - Mechanistic 17.2%, data-driven 10.4%, best hybrid 10.3%; per-well range
    1.8–40.6%.
  - With plentiful labels, physics no longer wins.
- **Løvland, Grimstad, Imsland: few-shot VFM**, 2023
  ([arXiv 2309.15828](https://arxiv.org/abs/2309.15828)). A net pretrained on
  80 wells reaches under 5% median error on a new well after 3 data points.
  ML can work with few labels, but only with a big multi-well prior, which we
  don't have *(inference)*.
- **Other ML-favourable results**, all with dense or random-split labels or
  many wells *(inference)*:
  - Sandnes et al. 2021, multi-task learning
    ([arXiv 2103.08713](https://arxiv.org/abs/2103.08713)): error cut 25–50%
    on difficult assets.
  - Al-Qutami et al. 2018, neural-net ensemble
    ([DOI](https://doi.org/10.1016/j.eswa.2017.10.014)): 1.5% gas, 4.2% oil,
    4.7% water.
  - Dabiri et al. 2024, *Scientific Reports*
    ([DOI](https://doi.org/10.1038/s41598-024-54010-2)): ML 5.2% vs untuned
    Gilbert 19–22%, on a random split.
  - D'Souza et al. 2025, LSTM on two simulated gas-lift wells
    ([link](https://ecp.ep.liu.se/index.php/sims/article/view/1072)):
    1.6–2.0%.

**D. Gas-lift specific**
- **Davila et al. (ADNOC): well-test advisory system with VFM**, ADIPEC 2024
  ([DOI](https://doi.org/10.2118/222914-MS)). Pilot on 10 gas-lifted
  producers with Palantir, delivered in 3 months. Cites "high uncertainty on
  well allocation factors, especially for gas lifted wells". **Very close to
  our setting.**
- **Bloemen et al.: soft sensing for gas-lift wells**, SPE 2006. Extended
  Kalman filter; cited in the Bikmukhametov review [unverified].

**E. Anchors for our fitted choke exponents**
- Published Gilbert-type choke-size exponents run 1.63–2.275 (Gilbert 1.89,
  Ros 2.0; Table 1 of Dabiri 2024). Those correlations assume critical flow,
  where rate doesn't depend on downstream pressure.
- Our d^2.06 and ΔP^0.47 match **subcritical** orifice/Bernoulli flow:
  Sachdeva 1986 ([DOI](https://doi.org/10.2118/15657-MS)) and Perkins 1993
  ([DOI](https://doi.org/10.2118/20633-PA)).
- Hotvedt 2020 ([arXiv 2002.02737](https://arxiv.org/abs/2002.02737)) is a
  precedent for a hybrid choke model whose flow coefficient comes from a
  neural net.

## 8. Research: automated PTA and the VFM → PTA link

- **Shchipanov, Cui, Starikov, Muradov et al. (NORCE / Heriot-Watt, AutoWell
  project): "A new automated workflow for well monitoring using permanent
  pressure and rate measurements"**, SPE-218470-MS, 2024
  ([DOI](https://doi.org/10.2118/218470-MS),
  [JPT](https://jpt.spe.org/automated-workflow-uses-pressure-rate-measurements-for-well-monitoring-restricted)).
  - Chains VFM, transient identification, pattern recognition and PTA
    metrics; validated over 3 years on a Norwegian Continental Shelf
    *injector*.
  - **The closest prior art to our chain.** *(inference)* Our differentiators:
    gas-lifted producers, a choke-physics VFM, and an operational UI.
  - Related NORCE papers:
    - PTA metrics for automated monitoring (SPE-214425, 2023,
      [DOI](https://doi.org/10.2118/214425-MS))
    - automatic shut-in and multi-rate transient detection (Cui et al.,
      *Geoenergy Sci. Eng.* 2025, [DOI](https://doi.org/10.1016/j.geoen.2025.214203))
    - time-lapse pattern recognition (Starikov et al. 2024,
      [DOI](https://doi.org/10.1016/j.geoen.2024.213160))
- **Camilleri et al. (SLB): converting ESP real-time data into flow rate and
  reservoir information**, SPE-176780, 2015
  ([DOI](https://doi.org/10.2118/176780-MS)). Estimated rates are used to
  track reservoir pressure and skin without dedicated tests. The same idea,
  for ESP wells.
- **Ursini, Rossi, Castelnuovo, Perrone: benefits of virtual meter
  applications**, SPE-196654, 2019 ([DOI](https://doi.org/10.2118/196654-MS)).
  Virtual meter plus real-time PTA; meter rates seed the build-up analysis
  and PTA helps calibrate the meter [unverified detail; Eni affiliation
  unverified].
- **Shut-in and transient detection:** Athichanagorn, Horne, Kikani 2002,
  *SPE REE*, wavelet detection on permanent-gauge data
  ([DOI](https://doi.org/10.2118/80287-PA)).
- **ML on permanent-gauge data:** Tian & Horne 2019, *SPE REE*, kernel and RNN
  models that reconstruct missing rate history from pressure
  ([DOI](https://doi.org/10.2118/174034-PA)).
- **Deep-learning type-curve and model identification:**
  - Dong et al. 2021 *JPSE* ([DOI](https://doi.org/10.1016/j.petrol.2021.109264)):
    1D CNN, 97% classification
  - Liu et al. 2020 *JPSE* ([DOI](https://doi.org/10.1016/j.petrol.2020.107618)):
    CNN, Daqing field
  - Li et al. 2020 ([DOI](https://doi.org/10.1016/S1876-3804(20)60079-9))
  - Chu et al. 2019 *Energies* ([DOI](https://doi.org/10.3390/en12152846)):
    21 of 25 field cases classified correctly
  - Allain & Horne 1990 ([DOI](https://doi.org/10.2118/18160-PA)): early AI
    work
- **Rate uncertainty in PTA:**
  - von Schroeter, Hollaender, Gringarten: deconvolution with total least
    squares, which explicitly allows rate errors (SPE 2001,
    [DOI](https://doi.org/10.2118/71574-MS))
  - Botsas et al. 2020: Bayesian deconvolution that infers the true rates
    jointly ([arXiv 2012.03217](https://arxiv.org/abs/2012.03217))
- **How a rate error moves the Horner results** *(inference, from the
  standard equations)*:
  - k = 162.6·q·B·μ/(m·h), so a relative rate error ε passes one-to-one into k.
  - Skin s moves by about −0.5ε (a 2.6% rate error shifts s by about 0.013).
  - ΔP skin = 0.869·m·s barely moves, because m comes from pressure alone.

## 9. Open-source tools (licences from the GitHub API)

The hackathon rules forbid licences that force derived software to be
licensed to others, so GPL is out.

| Tool | Use | Licence |
|---|---|---|
| [pta-learn](https://github.com/vitaliistarr/pta-learn) (NORCE/AutoWell) | Shut-in detection, Bourdet derivative, derivative uncertainty, rate-error metric | Apache-2.0, OK |
| [welltest-pta](https://github.com/geoharkat/welltest-pta) | Event detection, Horner/MDH, Bourdet, k and skin, deconvolution | MIT, OK (new, immature) |
| [neqsim](https://github.com/equinor/neqsim) (Equinor) | PVT and process (valves) | Apache-2.0, OK |
| [fluids](https://github.com/CalebBell/fluids) / [thermo](https://github.com/CalebBell/thermo) / [CoolProp](https://github.com/CoolProp/CoolProp) | Two-phase flow, valve sizing, fluid properties | MIT, OK |
| [unifloc_vba](https://github.com/unifloc/unifloc_vba) | Choke, gas-lift and well models (Excel/VBA) | MIT, OK |
| [PressureDrop.jl](https://github.com/jnoynaert/PressureDrop.jl) | Gas-lift pressure profiles (Julia) | Apache-2.0, OK |
| [petbox-dca](https://github.com/petbox-dev/dca), [equinor/decline-curve-analysis](https://github.com/equinor/decline-curve-analysis) | Decline curve analysis | MIT, OK |
| [petrobras/3W](https://github.com/petrobras/3W) | 3W dataset toolkit | Apache-2.0, OK |
| [HVFM](https://github.com/mmmahhhhe/HVFM) | Code for a 2024 hybrid VFM paper | MIT, OK |
| [welltestpy](https://github.com/GeoStat-Framework/welltestpy) / [AnaFlow](https://github.com/GeoStat-Framework/AnaFlow) | Hydrogeology pumping tests (not Horner) | MIT |
| [khabibullinra/welltest_examples](https://github.com/khabibullinra/welltest_examples) | Well-test course code | BSD-3-Clause |
| [pyResToolbox](https://github.com/mwburgoyne/pyResToolbox) | Reservoir engineering utilities | **GPL-3.0, avoid** |
| [OPM](https://github.com/OPM/opm-simulators) | Reservoir simulation | **GPL-3.0, avoid** (MRST also GPL [unverified]) |
| [ManyWells](https://github.com/solution-seeker-as/manywells) | Simulator and data | **CC BY-NC 4.0, non-commercial** |
| [Andrianov VFM](https://github.com/nikolai-andrianov/VFM), [jshiriyev/production-data-analysis](https://github.com/jshiriyev/production-data-analysis) | VFM scripts; production data analysis | **No licence (all rights reserved)** |

## 10. Datasets and competitions

- **Datasets:**
  - **Volve** (Equinor, 2008–2016): daily per-well volumes, choke, wellhead
    and downhole pressure ([page](https://www.equinor.com/energy/volve-data-sharing)).
    The Equinor Open Data Licence isn't an OSI or Open Definition licence
    ([critique](https://agilescientific.com/blog/2018/10/16/volve-not-open-after-all)).
  - **3W** (Petrobras): Vargas et al. 2019, *JPSE*, about 116 citations
    ([DOI](https://doi.org/10.1016/j.petrol.2019.106223),
    [repo](https://github.com/petrobras/3W)). Labelled undesirable events,
    not phase rates. Licence unclear (CC BY 4.0 per UCI, MIT in the old repo).
  - **ManyWells** (Solution Seeker,
    [Hugging Face](https://huggingface.co/datasets/solution-seeker-as/manywells)):
    2,000 simulated wells including lift gas. CC BY-NC 4.0.
  - **D'Souza et al. 2025** ([dataset](https://doi.org/10.18710/KIJEWJ)): two
    simulated gas-lifted subsea wells. CC0.
  - **UK NSTA daily well data** for ceased fields
    ([announcement](https://www.nstauthority.co.uk/news-publications/daily-well-production-figures-will-help-mer-uk-and-net-zero-goal/)).
    Licence not stated.
- **Competitions:**
  - [SPE Africa Datathon 2025](https://jpt.spe.org/twa/spe-africa-region-datathon-2025-drives-collaboration-innovation-and-industry-impact):
    anomaly classification from GOR, water cut and PI.
  - [SPE-GCS ML Challenge 2021](https://jpt.spe.org/generating-shear-sonic-logs-by-machine-learning-lessons-learned-from-a-competition):
    sonic logs.
  - A Honeywell hackathon on ManyWells, evidenced only by a
    [GitHub repo](https://github.com/OM-HASE/Honeywell-Hackathon) [unverified].
  - No Kaggle competition on VFM or PTA found.
- **SOCAR and Azerbaijan hackathons:**
  - [SOCAR Hackathon 2025](https://azertag.az/en/xeber/socar_holds_hackathon_2025_with_microsoft_as_official_partner-3922267):
    with Microsoft, Dec 2025; AI and data engineering tracks (handwritten
    data to email, seismic data restoration).
  - [Energy & 4IR hackathon](https://www.economy.gov.az/en/post/875/enerji-ve-dorduncu-senaye-inqilabi-hakatonunun-qaliblerine-mukafatlar-teqdim-edilib):
    SOCAR + C4IR, Sep 2022.
  - [Energy Ministry + SOCAR Energy & AI hackathon](https://azertag.az/en/xeber/azerbaijans_energy_ministry_socar_organize_energy_and_ai_hackathon-4486827):
    11 Dec 2026, energy-consumption data.
  - None of these covered VFM or PTA, so the topic is new for SOCAR events
    *(inference)*.

## 11. Industry evidence for the problem

- **How often wells are tested:**
  - [AER Directive 017](https://static.aer.ca/prd/documents/directives/Directive017.pdf)
    (Sep 2026), Table 6.1: oil wells above 30 m³/d need at least 3 tests per
    month of 12 h each; 6–30 m³/d need 2; 2–6 m³/d need 1; stripper wells need
    one per quarter. Even then, allowed monthly uncertainty is 5/10/20/40% by
    class.
  - Field practice: 1–2 tests per month (Grimstad 2021); gaps of over a
    month, the longest over a year (Hotvedt 2022); about 2 per year in the
    Gulf of Mexico (Akhiiartdinov 2023).
- **Value of VFM:** ADNOC edge-AI autonomous testing with a hybrid VFM (Ahmed
  et al., ADIPEC 2026, [DOI](https://doi.org/10.2118/235251-MS)):
  - 10–15% fewer physical tests, 50% fewer failed tests
  - about 3× testing throughput, about 200 h per month saved
- **Value of skin and stimulation-candidate screening:** PETRONAS, SPE-199253
  (2020) ([DOI](https://doi.org/10.2118/199253-MS)):
  - 750 strings screened → 101 candidates → 28 jobs → +6,500 bopd
  - success rate 55% → 73%; screening time 2 weeks → 1 day
- **Lost production from skin:** flow efficiency = (ln(re/rw) − 0.75) /
  (ln(re/rw) − 0.75 + s) ([SLB glossary](https://glossary.slb.com/terms/f/flow_efficiency)).
  With re/rw = 1000, a skin of 5 costs about 45% of rate *(inference)*.

## 12. What the problem costs

Checked 2026-11-21. Labels: **[P]** read in the primary source; **[S]** read
in a secondary source or snippet only; **[V]** vendor claim; *(inference)*
our own arithmetic.

**Deferred production and late detection**
- **NSTA (UK regulator), Aug 2026 [P]:** one percentage point of production
  efficiency = "21,000 additional boe per day … more than 7.5 million boe" in
  a year. Fields ran at 76%, so about 24% of potential wasn't produced
  ([link](https://www.nstauthority.co.uk/news-publications/industry-boosts-efficiency-to-deliver-millions-more-barrels-from-existing-fields/)).
  In 2021, "Production losses increased by 25% to a total of 176 million
  barrels of oil equivalent"
  ([PE 2021](https://www.nstauthority.co.uk/media/qogllhu3/ukcs-pe-2021.pdf)).
- **PDO (Oman), SPE-214005-MS, 2023 [P, abstract]:** in a field with 2,200+
  producers, unscheduled subsurface deferment reached "3.7% of total field
  potential" (about 3,800 bbl/d). The "global (1%) top quartile" is the
  benchmark, and the field later cut deferment to 0.8%.
- **Wood Mackenzie, 2014 [P]:** deepwater Gulf of Mexico wells were "online
  on average only 79% of the time"; "less than a 10% change in producing days
  … as much as a 15% change in NPV"
  ([link](https://offshore-mag.com/production/article/16757122/offline-wells-reduce-value-in-us-deepwater-gulf)).
- **Shell (OGJ 2009) [P]:** a well test covers "about 1% of the time", and the
  flow is assumed unchanged for the other "99% of the time". *(inference)*
  With monthly tests, a problem stays hidden for about 15 days on average.
- **Downtime surveys [V]:**
  - GE/Kimberlite 2016: about 27 days of downtime a year, costing
    "$38 million" or "$49 million" (the paper contradicts itself)
  - Siemens/Senseye 2022: "almost $500,000" per hour of downtime in oil and
    gas
  - SLB/PEMEX: anomaly detection on 2,100+ wells cut deferred production by
    "around 30%"

**Measurement and allocation error**
- **NEL (UK national flow lab), NFOGM 2014 [P]:** on 20,000 bbl/d at $50,
  "1% → Loss of $10,000 per day"; a 0.1% bias on 500,000 bbl/d = "$7,500,000
  per annum misallocation"
  ([PDF](https://nfogm.no/wp-content/uploads/2016/08/5-MacGillivray-A-Stockton-P-Using-uncertainty-analysis-to-optimise-allocation-Measurement-system-performance.pdf)).
  *(inference)* At today's $92 that's about $18,000 a day.
- **Sadri & Shariatipour, ASME JERT 2020 [P] (simulation):** a 36-well,
  ~193,000 stb/d field at $60/bbl. Testing weekly instead of monthly cuts
  misallocation by **$27–80M a year**. *(inference)* That's a proxy for what
  continuous VFM rates are worth.
- **Shell, OGJ 2009 [P]:** a well-test allocation factor "averages about
  0.88"; on an FPSO, "the old method gave allocation factors which erred 4% on
  the high side".
- **Shell/PDO, NSFMW 2002 [P]:** a "+2% in the watercut measurement" cost
  about "380,000 US$/year" on one 500 m³/d well, at about $16/bbl.

**Skin and gas lift**
- **PETRONAS, SPE-199253 (2020) [P, abstract]:** 750 strings → 101 candidates
  → 28 jobs → +6,500 bopd (about 230 bopd per job); success rate 55% → 73%;
  screening time from two weeks to one day.
- **Skin arithmetic** *(inference)*: at the same drawdown, skin +5 cuts rate
  by about 40%, and skin +10 by about 57%.
- **Gas-lift optimisation:**
  - ExxonMobil (URTeC 2024) [S]: ">5%" uplift on a 30-well pilot; "average 7%
    increase" across 200+ wells
  - ONGC Mumbai High (SPE 123799) [P]: +2,000 bopd from 160 wells, with up to
    6% possible field-wide
  - Rockwell [V]: gas-lift inefficiency explains "up to 5% of production
    shortfall"
- **Cost of testing (Scheers, Shell/PDO 2002, 2002 dollars) [P]:**
  - test separator US$0.8–1.5M, plus US$20–80k a year to run
  - multiphase meter US$100–250k
  - test flowlines US$200–400k per km

**SOCAR scale (SOCAR Annual Report 2024 [P])**
([PDF](https://socar.jobs/mediafiles/reports/illik-hesabatlar/en/SOCAR_ANNUAL_REPORT_2024_rUz4KJ5.pdf))
- **52.4%** of SOCAR's oil comes from gas lift (3,921.7 kt). At Azneft it's
  **64.6%** (3,872.5 kt).
- Well stock: 7,610 wells, 5,715 operating. *(inference)* That's about 26
  bbl/d per operating well; our hackathon wells average about 1,450, so they
  aren't typical of SOCAR.
- 2025 output: 7.1 Mt (about 142,600 bbl/d, *inference*).
- **Prices:** Brent "$91.98" (20 Nov 2026); Azeri Light CIF "$97.62" (19 Nov
  2026, [Trend](https://trend.az/azerbaijan/4248155.html)).

**Worked example** *(inference)*: Brent $91.98, 365 days, 7.33 bbl/t, gross
revenue before PSA split and costs. Deferred barrels are partly recovered
later, so treat these figures as revenue at risk.

| Scope | Rate | 1% lost per year | 5% lost per year |
|---|---|--:|--:|
| Our 10 wells | ~14,500 stb/d | **$4.9M** | **$24.3M** |
| SOCAR gas-lifted oil (2024) | ~78,800 bbl/d | **~$26M** | **~$132M** |
| SOCAR total (2025) | ~142,600 bbl/d | **$47.9M** | **$239M** |

- **Single event:** one well loses 20% of 1,450 bopd unseen for 15 days
  (half a monthly test interval). That's 4,350 bbl, about **$0.4M**.
- **Why 1–5% is a defensible range:** 1% is the top-quartile deferment
  benchmark (PDO); 1.5% is the VFM gain in an SLB Ecuador case [V]; 5–7% is
  the documented gas-lift optimisation gain.
- **Not found:** mobile test-unit day rates, a field-wide statistic on the
  share of damaged wells, SOCAR's count of gas-lift wells, and a published
  average detection delay.

---

## Still unverified
- PanSystem's current status; whether the ABB VFM is still sold.
- How Xecta packages its product.
- Most vendors' on-prem vs cloud options.
- Which three KAPPA products SOCAR uses.
- tNavigator: whether Reservoir Performance can do a Horner build-up; whether SOCAR holds any licence; who ultimately owns its Cyprus holding.
- All vendor accuracy claims (e.g. Turbulent Flux's "<5%").
- The Ursini et al. (SPE-196654) details and affiliation.
