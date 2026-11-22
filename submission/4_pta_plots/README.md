# PTA plots — Phase 2 (deliverable 4: all PTA plots)

Everything in this folder is produced by one script. The submitted result file comes from a second script that reuses the same functions:

```bash
python ml/eda/pta_explore.py   # ~60 s: the figures and reference tables in this folder
python ml/make_pta.py          # ~25 s: ml/outputs/pta_submission.csv + pta_results.xlsx (the scored answer)
```

Both need `data/processed/high_freq_clean.parquet`.

**The submitted answer is the exact model match.** It scored **8.3840 / 20**, the best of the PTA submissions. The Horner straight-line results for windows A and B are kept as the hand-calculation reference and for comparison.

## Files

| File | What it shows |
|---|---|
| `pta_00_theory_flow_regime_atlas.png` | **Theory.** Analytical log-log type curves (Δp and Bourdet derivative) from Laplace solutions with Stehfest inversion, for six reservoirs: homogeneous infinite-acting (WBS → hump → IARF); closed circle, drawdown vs build-up (PSS unit slope vs derivative falling to p̄); constant-pressure boundary; one sealing fault (derivative doubles); channel (½ slope); dual porosity (valley). Reference for reading the real derivatives. |
| `pta_01_theory_skin_storage_hump.png` | **Theory.** Same storage, skin −2 / 0 / 5 / 12. The storage hump grows with C_D·e^(2S) while the IARF level does not move, which is why k from the IARF level is skin-free. Negative skin is modelled with the effective wellbore radius. |
| `pta_02_overview_six_buildups_loglog.png` | All six real build-ups on one page. Dots are measured Δp and derivative; lines are the model match; window A is shaded. Each panel gives the regime diagnosis, the model's k, S and m, and the fit RMS. |
| `pta_10_GL-01_2025-04-15_buildup_all_plots.png` | GL-01, 72 h shut-in. Closed boundary: the derivative falls after ~5 h and pressure plateaus near 3511.5 psia (p̄). Model: closed circle, r_e 1367 ft. |
| `pta_10_GL-02_2025-03-08_buildup_all_plots.png` | GL-02, 5.6 h shut-in. Short; the derivative is still settling onto the IARF level when the test ends. |
| `pta_10_GL-04_2025-06-03_buildup_all_plots.png` | GL-04, 48 h shut-in. Cleanest wellbore-storage unit slope and the largest hump (lowest kh/μ). |
| `pta_10_GL-06_2025-07-22_buildup_all_plots.png` | GL-06, 8 h shut-in. Short. |
| `pta_10_GL-08_2025-08-19_buildup_all_plots.png` | GL-08, 72 h shut-in. Infinite-acting for the whole test; the textbook case. |
| `pta_10_GL-10_2025-05-27_buildup_all_plots.png` | GL-10, 9 h shut-in. Short and boundary-affected: the derivative keeps falling. Model: closed circle, r_e 1048 ft. |
| `pta_reference_model_match.csv` | The submitted model-match results at full precision: k, S, ΔP_skin, m, storage C, r_e, fit RMS and max residual, both boundary fits, the Horner-B comparison and `der_B_over_iarf`. |
| `pta_reference_window_A.csv` | Horner results per shut-in, window A (IARF plateau). |
| `pta_reference_window_B.csv` | Horner results per shut-in, window B (late IARF points). |

Every `pta_10_*` figure has six panels, all built from the same data:

- **A. Pressure history** around the shut-in (gauge depth), with the rate used.
- **B. Cartesian build-up**, measured p_ws vs Δt with the model match overlaid, and p* from window A.
- **C. Log-log diagnostic.** Measured Δp and Bourdet derivative (dots); model Δp and Δp′ (lines). Also shown: a unit-slope (WBS) guide and the IARF level m/2.303 of the submitted slope (dashed). Window A is grey and window B hatched.
- **D. Horner plot**, p_ws vs (t_p+Δt)/Δt, with two straight lines:
  - the radial-flow line implied by the submitted k, S and m. Its slope is the submitted `horner_slope`, and Horner's skin formula applied to it returns the submitted skin exactly;
  - the window-A least-squares line, for comparison.
- **E. MDH plot**, p_ws vs log Δt.
- **F. Results table:** Horner A, Horner B and the model match (submitted). The subtitle repeats the submitted values.

## Inputs and conventions

| Item | Choice |
|---|---|
| Pressure | `dh_pressure_psia` at **gauge depth**, 1-minute data. The cleaning step leaves every build-up window untouched (checked minute by minute). Noise ≈ 0.03 psi; no segregation humps. |
| Δt = 0 | the `choke_events.csv` shut-in timestamp; pressure starts rising in the first minute |
| p_wf(Δt=0) | last flowing gauge reading at the shut-in minute |
| Rate q | VFM **oil** rate of the shipped Task 1 file (`ml/outputs/submitted/lam0.80_21.0200_SHIPPED.csv`, λ = 0.80) on the **last full flowing day** before the shut-in. The brief asks for single-phase oil on predicted Qo, so k is the effective oil permeability. |
| N_p, t_p | N_p = `cum_oil_at_2025_01_01` + VFM daily oil up to the shut-in; t_p = 24·N_p/q (Horner pseudo-producing time) |
| Derivative | Bourdet, L = 0.10, with respect to ln of the Agarwal time t_p·Δt/(t_p+Δt), on a 40-points-per-cycle log grid |
| **Model match (submitted)** | The radial diffusivity equation with wellbore storage C, skin S, permeability k and an outer boundary (infinite, or a closed circle of radius r_e). It is solved in Laplace space and inverted with Stehfest (N = 12), code in `ml/src/pta_model.py`. ln k, S, ln C (+ ln r_e) are fitted by least squares to every log-grid point, seeded from Horner B. The closed circle is kept only when it cuts the RMS misfit by more than 30% (GL-01, GL-10). Reported: m = 162.6·q·B·μ/(k·h), ΔP_skin = 0.869·m·S. |
| **Window A** | longest run after the storage hump where the derivative's log-slope is within ±0.10. If shorter than 0.3 log-cycle, the flattest 0.3 cycle is used and the row is flagged. |
| **Window B** | the last 0.3 log-cycle of the window-A plateau. With no boundary these are the last points of the build-up, the furthest from wellbore storage. Where a boundary bends the derivative down, the last points are in the p̄ regime, not IARF, so B stops where the plateau stops. With no plateau, B = A (flagged). |
| Horner → k, S | k = 162.6·q·B·μ/(m·h); S = 1.151·[(P1hr − p_wf)/m − log10(k/(φ·μ·c_t·r_w²)) + 3.2275]; ΔP_skin = 0.869·m·S |
| Datum | A constant gauge→datum offset (56.9–123.1 psi) is added to p_wf and p_ws alike, so it cancels in every pressure difference: **k, S, m and ΔP_skin do not depend on it.** `ml/make_pta.py` asserts this for every event (relative change < 1e-6). Only reported pressures move: `p_star_datum_psia` = p* + gradient × (datum − gauge), with the gradient from test-average oil API, Rs, salinity and water cut. |
| Storage (Horner tables) | C = q·B·Δt / (24·Δp) on the first three minutes (afterflow unit slope). The model fits its own C. |

## Results (rate = shipped Task 1, λ = 0.80)

**Submitted — exact model match** (`ml/outputs/pta_submission.csv`, identical to the scored file `ml/outputs/submitted/pta_model_match_8.3840_SHIPPED.csv`):

| Well | Model | k (md) | S | ΔP_skin (psi) | m (psi/cycle) | C (bbl/psi) | r_e (ft) | fit RMS (psi) |
|---|---|--:|--:|--:|--:|--:|--:|--:|
| GL-01 | closed circle | 105.25 | 5.741 | 116.78 | 23.410 | 0.0229 | 1367 | 0.038 |
| GL-02 | infinite | 61.34 | −0.264 | −11.49 | 50.141 | 0.0166 | — | 0.076 |
| GL-04 | infinite | 57.35 | −0.904 | −108.13 | 137.570 | 0.0294 | — | 0.044 |
| GL-06 | infinite | 295.48 | 2.307 | 29.04 | 14.483 | 0.0163 | — | 0.065 |
| GL-08 | infinite | 43.07 | −1.589 | −127.44 | 92.274 | 0.0099 | — | 0.053 |
| GL-10 | closed circle | 176.40 | 2.195 | 54.41 | 28.520 | 0.0212 | 1048 | 0.026 |

The largest single residual is 0.07–0.46 psi per build-up.

**Horner reference — windows A and B:**

| Well | Window A, h | m | k | S | ΔP_skin | Window B, h | m | k | S | ΔP_skin | Note |
|---|---|--:|--:|--:|--:|---|--:|--:|--:|--:|---|
| GL-01 | 2.375–4.725 | 23.443 | 105.10 | 5.642 | 114.93 | same | 23.443 | 105.10 | 5.642 | 114.93 | no IARF plateau (boundary) |
| GL-02 | 1.558–4.883 | 52.734 | 58.33 | −0.566 | −25.92 | 2.447–4.883 | 52.310 | 58.80 | −0.522 | −23.71 | |
| GL-04 | 12.483–41.600 | 145.160 | 54.35 | −1.255 | −158.29 | 20.849–41.600 | 143.581 | 54.95 | −1.190 | −148.42 | long storage |
| GL-06 | 1.317–6.925 | 15.109 | 283.24 | 1.931 | 25.36 | 3.471–6.925 | 14.915 | 286.93 | 2.040 | 26.44 | |
| GL-08 | 0.850–62.400 | 93.471 | 42.52 | −1.664 | −135.17 | 31.274–62.400 | 92.571 | 42.93 | −1.610 | −129.50 | infinite-acting |
| GL-10 | 1.250–2.483 | 28.615 | 175.82 | 2.103 | 52.30 | same | 28.615 | 175.82 | 2.103 | 52.30 | no IARF plateau (boundary) |

### How to read the comparison

- **Where IARF is long and clean, model and Horner agree.** On GL-08 (72 h, infinite-acting), the derivative in window B sits 0.4% above the IARF level. Model and Horner B agree within 0.32% on k and 0.02 on skin. This validates the model against the textbook method where the textbook method holds.
- **Where the build-up is short or storage-dominated, the Horner line is too steep.** On GL-02, GL-04 and GL-06 the measured derivative in window B is still 3.4–5.0% above the IARF level (`der_B_over_iarf` 1.034–1.050): it is still coming down from the storage hump when the test ends. A straight line through those points overstates m. The model fits the storage→IARF transition explicitly, so it uses the true level: its k is 3.0–4.4% higher than Horner B's and its skin 0.26–0.29 higher.
- **On GL-01 and GL-10 the late points are boundary-dominated.** A closed circle (r_e 1367 and 1048 ft) fits them to 0.038 and 0.026 psi RMS, against 1.89 and 0.42 psi for the infinite model. Model and Horner agree within 0.33% on k there; the model's skin is ~0.1 higher.
- **Windows A and B agree within 1.3% on k and 0.11 on skin** on the four infinite-acting build-ups.

### What the leaderboard said (PTA parameters, out of 20)

| Submission | Rate | Score |
|---|---|--:|
| Horner, window A | S1 (λ = 1.0) | 7.2458 |
| Horner, window B | S1 (λ = 1.0) | 7.3809 |
| **Exact model match** | **λ = 0.80 (shipped Task 1)** | **8.3840** |
| Same values, slope reported negative | λ = 0.80 | rejected: the platform requires `horner_slope` ≥ 0 |
| Horner B, k from total liquid rate (k·q_L/q_o) | λ = 0.80 | 4.8375 |

- **The model match changed two things at once** relative to Horner B: the rate (S1 → λ = 0.80) and the method. No single-change probe isolated them.
  - The rate alone moves k by the ratio of the two rates, 0.4–1.1% on these wells (k ∝ q; per-well factors in `_ROUTING_FACTORS_RAW`, `ml/src/vfm.py`).
  - The method moves k by up to 4.4% and skin by up to 0.29.
  - So most of the +1.0 point is the method, but this is an inference, not a measurement.
- **The liquid-rate probe scored 4.8375**, far below every oil-rate submission (7.2–8.4). The reference therefore uses the oil rate, as the brief says.

## Known limits

- **Numerical precision.** k and S are correlated, so the misfit valley is flat. Running on float64 instead of the stored float32 readings moves k by ≤ 0.042% and skin by ≤ 0.0034 (GL-06). This sets how many digits are meaningful.
- **r_e is an equivalent closed circle.** Other closed shapes (rectangles, faults) were not fitted.
- **p\* depends strongly on t_p.** It is reported for completeness only; the brief asks for m, k, S and ΔP_skin.
- **The rate is a daily VFM value at constant q with t_p = 24·N_p/q.** The brief requires this. An hourly rate history would make the superposition exact.
