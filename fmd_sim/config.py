"""
All simulation settings in one place.

All values are decided and match the report (Table 1). Change them here
only; no other file contains hard-coded settings.
"""

PARAMS = {
    # --- Networks ---------------------------------------------------------
    "n_farms": 300,              # modelling choice (small region)
    "hub_links_per_new_farm": 3, # m = 3 gives about 6 links per farm on average (Barabasi and Albert, 1999)
    # The even network's link chance is worked out automatically so its
    # average number of links matches the hub network (see networks.py).

    # --- Disease ----------------------------------------------------------
    "days_infectious": 14,       # based on 10.8 days (95% CI 8.2-14.2) in cattle (Yadav et al., 2019); 11 and 9 as checks

    # --- Experiment -------------------------------------------------------
    # We choose transmissibility T values and work out the daily chance p
    # from them, because T means the same thing on both networks.
    "T_min": 0.0,
    "T_max": 0.6,                # covers both thresholds
    "T_steps": 60,               # how many T values between T_min and T_max
    "runs_per_setting": 500,     # standard error of any proportion <= 0.022
    "new_network_each_run": True,  # True = fresh network for every run
    "seed_rule": "random_farm",  # one farm picked at random is infected on day 0
    "major_outbreak_cutoff": 0.10,  # fraction of farms infected to count as "major"
    "threshold_detect_level": 0.05,  # simulated threshold = first T where P(major) is above this
    "random_seed": 2026,         # any fixed number, so results can be repeated exactly

    # --- Report -----------------------------------------------------------
    "report_T": 0.25,            # T used for the peak comparison (nearest grid value is 0.254)
}

# Settings still to be decided. The app flags these on the Settings and Report pages.
PLACEHOLDER_KEYS = []

# Smaller settings for a quick test run (python run_all.py --quick)
QUICK_OVERRIDES = {
    "T_steps": 13,
    "runs_per_setting": 100,
}
