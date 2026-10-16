"""
Checks that the simulation agrees with known theory, so we can trust the code.

1. Threshold: simulated threshold vs theory threshold T_c (both networks).
   Theory is accurate for the even network, only approximate for the hub one.
2. Final size (even network): simulated size of major outbreaks vs the
   formula S = 1 - exp(-T<k> S).
3. Outbreak chance = final size: with a fixed infectious period, theory says
   the chance of a major outbreak should equal its final size.

With only 300 farms, expect close agreement, not perfect agreement.
(The farm count staying constant is checked inside every run, in model.py.)
"""

import pandas as pd

from . import theory
from .experiments import simulated_threshold


def threshold_check(summary, degree_summary, detect_level):
    rows = []
    for _, d in degree_summary.iterrows():
        rows.append({
            "network": d["network"],
            "threshold_T_theory": d["threshold_T_theory"],
            "threshold_T_simulated": simulated_threshold(summary, d["network"], detect_level),
        })
    return pd.DataFrame(rows)


def final_size_check(summary, degree_summary):
    mean_k = degree_summary.set_index("network").loc["even", "mean_k"]
    even = summary[summary["network"] == "even"].copy()
    even["final_size_theory"] = [theory.final_size_even(T, mean_k) for T in even["T"]]
    even = even[even["final_size_theory"] > 0]
    return even[["T", "final_size_major", "final_size_theory", "P_major"]].rename(
        columns={"final_size_major": "final_size_simulated", "P_major": "P_major_simulated"})


def report(summary, degree_summary, params):
    lines = ["NETWORKS (averaged over all networks built)", degree_summary.round(3).to_string(index=False), ""]
    lines += ["CHECK 1: threshold, theory vs simulation",
              threshold_check(summary, degree_summary, params["threshold_detect_level"]).round(3).to_string(index=False),
              "(Theory is accurate for 'even', only approximate for 'hub'.)", ""]
    lines += ["CHECKS 2 and 3: even network final size (formula) and outbreak chance",
              "final_size_theory should be close to final_size_simulated AND to P_major_simulated.",
              final_size_check(summary, degree_summary).round(3).to_string(index=False)]
    return "\n".join(lines)
