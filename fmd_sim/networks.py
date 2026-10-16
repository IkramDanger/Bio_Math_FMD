"""
Building the two kinds of farm network.

Each farm is a node; each link is a contact that can carry the disease.

- Hub-heavy network: Barabasi-Albert. Farms are added one at a time, and each
  new farm makes m links, preferring farms that already have many links.
  This creates a few hubs. We start from m+1 fully linked farms, so no farm
  ever has fewer than m links. (networkx's default start is a star shape,
  which can leave a few farms with only 1 link.)
- Even network: random links. We give it exactly the same number of links as
  the hub network and place them completely at random, so both networks have
  exactly the same average number of links per farm.
"""

import networkx as nx
import numpy as np
import scipy.sparse as sp


def make_hub_network(n_farms, links_per_new_farm, rng):
    """Hub-heavy (Barabasi-Albert) network."""
    seed = int(rng.integers(0, 2**31 - 1))
    start = nx.complete_graph(links_per_new_farm + 1)
    return nx.barabasi_albert_graph(n_farms, links_per_new_farm, seed=seed, initial_graph=start)


def make_even_network(n_farms, n_links, rng):
    """Even (random) network with exactly n_links links."""
    seed = int(rng.integers(0, 2**31 - 1))
    return nx.gnm_random_graph(n_farms, n_links, seed=seed)


def make_matched_pair(n_farms, links_per_new_farm, rng):
    """Build one hub network and one even network with the same number of links."""
    hub = make_hub_network(n_farms, links_per_new_farm, rng)
    even = make_even_network(n_farms, hub.number_of_edges(), rng)
    return {"even": even, "hub": hub}


def to_adjacency(graph):
    """Sparse adjacency matrix: row i has a 1 for every farm linked to farm i."""
    n = graph.number_of_nodes()
    return nx.to_scipy_sparse_array(graph, nodelist=range(n), format="csr", dtype=np.int32)


def degree_stats(graph):
    """Average links <k>, average of squared links <k^2>, variance and busiest farm."""
    k = np.array([d for _, d in graph.degree()], dtype=float)
    mean_k = k.mean()
    mean_k2 = (k ** 2).mean()
    return {
        "mean_k": mean_k,
        "mean_k2": mean_k2,
        "variance": mean_k2 - mean_k ** 2,   # variance = <k^2> - <k>^2 (divides by N)
        "min_k": int(k.min()),
        "max_k": int(k.max()),
    }
