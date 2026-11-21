"""Generate and execute notebooks/PTA_Phase2.ipynb -- the Phase 2 (PTA) part of deliverable 3.

    python ml/build_pta_notebook.py           build and execute (nbformat, nbclient, ipykernel; ~3 min)
    python ml/build_pta_notebook.py --check   run the code cells as plain Python, no Jupyter needed

Same pattern as ml/build_notebook.py: cells import from ml/src and ml/eda, so the notebook is the
narrative and the modules stay the source of truth, and the committed outputs always come from a
fresh run. Figures are shown inline; running the notebook writes no files.
Needs data/processed/high_freq_clean.parquet (AGENTS.md run order, step 1).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "PTA_Phase2.ipynb"

CELLS = [
    ("md", """# SOCAR Hackathon 2026 — Phase 2: Pressure Transient Analysis

Six shut-ins, six build-ups. For each one: permeability, skin, ΔP_skin and the Horner slope,
computed on the oil rate predicted in Phase 1, as the brief requires.

**Result: 8.3840 / 20 on the leaderboard, the best of the PTA submissions.**

The submitted answer is an **exact model match**. The radial diffusivity equation, with wellbore
storage, skin and an outer boundary, is solved in Laplace space and fitted to every point of each
build-up. The Horner straight line is computed alongside it as the textbook reference.

This notebook rebuilds the submitted file from the 1-minute gauge data. It also shows the evidence
behind each choice, including two checks on data the fit never saw:
- a forecast of the late build-up from its early part;
- an alternative boundary that the data reject."""),

    ("md", "## Setup"),
    ("code", """import sys, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
for p in ("ml/src", "ml/eda", "ml"):
    sys.path.insert(0, str(ROOT / p))
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)

import viz
import pta_model as PM       # diffusivity equation: Laplace solutions, Stehfest inversion, least-squares fit
import pta_explore as X      # data access, Horner windows, figures (loads the 1-minute gauge data)
import make_pta as MP        # builds and checks the submitted file

try:
    from IPython.display import display
except ImportError:          # plain-Python check run
    display = print

def show(fig, path=None):
    # pta_explore saves its figures to ml/outputs/figures/pta/; here they are shown inline instead
    fig.tight_layout(rect=(0, 0, 1, getattr(fig, "_viz_top", 0.95)))
    display(fig)
    plt.close(fig)

viz.save = show
viz.apply_style()
print(f"{len(X.HF):,} gauge readings loaded")"""),

    ("md", """## 1. The build-ups

A build-up exists only where the choke closes: `choke_opening_pct = 0` in `choke_events.csv`,
which also stops gas lift. That gives six events on six wells. GL-03, GL-05, GL-07 and GL-09
never shut in, so no PTA is possible on them."""),
    ("code", """ev = X.shut_in_events()
evd = {e.well: e for e in ev.itertuples()}
rows = []
for e in ev.itertuples():
    r, _ = X.interpret(e, "T1", "B")
    rows.append(dict(well=e.well, shut_in=e.start, reopened=e.end, duration_h=r["duration_h"],
                     pwf_at_shut_in_psia=r["pwf_gauge_psia"], last_pressure_psia=r["p_end_gauge_psia"],
                     build_up_psi=round(r["p_end_gauge_psia"] - r["pwf_gauge_psia"], 1)))
pd.DataFrame(rows)"""),

    ("md", """## 2. Inputs

**Rate.** q is the Phase 1 predicted **oil** rate on the last full flowing day before the shut-in.
It comes from the shipped Task 1 file, which scored 21.0200 on the VFM leaderboard.
- k is proportional to q, so the VFM accuracy carries straight into k.
- m and ΔP_skin are set by the pressure data and barely depend on q.

**Producing time.** N_p = cumulative oil at 2025-01-01 + predicted daily oil up to the shut-in.
t_p = 24·N_p/q is the Horner pseudo-producing time.

**Rock and fluid** come from `reservoir_pvt.csv`. Single-phase oil holds, because the downhole
pressure stays above the bubble point on every well.

**Datum.** The gauge sits above the datum. The hydrostatic offset is constant through a build-up,
so it cancels in every pressure difference (checked in section 6)."""),
    ("code", """inp = []
for e in ev.itertuples():
    r, _ = X.interpret(e, "T1", "B")
    P = X.PVT.loc[e.well]
    inp.append(dict(well=e.well, q_oil_stbd=r["qo_stbd"], Np_stb=r["np_stb"], tp_h=r["tp_h"],
                    h_ft=P.net_pay_thickness_ft, phi=P.porosity_frac, ct_per_psi=P.total_compressibility_1_psi,
                    rw_ft=P.wellbore_radius_ft, Bo_rb_stb=P.oil_fvf_rb_stb, mu_cp=P.oil_viscosity_cp,
                    gauge_to_datum_psi=r["datum_offset_psi"]))
pd.DataFrame(inp)"""),

    ("md", """## 3. How to read a build-up

These are analytical type curves from the same Laplace solutions the fit uses. Each panel shows
Δp and the Bourdet derivative for a different reservoir, and these are the shapes to compare the
real derivatives against:
- **Wellbore storage:** unit slope.
- **IARF:** flat derivative at m/2.303.
- **Closed boundary in a build-up:** the derivative falls towards p̄.
- **Sealing fault:** the derivative doubles.

The second figure shows that skin changes the size of the storage hump but not the IARF level.
This is why k from the IARF level is skin-free."""),
    ("code", """X.theory_figures()"""),

    ("md", """## 4. The six build-ups and the model match

Dots are the measured Δp and Bourdet derivative, on a 40-points-per-log-cycle grid where each
point is the median of the 1-minute readings in its bin. Lines are the fitted model:
wellbore storage + skin + radial flow + boundary.

The boundary is chosen per well:
- the closed circle is kept only when it cuts the misfit by more than 30%, which happens on
  GL-01 and GL-10;
- the other four wells are infinite-acting for the whole test."""),
    ("code", """A, B, M, plots, curves = {}, {}, {}, {}, {}
for e in ev.itertuples():
    A[e.well], plots[e.well] = X.interpret(e, "T1", "A")
    B[e.well], _ = X.interpret(e, "T1", "B")
    M[e.well], curves[e.well] = X.model_match(e, "T1")
X.overview_figure(ev, plots, A, M, curves)"""),
    ("md", """Every build-up with all the classic plots:
- **A.** pressure history;
- **B.** Cartesian build-up with the model;
- **C.** log-log diagnostic with the model;
- **D.** Horner plot;
- **E.** MDH plot;
- **F.** results table comparing Horner windows A and B with the model."""),
    ("code", """for e in ev.itertuples():
    X.event_figure(e, A[e.well], plots[e.well], B[e.well], M[e.well], curves[e.well])"""),

    ("md", """## 5. Horner straight line vs exact model

The Horner line uses k = 162.6·q·B·μ/(m·h) and
S = 1.151·[(P1hr − p_wf)/m − log10(k/(φ·μ·c_t·r_w²)) + 3.2275]. It is fitted on two windows:
- **Window A:** the IARF plateau, i.e. the longest run where the derivative is flat within ±0.10
  in log-slope.
- **Window B:** the last 0.3 log-cycle of that plateau, the points furthest from wellbore storage.

The model needs no window. It fits every point and reports the slope it implies,
m = 162.6·q·B·μ/(k·h), and ΔP_skin = 0.869·m·S."""),
    ("code", """cols = ["well_name", "window", "window_start_h", "window_end_h", "horner_slope_psi_per_cycle",
        "permeability_md", "skin", "delta_p_skin_psi", "note"]
pd.concat([pd.DataFrame(A.values()), pd.DataFrame(B.values())])[cols].sort_values(["well_name", "window"]).reset_index(drop=True)"""),
    ("code", """tM = pd.DataFrame(M.values())
tM[["well_name", "boundary", "permeability_md", "skin", "delta_p_skin_psi", "horner_slope_psi_per_cycle",
    "storage_bbl_per_psi", "r_e_ft", "fit_rms_psi", "fit_max_abs_psi", "rms_infinite_psi", "rms_closed_psi"]].round(4)"""),
    ("md", """**Why the model and the Horner line differ.** `der_B_over_iarf` divides the median measured
derivative in window B by the IARF level the model converges to.

- **GL-08 (72 h, infinite-acting):** the ratio is 1.004, and model and Horner agree within 0.3% on k.
  This is the textbook case, and the two methods agree where the textbook method holds.
- **GL-02, GL-04 and GL-06:** the derivative is still 3–5% above the IARF level when the test ends,
  because it is still coming down from the storage hump.
  - A straight line through those points is too steep.
  - The model fits the storage-to-IARF transition explicitly, so its k is 3–4.4% higher than Horner B
    and its skin about 0.26–0.29 higher.
- **Leaderboard:** together with a rate update, this took the score from 7.38 (Horner B) to 8.38
  (section 8)."""),
    ("code", """cmp = tM[["well_name", "boundary", "der_B_over_iarf"]].copy()
cmp["k_model_vs_hornerB_pct"] = 100 * (tM.permeability_md / tM.k_horner_B - 1)
cmp["skin_model_minus_hornerB"] = tM.skin - tM.skin_horner_B
cmp.round(3)"""),

    ("md", """## 6. The submitted file, rebuilt and checked

`ml/make_pta.py` builds the result file and refuses to write unless all of these hold:
- the columns match the template;
- `horner_slope` ≥ 0 (the platform rejects negative slopes);
- every fit is under 0.2 psi RMS;
- k, S, m and ΔP_skin are unchanged (relative change < 1e-6) when every pressure is shifted by the
  gauge→datum offset;
- the output is **identical to the file that was scored**.

It also measures the numerical precision of the fit. k and S are correlated, so the misfit valley
is flat."""),
    ("code", """sub, full, horner = MP.build()     # datum-invariance and fit checks run inside, per event
MP.check(sub)                      # template, slope >= 0, identical to the scored file
print("identical to the scored file:", MP.SHIPPED.name)
print(f"numerical precision (float32 vs float64 input): k <= {100 * full.k_rel_diff_float64.max():.3f} %, "
      f"skin <= {full.skin_diff_float64.max():.4f}")
sub"""),

    ("md", """## 7. Validation on data the fit never saw

A good fit is not proof: with three or four free parameters, a wrong model can still fit well.
Two tests use information the fit did not see.

**(a) Forecast.** Fit the model on the early part of a build-up only, then predict the rest. This
needs the long build-ups: GL-01 and GL-08 (72 h), GL-04 (48 h); GL-10 has 9 h.

**(b) The alternative boundary.** A constant-pressure boundary (aquifer support) also makes a
build-up derivative fall, so on GL-01 and GL-10 the log-log shape alone does not exclude it. It is
fitted the same way and compared."""),
    ("code", """def residual_runs(res):
    s = np.sign(res)
    return 1 + int(np.sum(s[1:] != s[:-1]))

def full_fit(w, boundary):
    e = evd[w]; r, p = X.interpret(e, "T1", "B"); m = M[w]
    tg, dp, rk = p["tg"], p["dpg"], X.rock(w)
    if boundary == m["boundary"]:   # the submitted fit
        f = dict(k=m["permeability_md"], S=m["skin"], C=m["storage_bbl_per_psi"], re=m["r_e_ft"])
        f["theta"] = np.array([np.log(f["k"]), f["S"], np.log(f["C"])] + ([np.log(f["re"])] if np.isfinite(f["re"]) else []))
    else:                           # alternative boundary: several r_e seeds, keep the best
        area_r = np.sqrt(X.PVT.loc[w, "estimated_drainage_area_acres"] * 43560 / np.pi)
        f = min((PM.fit_buildup(tg, dp, r["tp_h"], r["qo_stbd"], rk, m["permeability_md"], m["skin"],
                                m["storage_bbl_per_psi"], boundary, re0) for re0 in (m["r_e_ft"], area_r, 0.8 * m["r_e_ft"])),
                key=lambda d: d["rms_psi"])
    res = PM.buildup_dp(f["theta"], tg, r["tp_h"], r["qo_stbd"], rk, boundary) - dp
    late = tg >= 0.1 * tg.max()
    return dict(f, rms=float(np.sqrt(np.mean(res ** 2))), runs=f"{residual_runs(res[late])}/{late.sum()}")

def forecast(w, t_fit, boundary):
    e = evd[w]; r, p = X.interpret(e, "T1", "B")
    tg, dp, rk = p["tg"], p["dpg"], X.rock(w)
    f0 = full_fit(w, boundary)
    fit = PM.fit_buildup(tg[tg <= t_fit], dp[tg <= t_fit], r["tp_h"], r["qo_stbd"], rk, f0["k"], f0["S"], f0["C"],
                         boundary, f0["re"] if boundary != "infinite" else None)
    rest = tg > t_fit
    err = PM.buildup_dp(fit["theta"], tg[rest], r["tp_h"], r["qo_stbd"], rk, boundary) - dp[rest]
    return dict(well=w, model=boundary, fitted_on=f"dt <= {t_fit:g} h", forecast=f"{t_fit:g} - {tg.max():.0f} h",
                rms_in_fit_psi=round(fit["rms_psi"], 4), rms_forecast_psi=round(float(np.sqrt(np.mean(err ** 2))), 4),
                max_forecast_error_psi=round(float(np.abs(err).max()), 3),
                rise_over_forecast_psi=round(float(dp[rest][-1] - dp[~rest][-1]), 1),
                k_early_part_vs_full_pct=round(100 * (fit["k"] / f0["k"] - 1), 2))

pd.DataFrame([forecast("GL-08", 7.2, "infinite"), forecast("GL-04", 16, "infinite"),
              forecast("GL-01", 24, "closed"), forecast("GL-10", 3, "closed"),
              forecast("GL-01", 24, "constant_pressure"), forecast("GL-10", 3, "constant_pressure")])"""),
    ("code", """alt = []
for w in ("GL-01", "GL-10"):
    for b in ("closed", "constant_pressure"):
        f = full_fit(w, b)
        alt.append(dict(well=w, boundary=b, k_md=round(f["k"], 2), skin=round(f["S"], 3), r_e_ft=round(f["re"]),
                        fit_rms_psi=round(f["rms"], 4), late_residual_sign_runs=f["runs"]))
pd.DataFrame(alt)"""),
    ("md", """**Reading.**

- **Closed wells forecast at noise level.**
  - GL-01, fitted on its first 24 h, forecasts the next 48 h at 0.04 psi RMS, the same as its
    in-fit misfit.
  - GL-10, fitted on 3 h, forecasts the next 6 h at 0.07 psi.
- **Infinite-acting wells extrapolate well, but not to noise level.**
  - GL-08 and GL-04 forecast a decade and half a decade ahead to 0.15–0.18 psi RMS, which is about
    0.2% of the pressure rise over that period.
  - k from the early part alone is within 0.2% of the full-data k.
  - The forecast error is above noise because the late data carry small systematic effects that a
    constant-rate model does not contain, such as the rate history before the shut-in.
- **The constant-pressure alternative fails.** It misses by 7–9x in the full fit and 8–48x in the
  forecast. It also leaves long same-sign residual runs (3 in 41). A model that leaves only noise
  flips sign about every other point (≈ 21 runs in 41).

So the build-ups say closed boundary on GL-01 and GL-10. The k and skin reported for those wells
rest on a boundary model the data support, not on a choice."""),

    ("md", """## 8. Leaderboard and limits

| submission | rate | score / 20 |
|---|---|--:|
| Horner, window A (IARF plateau) | Phase 1 S1 | 7.2458 |
| Horner, window B (late IARF points) | Phase 1 S1 | 7.3809 |
| **Exact model match (this notebook)** | **Phase 1 shipped, λ = 0.80** | **8.3840** |
| same values, slope reported negative | — | rejected: `horner_slope` must be ≥ 0 |
| Horner B with k from the total liquid rate | — | 4.8375 |

**What the leaderboard settled:**
- the reference uses the **oil** rate;
- the slope is a **positive** m.

**What it did not settle:** the model match changed two things at once against Horner B, the rate
and the method. The rate alone moves k by only 0.4–1.1% on these wells, so most of the gain is the
method. That is an inference; no single-change probe isolated it.

**Limits:**
- **Daily rate.** The rate is a daily Phase 1 value at constant q with t_p = 24·N_p/q, as the brief
  asks. An hourly rate history would make the superposition exact.
- **Equivalent radius.** r_e is the radius of an equivalent closed circle. Other closed shapes were
  not fitted.
- **p\\*.** p* depends on t_p and is reported for completeness only."""),
]


def check() -> None:
    """Run every code cell as plain Python in one namespace (no Jupyter)."""
    import ast
    import matplotlib
    matplotlib.use("Agg")
    os.chdir(ROOT)
    ns: dict = {"__name__": "__pta_notebook_check__"}
    for i, (kind, src) in enumerate(CELLS):
        if kind != "code":
            continue
        tree = ast.parse(src)
        last = tree.body[-1] if tree.body and isinstance(tree.body[-1], ast.Expr) else None
        if last is not None:                   # mimic Jupyter: show the value of a trailing expression
            tree.body = tree.body[:-1]
        exec(compile(tree, f"<cell {i}>", "exec"), ns)
        if last is not None:
            val = eval(compile(ast.Expression(last.value), f"<cell {i}>", "eval"), ns)
            if val is not None:
                print(val.to_string() if hasattr(val, "to_string") else val)
        print(f"--- cell {i} ok")
    print("all code cells ran")


def main() -> None:
    import nbformat as nbf
    from nbclient import NotebookClient
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    nb = nbf.v4.new_notebook(cells=[md(s) if k == "md" else code(s) for k, s in CELLS])
    nb.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python"}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"executing {len(CELLS)} cells...")
    NotebookClient(nb, timeout=1800, kernel_name="python3",
                   resources={"metadata": {"path": str(OUT.parent)}}).execute()
    nbf.write(nb, OUT)
    n_out = sum(1 for c in nb.cells if c.cell_type == "code" and c.get("outputs"))
    print(f"wrote {OUT.relative_to(ROOT)} -- {n_out} code cells with outputs")


if __name__ == "__main__":
    check() if "--check" in sys.argv else main()
