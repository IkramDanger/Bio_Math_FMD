"""
Formulas from the theory, used to make predictions and to check the code.

- transmissibility: our day-by-day version of Newman's (2002) T.
- R0 and threshold: Newman (2002), R0 = T * (<k^2> - <k>) / <k>.
- final_size_even: final outbreak size on the even (random) network.
"""

import numpy as np
from scipy.optimize import brentq


def transmissibility(p, days_infectious):
    """Chance the disease crosses one link during a farm's infectious period.

    One try per day with chance p, for exactly D days:
        T = 1 - (1 - p)^D
    """
    return 1.0 - (1.0 - p) ** days_infectious


def daily_chance_from_T(T, days_infectious):
    """The daily chance p that gives transmissibility T (the formula above, reversed)."""
    return 1.0 - (1.0 - T) ** (1.0 / days_infectious)


def excess_degree(mean_k, mean_k2):
    """How many further farms a newly infected farm can reach: (<k^2> - <k>) / <k>."""
    return (mean_k2 - mean_k) / mean_k


def R0(T, mean_k, mean_k2):
    """Newman's R0 = T * (<k^2> - <k>) / <k>."""
    return T * excess_degree(mean_k, mean_k2)


def threshold_T(mean_k, mean_k2):
    """Threshold T_c, found by setting R0 = 1: T_c = <k> / (<k^2> - <k>)."""
    return mean_k / (mean_k2 - mean_k)


def final_size_even(T, mean_k):
    """Fraction of farms infected in a major outbreak on the even network.

    For random networks, the final size S solves S = 1 - exp(-R0 * S),
    with R0 = T * <k>. Below the threshold (R0 <= 1) the answer is 0.
    """
    r0 = T * mean_k
    if r0 <= 1.0:
        return 0.0
    f = lambda s: s - (1.0 - np.exp(-r0 * s))
    return brentq(f, 1e-9, 1.0)
