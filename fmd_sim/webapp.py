"""
The browser app. Start it with  python app.py  and open the address it prints.

Pages (linked from the navbar):
  /even      the even network as an interactive, animated scene
  /hub       the hub-heavy network as an interactive, animated scene
  /report    the report for the last run
  /settings  every setting, with a button to run the experiment again

Every outbreak shown in the browser is run by the same Python model
(fmd_sim/model.py) that the experiment uses.
"""

import threading
import time
from pathlib import Path

import networkx as nx
import numpy as np
from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for

from . import pipeline, theory
from .config import PARAMS, PLACEHOLDER_KEYS
from .model import run_outbreak
from .report import report_html

NETWORK_PAGES = {
    "even": {
        "title": "Even network",
        "blurb": "Links are placed completely at random, so most farms have close to the average number of links.",
    },
    "hub": {
        "title": "Hub-heavy network",
        "blurb": "New farms prefer to link to farms that are already busy, so a few hubs collect many links.",
    },
}

# Everything the Settings page shows, in order.
FIELDS = [
    {"group": "The networks", "key": "n_farms", "kind": "int", "min": 50, "max": 1000, "step": 1,
     "label": "Number of farms", "help": "How many farms are in each network."},
    {"group": "The networks", "key": "hub_links_per_new_farm", "kind": "int", "min": 1, "max": 10, "step": 1,
     "label": "Links each new farm makes (m)",
     "help": "Sets the average number of links per farm in both networks: m = 3 gives about 6, m = 4 about 8."},
    {"group": "The disease", "key": "days_infectious", "kind": "int", "min": 1, "max": 60, "step": 1,
     "label": "Days infectious (D)", "help": "How many days an infected farm can pass the disease on before it is removed."},
    {"group": "The experiment", "key": "T_min", "kind": "float", "min": 0, "max": 1, "step": 0.01,
     "label": "Lowest T tested", "help": "Transmissibility: the chance the disease crosses one link during a farm's infectious period."},
    {"group": "The experiment", "key": "T_max", "kind": "float", "min": 0, "max": 1, "step": 0.01,
     "label": "Highest T tested", "help": "Must be higher than the lowest T."},
    {"group": "The experiment", "key": "T_steps", "kind": "int", "min": 2, "max": 60, "step": 1,
     "label": "Number of T values", "help": "How many evenly spaced T values to test between the lowest and highest."},
    {"group": "The experiment", "key": "runs_per_setting", "kind": "int", "min": 10, "max": 5000, "step": 10,
     "label": "Runs per T value", "help": "How many outbreaks to simulate for each T value and network. More runs give smoother results but take longer."},
    {"group": "The experiment", "key": "new_network_each_run", "kind": "bool",
     "label": "New network for each run", "help": "On: every run uses a freshly built network, so results don't depend on one lucky or unlucky network."},
    {"group": "The experiment", "key": "seed_rule", "kind": "choice", "choices": [["random_farm", "One farm, picked at random"]],
     "label": "How each outbreak starts", "help": "Which farm is infected on day 1."},
    {"group": "The experiment", "key": "random_seed", "kind": "int", "min": 0, "max": 999999, "step": 1,
     "label": "Random seed", "help": "Any whole number. The same seed always gives exactly the same results."},
    {"group": "Reading the results", "key": "major_outbreak_cutoff", "kind": "float", "min": 0.01, "max": 0.9, "step": 0.01,
     "label": "Major outbreak cutoff", "help": "An outbreak counts as major if more than this fraction of farms are infected (0.10 = 10%)."},
    {"group": "Reading the results", "key": "threshold_detect_level", "kind": "float", "min": 0.01, "max": 0.9, "step": 0.01,
     "label": "Threshold detection level", "help": "The simulated threshold is the first T where the chance of a major outbreak is above this."},
    {"group": "Reading the results", "key": "report_T", "kind": "float", "min": 0, "max": 1, "step": 0.01,
     "label": "T for the peak comparison", "help": "The report compares peak height and peak day at the tested T closest to this value."},
]

SECONDS_PER_RUN = 0.0022   # measured: about 2.2 ms per outbreak with 300 farms


def validate(form):
    """Turn submitted settings into a params dict, or return (None, errors)."""
    params, errors = dict(PARAMS), {}
    for f in FIELDS:
        key, raw = f["key"], form.get(f["key"])
        try:
            if f["kind"] == "bool":
                value = raw in (True, "true", "on", "1", 1)
            elif f["kind"] == "choice":
                if raw not in [c[0] for c in f["choices"]]:
                    raise ValueError
                value = raw
            elif f["kind"] == "int":
                value = int(raw)
                if float(raw) != value:
                    raise ValueError
            else:
                value = float(raw)
        except (TypeError, ValueError):
            errors[key] = "Enter a valid value."
            continue
        if f["kind"] in ("int", "float") and not (f["min"] <= value <= f["max"]):
            errors[key] = f"Enter a value from {f['min']} to {f['max']}."
            continue
        params[key] = value
    if not errors:
        if params["T_min"] >= params["T_max"]:
            errors["T_max"] = "Must be higher than the lowest T."
        if params["hub_links_per_new_farm"] >= params["n_farms"]:
            errors["hub_links_per_new_farm"] = "Must be smaller than the number of farms."
        if not params["T_min"] <= params["report_T"] <= params["T_max"]:
            errors["report_T"] = "Must be between the lowest and highest T tested."
    return (None, errors) if errors else (params, {})


def _declutter(xy, radius, iterations=120):
    """Nudge apart farms that overlap, keeping the overall shape of the layout."""
    from scipy.spatial import cKDTree
    xy = xy.copy()
    reach = 2 * radius.max()
    for _ in range(iterations):
        pairs = cKDTree(xy).query_pairs(reach, output_type="ndarray")
        if not len(pairs):
            break
        i, j = pairs[:, 0], pairs[:, 1]
        gap = xy[j] - xy[i]
        dist = np.linalg.norm(gap, axis=1) + 1e-9
        overlap = radius[i] + radius[j] - dist
        hit = overlap > 0
        if not hit.any():
            break
        push = gap[hit] / dist[hit, None] * (overlap[hit, None] / 2)
        np.add.at(xy, i[hit], -push)
        np.add.at(xy, j[hit], push)
    return xy


def _layout(adjacency, degree):
    """Drawing positions for the network pages.

    1. Kamada-Kawai layout of the largest connected group: farms that are a few
       links apart are placed roughly that far apart, which spreads both networks
       evenly. The same method is used for both, so the pages are comparable.
    2. Any farms that still overlap are nudged apart (bigger farms need more room).
    3. Farms outside the largest group (for example farms with no links, which
       happen in the even network) are lined up along the bottom edge.
    """
    g = nx.from_scipy_sparse_array(adjacency)
    n = adjacency.shape[0]
    main = sorted(max(nx.connected_components(g), key=len))
    pos = nx.kamada_kawai_layout(g.subgraph(main))
    pts = np.array([pos[i] for i in main])
    pts = (pts - pts.min(axis=0)) / (pts.max(axis=0) - pts.min(axis=0))
    # room each farm needs, in the same units as the 0-1 layout (matches scene.js sizes)
    room = (2.5 + 0.32 * degree[main] + 4.0) / 1000
    pts = _declutter(pts, room)
    pts = (pts - pts.min(axis=0)) / (pts.max(axis=0) - pts.min(axis=0))

    others = sorted(set(range(n)) - set(main))
    height = 0.92 if others else 1.0
    xy = np.zeros((n, 2))
    xy[main] = pts * [1.0, height]
    for j, i in enumerate(others):
        xy[i] = ((j + 0.5) / len(others), 1.0)
    return xy


class AppState:
    """What the app currently holds: settings, displayed networks, last results, run status."""

    def __init__(self, results_dir):
        self.results_dir = Path(results_dir)
        self.lock = threading.Lock()
        self.result = pipeline.load_saved(self.results_dir)
        self.params = dict(PARAMS)
        if self.result:
            self.params.update({k: v for k, v in self.result["params"].items() if k in PARAMS})
        self.status = {"state": "idle", "progress": 0.0, "message": "", "started": None}
        self.rng = np.random.default_rng()
        self._build_networks()

    def _build_networks(self):
        built = pipeline.display_networks(self.params)
        self.networks = {}
        for name, d in built.items():
            adj = d["adjacency"]
            degree = np.asarray(adj.sum(axis=1)).ravel().astype(float)
            mean_k, mean_k2 = degree.mean(), (degree ** 2).mean()
            xy = _layout(adj, degree)
            self.networks[name] = {
                "adjacency": adj,
                "payload": {
                    "name": name,
                    "n": int(adj.shape[0]),
                    "x": np.round(xy[:, 0], 4).tolist(),
                    "y": np.round(xy[:, 1], 4).tolist(),
                    "degree": degree.astype(int).tolist(),
                    "edges": np.argwhere(np.triu(adj.toarray(), 1) > 0).astype(int).tolist(),
                    "mean_k": mean_k, "mean_k2": mean_k2, "variance": mean_k2 - mean_k ** 2,
                    "min_k": int(degree.min()), "max_k": int(degree.max()),
                    "excess_degree": theory.excess_degree(mean_k, mean_k2),
                    "threshold_T": theory.threshold_T(mean_k, mean_k2),
                    "days_infectious": self.params["days_infectious"],
                },
            }

    def start_run(self, params):
        with self.lock:
            if self.status["state"] == "running":
                return False
            self.status = {"state": "running", "progress": 0.0, "message": "Building networks...", "started": time.time()}
        threading.Thread(target=self._run, args=(params,), daemon=True).start()
        return True

    def _run(self, params):
        def on_progress(fraction):
            with self.lock:
                self.status["progress"] = fraction
                self.status["message"] = f"Simulating... {round(100 * fraction)}%"
        try:
            pipeline.run_and_save(params, self.results_dir, on_progress=on_progress)
            result = pipeline.load_saved(self.results_dir)
            with self.lock:
                self.params = dict(params)
                self.result = result
                self.status["message"] = "Rebuilding the network pages..."
            self._build_networks()
            with self.lock:
                self.status = {"state": "done", "progress": 1.0, "started": None,
                               "message": f"Finished {result['finished']}."}
        except Exception as exc:   # report any failure on the Settings page
            with self.lock:
                self.status = {"state": "error", "progress": 0.0, "started": None, "message": f"The run failed: {exc}"}


def create_app(results_dir="results"):
    web = Path(__file__).with_name("web")
    app = Flask(__name__, template_folder=str(web / "templates"), static_folder=str(web / "static"))
    state = AppState(results_dir)

    def n_placeholders(params):
        return sum(1 for k in params if k in PLACEHOLDER_KEYS)

    @app.context_processor
    def nav():
        return {"active": request.endpoint}

    # ---- pages ----
    @app.route("/")
    def home():
        return redirect(url_for("even"))

    @app.route("/even")
    def even():
        return render_template("network.html", name="even", page=NETWORK_PAGES["even"])

    @app.route("/hub")
    def hub():
        return render_template("network.html", name="hub", page=NETWORK_PAGES["hub"])

    @app.route("/report")
    def report():
        result = state.result
        body = None
        if result:
            version = result["finished"].replace(" ", "").replace(",", "").replace(":", "")
            srcs = [url_for("results_file", filename=f) + f"?v={version}" for f in pipeline.FIGURES]
            body = report_html(result["summary"], result["degree_summary"], result["params"], PLACEHOLDER_KEYS, srcs)
        return render_template("report.html", body=body, result=result,
                               placeholders=n_placeholders(result["params"]) if result else 0,
                               running=state.status["state"] == "running")

    @app.route("/settings")
    def settings():
        return render_template("settings.html", fields=FIELDS, values=state.params, defaults=PARAMS,
                               placeholder_keys=PLACEHOLDER_KEYS, seconds_per_run=SECONDS_PER_RUN,
                               last=state.result["finished"] if state.result else None)

    @app.route("/results/<path:filename>")
    def results_file(filename):
        allowed = {*pipeline.FIGURES, "summary.csv", "all_runs.csv", "network_stats.csv", "checks.txt", "settings_used.json"}
        if filename not in allowed:
            abort(404)
        return send_from_directory(state.results_dir.resolve(), filename)

    # ---- data for the pages ----
    @app.route("/api/network/<name>")
    def api_network(name):
        if name not in state.networks:
            abort(404)
        return jsonify(state.networks[name]["payload"])

    @app.route("/api/outbreak", methods=["POST"])
    def api_outbreak():
        body = request.get_json(silent=True) or {}
        name = body.get("network")
        if name not in state.networks:
            return jsonify({"error": "Unknown network."}), 400
        try:
            T = float(body.get("T"))
        except (TypeError, ValueError):
            return jsonify({"error": "T must be a number."}), 400
        if not 0 <= T <= 1:
            return jsonify({"error": "T must be between 0 and 1."}), 400
        net = state.networks[name]
        n = net["payload"]["n"]
        seed = body.get("seed")
        if seed is None:
            seed = int(state.rng.integers(n))
        elif not (isinstance(seed, int) and 0 <= seed < n):
            return jsonify({"error": "Unknown farm."}), 400
        D = state.params["days_infectious"]
        p = theory.daily_chance_from_T(T, D)
        out = run_outbreak(net["adjacency"], p, D, seed, state.rng, track_sources=True)
        return jsonify({
            "T": T, "p": p, "seed": seed, "days_infectious": D,
            "R0": T * net["payload"]["excess_degree"],
            "infection_day": out["infection_day"].tolist(),
            "infected_by": out["infected_by"].tolist(),
            "final_size": out["final_size"], "duration": out["duration"],
        })

    @app.route("/api/run", methods=["POST"])
    def api_run():
        params, errors = validate(request.get_json(silent=True) or {})
        if errors:
            return jsonify({"errors": errors}), 400
        if not state.start_run(params):
            return jsonify({"errors": {"_": "A run is already in progress."}}), 409
        return jsonify({"ok": True})

    @app.route("/api/status")
    def api_status():
        with state.lock:
            return jsonify(state.status)

    return app
