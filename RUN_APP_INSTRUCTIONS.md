# How to run the Music Recommender (local)

This document collects practical, copy-pasteable instructions to run the project locally on Windows (PowerShell). It covers: quick setup (venv + deps), the built-in launcher (`run_app.py`), running backend and frontend separately, Docker / docker-compose, and troubleshooting tips.

## Quick summary

- Launcher (starts both services): `python .\run_app.py`
- Backend only (FastAPI / Uvicorn): `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload`
- Frontend only (Streamlit): `python -m streamlit run frontend/app.py --server.port 8503`
- Install dependencies: `python -m pip install -r requirements.txt`

Notes:
- `run_app.py` performs a dependency check and verifies the local database file `music_recommender.db` before starting. If dependencies are missing it will print the packages and exit — it does not auto-install them.
- Default ports used by the launcher: Backend = 8001, Frontend = 8503.

---

## 1) Prepare Python environment (recommended)

1. Create and activate a virtual environment (PowerShell):
```markdown
# How to run the Music Recommender (local)

Practical, copy-pasteable instructions to run the project locally on Windows (PowerShell). This file covers virtualenv + deps, the canonical launcher (`bin/run_app_launcher.py`), the compatibility shim (`run_app.py`), running backend and frontend separately, Docker, data loading, and troubleshooting.

## Quick summary

- Launcher (starts both services):
  - Preferred (explicit): `python -m bin.run_app_launcher`
  - Backwards-compatible shim: `python .\run_app.py`
- Backend only (FastAPI / Uvicorn): `python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload`
- Frontend only (Streamlit): `python -m streamlit run frontend/app.py --server.port 8503`
- Install dependencies: `python -m pip install -r requirements.txt`

Notes:
- The canonical launcher is `bin/run_app_launcher.py`. The top-level `run_app.py` is now a small shim that forwards to the canonical launcher for backward compatibility.
- The launcher checks for required packages and verifies the local database file `music_recommender.db` by default. It will print missing packages and exit if any are missing (it does not auto-install them unless you add that feature).
- Default ports used by the launcher: Backend = 8001, Frontend = 8503.

---

## 1) Prepare Python environment (recommended)

1. Create and activate a virtual environment (PowerShell):

```powershell
# from project root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Upgrade pip and install the requirements:

```powershell
python -m pip install --upgrade pip
python -m pip install -r .\requirements.txt
```

Tip: If your machine has multiple Python versions, use the full path to the desired interpreter, e.g.:

```powershell
C:/Users/aubre/AppData/Local/Programs/Python/Python313/python.exe -m pip install -r .\requirements.txt
```

---

## 2) Run the built-in launcher (start both services)

The canonical launcher lives at `bin/run_app_launcher.py`. For convenience the root `run_app.py` still exists as a shim.

```powershell
# Preferred (explicit)
python -m bin.run_app_launcher

# Backwards-compatible shim (older habit)
python .\run_app.py
```

What it does:
- Checks required Python packages (will print which are missing and exit if any are missing)
- Verifies `music_recommender.db` exists in the project root (unless you set a `DATABASE_URL` pointing elsewhere)
- Starts backend on `http://localhost:8001` and frontend on `http://localhost:8503` by default
- Monitors both processes and attempts a graceful shutdown on Ctrl+C

If you need to change ports, edit the `backend_port` / `frontend_port` values in `bin/run_app_launcher.py` or run services separately (see next section).

---

## 3) Run backend and frontend separately (useful for debugging)

Backend (FastAPI + Uvicorn):

```powershell
# Start backend API
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

OpenAPI docs:

- http://localhost:8001/docs

Frontend (Streamlit):

```powershell
# Start Streamlit frontend
python -m streamlit run frontend/app.py --server.port 8503
```

If Streamlit dies immediately, run the command interactively to capture full stdout/stderr and inspect logs.

---

## 4) Docker / docker-compose (containerized)

If a `docker-compose.yml` exists you can start the services with Docker:

```powershell
# from project root
docker-compose up --build
```

Stop with:

```powershell
docker-compose down
```

Check the compose file for mapped ports and environment variables before running.

---

## 5) Loading data

- Fetch data from Spotify: use fetcher scripts in `fetchers/` (e.g. `fetchers/spotify_simple_fetcher.py` or `fetchers/spotify_data_fetcher.py`) which write cleaned CSV files to `data/sample/`.
- Import CSVs into DB: use the loader in `ml/data_pipeline/data_loader.py` or the convenience loader script `tools/reload_data.py`.

Example: fetch with the simple fetcher (you will need Spotify client credentials in environment variables):

```powershell
# set env vars temporarily in PowerShell
$env:SPOTIFY_CLIENT_ID = "<your-client-id>"
$env:SPOTIFY_CLIENT_SECRET = "<your-client-secret>"
python .\fetchers\spotify_simple_fetcher.py
```

Load Spotify CSVs into the database:

```powershell
python .\tools\reload_data.py
```

The data loader validates required columns, deduplicates songs (by track metadata/spotify_id), and skips malformed rows while logging errors.

---

## 6) Troubleshooting

- Missing dependencies
  - Install all required packages:

```powershell
python -m pip install -r .\requirements.txt
```

- Streamlit frontend dies immediately
  - Run the Streamlit command interactively to view logs:

```powershell
python -m streamlit run frontend/app.py --server.port 8503
```

  - Common causes: port already in use, incompatible Streamlit installation in the environment, or missing frontend files. Logs will show details.

- Database not found
  - By default the app uses `music_recommender.db` in the project root. You can either create the SQLite DB via the setup script or set a Postgres URL using the environment variable `DATABASE_URL`.

Create SQLite DB (example):

```powershell
python scripts/setup_database.py --sqlite
# or
python bin/setup_database.py --sqlite
```

If you set `DATABASE_URL` to a Postgres connection string, ensure Postgres is running and you run the appropriate setup/migrations for Postgres.

- Port conflicts
  - If ports 8001 or 8503 are already in use, either stop the conflicting service or change the ports in the startup commands.

- Permission errors on PowerShell when activating venv
  - If you see an execution policy error when running `Activate.ps1`, run PowerShell as admin and execute:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 7) Useful commands

Open the API docs (after backend starts):

- http://localhost:8001/docs

Run tests:

```powershell
python -m pytest -q
```

Show installed packages in the active environment:

```powershell
python -m pip list
```

---

## 8) Notes & tips

- The ETL pipeline deduplicates tracks by `spotify_id` at fetch time and ensures required columns (`track_name`, `artist`, `genre`, `popularity_score`) exist before inserting into the DB.
- Some helper/debug scripts may still hardcode a SQLite URL (for example `ml_scripts/debug_apriori_service.py`). If you switch to Postgres, update those scripts to use `settings.DATABASE_URL`.
- If you'd like, I can add an optional `--install-missing` flag to the launcher that safely installs only the missing pip packages before restarting. I can also add a `start-all.ps1` script that activates the venv and runs the canonical launcher.

---

If you want me to add the PowerShell helper or the `--install-missing` feature, tell me which and I'll implement it.
```

CLI flags (new)
----------------
- `--install-missing` : Attempt to install missing pip packages automatically. The launcher will prompt for confirmation by default.
- `--yes` / `-y`       : When used with `--install-missing`, skip confirmation and install non-interactively.

Examples
--------
# Run and prompt before installing missing packages (recommended)
python -m bin.run_app_launcher --install-missing

# Run and auto-install missing packages (non-interactive)
python -m bin.run_app_launcher --install-missing --yes