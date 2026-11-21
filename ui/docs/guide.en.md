## How to use

**RizzML** turns the sensor data of gas-lifted wells into a daily oil, water and gas rate for every
well (virtual flow metering, **VFM**), and reads every shut-in as a pressure build-up
(pressure transient analysis, **PTA**).

1. **Sign in** with your SOCAR email. You can change the language here and later in **Settings**.
2. **Load Data.** Drop in the raw files, CSV or Excel. The checklist under the upload box turns green
   for each file it recognises. Or click **Sample Data** on Home to run the hackathon field.
3. **Run analysis.** Cleaning, rate prediction and well-test analysis take about 30 seconds for
   10 wells over 9 months. You land back on Home and the tiles unlock.
4. **Read the results.** Every page has the menu on the left.
   - **Production Rates:** daily oil, water and gas per well. Dots are measured well tests, when the
     upload includes them.
   - **Well Tests:** every shut-in with permeability, skin, ΔP skin, Horner slope and flow efficiency,
     a plain-language interpretation, and the Horner, log-log and pressure-history plots.
   - **Generate Graph:** any chart from the results: trend, cross-plot, distribution, histogram or a
     comparison of wells. Its data downloads as CSV.
   - **Field Data:** the cleaned sensor history per well, shut-ins shaded.
   - **Data Quality:** what the cleaning found and fixed.
5. **Export:** rates and PTA results as CSV or Excel, one workbook with everything, and an HTML report
   with every chart.
6. **History** keeps your uploads, analyses and downloaded files, to open or download again later.
   **Convert** turns any CSV into Excel and back.

## Your data

| File | Needed | What it holds |
|---|---|---|
| `high_freq_data` | yes | Per-minute sensors: `timestamp`, `well_name`, `whp_psia`, `whp_downstream_psia`, `dh_pressure_psia`, `dh_temperature_degf`, `annulus_pressure_psia`, `gas_lift_rate_mscfd` |
| `choke_events` | yes | Choke changes: `timestamp`, `well_name`, `choke_opening_pct` (0% = shut in) |
| `reservoir_pvt` | yes | One row per well: pay thickness, porosity, compressibility, wellbore radius, oil FVF and viscosity, bubble point, datum, drainage area |
| `well_completion` | yes | One row per well: gauge depth, gas-lift valve, tubing size, manifold, solution GOR, cumulative oil |
| `well_tests` | no | Measured test rates. Adds an accuracy check against them |

- A file is recognised by its name: it only has to contain `high`, `choke`, `pvt`, `completion`
  or `test`.
- Excel files are read from their first sheet. Up to 1 GB per file.
- Cleaning is automatic: the missing-value code −999.25, duplicate rows and sensor spikes. Data Quality
  shows how many of each.

## How it works

**Rates (VFM).** A physics model, not a black box.

- The liquid rate follows the choke-flow law: choke size, pressure drop across the choke, wellhead
  pressure and gas-liquid ratio.
- The tubing pressure drop splits it into oil and water; gas follows from the solution gas-oil ratio.
- Fitted to the 85 measured well tests, the model found the textbook choke law on its own: choke size
  to the power 2.06 and pressure drop to the power 0.47 (textbook: 2 and 0.5).
- It beat machine learning on this data. With only 85 measured rates, physics generalises better.
- Well tests read about 2.5% high against normal production days (the test separator runs at a
  lower pressure), and the daily rates are corrected for it.

**Well tests (PTA).** Shut-ins are found where the choke is at 0%. For each build-up:

- a Horner analysis finds the radial-flow straight line;
- a model of the well (wellbore storage, skin, radial flow, closed or infinite boundary) is then
  fitted to every point of the build-up and gives the reported permeability and skin;
- the oil rate used is the predicted daily rate before the shut-in.

The downhole gauge sits above the datum. The offset is constant through a build-up, so it cancels in
permeability, skin, slope and ΔP skin. Only p\* is shown at both gauge and datum.

**Accuracy.** Each measured test predicted only from earlier data:

| Phase | Error (MAPE) | Volume-weighted (WAPE) | R² |
|---|---|---|---|
| Oil | 2.56% | 2.33% | 0.998 |
| Water | 3.82% | 3.48% | 0.996 |
| Gas | 5.65% | 4.61% | 0.994 |

The PTA model matches each build-up to within 0.03–0.08 psi (RMS).

**Limits.**

- A well the model was not trained on gets the field average, and the app flags it. Its rates are not
  reliable until a few well tests calibrate it.
- Only wells that were shut in get a well-test analysis.
- The build-up analysis assumes single-phase oil. That holds here: pressure stays above the bubble point.
- Sign-in is a demo account, not real authentication yet.

## Glossary

| Term | Meaning |
|---|---|
| VFM | Virtual flow metering: rates estimated from sensors instead of a test separator or a meter |
| PTA | Pressure transient analysis: reservoir properties read from how pressure changes, here during a shut-in |
| Shut-in, build-up | The choke closes, flow stops and downhole pressure rises |
| Permeability (k, md) | How easily oil flows through the rock |
| Skin (S) | Extra pressure loss near the wellbore. Positive: damaged. Negative: stimulated |
| ΔP skin (psi) | The pressure lost to skin |
| Flow efficiency | The share of its undamaged potential the well achieves |
| Horner plot, slope m | Pressure against log((tp + Δt) / Δt). The straight part gives m, and m gives k |
| p\* | Pressure extrapolated to an infinitely long shut-in |
| Log-log, Bourdet derivative | Diagnostic plot. A flat derivative means radial flow |
| MAPE, WAPE, R² | Average % error, volume-weighted % error, share of variation explained |
| Water cut, GOR | Water share of the liquid; gas per barrel of oil |
| stb/d, Mscf/d, psia | Stock-tank barrels a day, thousand standard cubic feet a day, absolute pressure |

## Troubleshooting

| What you see | What to do |
|---|---|
| A file stays grey in the checklist | Its name must contain `high`, `choke`, `pvt`, `completion` or `test`. Rename it |
| "The data could not be analysed" | A required column is missing or renamed. Compare with **Your data** |
| Sample Data is locked | The sample sensor file is missing on the server. Run `git lfs pull` there |
| A well has no Well Tests result | It was never shut in: its choke never reached 0% |
| "Not in the trained model" | A new well. Its rates use the field average |
| A page asks to load data first | Run an analysis, or reopen one from **History** |
| The page reloads after a theme change | Expected. You come back to the same page with your results |
| Uploading is slow | The per-minute file is about 260 MB. Upload over the office network |
