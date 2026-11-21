# Hackathon2026
## Challenge: Intelligent Well Performance Analysis

## 1. Overview

Develop an interactive user interface that combines Virtual Flow Metering (VFM) and Pressure Transient Analysis (PTA) in a single workflow.

Production rates are not always directly available from field measurements. In such cases, Virtual Flow Metering can be used to estimate oil, gas, and water production from operational data. These estimated production rates can then be integrated with pressure-transient analysis to characterize reservoir behaviour and evaluate well performance.

The objective of this challenge is to build a user interface that guides users through the complete engineering workflow, from production-rate estimation to well-test interpretation and reservoir analysis.

## 2. Challenge Phases

### Phase 1 — Virtual Flow Metering

Virtual Flow Metering (VFM) is a technique that estimates the flow rates of oil, gas, and water from readily available sensor measurements, such as pressure, temperature, and choke position, instead of relying on physical multiphase flow meters. This improves production monitoring, supports allocation, and helps engineers detect issues earlier.

Using the provided data, develop a machine-learning model capable of predicting:

- Daily oil production rate
- Daily gas production rate
- Daily water production rate

### Phase 2 — Pressure Transient Analysis

Well-test interpretation is a technique used to estimate key reservoir characteristics by analyzing how a well's pressure responds to changes in its flow rate.
Although the Virtual Flow Metering model will predict oil, gas, and water production rates, for the purposes of this challenge the well-test interpretation should be done as a single-phase oil reservoir based exclusively on the predicted daily oil production rate (Qo).

Use the predicted production rate of oil together with pressure measurements to perform build-up test analysis from daily predicted data. Participants should create relevant plots and obtain reservoir properties: Horner plot slope, skin, permeability, delta P skin.


> **Note:** PTA tests are usually done usually done with well tests rather than high-frequency data; however, to connect the two parts of the challenge we ask you to do it on predicted daily oil rates.

### Phase 3 — Integrated User Interface

An integrated user interface brings the separate analytical modules together into one workflow, so engineers can move from raw field data to final interpretation without switching between tools. A well-designed application makes advanced modeling accessible to users who are not data scientists, and ensures that results are consistent, traceable, and easy to share.
The final deliverable must be an interactive application that combines both modules into a single, user-friendly interface.

The application should allow users to:

- Upload well data
- Visualize field measurements
- Use trained models
- Predict production rates using VFM
- Generate well-test plots
- Estimate reservoir properties
- Interpret reservoir behaviour
- Export results and reports for both parts

## 3. Dataset

The provided dataset consists of the following:

| Data source | Description |
| --- | --- |
| Well Testing Data | Periodic well tests measured oil, water and gas rates, the pressures, temperatures and gas-lift rate during each test, and fluid properties (API, gas SG, water salinity). |
| High-Frequency Data | Per-minute data for all wells, containing wellhead pressures, downhole pressure and temperature, annulus pressure and gas-lift rate. Raw, as recorded. |
| Choke Data | Additional data related to the choke settings and adjustments over time. |
| PVT Data | Rock and fluid properties for PTA: net pay, porosity, water saturation, total compressibility, wellbore radius, oil FVF, viscosity, bubble point, reservoir temperature, datum depth and drainage area. |
| Well completion data | Gauge and gas-lift valve depths, tubing size and choke size, lift-gas and fluid properties, and cumulative oil to 1 Jan 2025. |

Link to download the dataset: [SOCAR Hackathon 2026 Dataset](https://socaraz-my.sharepoint.com/:f:/r/personal/parvin_hajiyeva_socartech_az/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fparvin%5Fhajiyeva%5Fsocartech%5Faz%2FDocuments%2FDesktop%2Fdata&share=cgrdROBtVzKpTrKeEHsqe%2DC8EgUCSMXcCw1eZMpreaRSX0GixA)

## 4. Expected Deliverables

### Phase 1: Virtual Flow Metering

Use the provided dataset to develop a machine-learning model capable of predicting daily production rates.

**Deliverables:**

- Trained VFM model loaded inside the UI
- Excel with predictions for given high-frequent data: ‘date’, ‘well_name’, ‘oil_rate_stbd’, ‘water_rate_stbd’, ‘gas_rate_mscfd’

### Phase 2: Automated Well-Test Interpretation

Use the predicted daily oil production rate together with pressure measurements to perform build-up test analysis.

**Deliverables:**

- PTA plots: all relevant plots for each shut-in event accesible through UI
- Excel with estimated reservoir properties for each shut-in event: Horner plot slope, skin, permeability(md), delta P skin (psi)

### Phase 3: Integrated User Interface

Create an interactive application that combines the VFM and PTA modules into a user-friendly interface.

**Deliverable:**

- A fully functional UI that delivers the Phase 1 and Phase 2 deliverables through the interface

## 5. Evaluation Criteria

Scoring is out of 100 points across four categories:

| Criterion | Points |
| --- | ---: |
| **VFM** | **50** |
| **Auto PTA** | **30** |
| **UI** | **10** |
| **Presentation** | **10** |

### Score breakdown

- **VFM — 50 points**
  - Development methodology — 20 points
  - Prediction accuracy — 30 points
- **PTA — 30 points**
  - Required plots — 10 points
  - Parameter results — 20 points
- **UI — 10 points**
  - Functionality, usability — 4 points
  - Workflow — 6 points
- **Presentation — 10 points**
