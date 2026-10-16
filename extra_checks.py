"""
Extra checks reported in the Method (2.6) and Discussion (4.2).

Run AFTER run_all.py (it reads results/all_runs.csv):

    python extra_checks.py

1. Final-size comparison with a Bonferroni correction
   For every T where both networks had at least 25 major outbreaks (5% of 500 runs),
   compares the mean final size of major outbreaks (scale-free minus random) and
   tests it at alpha = 0.05 / (number of T values compared).

2. Short loops (triangles and clustering) in the two network types
   Builds 200 matched network pairs with the same code as the main experiment
   and reports the mean number of triangles, the clustering coefficient
   (NetworkX transitivity) and the number of neighbours shared by the two largest hubs.

Results are printed and saved to results/extra_checks.txt.
"""

import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import norm

from fmd_sim.config import PARAMS
from fmd_sim.networks import make_hub_network, make_even_network

N_FARMS = PARAMS["n_farms"]
M = PARAMS["hub_links_per_new_farm"]
MIN_MAJOR = 25          # at least 5% of 500 runs must be major outbreaks
N_PAIRS = 200           # network pairs for the short-loop check
lines = []


def say(text=""):
    print(text)
    lines.append(text)


# ---------------------------------------------------------------- 1. Bonferroni
runs = pd.read_csv("results/all_runs.csv")
major = runs[runs["major"]]

rows = []
for T, g in major.groupby("T"):
    rnd = g.loc[g["network"] == "even", "final_size"] * N_FARMS
    sf = g.loc[g["network"] == "hub", "final_size"] * N_FARMS
    if len(rnd) < MIN_MAJOR or len(sf) < MIN_MAJOR:
        continue
    diff = sf.mean() - rnd.mean()
    se = np.sqrt(rnd.var() / len(rnd) + sf.var() / len(sf))
    p = 2 * norm.sf(abs(diff / se))
    rows.append((T, diff, p))

res = pd.DataFrame(rows, columns=["T", "diff_farms", "p"])
m = len(res)
alpha = 0.05 / m
res["significant_bonferroni"] = res["p"] < alpha

say("1. Final size of major outbreaks: scale-free minus random (farms)")
say(f"   T values compared: {m}; Bonferroni alpha = 0.05/{m} = {alpha:.5f}")
sf_larger = res[res["diff_farms"] > 0]
rnd_larger = res[res["diff_farms"] < 0]
say(f"   Scale-free larger: {len(sf_larger)} values, "
    f"{sf_larger['significant_bonferroni'].sum()} significant after correction")
say(f"   Random larger:     {len(rnd_larger)} values, "
    f"{rnd_larger['significant_bonferroni'].sum()} significant after correction")
not_sig = res.loc[~res["significant_bonferroni"], "T"].round(3).tolist()
say(f"   Not significant at T = {not_sig}")
say()

# ---------------------------------------------------------------- 2. Short loops
rng = np.random.default_rng(PARAMS["random_seed"])
tri = {"hub": [], "even": []}
clu = {"hub": [], "even": []}
shared = []
for _ in range(N_PAIRS):
    hub = make_hub_network(N_FARMS, M, rng)
    even = make_even_network(N_FARMS, hub.number_of_edges(), rng)
    for name, g in (("hub", hub), ("even", even)):
        tri[name].append(sum(nx.triangles(g).values()) / 3)
        clu[name].append(nx.transitivity(g))
    top2 = sorted(hub.degree, key=lambda x: -x[1])[:2]
    shared.append(len(set(hub[top2[0][0]]) & set(hub[top2[1][0]])))

say(f"2. Short loops ({N_PAIRS} matched network pairs)")
say(f"   Triangles per network:  scale-free {np.mean(tri['hub']):.0f}, random {np.mean(tri['even']):.0f}")
say(f"   Clustering coefficient: scale-free {np.mean(clu['hub']):.3f}, random {np.mean(clu['even']):.3f}")
say(f"   Neighbours shared by the two largest hubs: {np.mean(shared):.1f}")

with open("results/extra_checks.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
