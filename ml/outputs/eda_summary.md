# EDA summary - SOCAR 2026 Intelligent Well Performance

- High-frequency rows (cleaned): **3,914,560** over 2025-01-01 to 2025-09-30, 10 wells, 1-minute grid
- Well tests (labels): **85** (7-9 per well)
- Choke events: **65**; shut-in (build-up) events >=1 h: **6**

## VFM framing
- Labels are scarce: 85 tests vs 3,914,560 feature rows. Aggregate per test window; validate by well (GroupKFold), never by random row.
- Well-test sensor columns reconcile to ~0 against high-frequency window means, so a test row *is* the window average. That fixes the label join.
- Test windows are 12-24 h (721-1441 minutes of data each).

## PTA framing
| well | start | duration (h) | build-up (psi) |
|---|---|---|---|
| GL-01 | 2025-04-15 08:00 | 72.0 | +271 |
| GL-02 | 2025-03-08 14:23 | 5.7 | +281 |
| GL-04 | 2025-06-03 08:00 | 48.0 | +837 |
| GL-06 | 2025-07-22 03:11 | 8.0 | +119 |
| GL-08 | 2025-08-19 09:00 | 72.0 | +522 |
| GL-10 | 2025-05-27 21:04 | 9.0 | +228 |

- GL-03, GL-05, GL-07, GL-09 never shut in -> **no PTA possible** for them.
- GL-02 (5.7 h) and GL-06 (8.0 h) are short build-ups; radial flow may not develop, so Horner slope will be uncertain there.

## Where the rate signal actually is
Pooled correlation is misleading: choke opening scores r=0.84 against oil rate, but that reflects well size, not physics. Removing each well's mean gives the usable signal:

| feature | oil (pooled -> within) | water | gas |
|---|---|---|---|
| whp_downstream_psia | +0.65 -> **+0.76** | +0.34 -> +0.13 | +0.66 -> **+0.70** |
| dh_temperature_degf | -0.41 -> **+0.57** | -0.52 -> -0.00 | -0.39 -> +0.48 |
| annulus_pressure_psia | -0.32 -> +0.15 | -0.49 -> **-0.50** | -0.29 -> +0.21 |
| gas_lift_rate_mscfd | +0.05 -> +0.33 | +0.03 -> -0.38 | -0.02 -> +0.30 |
| choke_pct | +0.84 -> +0.20 | +0.93 -> +0.47 | +0.86 -> +0.15 |

- Downhole temperature **flips sign** between the two views - a Simpson's paradox. Any model must carry well identity (or well-level normalisation) or it will learn the between-well trend and invert the within-well one.
- Water rate is driven by a different group (annulus pressure, choke) than oil and gas.

## Recording gaps
- 33 gaps longer than 1 minute; longest 2,160 min (1.5 days).
- **2025-08-09: all 10 wells drop out simultaneously** (01:09-05:40, 270 min each). A historian/SCADA failure, not independent sensor faults - so no well can impute another across it, and every daily aggregate for that date is ~19% short.

## Figures
- `fig01_data_quality.png`
- `fig02_coverage_timeline.png`
- `fig03_pressure_series.png`
- `fig04_buildups.png`
- `fig05_vfm_relationships.png`
- `fig06_rate_history.png`
- `fig07_correlation.png`