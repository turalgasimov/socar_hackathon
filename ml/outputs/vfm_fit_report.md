# VFM fit report

Model: `ml/models/vfm.joblib`, fitted on all 85 well tests.
Structure: choke law for liquid x water-cut split from the tubing gradient; gas from static Rs. See `ml/src/vfm.py`.

## Time-forward scores (55 of 85 tests)

| phase | MAPE | bias |
|---|--:|--:|
| oil | 2.56% | +0.25% |
| water | 3.82% | +0.15% |
| gas | 5.65% | +2.04% |

Each test is predicted from the other nine wells plus that well's own
earlier tests. No future information, no same-test leakage.

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
| GL-01 | 905 | 1,008 | -10.2% |
| GL-02 | 1,193 | 1,281 | -6.8% |
| GL-03 | 712 | 750 | -5.1% |
| GL-04 | 705 | 764 | -7.7% |
| GL-05 | 736 | 790 | -6.9% |
| GL-06 | 696 | 720 | -3.3% |
| GL-07 | 4,284 | 4,458 | -3.9% |
| GL-08 | 1,422 | 1,476 | -3.6% |
| GL-09 | 1,219 | 1,260 | -3.3% |
| GL-10 | 1,858 | 1,956 | -5.0% |

Predicted daily rates sitting a few per cent below tested rates is the
expected direction: a test runs the well at lower back-pressure than normal
production, so it flows harder. Whether that gap should be corrected depends
on how the organisers defined the daily ground truth — see
`agent/PROJECT_STATE.md`, Open risks.