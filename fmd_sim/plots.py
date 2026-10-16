"""
Figures, one per part of the hypothesis.

Figure 1 (part a, how easily): chance of a major outbreak vs T.
Figure 2 (part b, how quickly): peak size and peak day vs T.
Figure 3 (part c, how far): final size of major outbreaks vs T.

Changes from the first version (for the report):
- Colours that colour-blind readers can tell apart (blue / orange), plus a
  different marker for each network, so the figures also work in black and white.
- Network names match the report (random / scale-free).
- No titles inside the figures: the report gives each figure a numbered caption.
- Axis labels give the full quantity and its units.
- Figures 2 and 3 only show T values where at least MIN_MAJOR_SHARE of runs were
  major outbreaks, because averages over a handful of outbreaks are unreliable.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import theory

COLOURS = {"even": "#2a78d6", "hub": "#eb6834"}
MARKERS = {"even": "o", "hub": "s"}
LABELS = {"even": "Random network (Erdős–Rényi)", "hub": "Scale-free network (Barabási–Albert)"}
MIN_MAJOR_SHARE = 0.05   # plot averages only where at least 5% of runs (25 of 500) were major

plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e4e3df",
    "grid.linewidth": 0.7,
})


def _style(ax):
    ax.set_xlabel("Transmissibility, T")
    ax.set_xlim(0, None)


def fig_how_easily(summary, degree_summary, path):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for name in ("even", "hub"):
        s = summary[summary["network"] == name]
        ax.plot(s["T"], s["P_major"], marker=MARKERS[name], ls="-", lw=1.3, ms=4,
                color=COLOURS[name], label=LABELS[name])
    for _, d in degree_summary.iterrows():
        ax.axvline(d["threshold_T_theory"], color=COLOURS[d["network"]], ls=":", lw=1.4)
    ax.plot([], [], color="0.35", ls=":", lw=1.4, label="Theoretical threshold, $T_c$ (Newman, 2002)")
    _style(ax)
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Proportion of runs causing a major outbreak\n(> 10% of farms infected)")
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=300); plt.close(fig)


def fig_how_quickly(summary, degree_summary, path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    for name in ("even", "hub"):
        s = summary[(summary["network"] == name) & (summary["P_major"] >= MIN_MAJOR_SHARE)]
        kw = dict(marker=MARKERS[name], ls="-", lw=1.3, ms=4, color=COLOURS[name], label=LABELS[name])
        a1.plot(s["T"], s["peak_major"] * 100, **kw)
        a2.plot(s["T"], s["peak_day_major"], **kw)
    for ax, letter in ((a1, "(a)"), (a2, "(b)")):
        _style(ax)
        ax.text(-0.13, 1.02, letter, transform=ax.transAxes, fontsize=11, fontweight="bold")
    a1.set_ylim(0, None)
    a1.set_ylabel("Peak prevalence\n(% of farms infected at the same time)")
    a2.set_ylabel("Day of peak prevalence (days)")
    a1.legend(frameon=False, loc="upper left", fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=300); plt.close(fig)


def fig_how_far(summary, degree_summary, path):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for name in ("even", "hub"):
        s = summary[(summary["network"] == name) & (summary["P_major"] >= MIN_MAJOR_SHARE)]
        ax.plot(s["T"], s["final_size_major"] * 100, marker=MARKERS[name], ls="-", lw=1.3, ms=4,
                color=COLOURS[name], label=LABELS[name])
    mean_k = degree_summary.set_index("network").loc["even", "mean_k"]
    Ts = np.linspace(summary["T"].min(), summary["T"].max(), 300)
    ax.plot(Ts, [theory.final_size_even(T, mean_k) * 100 for T in Ts], color=COLOURS["even"],
            ls="--", lw=1.2, label="Random network, theory (Newman, 2002)")
    _style(ax)
    ax.set_ylim(0, 102)
    ax.set_ylabel("Final outbreak size\n(% of farms infected, major outbreaks)")
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    fig.tight_layout(); fig.savefig(path, dpi=300); plt.close(fig)
