"""
All simulation settings in one place.

Values marked PLACEHOLDER are not final. They still need to be decided
(see the project's follow-up document). Change them here only; no other
file contains hard-coded settings.
"""

PARAMS = {
    # --- Networks ---------------------------------------------------------
    "n_farms": 300,              # decided
    "hub_links_per_new_farm": 3, # PLACEHOLDER: m = 3 gives about 6 links per farm on average, m = 4 about 8
    # The even network's link chance is worked out automatically so its
    # average number of links matches the hub network (see networks.py).

    # --- Disease ----------------------------------------------------------
    "days_infectious": 14,       # decided, but still needs a source

    # --- Experiment -------------------------------------------------------
    # We choose transmissibility T values and work out the daily chance p
    # from them, because T means the same thing on both networks.
    "T_min": 0.0,                # PLACEHOLDER
    "T_max": 0.6,                # PLACEHOLDER
    "T_steps": 60,               # PLACEHOLDER: how many T values between T_min and T_max
    "runs_per_setting": 500,     # PLACEHOLDER
    "new_network_each_run": True,  # PLACEHOLDER: True = fresh network for every run
    "seed_rule": "random_farm",  # PLACEHOLDER: one farm picked at random is infected on day 1
    "major_outbreak_cutoff": 0.10,  # PLACEHOLDER: fraction of farms infected to count as "major"
    "threshold_detect_level": 0.05,  # PLACEHOLDER: simulated threshold = first T where P(major) is above this
    "random_seed": 2026,         # PLACEHOLDER: any fixed number, so results can be repeated exactly

    # --- Report -----------------------------------------------------------
    "report_T": 0.25,            # PLACEHOLDER: T used for the peak comparison in the report
}

# Settings still to be decided. The app flags these on the Settings and Report pages.
PLACEHOLDER_KEYS = [
    "hub_links_per_new_farm", "T_min", "T_max", "T_steps", "runs_per_setting",
    "new_network_each_run", "seed_rule", "major_outbreak_cutoff",
    "threshold_detect_level", "random_seed", "report_T",
]

# Smaller settings for a quick test run (python run_all.py --quick)
QUICK_OVERRIDES = {
    "T_steps": 13,
    "runs_per_setting": 100,
}
