# VFM fit report

Model: `ml/models/vfm.joblib`, fitted on all 85 well tests.
Structure: choke law for liquid x water-cut split from the tubing gradient; gas from static Rs. See `ml/src/vfm.py`.

## Time-forward scores (55 of 85 tests)

Scored as R² /3 + MAPE /2 + **WAPE /5** = 10 points per phase, 30 total.
WAPE carries half of each phase's score: it is volume-weighted, so the
large wells dominate and a systematic bias passes straight through.

| phase | R² | MAPE | WAPE | bias |
|---|--:|--:|--:|--:|
| oil | 0.9981 | 2.56% | **2.33%** | +0.25% |
| water | 0.9959 | 3.82% | **3.48%** | +0.15% |
| gas | 0.9940 | 5.65% | **4.61%** | +2.04% |

Each test is predicted from the other nine wells plus that well's own
earlier tests. No future information, no same-test leakage.

These are measured in the test-routed regime: all 85 labels were recorded
while the well flowed to the test separator. The routing correction acts
only on normal-production days, so it does not change this table (the
time-forward fits are uncorrected). Only the leaderboard measures it:
**21.0200 / 30** with it, 20.2110 without.

## Fitted choke exponents

| term | exponent | textbook |
|---|--:|--:|
| choke size S | +2.057 | +2 (area ~ d²) |
| choke dP | +0.472 | +0.5 (√ΔP) |
| WHP | +0.472 | — |
| GLR | -0.612 | — |

The first two land on the subcritical choke law without being told to, which is the evidence that the form is right rather than fitted to noise.

## Daily predictions

`ml/outputs/vfm_daily_predictions.xlsx` — 2,729 well-days, 14 flagged below 80% minute coverage.

| well | mean predicted oil | mean tested oil | diff |
|---|--:|--:|--:|
| GL-01 | 937 | 1,008 | -7.0% |
| GL-02 | 1,222 | 1,281 | -4.6% |
| GL-03 | 738 | 750 | -1.7% |
| GL-04 | 738 | 764 | -3.5% |
| GL-05 | 756 | 790 | -4.3% |
| GL-06 | 710 | 720 | -1.3% |
| GL-07 | 4,353 | 4,458 | -2.4% |
| GL-08 | 1,440 | 1,476 | -2.5% |
| GL-09 | 1,254 | 1,260 | -0.5% |
| GL-10 | 1,891 | 1,956 | -3.3% |

Predicted daily rates sit -7.0% to -0.5% against the tested rates. Below
is the expected direction: a test routes the well to the test separator at
lower back-pressure than normal production, so it flows harder.

**The routing correction is applied:** λ = 0.80 times the per-well
factor in `ml/src/vfm.py`, already included in the numbers above. It scored
**21.0200 / 30** on the leaderboard against 20.2110 uncorrected, the only change
that ever gained points. It corrects the choke law's over-response to the
routing switch (~5.9% where the downhole physics says ~2.5%), so the gap
above is meant to remain. See `agent/PROJECT_STATE.md` → Leaderboard.