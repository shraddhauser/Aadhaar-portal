# Testing

## Running the tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite needs no internet, no API keys, no `.env` and no database server.
Every test gets a fresh in-memory SQLite database (`tests/conftest.py`), and
the Anthropic client is replaced with a fake.

Coverage:

```bash
pytest --cov=backend --cov-report=term
```

Last measured on 2026-11-25: **69% line coverage of `backend/`**, from
77 collected tests (72 passed, 5 expected failures; see below). Re-run the
command above to check the current figure.

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

## What each file covers

| File | Covers | Why it matters |
|---|---|---|
| `integration/test_health.py` | `GET /health` returns 200 | Used by the deploy health check; it used to return 404 |
| `integration/test_auth.py` | Login success; wrong password, unknown user, no token, expired, forged and tampered tokens, deleted user → 401 | Every other route depends on this check |
| `integration/test_live_stats.py` | `/api/live/summary` equals the seeded latest day (overall and per region); gender split adds up to the total; default 30-day window; regions list; empty DB gives zeros, not 500 | The dashboard's headline numbers |
| `integration/test_import.py` | Valid CSV adds N rows; missing column → 400 naming it; empty, header-only and non-CSV files → 400; oversize → 413; no token → 401; non-admin → 403 | Uploads are the only write path from the UI |
| `integration/test_anomalies.py` | A 5× spike today in one region is flagged for that region only; flat data → no surges; threshold respected; empty list | Surge detection is a headline feature |
| `integration/test_insights.py` | Forecast returns exactly `months_ahead` non-negative values; out-of-range horizon → 422; too little history → error message; `trends-forecast` values non-negative | Forecast output feeds charts directly |
| `integration/test_export.py` | `/api/export/summary-report` JSON schema and 30-day totals; top regions sorted and ≤ 5; needs a token | The report the PDF export is built from |
| `integration/test_chat.py` | Mocked answer returned and prompt built; no key → 503; missing package → 503; over-long, empty, too much history or a `system` role → 422 without calling the LLM; no token → 401 | The chatbot must fail safely without a key |
| `unit/test_secret_key.py` | `JWT_SECRET_KEY` from env; missing in production → startup error; missing in dev → random key and a warning | Prevents running production with a guessable key |
| `unit/test_ingestion_cleaning.py` | Gender and age normalisation, district → region mapping, date handling, biometric score clipping | The cleaning rules decide what lands in the database |

Note on export: the server only produces a JSON report. CSV and PDF files are
generated in the browser (`frontend/js/app.js`, `exportCSV` and `exportPDF`),
so they are not covered by these tests.

## Known bugs recorded as expected failures

These tests are marked `xfail(strict=True)`. They describe the correct
behaviour, currently fail, and will turn into failures the moment the bug is
fixed, as a reminder to remove the marker.

| Test | Bug |
|---|---|
| `test_parsed_date_is_kept`, `test_rows_without_a_date_are_dropped`, `test_upload_keeps_the_dates_from_the_csv` | `clean_and_normalize_enrollment_data` drops the parsed `enrollment_date` column and refills it with the current time, so every imported enrolment gets the import date. `clean_and_normalize_demographic_data` does the same with `update_date`. |
| `test_gender_is_normalised[male-Male]` | Lower-case `male` / `female` are not in the gender map and become `Other`. |
| `test_biometric_scores_are_clipped_to_0_100` | `fillna(ndarray)` is rejected by pandas 3.x, which `pandas>=2.0.0` in `requirements.txt` allows. Biometric loading stores 0 rows. |

## Current behaviour that is tested but questionable

These pass, and are named `..._currently_...` so the behaviour is visible:

- Unknown districts are mapped to `MH-MUM` (Mumbai).
- Invalid ages (negative, over 150, not a number) are mapped to `36-60`.
