"""Why does VFM move more than the IPR between a test day and a normal day?

    python ml/check_choke_response.py

The other agent's #2 found that on GL-06 the same choke setting (29.7%) on the
19 Jul test and the 21 Jul last full flowing day gives VFM 696.7 -> 654.1
(-6.1%), while an IPR built on the measured drawdown says about -3%. Same for
GL-02 (VFM -1.8% vs IPR -5.0%) and GL-10 (VFM -9.8% vs IPR -7.1%). They called
it "choke-law routing over-response". This checks that premise from the VFM side
and asks whether the choke law can be responsible.

THE MECHANISM UNDER TEST
------------------------
The shipped VFM liquid rate is a subcritical choke law,

    qL  ~  S^2.057 * dPc^0.472 ,      dPc = whp - whp_downstream

so at a FIXED choke setting S the only thing that can move qL is dPc. A well
routed to the test separator sees a different downstream pressure than one
routed to the production manifold, so routing moves whp_downstream, which moves
dPc, which moves qL through the 0.472 exponent. That is a real path by which
routing changes the predicted rate, and it is separate from the multiplicative
ROUTING_FACTORS already in the model.

CRITICAL FLOW IS *NOT* THE EXPLANATION -- THAT WAS ALREADY REJECTED
-------------------------------------------------------------------
The tempting story is that these wells are in CRITICAL (sonic) flow, where the
rate does not depend on downstream pressure at all, so dPc^0.472 would be
attributing a sensitivity the physics does not have.

`ml/eda/routing_checks.py` already tested that and rejected it, and its test is
much stronger than anything here: it fits the dPc exponent separately above and
below a pressure ratio of 0.60 AGAINST THE MEASURED RATES, and gets 0.475 above
versus 0.478 below, zero mean residual either side, with 46 of 85 tests on the
low side. Critical flow would drive the low-ratio exponent toward zero. It does
not budge.

So section 1 below reports the pressure-ratio regime per well as context ONLY.
Do not read a criticality explanation into it: knowing which side of 0.60 a well
sits on says nothing about whether its rate responds to dPc, and the labelled
test above answers that question directly.

What this script does establish is narrower and already-known in direction: the
choke law's dPc term is the specific channel through which routing moves the
predicted rate, and it over-responds. PROJECT_STATE.md records the magnitude
(choke law 5.89% against the adopted 2.5%, overstating by ~2.4x); sections 2 and
4 decompose it per case and per well.

Sections:
  1. pressure-ratio regime per well, flowing minutes only -- CONTEXT ONLY
  2. test day vs normal day at MATCHED CHOKE, so the S^2.057 term drops out and
     the dPc term is isolated -- the direct answer to "why does VFM move more
     than the IPR"
  3. whp against whp_downstream at fixed choke -- CONFOUNDED, kept for
     completeness, not evidence
  4. how much of each measured routing factor the dPc term alone reproduces

Diagnostic only. Writes ml/outputs/choke_response_check.csv and changes nothing
that ships.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml" / "src"))
warnings.filterwarnings("ignore")

from config import F_HF_CLEAN, F_WT_CLEAN, OUT  # noqa: E402

S_EXP, DP_EXP = 2.057, 0.472          # the shipped choke-law exponents
CRIT = 0.60                            # conventional multiphase critical ratio

# the three wells the other agent flagged, with their last full flowing day
CASES = {
    "GL-06": ("2025-07-21", -6.1, -3.0),
    "GL-02": ("2025-03-07", -1.8, -5.0),
    "GL-10": ("2025-05-26", -9.8, -7.1),
}


def main() -> None:
    hf = pd.read_parquet(F_HF_CLEAN, columns=[
        "timestamp", "well_name", "whp_psia", "whp_downstream_psia",
        "choke_pct", "is_shut_in", "dp_choke"])
    hf = hf[~hf.is_shut_in].dropna(
        subset=["whp_psia", "whp_downstream_psia", "choke_pct"])
    hf["ratio"] = hf.whp_downstream_psia / hf.whp_psia

    print("1. PRESSURE-RATIO REGIME  whp_downstream / whp, flowing minutes "
          "only -- CONTEXT ONLY")
    print(f"   {CRIT:.2f} is the conventional critical threshold, but "
          f"ml/eda/routing_checks.py already REJECTED")
    print("   critical flow on the labelled rates (dPc exponent 0.475 above vs "
          "0.478 below 0.60).")
    print("   Do NOT read an explanation into this table.\n")
    print(f"   {'well':7s} {'n min':>9s} {'whp':>8s} {'whp_dn':>8s} "
          f"{'ratio p5':>9s} {'median':>8s} {'p95':>7s} {'% < 0.60':>9s} "
          f"{'regime':>12s}")
    rows = []
    for w, g in hf.groupby("well_name", observed=True):
        q = g.ratio.quantile([0.05, 0.5, 0.95]).to_numpy()
        frac = float((g.ratio < CRIT).mean() * 100)
        regime = ("critical" if frac > 95 else
                  "subcritical" if frac < 5 else "mixed")
        print(f"   {w:7s} {len(g):9,d} {g.whp_psia.mean():8.1f} "
              f"{g.whp_downstream_psia.mean():8.1f} {q[0]:9.3f} {q[1]:8.3f} "
              f"{q[2]:7.3f} {frac:8.1f}% {regime:>12s}")
        rows.append(dict(well_name=w, n_min=len(g), whp_mean=g.whp_psia.mean(),
                         whp_dn_mean=g.whp_downstream_psia.mean(),
                         ratio_p5=q[0], ratio_median=q[1], ratio_p95=q[2],
                         pct_below_crit=frac, regime=regime))
    crit = pd.DataFrame(rows)
    nc = int((crit.regime == "critical").sum())
    print(f"\n   {nc}/{len(crit)} wells sit below {CRIT:.2f} on >95% of "
          f"flowing minutes (field median ratio "
          f"{crit.ratio_median.median():.3f}).")
    print("   A description of the operating point, not evidence about the "
          "rate's dPc response.")

    print("\n2. TEST DAY vs NORMAL DAY at matched choke -- how much does the "
          "dPc term explain?\n")
    tests = pd.read_parquet(F_WT_CLEAN)
    print("   the test is chosen for the CLOSEST CHOKE to the normal day, not "
          "the closest date: a choke")
    print("   mismatch would put a large S^2.057 term into a comparison meant "
          "to isolate dPc.\n")
    print(f"   {'well':7s} {'test day':>11s} {'days':>5s} {'choke t':>8s} "
          f"{'choke n':>8s} | {'dPc t':>7s} {'dPc n':>7s} {'d dPc':>7s} | "
          f"{'S term':>7s} {'dPc term':>9s} {'law tot':>8s} {'VFM obs':>8s} "
          f"{'IPR':>7s}")
    out = []
    for w, (day, vfm_pct, ipr_pct) in CASES.items():
        t = tests[tests.well_name == w].copy()
        t["mid"] = t.test_start + (t.test_end - t.test_start) / 2
        nd = pd.Timestamp(day)
        gn = hf[(hf.well_name == w) & (hf.timestamp >= nd)
                & (hf.timestamp < nd + pd.Timedelta("1D"))]
        if gn.empty:
            continue
        cn, dn = gn.choke_pct.mean(), gn.dp_choke.mean()
        # pick the test whose choke matches the normal day most closely
        cand = []
        for tr in t.itertuples():
            gt = hf[(hf.well_name == w) & (hf.timestamp >= tr.test_start)
                    & (hf.timestamp <= tr.test_end)]
            if gt.empty:
                continue
            cand.append((abs(gt.choke_pct.mean() - cn), tr, gt))
        if not cand:
            continue
        _, tr, gt = min(cand, key=lambda z: z[0])
        ct, dt_ = gt.choke_pct.mean(), gt.dp_choke.mean()
        dpc_term = ((dn / dt_) ** DP_EXP - 1) * 100
        s_term = ((cn / ct) ** S_EXP - 1) * 100
        law = ((cn / ct) ** S_EXP * (dn / dt_) ** DP_EXP - 1) * 100
        gap_d = abs((tr.mid - nd).days)
        print(f"   {w:7s} {tr.mid.strftime('%Y-%m-%d'):>11s} {gap_d:5d} "
              f"{ct:8.2f} {cn:8.2f} | {dt_:7.1f} {dn:7.1f} "
              f"{(dn/dt_-1)*100:+6.1f}% | {s_term:+6.1f}% {dpc_term:+8.1f}% "
              f"{law:+7.1f}% {vfm_pct:+7.1f}% {ipr_pct:+6.1f}%")
        out.append(dict(well_name=w, test_day=tr.mid.strftime("%Y-%m-%d"),
                        gap_days=gap_d, law_total_pct=law,
                        normal_day=day, choke_test=ct, choke_normal=cn,
                        dpc_test=dt_, dpc_normal=dn,
                        dpc_change_pct=(dn / dt_ - 1) * 100,
                        dpc_term_pct=dpc_term, choke_term_pct=s_term,
                        vfm_observed_pct=vfm_pct, ipr_pct=ipr_pct,
                        whp_test=gt.whp_psia.mean(), whp_normal=gn.whp_psia.mean(),
                        whp_dn_test=gt.whp_downstream_psia.mean(),
                        whp_dn_normal=gn.whp_downstream_psia.mean(),
                        ratio_test=gt.ratio.mean(), ratio_normal=gn.ratio.mean()))
    cases = pd.DataFrame(out)
    print("\n   'law tot' is the whole choke law S^2.057 dPc^0.472; the gap to "
          "'VFM obs' is the water-cut\n   and GOR split, which the law does not "
          "carry. The dPc term is the channel\n   routing acts through, and it "
          "over-responds -- the known defect: the choke law says\n   5.89% "
          "against the 2.5% four other methods agree on.")

    print("\n3. DOES whp RESPOND TO whp_downstream AT A FIXED CHOKE?")
    print("   CONFOUNDED, reported for completeness only: whp and "
          "whp_downstream both drift with")
    print("   manifold conditions over nine months, so a positive slope can be "
          "common-mode movement")
    print("   rather than choke coupling. The criticality ratio in section 1 is "
          "the standard test.\n")
    print(f"   {'well':7s} {'choke':>7s} {'n min':>8s} {'slope':>8s} "
          f"{'r':>7s} {'sd whp_dn':>10s} {'reads as':>14s}")
    srows = []
    for w, g in hf.groupby("well_name", observed=True):
        big = g.choke_pct.value_counts().idxmax()
        s = g[(g.choke_pct == big)
              & g.whp_psia.notna() & g.whp_downstream_psia.notna()]
        if len(s) < 500 or s.whp_downstream_psia.std() < 0.5:
            continue
        x = s.whp_downstream_psia.to_numpy(float)
        y = s.whp_psia.to_numpy(float)
        slope = float(np.polyfit(x, y, 1)[0])
        r = float(np.corrcoef(x, y)[0, 1])
        reads = "subcritical" if slope > 0.5 and r > 0.3 else "critical-like"
        print(f"   {w:7s} {big:7.2f} {len(s):8,d} {slope:+8.3f} {r:+7.3f} "
              f"{x.std():10.2f} {reads:>14s}")
        srows.append(dict(well_name=w, choke_pct=big, n_min=len(s),
                          whp_slope=slope, whp_r=r, whp_dn_sd=x.std(),
                          reads_as=reads))
    sl = pd.DataFrame(srows)

    print("\n4. HOW MUCH OF THE ROUTING FACTOR IS JUST THE dPc TERM?")
    print("   test windows are test-separator routed; all other flowing "
          "minutes are manifold routed.")
    print("   If routing moves whp_downstream, the dPc^0.472 term turns that "
          "into a rate change -- which")
    print("   predicted rate change, and ROUTING_FACTORS is what then undoes "
          "the part reality\n   does not show.\n")
    from vfm import _ROUTING_FACTORS_RAW as RAW  # noqa: E402
    tw = []
    for tr in tests.itertuples():
        tw.append(hf[(hf.well_name == tr.well_name)
                     & (hf.timestamp >= tr.test_start)
                     & (hf.timestamp <= tr.test_end)].assign(on_test=True))
    tw = pd.concat(tw, ignore_index=True)
    print(f"   {'well':7s} {'regime':>12s} {'dPc test':>9s} {'dPc other':>10s} "
          f"{'d dPc':>7s} {'dPc^0.472':>10s} {'routing raw':>12s} "
          f"{'explained':>10s}")
    rrows = []
    for w in sorted(RAW):
        a = tw[tw.well_name == w].dp_choke.mean()
        idx = tw[tw.well_name == w].index
        b = hf[(hf.well_name == w)
               & ~hf.timestamp.isin(tw.loc[idx, "timestamp"])].dp_choke.mean()
        if not (np.isfinite(a) and np.isfinite(b)):
            continue
        implied = (a / b) ** DP_EXP          # test/other, same sense as RAW
        reg = crit.loc[crit.well_name == w, "regime"].iloc[0]
        share = (implied - 1) / (RAW[w] - 1) * 100 if RAW[w] != 1 else np.nan
        print(f"   {w:7s} {reg:>12s} {a:9.1f} {b:10.1f} "
              f"{(a/b-1)*100:+6.1f}% {implied:10.4f} {RAW[w]:12.4f} "
              f"{share:9.0f}%")
        rrows.append(dict(well_name=w, dpc_on_test=a, dpc_off_test=b,
                          dpc_implied_factor=implied, routing_raw=RAW[w],
                          explained_pct=share))
    rt = pd.DataFrame(rrows)
    print(f"\n   'explained' is how much of the measured routing factor the "
          f"spurious dPc term alone")
    print(f"   accounts for: median {rt.explained_pct.median():.0f}% across "
          f"the ten wells.")

    dest = OUT / "choke_response_check.csv"
    crit.merge(sl, on="well_name", how="outer").merge(
        cases, on="well_name", how="outer").merge(
        rt, on="well_name", how="outer").round(6).to_csv(dest, index=False)
    print(f"\n   wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
