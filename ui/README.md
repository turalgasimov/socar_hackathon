# RizzML app

Daily oil, water and gas rates (VFM) and well-test analysis (PTA) from raw well sensor data, in the
browser. The app uses the ML team's code and model unchanged (`ml/src`, `ml/models/vfm.pkl`).

## Run it

Once, from the repository root:

```bash
sudo apt install git-lfs                         # if `git lfs` is missing (Ubuntu / Debian)
git lfs install && git lfs pull                  # the 257 MB sensor file, needed for Sample Data
python3 -m venv ui/.venv                         # the system Python refuses pip installs
ui/.venv/bin/python -m pip install -r ui/requirements.txt
```

Then, every time. Run from `ui/`, so `.streamlit/config.toml` (theme, 1 GB uploads) is picked up:

```bash
cd ui
.venv/bin/python -m streamlit run app.py
```

Open http://localhost:8501 and sign in with `rizzman@socar.az` / `guessme`.

Or activate the environment once per terminal and use the short command:

```bash
source ui/.venv/bin/activate
cd ui && streamlit run app.py
```

### On a server, for other PCs

```bash
cd ui
.venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Engineers open `http://<server address>:8501` in their browser.

### "streamlit: command not found"

Streamlit is not installed for the Python you are calling. Use the environment above:
`.venv/bin/python -m streamlit run app.py` from `ui/`, or `source ui/.venv/bin/activate` first.
On Windows the same steps are `py -m venv ui\.venv`, `ui\.venv\Scripts\python -m pip install -r ui\requirements.txt`
and `.venv\Scripts\python -m streamlit run app.py`.

## Settings

| Variable | Default | What it sets |
|---|---|---|
| `RIZZML_DATA_DIR` | `data/` in the repo | Folder the **Sample Data** tile analyses |
| `RIZZML_HOME` | `ui/.rizzml/` | Per-user history, stored uploads, downloaded copies, sign-in key (git-ignored) |

```bash
RIZZML_DATA_DIR=/path/to/csvs .venv/bin/python -m streamlit run app.py      # Linux, from ui/
$env:RIZZML_DATA_DIR = "C:\path\to\csvs"; .venv\Scripts\python -m streamlit run app.py   # Windows
```

## Before a demo

From the repository root:

```bash
ui/.venv/bin/python ui/check_pipeline.py data   # full run on the raw CSVs: rates, PTA vs the submitted file, exports
ui/.venv/bin/python ui/i18n.py                  # every screen text has an Azerbaijani and a Russian version
ui/.venv/bin/python ui/store.py                 # sign-in, per-user history and stored files
```

Each prints a line starting with `OK` when it passes.

## Using it

1. **Sign in.** Choose the language on the sign-in screen if needed.
2. **Load Data:** drop in `high_freq_data`, `choke_events`, `reservoir_pvt` and `well_completion`
   (CSV or Excel; `well_tests` is optional and adds an accuracy check), then **Run analysis**
   (about 30 s). Or click **Sample Data** on Home to run the hackathon field.
3. The app opens on **Production Rates**, and **Well Tests**, **Generate Graph**, **Export**,
   **Field Data** and **Data Quality** unlock. Every page has the menu on the left; Home is the tile screen.
4. **History** lists your uploads, analyses and downloaded files, and reopens or re-downloads them.
5. **Settings** (top right on Home, bottom left elsewhere): dark or light, Azerbaijani, English or Russian.
   Remembered per browser.
6. **Help** (next to Settings): how to use the app, the data it expects, how the method works, a
   glossary and troubleshooting, in all three languages.

## Files

| File | Contents |
|---|---|
| `app.py` | Screens: sign-in, Home tiles, sidebar, every feature page |
| `pipeline.py` | Back end: cleaning, features, VFM prediction, shut-in detection, PTA model match, exports |
| `charts.py` | Plotly charts, light and dark |
| `i18n.py` | Screen text in Azerbaijani, English and Russian |
| `docs/guide.*.md` | The in-app Help guide, one file per language; each `##` section is a tab |
| `store.py` | Sign-in, per-user history, stored files |
| `style.css` | Tiles, sidebar and sign-in styling (SOCAR colours) |
| `check_pipeline.py` | End-to-end check against the submitted results |
| `.streamlit/config.toml` | Light and dark themes, upload limit |

## Known limits

- **One demo account, no real authentication.** Accounts are in `USERS` in `store.py`; connect SOCAR's
  directory (LDAP or SSO) before real use.
- **Stored uploads are never deleted** (about 260 MB per sensor file). Clear `ui/.rizzml/uploads/` when
  disk runs low.
- **pandas must stay below 3.** The ML pipeline was built and checked on pandas 2.3.
