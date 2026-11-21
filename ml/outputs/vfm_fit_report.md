# VFM fit report

Model: `ml/models/vfm.joblib`, fitted on all 85 well tests.
Structure: choke law for liquid x water-cut split from the tubing gradient; gas from static Rs. See `ml/src/vfm.py`.

## Time-forward scores (55 of 85 tests)

Scored as R² /3 + MAPE /2 + **WAPE /5** = 10 points per phase, 30 total.
WAPE carries half of each phase's score: it is volume-weighted, so the
large wells dominate and a systematic bias passes straight through.

| phase | R² | MAPE | WAPE | bias |
|---|--:|--:|--:|--:|
| oil | 0.9983 | 2.59% | **2.30%** | +0.33% |
| water | 0.9963 | 3.74% | **3.25%** | +0.24% |
| gas | 0.9945 | 5.67% | **4.52%** | +2.12% |

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
| GL-01 | 906 | 1,008 | -10.1% |
| GL-02 | 1,189 | 1,281 | -7.2% |
| GL-03 | 711 | 750 | -5.3% |
| GL-04 | 708 | 764 | -7.4% |
| GL-05 | 735 | 790 | -7.0% |
| GL-06 | 692 | 720 | -3.8% |
| GL-07 | 4,285 | 4,458 | -3.9% |
| GL-08 | 1,420 | 1,476 | -3.8% |
| GL-09 | 1,219 | 1,260 | -3.2% |
| GL-10 | 1,852 | 1,956 | -5.4% |

Predicted daily rates sitting a few per cent below tested rates is the
expected direction: a test runs the well at lower back-pressure than normal
production, so it flows harder. Whether that gap should be corrected depends
on how the organisers defined the daily ground truth — see
`agent/PROJECT_STATE.md`, Open risks.