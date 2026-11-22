# Deliverables — SOCAR Hackathon 2026

Everything `docs/Deliverables.pdf` asks for, in one place. The numbering follows that list.

| # | Required | Here |
|---|---|---|
| 1 | Result files for Phase 1 (VFM) and Phase 2 (PTA), CSV or Excel | [`1_results/`](1_results/) |
| 2 | The trained model file in `.pkl` format | [`2_model/vfm.pkl`](2_model/vfm.pkl) |
| 3 | A notebook with all cells run and outputs showing the best results | [`3_notebooks/`](3_notebooks/) |
| 4 | A folder containing all necessary PTA plots | [`4_pta_plots/`](4_pta_plots/) |

The application is in [`../ui/`](../ui/); see [`../ui/README.md`](../ui/README.md) to run it.

## 1. Result files

| File | Contents |
|---|---|
| `vfm_submission.csv` | **Phase 1.** Daily oil, water and gas rate for 10 wells × 273 days (2025-01-01 to 2025-09-30), 2,730 rows, in the organisers' template. These are the predictions that scored **21.0200 / 30** on the leaderboard; some rows differ from the uploaded file by 0.1 in the last decimal, from rounding. |
| `vfm_daily_predictions.xlsx` | The same daily rates as Excel, with the share of the day covered by sensor data and a low-coverage flag. |
| `pta_submission.csv` | **Phase 2.** Permeability, skin, ΔP skin and Horner slope for the 6 build-ups (GL-01, GL-02, GL-04, GL-06, GL-08, GL-10), in the organisers' template. Identical to the file that scored **8.3840 / 20**. |
| `pta_results.xlsx` | The same results as Excel. Sheets: `submission`, `results`, `horner_comparison`, `method`. |

Only six of the ten wells were ever shut in, so only those six have a well-test result.

## 2. Trained model

`vfm.pkl` is the VFM model: a choke-flow law for the liquid rate and a water-cut split from the
tubing pressure drop, fitted on the 85 measured well tests, with the per-well
test-separator routing correction attached. It holds a `VFMModel` object, whose class is defined
in `ml/src/vfm.py`, so that folder must be on the Python path. From the repository root:

```python
import sys; sys.path.insert(0, "ml/src")
from vfm import VFMModel, build_inputs
model = VFMModel.load("submission/2_model/vfm.pkl")
rates = model.predict(build_inputs(table))      # table: daily or test-window sensor means
```

Phase 2 has no trained model. Each build-up is matched by a physical well model (wellbore
storage, skin, radial flow, boundary) in `ml/src/pta_model.py`.

## 3. Notebooks

| File | Contents |
|---|---|
| `VFM_Phase1.ipynb` | Phase 1 end to end: data defects and cleaning, the model, time-forward validation, the routing correction, the daily predictions, and the three test months. 51 cells, 25 code cells, 6 figures, all run. |
| `PTA_Phase2.ipynb` | Phase 2 end to end: the six build-ups, the model match, the submitted table, and two tests on data the fit never saw. 25 cells, 12 code cells, all run. |

Both were executed in `notebooks/` at the repository root and read the code in `ml/`. To run
them again, use `python ml/build_notebook.py` and `python ml/build_pta_notebook.py` from the root.

## 4. PTA plots

9 figures: two on the theory, one overview of all build-ups, and one per build-up
(7 in total) with the pressure history, Cartesian, log-log with derivative,
Horner and MDH plots and the model match. `README.md` in that folder explains each panel, and
the three `pta_reference_*.csv` tables hold the numbers drawn.

---

The files here are copies of the originals in `ml/outputs/`, `ml/models/` and `notebooks/`.
`python ml/make_submission.py` rebuilds this folder after checking the originals, and
`python ml/make_submission.py --check` confirms that every copy still equals its original.
