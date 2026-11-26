# Troubleshooting

Problems seen while setting up, testing and deploying this project, and how to
fix them. Setup steps are in [SETUP.md](SETUP.md).

## Installing

| Symptom | Cause and fix |
|---|---|
| `Failed to build ... pydantic-core` during `pip install` | The pinned `pydantic==2.7.1` has no wheels for Python 3.13. Use Python 3.11 (`py -3.11 -m venv venv` on Windows). |
| `ModuleNotFoundError: No module named 'backend'` | Commands must run from the repository root, not from `backend/` or `scripts/`. |
| `pip check` reports a `bcrypt` conflict | Install from `requirements.txt` as pinned; `passlib` 1.7.4 needs `bcrypt` 4.0.x. |

## Database

| Symptom | Cause and fix |
|---|---|
| Dashboard shows no data | The database has not been built. Run `python scripts/setup_complete.py`. |
| "Last 30 days" charts are empty, but Past History has data | The committed CSVs end on 2026-04-19, so recent windows are empty. Tick "Use all-time if recent empty", or regenerate data ending today: `python scripts/generate_sample_data.py --days 730 --seed 2026`, then rebuild. |
| Totals doubled after running setup twice | `setup_complete.py` loads the CSVs again into an existing database. Delete the SQLite file (`aadhaar_analytics.db`) and run it once. |
| Server log: `Dropped N biometric rows with missing scores or dates` | Expected: incomplete biometric rows are skipped, not filled in ([DATA.md](DATA.md)). |
| Queries slow on an old database | Indexes were added in v1.0.0 and are not added to existing tables. Rebuild the database or run the `CREATE INDEX` statements in `database/schema.sql`. |
| `Access denied for user 'root'@'localhost'` (MySQL) | Wrong `DB_PASSWORD` in `.env`, or the MySQL root password was never set. |
| `Can't connect to MySQL server on 'localhost'` | MySQL is not running. On Windows: `Get-Service mysql* \| Start-Service`. |

## Logging in

| Symptom | Cause and fix |
|---|---|
| No account to log in with | Create one: `python scripts/create_admin.py`. |
| Logged out every time the server restarts | `JWT_SECRET_KEY` is empty, so a random key is generated per run. Set it in `.env`. |
| Server refuses to start: `JWT_SECRET_KEY must be set when ENV=production` | Set `JWT_SECRET_KEY`, or use `ENV=development` locally. |
| `POST /api/auth/login` returns 422 | It takes form fields (`username`, `password`), not a JSON body. |
| `429 Too Many Requests` on login | More than 5 attempts in a minute from your IP. Wait a minute, or raise `LOGIN_RATE_LIMIT` locally. |

## Dashboard and API

| Symptom | Cause and fix |
|---|---|
| Charts are blank; browser console shows `Chart is not defined` | Chart.js loads from `cdnjs.cloudflare.com`; the browser could not reach it (offline or blocked network). |
| The pages load but every API call fails from another host | The frontend calls `/api` on its own origin (`frontend/js/config.js`). If you host the pages elsewhere, set `window.APP_CONFIG.API_BASE` and add that origin to `CORS_ORIGINS`. |
| Upload returns 400 with `missing_columns` | The CSV lacks required columns; see [DATA.md](DATA.md#csv-formats). |
| Upload returns 403 | Only `SuperAdmin` users can import, and uploads are disabled when `DEMO_MODE=true`. |
| Upload returns 413 | The file is over `MAX_UPLOAD_MB` (default 10). |
| A list endpoint returns 422 | `limit` must be 1–500 and `offset` ≥ 0. |
| Any route returns `500 {"detail": "Internal server error"}` | The real error and stack trace are in the server log. |

## Chatbot

| Symptom | Cause and fix |
|---|---|
| "USTAD is not configured" / 503 | `ANTHROPIC_API_KEY` is not set. |
| 502 "API key was rejected" | The key in `ANTHROPIC_API_KEY` is wrong or revoked. |
| 429 from the chatbot | Either the portal's own limit (10 per minute per IP, `CHAT_RATE_LIMIT`) or Anthropic's rate limit. Wait and retry. |
| 503 "Could not reach the AI service" | Network or Anthropic outage; the SDK has already retried twice. |

## Tests and CI

| Symptom | Cause and fix |
|---|---|
| Tests fail with 429 | A test fixture that resets the rate limiter was bypassed; run tests through `pytest` from the repo root so `tests/conftest.py` loads. |
| Tests pick up your local `.env` | `tests/conftest.py` sets the database, secret and environment before import; chat tests set or clear `ANTHROPIC_API_KEY` themselves. If you add tests that read other variables, set them explicitly. |
| CI badge is red | Open the failing run under the repo's Actions tab; run the same step locally (`ruff check backend scripts tests`, `pytest`). |

## Demo on Render

| Symptom | Cause and fix |
|---|---|
| First request takes up to a minute | Free services sleep when idle; on wake the database is rebuilt. |
| Deploy fails: the service never becomes healthy | `DEMO_PASSWORD` is not set in the Render dashboard. `demo_bootstrap.py` exits with an error and, since the start command is `bootstrap && uvicorn`, the server never starts. The deploy log shows `DEMO_PASSWORD is not set`. |
| Data changes after a redeploy | Expected: the demo regenerates seeded data ending on the start date. |
