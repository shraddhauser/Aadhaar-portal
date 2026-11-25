# Setup

How to run the Aadhaar Analytics Portal locally. Every command is run from the
repository root.

## Requirements

- Python 3.11 (the pinned `pydantic==2.7.1` does not build on Python 3.13)
- Optional: MySQL 8 if you don't want the default SQLite database

## 1. Install

Linux / macOS:

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -3.11 -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Windows, `run_project.bat` does the install and start steps for you.

## 2. Configure

```bash
cp .env.template .env
```

The defaults use SQLite (`DB_ENGINE=sqlite`, `DB_FILE=./aadhaar_analytics.db`),
so nothing else is needed for a local run. `.env` is git-ignored: never commit it.

| Variable | Used for |
|---|---|
| `DB_ENGINE` | `sqlite` (default) or `mysql` |
| `DB_FILE` | SQLite file path, relative to the repo root |
| `DB_URL` | Full SQLAlchemy URL; overrides the other DB settings when set |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | MySQL connection (only when `DB_ENGINE=mysql`) |
| `ENV` | `development` (default) or `production`; production refuses to start without `JWT_SECRET_KEY` |
| `JWT_SECRET_KEY` | Token signing key. Empty in development = random key per run (logins reset on restart) |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Used by `scripts/create_admin.py` / `setup_complete.py`; prompted for if empty |
| `MAX_UPLOAD_MB` | CSV upload limit (default 10) |
| `ANTHROPIC_API_KEY` | AI chatbot (optional; without it the chatbot returns 503) |
| `ANTHROPIC_MODEL`, `ANTHROPIC_EFFORT` | Chatbot model and effort (default `claude-opus-5-5`, `low`) |
| `CORS_ORIGINS` | Comma-separated origins allowed to call the API from another site (default: localhost:8000) |
| `LOGIN_RATE_LIMIT`, `CHAT_RATE_LIMIT` | Per-IP limits (default `5/minute`, `10/minute`) |
| `DEMO_MODE`, `DEMO_USERNAME`, `DEMO_PASSWORD` | Public demo only, see below |

## 3. Build the database

The database is not committed. Build it from the CSVs in `data/`:

```bash
python scripts/setup_complete.py
```

This creates the tables, seeds the 10 regions, creates an admin user (from
`ADMIN_USERNAME` / `ADMIN_PASSWORD`, or it asks), loads `data/*.csv`,
aggregates daily statistics and runs anomaly detection.

To add or reset an admin later:

```bash
python scripts/create_admin.py            # asks for username and password
python scripts/create_admin.py --reset    # change an existing user's password
```

Check the result with:

```bash
python scripts/verify_database.py
```

To regenerate the synthetic CSVs first (see [DATA.md](DATA.md)):

```bash
python scripts/generate_sample_data.py
```

## 4. Run

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- Dashboard: http://localhost:8000
- Swagger API docs: http://localhost:8000/docs

Run uvicorn from the repo root as shown (`backend.main:app`); running it from
inside `backend/` breaks the package imports.

The login endpoint (`POST /api/auth/login`) takes **form data**
(`username`, `password`), not JSON:

```bash
curl -X POST http://localhost:8000/api/auth/login -d "username=admin&password=<password>"
```

## Running the demo build locally

This is what the Render service runs: synthetic data regenerated up to today,
a read-only `Viewer` login, and uploads disabled.

```bash
DEMO_MODE=true DEMO_PASSWORD=<choose one> DB_FILE=demo.db python scripts/demo_bootstrap.py
DEMO_MODE=true DB_FILE=demo.db python -m uvicorn backend.main:app --port 8000
```

## Deploying to Render

1. In Render, choose **New → Blueprint** and select this repository; it reads
   `render.yaml`.
2. Set `DEMO_PASSWORD` (shown publicly in the README, so use a demo-only
   value) and, optionally, `ANTHROPIC_API_KEY`.
3. Deploy. The first start takes about 20–60 seconds while the database is
   built. Free services sleep when idle and rebuild the database on wake.

## Upgrading an existing database

Indexes on the date and region columns were added in v1.0.0. `create_all`
does not add indexes to tables that already exist, so either rebuild the
database (delete the SQLite file and run `python scripts/setup_complete.py`)
or run the `CREATE INDEX` statements near the end of `database/schema.sql`.

## Using MySQL instead of SQLite

1. Create the database:

   ```bash
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS aadhaar_analytics;"
   ```

2. In `.env`, set `DB_ENGINE=mysql` and fill in `DB_USER`, `DB_PASSWORD`,
   `DB_HOST`, `DB_PORT` and `DB_NAME`.
3. Run `python scripts/setup_complete.py` as above.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Failed to build ... pydantic-core` during install | You are on Python 3.13. Use Python 3.11. |
| `Access denied for user 'root'@'localhost'` (MySQL) | Wrong `DB_PASSWORD` in `.env`, or the MySQL root password was never set. |
| `Can't connect to MySQL server on 'localhost'` | MySQL isn't running. On Windows: `Get-Service mysql* \| Start-Service`. |
| Dashboard shows no data | The database hasn't been built: run `python scripts/setup_complete.py`. |
| `429 Too Many Requests` on login | More than 5 attempts in a minute from your IP; wait a minute. |
| `ModuleNotFoundError: backend` | Run commands from the repo root, not from `backend/` or `scripts/`. |
| `POST /api/auth/login` returns 422 | Send form fields, not a JSON body (see above). |
