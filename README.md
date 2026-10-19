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

Every command in this guide must be run from inside the `Bio_Math_FMD` folder,
the one that contains `app.py`, `run_all.py` and this README.

- **Windows:** open the folder in File Explorer, click the address bar, type `cmd` and press Enter.
- **Mac:** open Terminal, type `cd ` (with a space), drag the folder into the window and press Enter.
- **VS Code:** use File → Open Folder, choose `Bio_Math_FMD`, then Terminal → New Terminal.

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
python run_all.py --quick
```

It should finish in a few seconds and say `Tables, checks and figures saved in results_quick/`.

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
| **Settings** | Change any setting and press **Run simulation** to run the experiment again. A setting marked *placeholder* is not final yet (none are at the moment). |

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
Healthy farms are blue, infected farms are amber, removed farms are dark
grey, and the dark ring marks where the outbreak started.

The network drawings use [Cytoscape.js](https://js.cytoscape.org) with the fcose
layout. The library files are included in `fmd_sim/web/static/vendor/`, so the
app works without an internet connection.

### How the app works

The app is a small website that runs on your own computer. Nothing is sent
over the internet.

- **`python app.py`** starts a [Flask](https://flask.palletsprojects.com) web
  server at `http://127.0.0.1:8000`. The code is in `fmd_sim/webapp.py`.
- **The same model, not a copy.** The app uses the model in `fmd_sim/model.py`
  and the formulas in `fmd_sim/theory.py`, the same code that `run_all.py` uses.
  The browser only draws the results.

**What happens on a network page**

1. When the app starts, it builds one even network and one hub-heavy network
   with the current settings and random seed. This is the same pair as the first
   pair in the experiment, so you see a network that was actually used.
2. The app works out where to draw each farm (Kamada-Kawai layout) and sends the
   farms, links and network statistics to the browser.
3. When you start an outbreak, the browser sends the farm and the T value to the
   app. The app runs one outbreak with the model and sends back the day each farm
   was infected and which farm it caught it from.
4. The browser plays that outbreak back day by day. Moving the day slider or
   changing the speed only changes the playback. It does not run the model again.

Each outbreak on these pages is random, so the same farm and T can give a
different outbreak each time. This is expected: the model is stochastic (it
uses chance).

**What happens when you press Run simulation**

1. The app checks the settings. If a value is not allowed, the Settings page
   tells you which one and why.
2. The full experiment runs in the background. The Settings page asks the app
   for progress every half second and shows it in the progress bar. You can
   refresh the page or leave it; the run keeps going. Only one run can
   go at a time.
3. When it finishes, the app saves everything to `results/` (the same files as
   `run_all.py`), rebuilds the network pages with the new settings and fills the
   Report page.

**Where settings are kept**

- The defaults come from `fmd_sim/config.py`.
- Settings you change in the app are saved with the results in
  `results/settings_used.json`. The app loads them again next time it starts.
  They do not change `fmd_sim/config.py`.
- A new run replaces the files in `results/`. To keep old results, copy the
  folder first.

| Part | File |
|---|---|
| Web server, pages and API | `fmd_sim/webapp.py` |
| Page layouts | `fmd_sim/web/templates/` |
| Network page drawing and playback | `fmd_sim/web/static/scene.js` |
| Settings page and progress bar | `fmd_sim/web/static/settings.js` |
| Colours and styles | `fmd_sim/web/static/style.css` |
| Report page content | `fmd_sim/report.py` |

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
