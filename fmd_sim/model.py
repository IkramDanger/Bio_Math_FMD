"""
The day-by-day stochastic SIR model on a farm network.

States: 0 = S (healthy, can catch it), 1 = I (infected, spreading it),
        2 = R (removed: culled or recovered, out for good).

Rules for each day (all farms update at the same time, based on yesterday):
1. Each healthy farm gets one try of chance p from EACH infected neighbour.
   With m infected neighbours, its chance of catching it is 1 - (1 - p)^m.
2. Every infected farm uses up one of its days. After exactly D days of
   tries it becomes R.
3. Newly infected farms start spreading from the next day.

This gives every infected farm exactly D tries per link, which is what the
formula T = 1 - (1 - p)^D assumes.
"""

import numpy as np

S, I, R = 0, 1, 2


def run_outbreak(adjacency, p, days_infectious, seed_farm, rng, track_sources=False):
    """Run one outbreak until no infected farms are left.

    Returns the daily counts of S, I and R plus summary measures.

    track_sources=True also records, for each newly infected farm, one of the
    infected neighbours it caught the disease from (picked at random if there
    were several). This is only used to animate the network pages; it does not
    change how the disease spreads, and the experiment leaves it off.
    """
    n = adjacency.shape[0]
    state = np.full(n, S, dtype=np.int8)
    days_left = np.zeros(n, dtype=np.int32)

    infection_day = np.full(n, -1, dtype=np.int32)   # day each farm was infected (-1 = never)
    infected_by = np.full(n, -1, dtype=np.int32)     # a neighbour it caught it from (-1 = none / not tracked)

    state[seed_farm] = I
    days_left[seed_farm] = days_infectious
    infection_day[seed_farm] = 0

    s_counts, i_counts, r_counts = [n - 1], [1], [0]

    while np.any(state == I):
        infected = state == I

        # Rule 1: number of infected neighbours of every farm, then infection.
        infected_neighbours = adjacency @ infected.astype(np.int32)
        chance = 1.0 - (1.0 - p) ** infected_neighbours
        newly_infected = (state == S) & (rng.random(n) < chance)

        # Rule 2: infected farms use up one day; those out of days are removed.
        days_left[infected] -= 1
        state[infected & (days_left == 0)] = R

        if track_sources:
            for farm in np.flatnonzero(newly_infected):
                neighbours = adjacency.indices[adjacency.indptr[farm]:adjacency.indptr[farm + 1]]
                sources = neighbours[infected[neighbours]]
                infected_by[farm] = rng.choice(sources)

        # Rule 3: new infections start spreading tomorrow.
        state[newly_infected] = I
        days_left[newly_infected] = days_infectious
        infection_day[newly_infected] = len(i_counts)

        s_counts.append(int(np.sum(state == S)))
        i_counts.append(int(np.sum(state == I)))
        r_counts.append(int(np.sum(state == R)))

        # Check: the number of farms never changes.
        assert s_counts[-1] + i_counts[-1] + r_counts[-1] == n

    i_counts = np.array(i_counts)
    return {
        "S": np.array(s_counts),
        "I": i_counts,
        "R": np.array(r_counts),
        "final_size": r_counts[-1] / n,       # fraction of farms ever infected
        "peak": i_counts.max() / n,            # largest fraction infected at once
        "peak_day": int(i_counts.argmax()),
        "duration": len(i_counts) - 1,
        # Farm infected on day d spreads it on days d+1 ... d+D and is removed on day d+D.
        "infection_day": infection_day,
        "infected_by": infected_by,
    }


def pick_seed_farm(n_farms, rule, rng):
    """Which farm is infected on day 0."""
    if rule == "random_farm":
        return int(rng.integers(n_farms))
    raise ValueError(f"Unknown seed rule: {rule}")
