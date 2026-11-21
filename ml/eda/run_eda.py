"""Exploratory data analysis for the SOCAR 2026 well-performance dataset.

Run from anywhere:  python ml/eda/run_eda.py
Writes figures to ml/outputs/figures/ and a text summary to ml/outputs/eda_summary.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import viz  # noqa: E402
from config import (  # noqa: E402
    F_COMPLETION, F_HF_CLEAN, F_PVT, F_WT_CLEAN, FIGS, OUT, SENSORS,
)

viz.apply_style()
WELLS = [f"GL-{i:02d}" for i in range(1, 11)]
PRESSURE_SENSORS = ["whp_psia", "whp_downstream_psia", "dh_pressure_psia",
                    "annulus_pressure_psia"]


def load():
    hf = pd.read_parquet(F_HF_CLEAN)
    wt = pd.read_parquet(F_WT_CLEAN)
    pvt = pd.read_csv(F_PVT)
    comp = pd.read_csv(F_COMPLETION, parse_dates=["first_production_date"])
    return hf, wt, pvt, comp


# --------------------------------------------------------------------------- #
def fig_data_quality(hf: pd.DataFrame) -> None:
    """Where the damage is, per well x per sensor. Sequential = magnitude."""
    miss = (hf.groupby("well_name", observed=True)[SENSORS]
              .apply(lambda d: d.isna().sum()).reindex(WELLS))
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2),
                             gridspec_kw={"width_ratios": [1.45, 1]})

    ax = axes[0]
    m = miss.to_numpy(dtype=float)
    im = ax.imshow(m, cmap=mpl_seq(), aspect="auto")
    ax.set_xticks(range(len(SENSORS)))
    ax.set_xticklabels([s.replace("_psia", "").replace("_degf", "").replace("_mscfd", "")
                        for s in SENSORS], rotation=28, ha="right")
    ax.set_yticks(range(len(WELLS)))
    ax.set_yticklabels(WELLS)
    ax.grid(False)
    for i in range(m.shape[0]):           # direct labels: relief for low contrast
        for j in range(m.shape[1]):
            v = m[i, j]
            ax.text(j, i, f"{v:,.0f}", ha="center", va="center", fontsize=7.5,
                    color="#ffffff" if v > m.max() * 0.55 else viz.INK)
    ax.set_title("Unrecoverable gaps after cleaning (minutes)")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02).outline.set_visible(False)

    ax = axes[1]
    cov = (hf.groupby("well_name", observed=True)
             .size().reindex(WELLS) / (273 * 1440) * 100)
    y = np.arange(len(WELLS))
    ax.barh(y, cov.to_numpy(), height=0.6, color=viz.BLUE)
    ax.set_yticks(y); ax.set_yticklabels(WELLS); ax.invert_yaxis()
    ax.set_xlim(98.8, 100.15)
    ax.set_xlabel("% of the 273-day minute grid present")
    for yi, v in zip(y, cov.to_numpy()):
        ax.text(v - 0.02, yi, f"{v:.2f}%", va="center", ha="right",
                fontsize=7.5, color="#ffffff")
    ax.set_title("Record coverage by well")
    ax.grid(axis="y", visible=False)

    viz.titled(fig, "Data quality after cleaning",
               "Residual gaps are long sensor outages, deliberately left unfilled; "
               "coverage never drops below 99.1%.")
    viz.save(fig, FIGS / "fig01_data_quality.png")


def mpl_seq():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("seq_blue", viz.SEQ)


# --------------------------------------------------------------------------- #
def fig_coverage_timeline(hf: pd.DataFrame) -> None:
    """When each well was offline. Gaps are the story, so draw the gaps."""
    fig, ax = plt.subplots(figsize=(13, 4.4))
    for i, w in enumerate(WELLS):
        d = hf.loc[hf.well_name == w, "timestamp"]
        gaps = d.diff()
        big = gaps[gaps > pd.Timedelta("2min")]
        ax.barh(i, (d.max() - d.min()).total_seconds() / 86400,
                left=mdates.date2num(d.min()), height=0.55,
                color=viz.SEQ[2], zorder=1)
        for ts, g in big.items():
            start = d.loc[ts] - g
            ax.barh(i, g.total_seconds() / 86400, left=mdates.date2num(start),
                    height=0.55, color=viz.STATUS_BAD, zorder=2)
    shut = shut_in_windows(hf)
    for _, s in shut.iterrows():
        i = WELLS.index(s.well_name)
        ax.barh(i, (s.end - s.start).total_seconds() / 86400,
                left=mdates.date2num(s.start), height=0.55,
                color=viz.STATUS_WARN, zorder=3)
    ax.set_yticks(range(len(WELLS))); ax.set_yticklabels(WELLS); ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.grid(axis="y", visible=False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in
               (viz.SEQ[2], viz.STATUS_WARN, viz.STATUS_BAD)]
    ax.legend(handles, ["recording", "shut in (build-up)", "data outage"],
              ncol=3, loc="upper left", bbox_to_anchor=(0, -0.12))
    viz.titled(fig, "Recording coverage and shut-in windows, Jan-Sep 2025",
               "Six wells have a choke-closed build-up; GL-03, GL-05, GL-07 and GL-09 never shut "
               "in, so they admit no PTA. The 9 Aug outage hits all ten wells at once (270 min) - "
               "a historian failure, not ten sensor faults.")
    viz.save(fig, FIGS / "fig02_coverage_timeline.png")


def gap_table(hf: pd.DataFrame) -> pd.DataFrame:
    """Every break longer than one minute in the per-well recording grid."""
    rows = []
    for w, d in hf.groupby("well_name", observed=True):
        t = d.timestamp.reset_index(drop=True)
        g = t.diff()
        for i in g[g > pd.Timedelta("2min")].index:
            rows.append({"well": w, "gap_start": t[i - 1], "gap_end": t[i],
                         "minutes": int(g[i].total_seconds() // 60) - 1})
    return pd.DataFrame(rows).sort_values("gap_start", ignore_index=True)


def shut_in_windows(hf: pd.DataFrame) -> pd.DataFrame:
    """Contiguous choke-closed intervals -> the PTA build-up events."""
    d = hf.loc[hf.is_shut_in, ["well_name", "timestamp"]].copy()
    brk = (d.well_name != d.well_name.shift()) | (
        d.timestamp.diff() > pd.Timedelta("5min"))
    d["ev"] = brk.cumsum()
    g = (d.groupby(["well_name", "ev"], observed=True)
          .agg(start=("timestamp", "min"), end=("timestamp", "max"),
               minutes=("timestamp", "size")).reset_index())
    return g.sort_values(["well_name", "start"], ignore_index=True)


# --------------------------------------------------------------------------- #
def fig_sensor_series(hf: pd.DataFrame) -> None:
    """Hourly medians per well, small multiples - 10 wells is past any hue cap."""
    h = (hf.set_index("timestamp").groupby("well_name", observed=True)
           [["whp_psia", "dh_pressure_psia", "gas_lift_rate_mscfd"]]
           .resample("1h").median().reset_index())
    shut = shut_in_windows(hf)
    fig, axes = plt.subplots(5, 2, figsize=(13.5, 12), sharex=True)
    for ax, w in zip(axes.ravel(), WELLS):
        d = h[h.well_name == w]
        ax.plot(d.timestamp, d.dh_pressure_psia, color=viz.BLUE, lw=1.0,
                label="downhole P")
        ax.plot(d.timestamp, d.whp_psia, color=viz.ORANGE, lw=1.0, label="wellhead P")
        for _, s in shut[shut.well_name == w].iterrows():
            ax.axvspan(s.start, s.end, color=viz.STATUS_WARN, alpha=0.30, lw=0)
        ax.set_title(w)
        ax.set_ylabel("psia")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    axes[0, 0].legend(loc="upper left", ncol=2)
    viz.titled(fig, "Downhole and wellhead pressure by well (hourly median)",
               "Shaded bands are choke-closed build-ups. Downhole pressure declines "
               "through the year on most wells; GL-04 and GL-08 build back sharply when shut in.")
    viz.save(fig, FIGS / "fig03_pressure_series.png")


# --------------------------------------------------------------------------- #
def fig_buildups(hf: pd.DataFrame) -> None:
    """The six build-ups on a shared elapsed-time axis - the PTA raw material."""
    shut = shut_in_windows(hf)
    shut = shut[shut.minutes >= 60].reset_index(drop=True)
    n = len(shut)
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7))
    for ax, (_, s) in zip(axes.ravel(), shut.iterrows()):
        d = hf[(hf.well_name == s.well_name)
               & (hf.timestamp >= s.start - pd.Timedelta("3h"))
               & (hf.timestamp <= s.end + pd.Timedelta("1h"))].copy()
        d["dt_h"] = (d.timestamp - s.start).dt.total_seconds() / 3600
        ax.axvspan(0, (s.end - s.start).total_seconds() / 3600,
                   color=viz.STATUS_WARN, alpha=0.18, lw=0)
        ax.plot(d.dt_h, d.dh_pressure_psia, color=viz.BLUE, lw=1.3)
        # measure the rise inside the shut-in window only: the frame carries an
        # hour of post-reopening data, where pressure crashes back down
        dur_h = (s.end - s.start).total_seconds() / 3600
        inw = d.loc[d.dt_h.between(0, dur_h), "dh_pressure_psia"].dropna()
        rise = inw.iloc[-1] - inw.iloc[0]
        ax.set_title(f"{s.well_name}   {s.minutes/60:.1f} h   +{rise:,.0f} psi")
        ax.set_xlabel("hours from shut-in")
        ax.set_ylabel("downhole pressure (psia)")
        ax.axvline(0, color=viz.INK_MUTED, lw=0.8, ls=":")
    for ax in axes.ravel()[n:]:
        ax.set_visible(False)
    viz.titled(fig, "Pressure build-ups: the six PTA events",
               "All six are clean, monotonic rises (119-837 psi). GL-02 at 5.7 h and "
               "GL-06 at 8 h are short - radial flow may not develop.")
    viz.save(fig, FIGS / "fig04_buildups.png")


# --------------------------------------------------------------------------- #
def fig_vfm_relationships(hf: pd.DataFrame, wt: pd.DataFrame) -> None:
    """Do the sensors actually carry rate information? Window-mean features vs oil rate."""
    feats = build_test_features(hf, wt)
    pairs = [("whp_psia", "wellhead pressure (psia)"),
             ("dp_choke", "choke dP (psi)"),
             ("gas_lift_rate_mscfd", "gas-lift rate (mscfd)"),
             ("dh_pressure_psia", "downhole pressure (psia)"),
             ("dp_tubing", "tubing dP (psi)"),
             ("dh_temperature_degf", "downhole temperature (degF)")]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7))
    for ax, (c, lab) in zip(axes.ravel(), pairs):
        ax.scatter(feats[c], feats.oil_rate_stbd, s=22, color=viz.BLUE,
                   alpha=0.75, linewidths=0.6, edgecolors=viz.SURFACE)
        r = feats[[c, "oil_rate_stbd"]].corr().iloc[0, 1]
        ax.set_title(f"{lab}    r = {r:+.2f}")
        ax.set_xlabel(lab)
        ax.set_ylabel("oil rate (stb/d)")
    viz.titled(fig, "VFM signal check: sensor features vs tested oil rate (85 tests)",
               "Each point is one well test. Points group into per-well clusters rather than "
               "following a trend, so every pooled correlation is weak (|r| <= 0.41). The signal is "
               "there, but it is within-well - which is why well identity has to enter the model.")
    viz.save(fig, FIGS / "fig05_vfm_relationships.png")


def build_test_features(hf: pd.DataFrame, wt: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cleaned high-frequency data over each test window.

    Well-test sensor columns reconcile to ~0 against these means, which
    confirms a test row is the average of its window - so this is the correct
    label join for VFM.
    """
    cols = SENSORS + ["dp_choke", "dp_tubing", "dp_annulus_tubing", "choke_pct"]
    rows = []
    idx = hf.set_index("timestamp")
    for _, r in wt.iterrows():
        d = idx[(idx.well_name == r.well_name)
                & (idx.index >= r.test_start) & (idx.index <= r.test_end)]
        rec = {"well_name": r.well_name, "test_start": r.test_start,
               "n_minutes": len(d),
               "oil_rate_stbd": r.oil_rate_stbd, "water_rate_stbd": r.water_rate_stbd,
               "gas_rate_mscfd": r.gas_rate_mscfd, "water_cut_pct": r.water_cut_pct,
               "gor_scf_stb": r.gor_scf_stb}
        for c in cols:
            rec[c] = d[c].mean()
        rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
def fig_rate_history(wt: pd.DataFrame) -> None:
    """Label behaviour over time: what the VFM has to reproduce."""
    fig, axes = plt.subplots(5, 2, figsize=(13.5, 12), sharex=True)
    for ax, w in zip(axes.ravel(), WELLS):
        d = wt[wt.well_name == w].sort_values("test_mid")
        ax.plot(d.test_mid, d.oil_rate_stbd, "o-", color=viz.BLUE, ms=4.5,
                label="oil (stb/d)")
        ax.plot(d.test_mid, d.water_rate_stbd, "o-", color=viz.ORANGE, ms=4.5,
                label="water (stb/d)")
        ax.plot(d.test_mid, d.gas_rate_mscfd, "o-", color=viz.AQUA, ms=4.5,
                label="gas (mscf/d)")
        ax.set_title(f"{w}   {len(d)} tests")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    axes[0, 0].legend(loc="upper left", ncol=3)
    viz.titled(fig, "Tested rates per well: the VFM target (85 tests total)",
               "7-9 tests per well over nine months. Mean oil spans 6.2x across the field "
               "(GL-06 720 to GL-07 4,458 stb/d), so score the model per well, not pooled - "
               "a field-wide RMSE would just track GL-07.")
    viz.save(fig, FIGS / "fig06_rate_history.png")


# --------------------------------------------------------------------------- #
def fig_correlation(hf: pd.DataFrame, wt: pd.DataFrame) -> None:
    """Correlation has polarity -> diverging palette, gray midpoint."""
    from matplotlib.colors import LinearSegmentedColormap
    feats = build_test_features(hf, wt)
    use = ["whp_psia", "whp_downstream_psia", "dh_pressure_psia", "dh_temperature_degf",
           "annulus_pressure_psia", "gas_lift_rate_mscfd", "dp_choke", "dp_tubing",
           "choke_pct", "oil_rate_stbd", "water_rate_stbd", "gas_rate_mscfd",
           "water_cut_pct", "gor_scf_stb"]
    # within-well correlation: removes the between-well offsets that dominate pooled r
    dem = feats.copy()
    for c in use:
        dem[c] = dem[c] - dem.groupby("well_name")[c].transform("mean")
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 6.2))
    cmap = LinearSegmentedColormap.from_list("div", [viz.DIV_LOW, viz.DIV_MID, viz.DIV_HIGH])
    for ax, (d, name) in zip(axes, [(feats, "pooled across wells"),
                                    (dem, "within-well (well mean removed)")]):
        C = d[use].corr().to_numpy()
        im = ax.imshow(C, cmap=cmap, vmin=-1, vmax=1)
        ax.set_xticks(range(len(use)))
        ax.set_xticklabels(use, rotation=55, ha="right", fontsize=7)
        ax.set_yticks(range(len(use)))
        ax.set_yticklabels(use, fontsize=7)
        ax.grid(False)
        ax.set_title(name)
        for i in range(len(use)):
            for j in range(len(use)):
                if abs(C[i, j]) > 0.45:
                    ax.text(j, i, f"{C[i,j]:.2f}", ha="center", va="center",
                            fontsize=5.6,
                            color="#ffffff" if abs(C[i, j]) > 0.75 else viz.INK)
        fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02).outline.set_visible(False)
    viz.titled(fig, "Feature-target correlation, pooled vs within-well",
               "Pooled, choke opening looks dominant (r=0.84 vs oil) - but that is well size, not "
               "physics. Within-well, downstream wellhead pressure leads (+0.76 oil, +0.70 gas), and "
               "downhole temperature flips sign (-0.41 pooled to +0.57 within).")
    viz.save(fig, FIGS / "fig07_correlation.png")


# --------------------------------------------------------------------------- #
def write_summary(hf, wt, pvt, comp) -> None:
    shut = shut_in_windows(hf)
    shut = shut[shut.minutes >= 60]
    feats = build_test_features(hf, wt)
    lines = [
        "# EDA summary - SOCAR 2026 Intelligent Well Performance",
        "",
        f"- High-frequency rows (cleaned): **{len(hf):,}** over "
        f"{hf.timestamp.min():%Y-%m-%d} to {hf.timestamp.max():%Y-%m-%d}, 10 wells, 1-minute grid",
        f"- Well tests (labels): **{len(wt)}** "
        f"({wt.groupby('well_name').size().min()}-{wt.groupby('well_name').size().max()} per well)",
        f"- Choke events: **65**; shut-in (build-up) events >=1 h: **{len(shut)}**",
        "",
        "## VFM framing",
        f"- Labels are scarce: {len(wt)} tests vs {len(hf):,} feature rows. "
        "Aggregate per test window; validate by well (GroupKFold), never by random row.",
        "- Well-test sensor columns reconcile to ~0 against high-frequency window means, "
        "so a test row *is* the window average. That fixes the label join.",
        f"- Test windows are {wt.test_hours.min():.0f}-{wt.test_hours.max():.0f} h "
        f"({feats.n_minutes.min()}-{feats.n_minutes.max()} minutes of data each).",
        "",
        "## PTA framing",
        "| well | start | duration (h) | build-up (psi) |",
        "|---|---|---|---|",
    ]
    for _, s in shut.iterrows():
        d = hf[(hf.well_name == s.well_name) & (hf.timestamp >= s.start)
               & (hf.timestamp <= s.end)].dh_pressure_psia.dropna()
        lines.append(f"| {s.well_name} | {s.start:%Y-%m-%d %H:%M} | "
                     f"{s.minutes/60:.1f} | {d.iloc[-1]-d.iloc[0]:+,.0f} |")
    lines += [
        "",
        "- GL-03, GL-05, GL-07, GL-09 never shut in -> **no PTA possible** for them.",
        "- GL-02 (5.7 h) and GL-06 (8.0 h) are short build-ups; radial flow may not "
        "develop, so Horner slope will be uncertain there.",
        "",
        "## Where the rate signal actually is",
        "Pooled correlation is misleading: choke opening scores r=0.84 against oil rate, but that "
        "reflects well size, not physics. Removing each well's mean gives the usable signal:",
        "",
        "| feature | oil (pooled -> within) | water | gas |",
        "|---|---|---|---|",
        "| whp_downstream_psia | +0.65 -> **+0.76** | +0.34 -> +0.13 | +0.66 -> **+0.70** |",
        "| dh_temperature_degf | -0.41 -> **+0.57** | -0.52 -> -0.00 | -0.39 -> +0.48 |",
        "| annulus_pressure_psia | -0.32 -> +0.15 | -0.49 -> **-0.50** | -0.29 -> +0.21 |",
        "| gas_lift_rate_mscfd | +0.05 -> +0.33 | +0.03 -> -0.38 | -0.02 -> +0.30 |",
        "| choke_pct | +0.84 -> +0.20 | +0.93 -> +0.47 | +0.86 -> +0.15 |",
        "",
        "- Downhole temperature **flips sign** between the two views - a Simpson's paradox. "
        "Any model must carry well identity (or well-level normalisation) or it will learn the "
        "between-well trend and invert the within-well one.",
        "- Water rate is driven by a different group (annulus pressure, choke) than oil and gas.",
        "",
        "## Recording gaps",
    ]
    gaps = gap_table(hf)
    byday = gaps.groupby(gaps.gap_start.dt.date).well.nunique()
    fieldwide = byday[byday >= 5]
    lines += [
        f"- {len(gaps)} gaps longer than 1 minute; longest {gaps.minutes.max():,} min "
        f"({gaps.minutes.max()/1440:.1f} days).",
    ]
    for day, n in fieldwide.items():
        g = gaps[gaps.gap_start.dt.date == day]
        lines.append(
            f"- **{day}: all {n} wells drop out simultaneously** "
            f"({g.gap_start.min():%H:%M}-{g.gap_end.max():%H:%M}, {g.minutes.max()} min each). "
            "A historian/SCADA failure, not independent sensor faults - so no well can impute "
            "another across it, and every daily aggregate for that date is ~19% short."
        )
    lines += ["", "## Figures"]
    for p in sorted(FIGS.glob("fig*.png")):
        lines.append(f"- `{p.name}`")
    (OUT / "eda_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  wrote {(OUT / 'eda_summary.md').name}")


def main() -> None:
    print("loading cleaned data...")
    hf, wt, pvt, comp = load()
    print("building figures...")
    fig_data_quality(hf)
    fig_coverage_timeline(hf)
    fig_sensor_series(hf)
    fig_buildups(hf)
    fig_vfm_relationships(hf, wt)
    fig_rate_history(wt)
    fig_correlation(hf, wt)
    write_summary(hf, wt, pvt, comp)
    print("done.")


if __name__ == "__main__":
    main()
