"""Shared matplotlib style for the SOCAR VFM/PTA figures.

Palette is the validated reference instance (dataviz skill). Only the first
three categorical slots are used: those are the ones that clear the all-pairs
CVD and normal-vision floors, which is the regime scatter plots and small
multiples live in. Ten wells is past any categorical cap, so per-well views are
small multiples rather than ten hues on one axes.
"""
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

# categorical slots 1-3 (validated all-pairs, light mode)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SERIES = [BLUE, ORANGE, AQUA]

# sequential blue ramp, light -> dark
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#256abf", "#184f95", "#0d366b"]
# diverging poles + neutral midpoint
DIV_LOW, DIV_MID, DIV_HIGH = "#2a78d6", "#f0efec", "#e34948"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#8a8982"
GRID = "#e4e3df"

STATUS_BAD = "#e34948"
STATUS_WARN = "#eda100"
STATUS_GOOD = "#1baf7a"


def apply_style() -> None:
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.size": 9,
        "font.family": "DejaVu Sans",
        "axes.edgecolor": GRID,          # recessive frame
        "axes.linewidth": 0.8,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "axes.titlesize": 10,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.labelsize": 8.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,             # recessive grid
        "grid.linewidth": 0.6,
        "grid.alpha": 0.9,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "lines.linewidth": 1.4,         # thin marks
        "lines.solid_capstyle": "round",
    })


def titled(fig, title: str, subtitle: str | None = None) -> None:
    """Left-aligned title block; subtitle carries the takeaway, not a restatement.

    Offsets are in inches and converted per-figure, so the block keeps the same
    physical spacing whether the figure is 4in or 12in tall. Fixed fractional
    offsets collapse the two lines onto each other on short figures.
    """
    h = fig.get_figheight()
    fig.suptitle(title, x=0.012, y=1 - 0.26 / h, ha="left", va="top",
                 fontsize=13, fontweight="semibold", color=INK)
    if subtitle:
        fig.text(0.012, 1 - 0.56 / h, subtitle, ha="left", va="top",
                 fontsize=9, color=INK_2, wrap=True)
    fig._viz_top = 1 - (0.92 if subtitle else 0.52) / h


def save(fig, path) -> None:
    fig.tight_layout(rect=(0, 0, 1, getattr(fig, "_viz_top", 0.95)))
    fig.savefig(path)
    plt.close(fig)
    print(f"  wrote {path.name}")
