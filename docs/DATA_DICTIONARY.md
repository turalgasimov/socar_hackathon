# Data dictionary

Ten gas-lifted wells (GL-01…GL-10), 1 Jan – 30 Sep 2025. Ranges below are from
the **cleaned** data (`data/processed/`); raw-file quirks are called out per
table. Regenerate with the commands in [`../README.md`](../README.md).

---

## `high_freq_data.csv` → `high_freq_clean.parquet`

3,914,560 rows, one per well-minute. **257 MB raw, stored in Git LFS.**

| column | unit | range (clean) | notes |
|---|---|---|---|
| `timestamp` | — | 2025-01-01 → 2025-09-30 23:59 | 1-minute grid |
| `well_name` | — | GL-01…GL-10 | |
| `whp_psia` | psia | 167.9 – 999.1 | wellhead (upstream of choke) |
| `whp_downstream_psia` | psia | 142.8 – 214.6 | downstream of choke |
| `dh_pressure_psia` | psia | 2,269 – 3,914 | downhole gauge, **not at datum** |
| `dh_temperature_degf` | °F | 165.3 – 203.7 | |
| `annulus_pressure_psia` | psia | 916.3 – 1,617 | lift-gas injection side |
| `gas_lift_rate_mscfd` | Mscf/d | 0 – 1,697 | 0 ⟺ well shut in |

Added by `clean.py`:

| column | unit | notes |
|---|---|---|
| `choke_pct` | % | forward-filled from `choke_events` (an event log, not a series) |
| `is_shut_in` | bool | `choke_pct == 0`; 12,879 minutes across 6 events |
| `dp_choke` | psi | `whp − whp_downstream` |
| `dp_tubing` | psi | `dh_pressure − whp` |
| `dp_annulus_tubing` | psi | `annulus_pressure − whp` |

**Raw-file defects** (all repaired):

- `-999.25` is the absent-value code — 7,410 readings. The raw file has **zero
  NaNs**, so a naive read treats these as real pressures.
- 2,513 duplicate `(well_name, timestamp)` rows.
- 449 isolated spikes (one `dh_pressure` jump of 5,691 psi).
- 33 gaps > 1 min. **2025-08-09 01:09–05:40 is field-wide** — all ten wells, 270
  min each. A historian failure, so no well can impute another across it.
- 2,130 values remain NaN after cleaning: long outages, left unfilled on purpose
  so daily aggregates can report honest coverage.

---

## `well_tests.csv` → `well_tests_clean.parquet`

85 rows, 7–9 per well. **These are the only VFM labels.**

The sensor columns reconcile to ~0 against high-frequency means over the same
window — a test row **is** the window average. That fixes the label join.

| column | unit | range | notes |
|---|---|---|---|
| `test_start`, `test_end` | — | 2025-01-03 → 2025-09-28 | 12–24 h windows |
| `oil_rate_stbd` | stb/d | 578 – 4,808 | **target** |
| `water_rate_stbd` | stb/d | 295 – 2,124 | **target** |
| `gas_rate_mscfd` | Mscf/d | 124.6 – 1,282 | **target**, produced gas only |
| `total_gas_rate_mscfd` | Mscf/d | 725 – 2,345 | `gas_rate + gas_lift_rate` |
| `liquid_rate_stbd` | stb/d | 886 – 6,672 | `oil + water` |
| `water_cut_pct` | % | 17.1 – 57.7 | `water / liquid × 100` |
| `gor_scf_stb` | scf/stb | 134.7 – 362.6 | `gas × 1000 / oil` |
| `glr_scf_stb` | scf/stb | 310.5 – 1,791 | `total_gas × 1000 / liquid` |
| `bsw_pct` | % | 16.1 – 57.8 | differs slightly from `water_cut_pct` |
| `separator_pressure_psia` | psia | 129.7 – 134.5 | not in high-frequency data |
| `separator_temperature_degf` | °F | 75.4 – 129.6 | not in high-frequency data |
| `oil_gravity_api` | °API | 23.8 – 38.0 | varies per test |
| `gas_sg` | — | 0.695 – 0.818 | |
| `water_salinity_ppm` | ppm | 55,700 – 163,300 | |
| sensor columns | | | window means — see above |

**Raw-file defects** (all repaired, each verified against redundant columns):

- **All 9 GL-06 rows: `gas_rate_mscfd` and `total_gas_rate_mscfd` in m³/d under
  an Mscf/d header.** Factor 28.3168 = 1 Mscf in m³. Uncorrected, GL-06 looks
  like it makes 28× its real gas. Rebuilt from GOR and GLR, which are correct.
- Five sign flips: `gas_lift_rate` (GL-06 18 Jun, GL-09 27 Jul), `water_rate`
  (GL-06 18 Aug), `gas_rate` (GL-08 24 Sep), `total_gas_rate` (GL-04 12 Jul).

After repair all five identities (`liquid = oil + water`, `gor = gas/oil`,
`total_gas = gas + lift`, `glr = total_gas/liquid`, `water_cut = water/liquid`)
close to ≤ 0.11 — 1-decimal rounding noise.

---

## `choke_events.csv`

65 rows. An **event log**, not a time series: each row is a change, so the
setting holds until the next event. `clean.py` forward-fills it onto the minute
grid with `merge_asof`.

| column | unit | range |
|---|---|---|
| `timestamp` | — | 2025-01-01 → 2025-09-29 |
| `choke_opening_pct` | % | 0 – 71.9 |

`choke_opening_pct == 0` marks a shut-in. There are exactly six, and they are
the **only** PTA build-up events:

| well | start | duration | build-up |
|---|---|--:|--:|
| GL-01 | 2025-04-15 08:00 | 72.0 h | +271 psi |
| GL-02 | 2025-03-08 14:23 | 5.7 h | +281 psi |
| GL-04 | 2025-06-03 08:00 | 48.0 h | +837 psi |
| GL-06 | 2025-07-22 03:11 | 8.0 h | +119 psi |
| GL-08 | 2025-08-19 09:00 | 72.0 h | +522 psi |
| GL-10 | 2025-05-27 21:04 | 9.0 h | +228 psi |

GL-03, GL-05, GL-07 and GL-09 never close their choke — **no PTA for those**.

---

## `reservoir_pvt.csv`

10 rows, one per well. Audited — clean, no repairs needed.

| column | unit | range |
|---|---|---|
| `net_pay_thickness_ft` | ft | 32 – 136 |
| `porosity_frac` | — | 0.161 – 0.258 |
| `water_saturation_frac` | — | 0.184 – 0.348 |
| `total_compressibility_1_psi` | 1/psi | 1.078e-05 – 1.561e-05 |
| `wellbore_radius_ft` | ft | 0.255 – 0.354 |
| `oil_fvf_rb_stb` | rb/stb | 1.092 – 1.189 |
| `oil_viscosity_cp` | cP | 0.919 – 3.008 |
| `bubble_point_pressure_psia` | psia | 1,177 – 1,595 |
| `reservoir_temperature_degf` | °F | 168.3 – 202.2 |
| `datum_tvd_ft` | ft TVD | 7,850 – 10,110 |
| `estimated_drainage_area_acres` | acres | 100 – 620 |

Every well's **minimum** downhole pressure sits well above its bubble point
(e.g. GL-04: 2,269 vs 1,265 psia), which justifies single-phase oil PTA.

---

## `well_completion.csv`

10 rows, one per well. Audited — clean, no repairs needed.

| column | unit | range |
|---|---|---|
| `gauge_tvd_ft` | ft TVD | 7,450 – 9,850 |
| `gl_valve_tvd_ft` | ft TVD | 2,680 – 5,770 |
| `gl_valve_port_64ths` | 1/64 in | 10 – 18 |
| `tubing_od_in` | in | 2.875 – 4.5 |
| `tubing_id_in` | in | 2.441 – 3.958 |
| `production_manifold` | — | A / B |
| `lift_gas_sg` | — | 0.65 (constant) |
| `solution_gor_at_pb_scf_stb` | scf/stb | 160 – 336.2 |
| `water_fvf_rb_stb` | rb/stb | 1.02 (constant) |
| `choke_max_size_64ths` | 1/64 in | 128 (constant) |
| `first_production_date` | date | 2009-10-07 – 2020-08-19 |
| `cum_oil_at_2025_01_01_stb` | stb | 1.75e6 – 3.43e7 |

Two things worth knowing:

- **`cum_oil_at_2025_01_01_stb` correlates r = +0.96 with a well's mean oil
  rate.** It is static and known before the test period, so it is a
  leakage-free capacity proxy — the single most useful static feature.
- **The gauge sits 150–420 ft shallower than `datum_tvd_ft` on every well.**
  The hydrostatic offset is constant through a build-up, so it cancels in every
  pressure difference: k, skin, Horner slope and ΔP_skin do not depend on it
  (asserted per event in `ml/make_pta.py`). Correct only reported absolute
  pressures (p*, p̄) to datum.
