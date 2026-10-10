"""
The report: headline results for each part of the hypothesis, the figures,
network statistics, checks against theory, and the settings used.

report_html() returns the report as an HTML fragment for the Report page.
"""

import html

import numpy as np

from . import checks
from .experiments import NETWORK_TYPES, simulated_threshold

NAMES = {"even": "Even network", "hub": "Hub-heavy network"}


def _fmt(x, digits=3):
    if isinstance(x, (bool, np.bool_)):
        return "yes" if x else "no"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    if isinstance(x, (float, np.floating)):
        return "–" if np.isnan(x) else f"{x:.{digits}f}"
    if isinstance(x, list):
        return ", ".join(_fmt(v) for v in x)
    return html.escape(str(x))


def _table(headers, rows, cls=""):
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="table-wrap"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


SETTING_LABELS = {
    "n_farms": "Number of farms",
    "hub_links_per_new_farm": "Links each new farm makes in the hub network (m)",
    "days_infectious": "Days infectious (D)",
    "T_min": "Lowest T tested",
    "T_max": "Highest T tested",
    "T_steps": "Number of T values tested",
    "runs_per_setting": "Runs per T value and network",
    "new_network_each_run": "New network for each run",
    "seed_rule": "How the outbreak starts",
    "major_outbreak_cutoff": "Major outbreak: more than this fraction of farms infected",
    "threshold_detect_level": "Simulated threshold: first T where the chance of a major outbreak is above",
    "random_seed": "Random seed",
    "report_T": "T used for the peak comparison",
}


def _glance(summary, degree_summary, params):
    """Headline numbers for each part of the hypothesis."""
    ds = degree_summary.set_index("network")
    level = params["threshold_detect_level"]
    sim = {n: simulated_threshold(summary, n, level) for n in NETWORK_TYPES}

    # (b) peak at the T value closest to report_T
    Ts = np.sort(summary["T"].unique())
    T_ref = float(Ts[np.argmin(np.abs(Ts - params["report_T"]))])
    at = summary[np.isclose(summary["T"], T_ref)].set_index("network")

    # (c) crossover: first T where the even network's major outbreaks end bigger than the hub's
    both = summary[summary["P_major"] > 0].pivot(index="T", columns="network", values="final_size_major").dropna()
    hub_bigger_seen, crossover = False, None
    for T, row in both.iterrows():
        if row["hub"] > row["even"]:
            hub_bigger_seen = True
        elif hub_bigger_seen and row["even"] >= row["hub"]:
            crossover = float(T)
            break

    return {
        "threshold_theory": {n: float(ds.loc[n, "threshold_T_theory"]) for n in NETWORK_TYPES},
        "threshold_sim": sim,
        "T_ref": T_ref,
        "peak": {n: float(at.loc[n, "peak_major"]) for n in NETWORK_TYPES},
        "peak_day": {n: float(at.loc[n, "peak_day_major"]) for n in NETWORK_TYPES},
        "crossover": crossover,
        "final_high": {n: float(both[n].iloc[-1]) for n in NETWORK_TYPES} if len(both) else None,
        "T_high": float(both.index[-1]) if len(both) else None,
    }


def _glance_html(g):
    def pct(x):
        return f"{100 * x:.0f}%"

    a = (f"<p>Theory threshold: even <b>{_fmt(g['threshold_theory']['even'])}</b>, "
         f"hub <b>{_fmt(g['threshold_theory']['hub'])}</b>.</p>"
         f"<p>Simulated threshold: even <b>{_fmt(g['threshold_sim']['even'])}</b>, "
         f"hub <b>{_fmt(g['threshold_sim']['hub'])}</b>.</p>"
         "<p>A lower threshold means outbreaks start more easily.</p>")
    b = (f"<p>At T = {_fmt(g['T_ref'], 2)}, major outbreaks peak at "
         f"<b>{pct(g['peak']['even'])}</b> of farms (even) vs <b>{pct(g['peak']['hub'])}</b> (hub).</p>"
         f"<p>Peak day: even <b>{_fmt(g['peak_day']['even'], 0)}</b>, hub <b>{_fmt(g['peak_day']['hub'], 0)}</b>.</p>")
    if g["crossover"] is not None:
        c = (f"<p>The even network's major outbreaks become bigger than the hub network's from about "
             f"<b>T = {_fmt(g['crossover'], 3)}</b>.</p>")
    else:
        c = "<p>No crossover found in the T range tested.</p>"
    if g["final_high"]:
        c += (f"<p>At T = {_fmt(g['T_high'], 2)}: even <b>{pct(g['final_high']['even'])}</b> of farms infected, "
              f"hub <b>{pct(g['final_high']['hub'])}</b>.</p>")

    card = '<section class="glance-card"><h3>{t}</h3><p class="glance-q">{q}</p>{body}</section>'
    return "".join([
        card.format(t="(a) How easily", q="Does an outbreak get started?", body=a),
        card.format(t="(b) How quickly", q="How high and how soon does it peak?", body=b),
        card.format(t="(c) How far", q="How many farms are infected in the end?", body=c),
    ])


def _figure_tag(src, alt):
    return f'<img src="{html.escape(str(src))}" alt="{html.escape(alt)}">'


def report_html(summary, degree_summary, params, placeholder_keys, figure_srcs):
    g = _glance(summary, degree_summary, params)
    level = params["threshold_detect_level"]

    readable = {"random_farm": "one farm, picked at random"}
    settings_rows = [
        [html.escape(SETTING_LABELS.get(k, k)), _fmt(readable.get(v, v) if isinstance(v, str) else v),
         '<span class="flag">placeholder</span>' if k in placeholder_keys else "decided"]
        for k, v in params.items()
    ]
    net_rows = [
        [NAMES[r["network"]], _fmt(r["mean_k"], 2), _fmt(r["mean_k2"], 1), _fmt(r["variance"], 1),
         _fmt(r["min_k"]), _fmt(r["max_k"]), _fmt(r["excess_degree"], 2), _fmt(r["threshold_T_theory"])]
        for _, r in degree_summary.iterrows()
    ]
    thr = checks.threshold_check(summary, degree_summary, level)
    thr_rows = [[NAMES[r["network"]], _fmt(r["threshold_T_theory"]), _fmt(r["threshold_T_simulated"])]
                for _, r in thr.iterrows()]
    fs = checks.final_size_check(summary, degree_summary)
    fs_rows = [[_fmt(r["T"]), _fmt(r["final_size_theory"]), _fmt(r["final_size_simulated"]), _fmt(r["P_major_simulated"])]
               for _, r in fs.iterrows()]

    figs = figure_srcs
    return f"""
<section class="report-block">
  <h2>Results at a glance</h2>
  <p class="lead">One headline per part of the hypothesis. A dash means the value could not be found in the T range tested.</p>
  <div class="glance">{_glance_html(g)}</div>
</section>

<section class="report-block">
  <h2>Figures</h2>
  <figure>{_figure_tag(figs[0], "Chance of a major outbreak against T for both networks")}
    <figcaption><b>Figure 1. How easily.</b> Chance that one infected farm starts a major outbreak, for each value of transmissibility T. Dotted lines show the threshold predicted by Newman's formula.</figcaption></figure>
  <figure>{_figure_tag(figs[1], "Peak size and peak day against T for both networks")}
    <figcaption><b>Figure 2. How quickly.</b> Left: the largest share of farms infected at the same time. Right: the day that peak happens. Averages over major outbreaks only.</figcaption></figure>
  <figure>{_figure_tag(figs[2], "Final outbreak size against T for both networks")}
    <figcaption><b>Figure 3. How far.</b> Share of farms infected by the end, averaged over major outbreaks. The dashed line is the formula for the even network.</figcaption></figure>
</section>

<section class="report-block">
  <h2>The two networks</h2>
  <p class="lead">Averaged over every network built for this run. Both have the same average number of links per farm; the hub network's links are far more uneven.</p>
  {_table(["Network", "Average links ⟨k⟩", "⟨k²⟩", "Variance", "Fewest links", "Most links", "Further farms reached", "Theory threshold"], net_rows)}
</section>

<section class="report-block">
  <h2>Checks against theory</h2>
  <p class="lead">If the code is right, the even network should match the formulas closely. The hub network is expected to match only roughly. With 300 farms, small differences are normal.</p>
  <h3>Threshold</h3>
  {_table(["Network", "Theory", "Simulation"], thr_rows)}
  <h3>Even network: final size and outbreak chance</h3>
  <p>The formula's final size should be close to both the simulated final size and the simulated chance of a major outbreak.</p>
  {_table(["T", "Final size, formula", "Final size, simulation", "Chance of major outbreak"], fs_rows, "numbers")}
</section>

<section class="report-block">
  <h2>Settings used</h2>
  <p class="lead">Settings marked placeholder are not final. Change them on the Settings page and run again.</p>
  {_table(["Setting", "Value", "Status"], settings_rows)}
</section>
"""
