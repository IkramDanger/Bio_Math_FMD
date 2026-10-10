"""
Start the browser app:

    python app.py

then open http://127.0.0.1:8000 in your browser. Stop it with Ctrl+C.

Pages: Even network, Hub-heavy network, Report, Settings (see the navbar).
Results are saved in the results/ folder, the same place run_all.py uses.
"""

import argparse

from fmd_sim.webapp import create_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000, help="port to serve on (default 8000)")
    args = parser.parse_args()

    app = create_app("results")
    print(f"\n  Open http://127.0.0.1:{args.port} in your browser.  Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
