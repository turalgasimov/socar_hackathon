# Feature engineering and normalisation - measured effect

Model held constant (RidgeCV on standardised inputs, scaler fit inside each
training fold). Only the feature set changes. Metric is MAPE on oil rate, %.

| feature set | n | leave-one-out | time-forward | random 10-fold | unseen well |
|---|--:|--:|--:|--:|--:|
| window means only | 10 | 23.29 | 26.99 | 22.73 | 54.7 |
| + per-well z-scores | 30 | 6.05 | 12.32 | 6.60 | 83.8 |
| + static properties | 52 | 3.99 | 6.44 | 4.33 | 55.2 |
| + physics interactions | 58 | 3.39 | 5.11 | 4.01 | 82.5 |
| *baseline: predict the global mean* | - | - | - | - | 55.5 |

## Reading this table

- **Per-well z-scoring is the single biggest win.** Time-forward error drops from 27.0% to 12.3% on that one change. 98.3% of rate variance is between wells, so raw sensor values mostly encode *which well this is*; the z-scores expose the 1.7% that is actual production change.
- **Static properties add the well-scale term** the z-scores deliberately removed, taking time-forward to 6.44%.
- **`random 10-fold` is not a valid score here.** It puts other tests from the same well in training, so the model reads off a memorised level. Treat it as a leakage check, not a result.
- **`unseen well` is near or worse than the baseline for every set.** With 10 wells there is not enough between-well data to generalise to an 11th. If the organisers score on a held-out *well*, this approach does not transfer - but the deliverable asks for daily rates on these same 10 wells, which is the time-forward column.

## Per-target error (leave-one-out, static set)

| target | MAPE |
|---|--:|
| oil_rate_stbd | 3.99% |
| water_rate_stbd | 3.85% |
| gas_rate_mscfd | 7.41% |

Gas is the hardest target (7.4%), as expected: it is the smallest-magnitude rate and the most sensitive to the separator conditions that the high-frequency sensors do not observe.

## Caveat

The full matrix is 136 features for 85 labelled rows. That is heavily p >> n, and the numbers above come from L2-regularised linear models chosen for that reason. A high-capacity model on this table will overfit; keep regularisation strong and prefer the smaller sets.