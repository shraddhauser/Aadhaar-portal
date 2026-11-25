# Testing

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest
ruff check backend scripts tests      # lint
```

The suite needs no internet, no API keys, no `.env` and no database server.
Every test gets a fresh in-memory SQLite database (`tests/conftest.py`), and
the Anthropic client is replaced with a fake. GitHub Actions runs the same
commands on every push (`.github/workflows/ci.yml`), plus `oxlint` on
`frontend/js`.

Coverage:

```bash
pytest --cov=backend --cov-report=term
```

Last measured on 2026-11-25 with the pinned `requirements-dev.txt` on
Python 3.11: **110 tests passed, 75% line coverage of `backend/`**, in about
10 seconds. Re-run the command above to check the current figure.

## How the fixtures work

`tests/conftest.py`:

- Sets `DB_URL=sqlite://`, `ENV=test` and a test-only `JWT_SECRET_KEY` before
  the app is imported.
- `db_session`: a new in-memory database (SQLAlchemy `StaticPool`, so every
  session shares one connection) with 3 regions, a `SuperAdmin` user and a
  `Viewer` user. It replaces the app's `get_db` dependency for the test.
- `seed_rows`: 200 synthetic, deterministic enrolments across 3 regions,
  2 genders, 4 age groups and 60 days ending today. `daily_stats` is then
  built with the app's own `DataIngestionPipeline.aggregate_daily_stats()`.
  The fixture returns the rows, so tests compute expected values from the
  seed instead of hard-coding numbers.
- `token` / `auth_headers` / `viewer_headers`: log in through
  `POST /api/auth/login` and return a bearer token.
- `reset_rate_limits` (automatic): clears the rate-limit counters before and
  after every test, since they are global.

## What each file covers

| File | Tests | Covers | Why it matters |
|---|---|---|---|
| `integration/test_health.py` | 1 | `GET /health` returns 200 | Used by the deploy health check; it used to return 404 |
| `integration/test_auth.py` | 9 | Login success; wrong password, unknown user, no token, expired, forged and tampered tokens, deleted user → 401 | Every other route depends on this check |
| `integration/test_live_stats.py` | 6 | `/api/live/summary` equals the seeded latest day (overall and per region); gender split adds up to the total; default 30-day window; regions list; empty DB gives zeros, not 500 | The dashboard's headline numbers |
| `integration/test_import.py` | 13 | Valid CSV adds N rows with the CSV's dates; missing column → 400 naming it; empty, header-only and non-CSV files → 400; oversize → 413; no token → 401; non-admin → 403; demo mode → 403 | Uploads are the only write path from the UI |
| `integration/test_anomalies.py` | 4 | A 5× spike today in one region is flagged for that region only; flat data → no surges; threshold respected; empty list | Surge detection is a headline feature |
| `integration/test_insights.py` | 9 | Forecast returns exactly `months_ahead` non-negative values; out-of-range horizon → 422; too little history → error message; `trends-forecast` values non-negative | Forecast output feeds charts directly |
| `integration/test_export.py` | 3 | `/api/export/summary-report` JSON schema and 30-day totals; top regions sorted and ≤ 5; needs a token | The report the PDF export is built from |
| `integration/test_chat.py` | 16 | Mocked answer returned; empty env overrides fall back to defaults; prompt has the data tags and security rules; refusal gives a safe reply; SDK errors map to 502/429/503 (never 401); no key or missing package → 503; over-long, empty, too much history or a `system` role → 422 without calling the LLM; fallbacks only on supporting models | The chatbot must fail safely and never look like an expired login |
| `integration/test_rate_limit.py` | 3 | 6th login in a minute → 429 (even with the right password); 11th chat request → 429 | Slows down password guessing and LLM cost abuse |
| `integration/test_api_hardening.py` | 14 | CORS allows only configured origins; unhandled errors → JSON 500 with no internal detail but logged; `limit`/`offset` paging and bounds on three list endpoints | API safety and predictable list sizes |
| `unit/test_secret_key.py` | 3 | `JWT_SECRET_KEY` from env; missing in production → startup error; missing in dev → random key and a warning | Prevents running production with a guessable key |
| `unit/test_chat_context.py` | 3 | The chatbot's data summary contains no IDs, usernames, password fields or per-record dates; its size does not grow with row count; it is capped | Only aggregates may leave the server |
| `unit/test_ingestion_cleaning.py` | 26 | Gender (any case) and age normalisation, district → region mapping, dates kept (also from alternative column names), rows without dates dropped, biometric scores clipped, incomplete biometric rows dropped instead of filled | The cleaning rules decide what lands in the database |

Note on export: the server only produces a JSON report. CSV and PDF files are
generated in the browser (`frontend/js/app.js`, `exportCSV` and `exportPDF`),
so they are not covered by these tests.

## Bugs found and fixed with these tests

All fixed on 2026-11-25; the tests that exposed them now pass normally.

- Imported enrolment and update dates were replaced with the import date
  (the cleaner dropped the column it had just parsed).
- Lower-case `male` / `female` became `Other`.
- Biometric loading failed on `fillna(ndarray)` under pandas 2.2 and 3, so
  no biometric rows were stored; it also invented random scores for missing
  values. Incomplete rows are now dropped.
- `/health` returned 404 because a static mount was registered first.

## Current behaviour that is tested but questionable

These pass, and are named `..._currently_...` so the behaviour is visible:

- Unknown districts are mapped to `MH-MUM` (Mumbai).
- Invalid ages (negative, over 150, not a number) are mapped to `36-60`.

## Not covered

- MySQL: tests run on SQLite only.
- The real Anthropic API: the client is always mocked.
- The browser code (`frontend/js`): linted by oxlint, not tested.
