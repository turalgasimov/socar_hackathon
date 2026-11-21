# PTA plots — Phase 2 exploration and hand-calculation reference

Everything in this folder is produced by one script:

```bash
python ml/eda/pta_explore.py        # ~40 s; needs data/processed/high_freq_clean.parquet
```

**This is the exploratory reference, not the Phase 2 deliverable.** The deliverable is an Excel with Horner slope, k, skin and ΔP_skin per shut-in, plus this kind of plot set. The two CSVs here are reference values that the deliverable pipeline should reproduce or explain.

## Files

| File | What it shows |
|---|---|
| `pta_00_theory_flow_regime_atlas.png` | Theory. Analytical log-log type curves (Δp and Bourdet derivative), from Laplace solutions with Stehfest inversion, for six reservoirs: homogeneous infinite-acting (WBS → hump → IARF); closed circle drawdown vs build-up (PSS unit slope vs derivative falling to p̄); constant-pressure boundary; one sealing fault (derivative doubles); channel (½ slope); dual porosity (valley). Reference for reading the real derivatives. |
| `pta_01_theory_skin_storage_hump.png` | Theory. Same storage, skin −2 / 0 / 5 / 12. The storage hump grows with C_D·e^(2S) while the IARF level does not move, which is why k from the IARF slope is skin-free. Negative skin is modelled with the effective wellbore radius. |
| `pta_02_overview_six_buildups_loglog.png` | All six real build-ups on one page: Δp and derivative vs Δt, with the window-A IARF plateau shaded and its derivative level dashed. Each panel title gives the regime diagnosis. |
| `pta_10_GL-01_2025-04-15_buildup_all_plots.png` | GL-01, 72 h shut-in. Closed boundary: the derivative falls after ~5 h and pressure plateaus near 3511.5 psia (p̄). No 0.3-cycle IARF plateau, so results are flagged. |
| `pta_10_GL-02_2025-03-08_buildup_all_plots.png` | GL-02, 5.6 h shut-in. Short, but the IARF plateau develops from ~1.6 h. |
| `pta_10_GL-04_2025-06-03_buildup_all_plots.png` | GL-04, 48 h shut-in. Cleanest wellbore-storage unit slope and the largest hump (lowest kh/μ); IARF from ~12 h. |
| `pta_10_GL-06_2025-07-22_buildup_all_plots.png` | GL-06, 8 h shut-in. Short; IARF from ~1.3 h. |
| `pta_10_GL-08_2025-08-19_buildup_all_plots.png` | GL-08, 72 h shut-in. Infinite-acting for the whole test; IARF from ~0.85 h. The textbook case. |
| `pta_10_GL-10_2025-05-27_buildup_all_plots.png` | GL-10, 9 h shut-in. Short and boundary-affected: the derivative keeps falling, so results are flagged. |
| `pta_reference_window_A.csv` | Results per shut-in with window A (IARF plateau). |
| `pta_reference_window_B.csv` | Results per shut-in with window B (late IARF points). |

Every `pta_10_*` figure has six panels, all from the same data:

- **A.** Pressure history around the shut-in (gauge depth).
- **B.** Cartesian build-up, p_ws vs Δt, with p*.
- **C.** Log-log diagnostic: Δp and Bourdet derivative, unit-slope (WBS) guide, IARF level m/2.303; window A grey, window B hatched.
- **D.** Horner plot, p_ws vs (t_p+Δt)/Δt, with the window-A straight line extended to p*.
- **E.** MDH plot, p_ws vs log Δt.
- **F.** Results table, window A vs window B.

## Inputs and conventions

| Item | Choice |
|---|---|
| Pressure | `dh_pressure_psia` at **gauge depth**, 1-minute data. The cleaning step leaves every build-up window untouched (checked minute by minute). Noise ≈ 0.03 psi, no segregation humps. |
| Δt = 0 | the `choke_events.csv` shut-in timestamp; pressure starts rising in the first minute |
| p_wf(Δt=0) | last flowing gauge reading at the shut-in minute |
| Rate q | VFM **oil** rate (champion S1, `ml/outputs/vfm_S1_routing.csv`) of the **last full flowing day** before the shut-in. The brief asks for single-phase oil on predicted Qo, so k is effectively the oil permeability. |
| N_p, t_p | N_p = `cum_oil_at_2025_01_01` + VFM daily oil up to the shut-in; t_p = 24·N_p/q (Horner pseudo-producing time) |
| Derivative | Bourdet, L = 0.10, with respect to ln of the Agarwal time t_p·Δt/(t_p+Δt), on a 40-points-per-cycle log grid |
| **Window A** | longest run after the storage hump where the derivative's log-slope is within ±0.10. If shorter than 0.3 log-cycle, the flattest 0.3 cycle is used and the row is flagged. |
| **Window B** | the last 0.3 log-cycle of the window-A plateau. With no boundary these are the last points of the build-up, the furthest from wellbore storage. Where a boundary bends the derivative down, the last points are p̄ regime, not IARF, so B stops where the plateau stops. With no plateau, B = A (flagged). |
| Horner → k, S | k = 162.6·q·B·μ/(m·h); S = 1.151·[(P1hr − p_wf)/m − log10(k/(φ·μ·c_t·r_w²)) + 3.2275]; ΔP_skin = 0.869·m·S |
| Datum | A constant gauge→datum offset is added to p_wf and p_ws alike, so it cancels in m and in (P1hr − p_wf): **k, S and ΔP_skin are unchanged.** Only reported pressures move. `p_star_datum_psia` = p* + gradient × (datum − gauge), with the gradient from test-average oil API, Rs, salinity and water cut. |
| Storage | C = q·B·Δt / (24·Δp) on the first three minutes (afterflow unit slope) |

## Results (rate = VFM S1)

| Well | Window A, h | m (psi/cycle) | k (md) | S | ΔP_skin (psi) | Window B, h | m | k | S | ΔP_skin | Note |
|---|---|--:|--:|--:|--:|---|--:|--:|--:|--:|---|
| GL-01 | 2.38–4.73 | 23.44 | 106.0 | 5.64 | 114.9 | same | 23.44 | 106.0 | 5.64 | 114.9 | no IARF plateau (boundary) |
| GL-02 | 1.56–4.88 | 52.73 | 58.7 | −0.57 | −26.1 | 2.45–4.88 | 52.31 | 59.2 | −0.53 | −23.9 | |
| GL-04 | 12.48–41.60 | 145.16 | 54.9 | −1.26 | −159.0 | 20.85–41.60 | 143.58 | 55.5 | −1.20 | −149.1 | long storage |
| GL-06 | 1.32–6.93 | 15.11 | 284.7 | 1.93 | 25.3 | 3.47–6.93 | 14.92 | 288.4 | 2.04 | 26.4 | |
| GL-08 | 0.85–62.40 | 93.47 | 42.7 | −1.67 | −135.3 | 31.27–62.40 | 92.57 | 43.1 | −1.61 | −129.6 | infinite-acting |
| GL-10 | 1.25–2.48 | 28.62 | 176.6 | 2.10 | 52.2 | same | 28.62 | 176.6 | 2.10 | 52.2 | no IARF plateau (boundary) |

How to read the comparison:

- **Windows A and B agree within ~1.3% on k and ~0.1 on skin on the four clean build-ups.** Once IARF is reached the semi-log line is stable, and the late points remove the last of the storage influence.
- **On GL-01 and GL-10 the true late points are boundary-dominated.** Fitting a Horner line through them would flatten m and inflate k, which is why B refuses to go there.

**Rate sensitivity (S0 → S1, window A):**

- k rises **1.8–5.7%**: k ∝ q, so it rises by exactly the VFM rate change.
- Skin changes by **≤ 0.03**.
- The VFM accuracy therefore carries straight into k.

## Known limits

- **GL-01 and GL-10** need a model-based check: an analytical closed-circle match, available in the theory code above, before their k and skin are quoted with confidence.
- **p\* depends strongly on t_p.** It is reported for completeness only; the brief asks for m, k, S and ΔP_skin.
- **The rate is a daily VFM value.** The brief requires this, but an hourly rate history would make the superposition exact.
