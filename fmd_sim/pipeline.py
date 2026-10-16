"""
The full pipeline, shared by run_all.py and the app:
run the experiment, save tables, checks and figures, and load them back.
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import checks, experiments, networks, plots

FIGURES = ("fig1_how_easily.png", "fig2_how_quickly.png", "fig3_how_far.png")


def run_and_save(params, out_dir, progress=False, on_progress=None):
    """Run the experiment with these settings and save everything in out_dir."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw, degree_summary, _pool = experiments.run_sweep(params, progress=progress, on_progress=on_progress)
    summary = experiments.summarise(raw)

    raw.to_csv(out / "all_runs.csv", index=False)
    summary.to_csv(out / "summary.csv", index=False)
    degree_summary.to_csv(out / "network_stats.csv", index=False)
    (out / "checks.txt").write_text(checks.report(summary, degree_summary, params))

    plots.fig_how_easily(summary, degree_summary, out / FIGURES[0])
    plots.fig_how_quickly(summary, degree_summary, out / FIGURES[1])
    plots.fig_how_far(summary, degree_summary, out / FIGURES[2])

    info = {"finished": datetime.now().strftime("%d %B %Y, %H:%M"), "params": params}
    (out / "settings_used.json").write_text(json.dumps(info, indent=2))
    return {"summary": summary, "degree_summary": degree_summary, "params": params, "finished": info["finished"]}


def load_saved(out_dir):
    """Load the results of the last run, or None if there is no complete run saved."""
    out = Path(out_dir)
    needed = ["settings_used.json", "summary.csv", "network_stats.csv", *FIGURES]
    if not all((out / f).exists() for f in needed):
        return None
    info = json.loads((out / "settings_used.json").read_text())
    if "params" not in info:          # older format: the file held only the settings
        info = {"finished": "an earlier run", "params": info}
    return {
        "summary": pd.read_csv(out / "summary.csv"),
        "degree_summary": pd.read_csv(out / "network_stats.csv"),
        "params": info["params"],
        "finished": info["finished"],
    }


def display_networks(params):
    """The network pair shown on the network pages.

    It is built exactly like the first pair in the experiment (same random seed),
    so the pages show a network that was actually used.
    """
    rng = np.random.default_rng(params["random_seed"])
    pair = networks.make_matched_pair(params["n_farms"], params["hub_links_per_new_farm"], rng)
    return {name: {"graph": g, "adjacency": networks.to_adjacency(g)} for name, g in pair.items()}
