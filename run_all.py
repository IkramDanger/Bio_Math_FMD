"""
Run the whole experiment from the command line and save tables, checks and
figures to the results/ folder. (To explore the networks and change settings
in your browser, use app.py instead.)

    python run_all.py           full run with the settings in fmd_sim/config.py
    python run_all.py --quick   small, fast run to test that everything works
"""

import argparse
import time
from pathlib import Path

from fmd_sim.config import PARAMS, QUICK_OVERRIDES
from fmd_sim import checks, pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="small, fast test run")
    args = parser.parse_args()

    params = dict(PARAMS)
    if args.quick:
        params.update(QUICK_OVERRIDES)
    out = Path("results_quick" if args.quick else "results")

    print("Running simulations...")
    start = time.time()
    result = pipeline.run_and_save(params, out, progress=True)
    print(f"Done in {time.time() - start:.0f} s\n")
    print(checks.report(result["summary"], result["degree_summary"], params))
    print(f"\nTables, checks and figures saved in {out}/")
    print("To explore the results in your browser, run:  python app.py")


if __name__ == "__main__":
    main()
