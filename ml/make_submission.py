"""Build submission/: one folder with every file docs/Deliverables.pdf asks for.

    python ml/make_submission.py            # verify the deliverables, then (re)build submission/
    python ml/make_submission.py --check    # verify submission/ is complete and in sync; change nothing

The files in submission/ are copies. The originals stay where the pipeline writes and reads them
(ml/outputs/, ml/models/, notebooks/), so nothing else in the repo depends on this folder. A copy
can go stale, so run this again after anything that regenerates a deliverable (ml/fit_vfm.py,
ml/make_pta.py, ml/eda/pta_explore.py, ml/build_notebook.py, ml/build_pta_notebook.py), and use
--check before a hand-in.

Before copying, the sources are checked: result files against the organisers' templates, the
model loads and carries its routing factors, every notebook cell has run without an error, and
every build-up in the PTA result file has its plot.
"""
from __future__ import annotations

import argparse
import json
import pickle
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))
OUT = ROOT / "submission"
PTA_PLOTS = ROOT / "ml" / "outputs" / "figures" / "pta"
TEXT = {".csv", ".md", ".ipynb"}          # compared with line endings normalised (git stores LF)

# leaderboard scores of the two result files, as recorded in agent/PROJECT_STATE.md
VFM_SCORE, PTA_SCORE = "21.0200 / 30", "8.3840 / 20"

# (folder in submission/, source file)
FILES = [
    ("1_results", ROOT / "ml" / "outputs" / "vfm_submission.csv"),
    ("1_results", ROOT / "ml" / "outputs" / "vfm_daily_predictions.xlsx"),
    ("1_results", ROOT / "ml" / "outputs" / "pta_submission.csv"),
    ("1_results", ROOT / "ml" / "outputs" / "pta_results.xlsx"),
    ("2_model", ROOT / "ml" / "models" / "vfm.pkl"),
    ("3_notebooks", ROOT / "notebooks" / "VFM_Phase1.ipynb"),
    ("3_notebooks", ROOT / "notebooks" / "PTA_Phase2.ipynb"),
]


def manifest() -> list[tuple[Path, Path]]:
    """(destination, source) for every file of the folder, the PTA plot folder included."""
    pairs = [(OUT / folder / src.name, src) for folder, src in FILES]
    pairs += [(OUT / "4_pta_plots" / f.name, f) for f in sorted(PTA_PLOTS.iterdir()) if f.is_file()]
    return pairs


def verify_sources() -> dict:
    """Refuse to package a deliverable that is missing, malformed or not fully run."""
    for _, src in manifest():
        assert src.exists(), f"missing: {src.relative_to(ROOT)}"

    vfm = pd.read_csv(ROOT / "ml" / "outputs" / "vfm_submission.csv")
    assert list(vfm.columns) == list(pd.read_csv(ROOT / "docs" / "vfm_submission_template.csv", nrows=0).columns), \
        "vfm_submission.csv does not have the template's columns"
    num = vfm.select_dtypes("number")
    assert not vfm.isna().any().any() and not (num < 0).any().any(), "vfm_submission.csv has NaN or negative rates"
    wells, days = vfm.well_name.nunique(), vfm.timestamp.nunique()
    assert len(vfm) == wells * days, "vfm_submission.csv is not one row per well per day"

    pta = pd.read_csv(ROOT / "ml" / "outputs" / "pta_submission.csv")
    assert list(pta.columns) == list(pd.read_csv(ROOT / "docs" / "pta_submission_template.csv", nrows=0).columns), \
        "pta_submission.csv does not have the template's columns"
    assert len(pta) and (pta.horner_slope >= 0).all() and not pta.isna().any().any(), "pta_submission.csv is malformed"
    sheets = {f: pd.ExcelFile(ROOT / "ml" / "outputs" / f).sheet_names
              for f in ("vfm_daily_predictions.xlsx", "pta_results.xlsx")}

    with (ROOT / "ml" / "models" / "vfm.pkl").open("rb") as fh:
        model = pickle.load(fh)
    assert type(model).__name__ == "VFMModel" and model.choke_coef is not None, "vfm.pkl is not a fitted VFMModel"
    assert isinstance(model.routing_factor, dict), "vfm.pkl carries no routing correction (not written by fit_vfm.py?)"

    cells = {}
    for name in ("VFM_Phase1.ipynb", "PTA_Phase2.ipynb"):
        nb = json.loads((ROOT / "notebooks" / name).read_text(encoding="utf-8"))
        code = [c for c in nb["cells"] if c["cell_type"] == "code"]
        assert all(c.get("execution_count") is not None for c in code), f"{name}: a code cell has not been run"
        assert not any(o.get("output_type") == "error" for c in code for o in c["outputs"]), f"{name}: a cell failed"
        figs = sum("image/png" in o.get("data", {}) for c in code for o in c["outputs"])
        cells[name] = (len(nb["cells"]), len(code), figs)

    pngs = sorted(f.name for f in PTA_PLOTS.glob("*.png"))
    for w in pta.well_name:
        assert any(f"_{w}_" in f for f in pngs), f"no PTA plot for {w}"
    return dict(vfm_rows=len(vfm), wells=wells, days=days, first=vfm.timestamp.min(), last=vfm.timestamp.max(),
                pta_rows=len(pta), pta_wells=", ".join(pta.well_name), sheets=sheets, trained_on=model.trained_on,
                cells=cells, pngs=len(pngs), buildup_pngs=sum("buildup" in f for f in pngs))


def readme(i: dict) -> str:
    v, p = i["cells"]["VFM_Phase1.ipynb"], i["cells"]["PTA_Phase2.ipynb"]
    return f"""# Deliverables — SOCAR Hackathon 2026

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
| `vfm_submission.csv` | **Phase 1.** Daily oil, water and gas rate for {i['wells']} wells × {i['days']} days ({i['first']} to {i['last']}), {i['vfm_rows']:,} rows, in the organisers' template. These are the predictions that scored **{VFM_SCORE}** on the leaderboard; some rows differ from the uploaded file by 0.1 in the last decimal, from rounding. |
| `vfm_daily_predictions.xlsx` | The same daily rates as Excel, with the share of the day covered by sensor data and a low-coverage flag. |
| `pta_submission.csv` | **Phase 2.** Permeability, skin, ΔP skin and Horner slope for the {i['pta_rows']} build-ups ({i['pta_wells']}), in the organisers' template. Identical to the file that scored **{PTA_SCORE}**. |
| `pta_results.xlsx` | The same results as Excel. Sheets: {", ".join(f"`{s}`" for s in i['sheets']['pta_results.xlsx'])}. |

Only six of the ten wells were ever shut in, so only those six have a well-test result.

## 2. Trained model

`vfm.pkl` is the VFM model: a choke-flow law for the liquid rate and a water-cut split from the
tubing pressure drop, fitted on the {i['trained_on']} measured well tests, with the per-well
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
| `VFM_Phase1.ipynb` | Phase 1 end to end: data defects and cleaning, the model, time-forward validation, the routing correction, the daily predictions, and the three test months. {v[0]} cells, {v[1]} code cells, {v[2]} figures, all run. |
| `PTA_Phase2.ipynb` | Phase 2 end to end: the six build-ups, the model match, the submitted table, and two tests on data the fit never saw. {p[0]} cells, {p[1]} code cells, all run. |

Both were executed in `notebooks/` at the repository root and read the code in `ml/`. To run
them again, use `python ml/build_notebook.py` and `python ml/build_pta_notebook.py` from the root.

## 4. PTA plots

{i['pngs']} figures: two on the theory, one overview of all build-ups, and one per build-up
({i['buildup_pngs']} in total) with the pressure history, Cartesian, log-log with derivative,
Horner and MDH plots and the model match. `README.md` in that folder explains each panel, and
the three `pta_reference_*.csv` tables hold the numbers drawn.

---

The files here are copies of the originals in `ml/outputs/`, `ml/models/` and `notebooks/`.
`python ml/make_submission.py` rebuilds this folder after checking the originals, and
`python ml/make_submission.py --check` confirms that every copy still equals its original.
"""


def same(a: Path, b: Path) -> bool:
    x, y = a.read_bytes(), b.read_bytes()
    if a.suffix in TEXT:
        x, y = x.replace(b"\r\n", b"\n"), y.replace(b"\r\n", b"\n")
    return x == y


def check(info: dict) -> list[str]:
    problems = []
    want = {dst for dst, _ in manifest()} | {OUT / "README.md"}
    for dst, src in manifest():
        if not dst.exists():
            problems.append(f"missing: {dst.relative_to(ROOT)}")
        elif not same(dst, src):
            problems.append(f"out of date: {dst.relative_to(ROOT)} differs from {src.relative_to(ROOT)}")
    if not (OUT / "README.md").exists():
        problems.append("missing: submission/README.md")
    elif (OUT / "README.md").read_text(encoding="utf-8").replace("\r\n", "\n") != readme(info):
        problems.append("out of date: submission/README.md")
    if OUT.exists():
        problems += [f"unexpected file: {f.relative_to(ROOT)}" for f in OUT.rglob("*") if f.is_file() and f not in want]
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify submission/ without changing it")
    a = ap.parse_args()
    info = verify_sources()
    if not a.check:
        if OUT.exists():
            shutil.rmtree(OUT)                  # generated folder: rebuilt from the originals every time
        for dst, src in manifest():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        (OUT / "README.md").write_text(readme(info), encoding="utf-8", newline="\n")
    problems = check(info)
    for x in problems:
        print("  " + x)
    if problems:
        print(f"FAILED: submission/ is not in sync ({len(problems)} problem(s)); run python ml/make_submission.py")
        sys.exit(1)
    files = [dst for dst, _ in manifest()] + [OUT / "README.md"]
    print(f"OK: submission/ holds {len(files)} files, {sum(f.stat().st_size for f in files) / 1e6:.1f} MB, "
          "every one equal to its original")
    for folder in sorted({f.parent for f in files}):
        print(f"  {folder.relative_to(ROOT).as_posix() + '/':26s} "
              + ", ".join(sorted(f.name for f in files if f.parent == folder)))


if __name__ == "__main__":
    main()
