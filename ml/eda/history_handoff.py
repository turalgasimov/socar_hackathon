"""Does an upload of later months still get the most out of the training months?

The test data are the next three months of the same wells: high_freq_data.csv, choke_events.csv
and well_tests.csv (with measured rates) for Oct-Dec only, PVT and completion unchanged. This
rehearses that hand-off inside the data we have, on the app back end (ui/pipeline.analyse):

    upload   = 1 Aug - 30 Sep   (sensors, tests, and choke events from 1 Aug only -- so no well has
                                 an opening choke row, the hardest case)

A. HISTORY, with the shipped model. History = 1 Jan - 31 Jul; run with it and without it.
   GL-08's 19 Aug build-up is the one shut-in in the upload and its submitted answer is known
   (ml/outputs/pta_submission.csv), so the run with history must reproduce it to the app's own
   tolerance (k 0.5%, skin 0.02), every well must be predicted on 1 Aug before its first choke
   change, and the uploaded days must equal the scored file. The shipped model was trained on the
   Aug-Sep tests, so nothing may be refitted here.

B. MONTHLY REFIT, with a model that has not seen Aug-Sep. A model fitted on the tests that ended
   before 1 Aug stands in for the shipped one (saved to a temp dir, never to ml/models/), and the
   history says so. Then the upload's tests are new: August must come from that model unchanged,
   September from a refit that adds the August tests, and the accuracy check must be held-out.
   The app's numbers are checked against the same schemes computed straight from
   data/processed/train_table.parquet, which shares no code path with the upload.

    python ml/eda/history_handoff.py      (~3 min: reads the 257 MB sensor file once)
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "ml"), str(ROOT / "ml" / "src"), str(ROOT / "ui")]

import build_history  # noqa: E402
import pipeline as P  # noqa: E402
from config import DATA  # noqa: E402
from fit_vfm import wape  # noqa: E402
from vfm import ROUTING_FACTORS, VFMModel  # noqa: E402

CUT = pd.Timestamp("2025-08-01")
MID = pd.Timestamp("2025-09-01")
RECORD = build_history.RECORD
PHASES = {"oil": "oil_rate_stbd", "water": "water_rate_stbd", "gas": "gas_rate_mscfd"}


def make_upload(dst: Path) -> None:
    hf = pd.read_csv(DATA / "high_freq_data.csv", parse_dates=["timestamp"])
    hf[hf.timestamp >= CUT].to_csv(dst / "high_freq_data.csv", index=False)
    ck = pd.read_csv(DATA / "choke_events.csv", parse_dates=["timestamp"])
    ck[ck.timestamp >= CUT].to_csv(dst / "choke_events.csv", index=False)
    wt = pd.read_csv(DATA / "well_tests.csv", parse_dates=["test_start"])
    wt[wt.test_start >= CUT].to_csv(dst / "well_tests.csv", index=False)
    for f in ("reservoir_pvt.csv", "well_completion.csv"):
        shutil.copy(DATA / f, dst / f)


def reference() -> dict[str, dict[str, float]]:
    """Frozen and monthly-refit WAPE on the Aug-Sep tests, straight from train_table.parquet."""
    rows = build_history.train_rows(None)
    gas = pd.read_parquet(P.ROOT / "data" / "processed" / "train_table.parquet").sort_values(
        ["well_name", "start"], ignore_index=True).gas_rate_mscfd.to_numpy(float)
    real = {"oil": rows.oil_rate_stbd.to_numpy(), "water": rows.water_rate_stbd.to_numpy(), "gas": gas}
    fit = lambda m: VFMModel().fit(rows[m], real["oil"][m], real["water"][m])  # noqa: E731
    te = (rows.start >= CUT).to_numpy()
    m0, m1 = fit((rows.end < CUT).to_numpy()), fit((rows.end < MID).to_numpy())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p0, p1 = m0.predict(rows[te]), m1.predict(rows[te])
    sep = (rows.start[te] >= MID).to_numpy()
    out = {"frozen": {}, "refit": {}}
    for ph, c in PHASES.items():
        out["frozen"][ph] = wape(real[ph][te], p0[c].to_numpy())
        out["refit"][ph] = wape(real[ph][te], np.where(sep, p1[c].to_numpy(), p0[c].to_numpy()))
    return out


def part_a(runs: dict, ok: bool) -> bool:
    ref = pd.read_csv(ROOT / "ml" / "outputs" / "pta_submission.csv").set_index("well_name")
    rec = pd.read_csv(RECORD)
    print(f"A. HISTORY (shipped model). Upload {CUT:%d %b} - 30 Sep, history to {CUT - pd.Timedelta(days=1):%d %b}; "
          f"choke events from {CUT:%d %b} only (no opening rows)\n")
    for name, r in runs.items():
        q = r["quality"]
        print(f"-- {name}")
        print(f"   choke from history: {q['Wells given their last known choke setting']}; "
              f"no choke: {q['Wells with no choke setting before their first event']}")
        # the uploaded days against the scored file, flowing days and shut-in days apart (both
        # paths time-integrate shut-in days; before 22 Nov the app used the daily mean there)
        m = r["rates"].merge(rec, on=["timestamp", "well_name"], suffixes=("", "_rec"))
        shut = {(e.well, d.strftime("%Y-%m-%d")) for e in r["events"].itertuples()
                for d in pd.date_range(e.start.normalize(), e.end.normalize())}
        in_shut = np.array([(w, t) in shut for w, t in zip(m.well_name, m.timestamp)])
        s = m[in_shut]
        sdev = (s.oil_rate_stbd - s.oil_rate_stbd_rec).abs()
        print(f"   shut-in well-days vs scored file: {len(s)} days, max |diff| {sdev.max():.1f} stb/d "
              f"({', '.join(f'{t} {a:.0f}/{b:.0f}' for t, a, b in zip(s.timestamp, s.oil_rate_stbd, s.oil_rate_stbd_rec))})")
        m = m[~in_shut]
        dev = (m.oil_rate_stbd / m.oil_rate_stbd_rec - 1).abs() * 100
        day1 = dev[m.timestamp.eq(f"{CUT:%Y-%m-%d}").to_numpy()]
        print(f"   1 Aug, before any choke change: {(day1 < 0.5).sum()}/10 wells within 0.5% of the scored file")
        print(f"   oil vs scored file, {len(m)} flowing well-days: median {dev.median():.3f}%, "
              f"p99 {dev.quantile(0.99):.3f}%, max {dev.max():.2f}%")
        for n in r["history_notes"]:
            print(f"   {n}")
        print(f"   monthly refit: {q['Model refitted for months (new tests added)']}")

        row = [x for x, _ in r["pta"] if x.get("well_name") == "GL-08"][0]
        if "error" in row:
            print(f"   GL-08 PTA failed: {row['error']}")
            ok = False
            continue
        k, S, kr, Sr = row["permeability_md"], row["skin"], ref.loc["GL-08", "permeability_md"], ref.loc["GL-08", "skin"]
        good = abs(k / kr - 1) < 0.005 and abs(S - Sr) < 0.02
        print(f"   GL-08 PTA: N_p {row['np_stb']:,} stb, tp {row['tp_h']:,.0f} h, k {k} md (submitted {kr}, "
              f"{(k / kr - 1) * 100:+.3f}%), skin {S} ({S - Sr:+.4f}) -> "
              f"{'matches' if good else 'DOES NOT match'} the submission")
        if name == "with history":
            ok &= good and (day1 < 0.5).sum() == 10 and dev.max() < 0.1 and not r["refit"]["refits"]
        print()
    s = runs["with history"]["score"]
    print(f"   accuracy check on the {s['tests_scored']} uploaded tests: basis '{s.get('basis')}' (the shipped model "
          f"was trained on them, so in-sample is the right label); oil WAPE {s['oil']['WAPE_%']}%\n")
    return ok and s.get("basis") == "in-sample"


def part_b(runs: dict, ok: bool) -> bool:
    want = reference()
    print(f"B. MONTHLY REFIT (a model fitted on tests that ended before {CUT:%d %b}). Same upload.\n")
    fr, rf = runs["frozen"], runs["refit"]
    for name, r in runs.items():
        s = r["score"]
        got = {ph: s[ph]["WAPE_%"] for ph in PHASES}
        same = all(abs(got[ph] - want[name][ph]) < 0.02 for ph in PHASES)
        ok &= same and s.get("basis") == "held-out"
        print(f"-- {name}: refits {r['quality']['Model refitted for months (new tests added)']}")
        print(f"   {s['tests_scored']} tests, basis '{s.get('basis')}', no routing correction. WAPE oil / water / gas: "
              f"{got['oil']:.2f} / {got['water']:.2f} / {got['gas']:.2f}%")
        print(f"   straight from train_table.parquet:                          "
              f"{want[name]['oil']:.2f} / {want[name]['water']:.2f} / {want[name]['gas']:.2f}%  -> "
              f"{'agrees' if same else 'DOES NOT agree'}")
    refits = rf["refit"]["refits"]
    n_aug = int((pd.read_csv(DATA / "well_tests.csv", parse_dates=["test_start", "test_end"])
                 .query("test_start >= @CUT and test_end < @MID")).shape[0])
    one = len(refits) == 1 and refits[0]["month"] == "2025-09" and refits[0]["tests_added"] == n_aug
    m = fr["rates"].merge(rf["rates"], on=["timestamp", "well_name"], suffixes=("_fr", "_rf"))
    d = (m.oil_rate_stbd_rf / m.oil_rate_stbd_fr.replace(0, np.nan) - 1) * 100
    aug = (m.timestamp < f"{MID:%Y-%m-%d}").to_numpy()
    print(f"\n   one refit, for September, adding the {n_aug} August tests: {'yes' if one else 'NO'}")
    print(f"   August daily oil, refit vs frozen: max |change| {d[aug].abs().max():.4f}% (must be 0)")
    print(f"   September daily oil, refit vs frozen: mean {d[~aug].mean():+.2f}%, range "
          f"{d[~aug].min():+.2f}% to {d[~aug].max():+.2f}%; no file written to ml/models/\n")
    return ok and one and d[aug].abs().max() == 0 and d[~aug].abs().max() > 0


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="handoff_"))
    try:
        up, hist_a, hist_b, empty = tmp / "upload", tmp / "history_a", tmp / "history_b", tmp / "none"
        for d in (up, empty):
            d.mkdir()
        make_upload(up)
        end = CUT - pd.Timedelta(days=1)
        build_history.build(end, hist_a)                       # shipped model: every test is training
        a = {"with history": P.analyse(up, history_dir=hist_a),
             "no history": P.analyse(up, history_dir=empty)}

        build_history.build(end, hist_b, trained_to=CUT)       # the stand-in model's training set
        rows = build_history.train_rows(CUT)
        july = VFMModel(routing_factor=dict(ROUTING_FACTORS)).fit(
            rows, rows.oil_rate_stbd.to_numpy(), rows.water_rate_stbd.to_numpy())
        july.save(tmp / "vfm_to_july.pkl")                     # temp dir only; ml/models/ is fit_vfm's
        b = {"frozen": P.analyse(up, history_dir=hist_b, model_path=tmp / "vfm_to_july.pkl", refit=False),
             "refit": P.analyse(up, history_dir=hist_b, model_path=tmp / "vfm_to_july.pkl")}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = part_a(a, True)
    ok = part_b(b, ok)
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
