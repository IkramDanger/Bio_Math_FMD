"""
The main experiment: run many outbreaks on both networks across a range of T.

For each T value and each network type we run many outbreaks and record:
- final size (how far, part c)
- peak and peak day (how quickly, part b)
- whether it was a major outbreak (used for how easily, part a)

Networks: we build one pool of matched network pairs and reuse it for every T.
Run number r always uses pair number r, so differences between T values come
from T, not from different networks.
"""

import numpy as np
import pandas as pd

from . import networks, theory
from .model import run_outbreak, pick_seed_farm

NETWORK_TYPES = ("even", "hub")


def build_network_pool(params, rng):
    """One matched (even, hub) pair per run, or a single pair reused for all runs."""
    n_pairs = params["runs_per_setting"] if params["new_network_each_run"] else 1
    pool = []
    for _ in range(n_pairs):
        pair = networks.make_matched_pair(params["n_farms"], params["hub_links_per_new_farm"], rng)
        pool.append({
            name: {"adjacency": networks.to_adjacency(g), "stats": networks.degree_stats(g)}
            for name, g in pair.items()
        })
    return pool


def pool_degree_summary(pool):
    """Average <k>, <k^2>, variance and theory threshold per network type, over the whole pool."""
    rows = []
    for name in NETWORK_TYPES:
        stats = [pair[name]["stats"] for pair in pool]
        mean_k = np.mean([s["mean_k"] for s in stats])
        mean_k2 = np.mean([s["mean_k2"] for s in stats])
        rows.append({
            "network": name,
            "mean_k": mean_k,
            "mean_k2": mean_k2,
            "variance": np.mean([s["variance"] for s in stats]),
            "min_k": min(s["min_k"] for s in stats),
            "max_k": max(s["max_k"] for s in stats),
            "excess_degree": theory.excess_degree(mean_k, mean_k2),
            "threshold_T_theory": theory.threshold_T(mean_k, mean_k2),
        })
    return pd.DataFrame(rows)


def run_sweep(params, progress=True, on_progress=None):
    """Run every (T, network, run) combination.

    Returns raw results, the degree summary, and the network pool.
    """
    rng = np.random.default_rng(params["random_seed"])
    pool = build_network_pool(params, rng)
    T_values = np.linspace(params["T_min"], params["T_max"], params["T_steps"])
    D = params["days_infectious"]

    rows = []
    for i, T in enumerate(T_values):
        p = theory.daily_chance_from_T(T, D)
        for name in NETWORK_TYPES:
            for r in range(params["runs_per_setting"]):
                pair = pool[r % len(pool)]
                seed_farm = pick_seed_farm(params["n_farms"], params["seed_rule"], rng)
                out = run_outbreak(pair[name]["adjacency"], p, D, seed_farm, rng)
                rows.append({
                    "T": T, "p": p, "network": name, "run": r,
                    "final_size": out["final_size"], "peak": out["peak"],
                    "peak_day": out["peak_day"], "duration": out["duration"],
                    "major": out["final_size"] > params["major_outbreak_cutoff"],
                })
        if progress:
            print(f"  T = {T:.3f} done ({i + 1}/{len(T_values)})")
        if on_progress is not None:
            on_progress((i + 1) / len(T_values))

    return pd.DataFrame(rows), pool_degree_summary(pool), pool


def summarise(raw):
    """One row per (T, network): chance of a major outbreak, and averages over major outbreaks."""
    def per_group(g):
        major = g[g["major"]]
        return pd.Series({
            "p": g["p"].iloc[0],
            "runs": len(g),
            "P_major": g["major"].mean(),
            "final_size_major": major["final_size"].mean() if len(major) else 0.0,
            "final_size_major_sd": major["final_size"].std() if len(major) > 1 else 0.0,
            "peak_major": major["peak"].mean() if len(major) else 0.0,
            "peak_day_major": major["peak_day"].mean() if len(major) else np.nan,
            "final_size_all": g["final_size"].mean(),
        })
    return raw.groupby(["network", "T"]).apply(per_group, include_groups=False).reset_index()


def simulated_threshold(summary, network, detect_level):
    """First T where the chance of a major outbreak rises above detect_level."""
    s = summary[summary["network"] == network].sort_values("T")
    above = s[s["P_major"] > detect_level]
    return float(above["T"].iloc[0]) if len(above) else np.nan
