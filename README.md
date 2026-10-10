# Foot-and-mouth disease on farm networks

This project simulates foot-and-mouth disease spreading between farms on two
kinds of network with the same average number of links: an **even** network and
a **hub-heavy** network. You can run it in two ways:

- **The web app**: explore both networks as animated scenes, change settings and read the report in your browser.
- **The command line**: run the full experiment and save the results to files.

Both use the same model and save results to the same place.

---

## What you need

- **Python 3.10 or newer.** Check with `python --version` (Windows) or `python3 --version` (Mac/Linux).
- A web browser.
- No internet connection is needed once the libraries are installed.

---

## 1. Open a terminal in the project folder

Every command in this guide must be run from inside the `fmd-network-sim` folder,
the one that contains `app.py`, `run_all.py` and this README.

- **Windows:** open the folder in File Explorer, click the address bar, type `cmd` and press Enter.
- **Mac:** open Terminal, type `cd ` (with a space), drag the folder into the window and press Enter.
- **VS Code:** use File → Open Folder, choose `fmd-network-sim`, then Terminal → New Terminal.

To check you're in the right place, type `dir` (Windows) or `ls` (Mac/Linux).
You should see `app.py` in the list.

> On Mac/Linux, use `python3` wherever this guide says `python`, if `python` doesn't work.

---

## 2. Set up (once only)

Create a separate space for the project's libraries and switch it on:

**Windows**
```
python -m venv .venv
.venv\Scripts\activate
```

**Mac/Linux**
```
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt should now start with `(.venv)`. Then install the libraries:

```
pip install -r requirements.txt
```

Optionally, check that everything works:

```
python -m pytest
```

You should see `12 passed` after about 20 seconds.

**Each time you open a new terminal later**, switch the project space back on with
the second line above (`.venv\Scripts\activate` or `source .venv/bin/activate`).
You don't need to install again.

---

## 3. Run the web app

```
python app.py
```

When it prints `Open http://127.0.0.1:8000 in your browser`, open that address.

**Keep the terminal open while you use the app.** To stop it, go back to the
terminal and press **Ctrl+C**.

If port 8000 is already in use, pick another port and open that address instead:

```
python app.py --port 8050
```

### First time: run the experiment once

The Report page is empty until the experiment has been run. Go to **Settings**
and press **Run simulation**. A progress bar shows how far it has got (about a
minute with the default settings). When it finishes, the Report page fills in.

### The pages

Use the navbar at the top to move between them.

| Page | What you can do |
|---|---|
| **Even network** | Watch outbreaks spread on the even network. |
| **Hub-heavy network** | The same for the hub-heavy network. |
| **Report** | Read the results of the last run: headline results, figures, network statistics, checks against theory, and the settings used. Download the tables. |
| **Settings** | Change any setting and press **Run simulation** to run the experiment again. Settings marked *placeholder* are not final yet. |

### Using the network pages

Each network page is just the graph, filling the screen. A bar along the bottom
has the main controls, and the **Details** button (top left, ☰) opens a side
panel with everything else.

**On the page**
- **Start an outbreak** by clicking any farm, or press **Start at a random farm** in the bottom bar.
- **Control the playback** with Play/Pause, **Back to day 0**, or the day slider. The bar also shows how many farms are healthy, infected and removed.
- **See a farm's connections** by hovering over it: its links and neighbours are highlighted and everything else fades. The tooltip shows when it was infected and which farm it caught it from.
- **Move around** by dragging the background. **Zoom** with the scroll wheel or the + / − buttons, and press **Fit** to see the whole network again. Drag a farm to move it.
- **Brown arrows** show the path the disease took: which link each farm caught it along.

**In the Details panel** (press **Details**, or the T = … label next to the title; close it with × or Esc)
- The network's statistics: average links, busiest farm, ⟨k²⟩, and the threshold from theory.
- **How contagious:** the T slider, the daily infection chance, and R₀ for this network.
- **This outbreak:** a chart of infected farms over time, how the outbreak ended, and the playback speed.
- **View:** which links to show (*All*, *Near infected* or *None*), whether to show the disease's path, and **Rearrange farms** for a fresh layout.

Bigger dots are farms with more links, using the same size rule on both pages.
Healthy farms are green-grey, infected farms are amber, removed farms are dark
grey, and the dark ring marks where the outbreak started.

The network drawings use [Cytoscape.js](https://js.cytoscape.org) with the fcose
layout. The library files are included in `fmd_sim/web/static/vendor/`, so the
app works without an internet connection.

---

## 4. Run from the command line (optional)

You can also run the experiment without the app:

```
python run_all.py --quick
```
A small test run that takes a few seconds. Results go in `results_quick/`.

```
python run_all.py
```
The full run, about a minute with the default settings. Results go in `results/`.

The full run saves:

| File | What it holds |
|---|---|
| `summary.csv` | Averages for each T value and network |
| `all_runs.csv` | One row per simulated outbreak |
| `network_stats.csv` | Average links, variance and theory threshold for each network |
| `checks.txt` | The simulation compared with the theory |
| `fig1_how_easily.png`, `fig2_how_quickly.png`, `fig3_how_far.png` | The three figures |
| `settings_used.json` | The exact settings of that run |

A full run from the command line also fills the app's Report page next time you start the app.

---

## Changing the default settings

The easiest way is the app's **Settings** page. To change the defaults the
program starts with, edit `fmd_sim/config.py` in any text editor and save it.

---

## If something goes wrong

| Message | What to do |
|---|---|
| `No module named fmd_sim` or `can't open file app.py` | You're in the wrong folder. Go back to step 1. |
| `No module named flask` (or numpy, networkx, pandas…) | The project space isn't switched on, or the libraries aren't installed. Run the activate line from step 2, then `pip install -r requirements.txt`. |
| `python is not recognised` | Try `python3`, or `py` on Windows. |
| `Address already in use` | Another program is using port 8000. Run `python app.py --port 8050`. |
| The page says it could not reach the app | The app has stopped. Check the terminal, and start it again with `python app.py`. |
| The Report page says "No results yet" | Run the experiment once from the Settings page. |
