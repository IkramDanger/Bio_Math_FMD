"""
Figures, one per part of the hypothesis.

Figure 1 (part a, how easily): chance of a major outbreak vs T.
Figure 2 (part b, how quickly): peak size and peak day vs T.
Figure 3 (part c, how far): final size of major outbreaks vs T.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import theory

COLOURS = {"even": "#6B7A2E", "hub": "#B4462E"}
LABELS = {"even": "Even network", "hub": "Hub-heavy network"}


def _threshold_lines(ax, degree_summary):
    for _, d in degree_summary.iterrows():
        ax.axvline(d["threshold_T_theory"], color=COLOURS[d["network"]], ls=":", lw=1.2)


def fig_how_easily(summary, degree_summary, path):
    fig, ax = plt.subplots(figsize=(6, 4))
    for name in ("even", "hub"):
        s = summary[summary["network"] == name]
        ax.plot(s["T"], s["P_major"], "o-", color=COLOURS[name], label=LABELS[name], ms=4)
    _threshold_lines(ax, degree_summary)
    ax.set_xlabel("Transmissibility T")
    ax.set_ylabel("Chance of a major outbreak")
    ax.set_title("How easily: chance of a major outbreak\n(dotted lines = theory threshold)")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def fig_how_quickly(summary, degree_summary, path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    for name in ("even", "hub"):
        s = summary[(summary["network"] == name) & (summary["P_major"] > 0)]
        a1.plot(s["T"], s["peak_major"], "o-", color=COLOURS[name], label=LABELS[name], ms=4)
        a2.plot(s["T"], s["peak_day_major"], "o-", color=COLOURS[name], label=LABELS[name], ms=4)
    a1.set_xlabel("Transmissibility T"); a1.set_ylabel("Peak fraction of farms infected at once")
    a2.set_xlabel("Transmissibility T"); a2.set_ylabel("Day of the peak")
    a1.set_title("How quickly: peak height (major outbreaks)")
    a2.set_title("How quickly: peak day (major outbreaks)")
    a1.legend(frameon=False)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def fig_how_far(summary, degree_summary, path):
    fig, ax = plt.subplots(figsize=(6, 4))
    for name in ("even", "hub"):
        s = summary[(summary["network"] == name) & (summary["P_major"] > 0)]
        ax.plot(s["T"], s["final_size_major"], "o-", color=COLOURS[name], label=LABELS[name], ms=4)
    mean_k = degree_summary.set_index("network").loc["even", "mean_k"]
    Ts = np.linspace(summary["T"].min(), summary["T"].max(), 200)
    ax.plot(Ts, [theory.final_size_even(T, mean_k) for T in Ts], color=COLOURS["even"],
            ls="--", lw=1, label="Even network, formula")
    ax.set_xlabel("Transmissibility T")
    ax.set_ylabel("Final fraction of farms infected")
    ax.set_title("How far: final size of major outbreaks")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)
