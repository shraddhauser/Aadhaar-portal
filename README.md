# Aadhaar Portal

Python utilities for validating Aadhaar analytics data flows across API, frontend, and SQLite/SQLAlchemy layers.

## At a Glance

- Focus: health checks, data sanity checks, and quick DB diagnostics
- Language: Python
- Database: SQLite (`aadhaar_analytics.db`)
- Typical local services:
  - Backend API: `http://127.0.0.1:8000`
  - Frontend: `http://127.0.0.1:3000`

## Table of Contents

- [What This Repository Contains](#what-this-repository-contains)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Runbook](#runbook)
- [Script Catalog](#script-catalog)
- [Configuration Notes](#configuration-notes)
- [Troubleshooting](#troubleshooting)
- [Roadmap Improvements](#roadmap-improvements)
- [License](#license)

## What This Repository Contains

This repository currently behaves as an operations/testing workspace around an Aadhaar portal stack. The tracked scripts help you:

- Verify backend routes and auth endpoints
- Validate frontend reachability
- Inspect and compare SQLite datasets
- Run quick SQLAlchemy-level checks against backend models

## Project Structure

```text
Aadhaar-portal/
├── aadhaar-portal/                # App folder (backend/frontend code expected here)
├── scripts/
│   ├── check_api_data.py
│   ├── check_both_dbs.py
│   ├── check_db_dates.py
│   ├── check_frontend.py
│   ├── inspect_db.py
│   ├── inspect_db_real.py
│   ├── inspect_outer_db.py
│   ├── list_tables_outer.py
│   ├── print_db_info.py
│   ├── query_with_sqlalchemy.py
│   ├── smoke_test.py
│   └── test_insert_enrollment.py
└── aadhaar_analytics.db           # Runtime SQLite DB (ignored by git)
```

## Prerequisites

- Python 3.9 or newer
- SQLite support (included with standard Python)
- Backend service running on port `8000` for API scripts
- Frontend service running on port `3000` for frontend checks

## Quick Start

1. Open a terminal at repository root.
2. Create a virtual environment.
3. Activate it.
4. Run one of the verification scripts.

PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python .\scripts\smoke_test.py
```

## Runbook

Use this sequence for a fast confidence pass after starting your services.

1. Backend route/auth smoke check

```powershell
python .\scripts\smoke_test.py
```

2. Frontend availability check

```powershell
python .\scripts\check_frontend.py
```

3. Database date-range and count check

```powershell
python .\scripts\check_db_dates.py
```

4. API data payload check (token + endpoint responses)

```powershell
python .\scripts\check_api_data.py
```

## Script Catalog

### API and Frontend Health

- `scripts/smoke_test.py`: checks backend root, dashboard, login API, and docs endpoint.
- `scripts/check_api_data.py`: logs in, retrieves token, and validates live/history API JSON responses.
- `scripts/check_frontend.py`: verifies the frontend login page is reachable.

### SQLite Inspection

- `scripts/inspect_db.py`: inspects root DB and prints enrollment + `daily_stats` date details.
- `scripts/check_db_dates.py`: prints min/max/count for `enrollments`, `daily_stats`, and `updates`.
- `scripts/inspect_outer_db.py`: inspects an external hardcoded DB path.
- `scripts/inspect_db_real.py`: inspects a local hardcoded DB path and table/date metadata.
- `scripts/check_both_dbs.py`: compares two hardcoded DB locations and key table counts.
- `scripts/list_tables_outer.py`: lists tables in `scripts/aadhaar_analytics.db`.

### SQLAlchemy Validation

- `scripts/print_db_info.py`: prints backend DB configuration values resolved by backend code.
- `scripts/query_with_sqlalchemy.py`: ORM count check for `Enrollment` and `DailyStat`.
- `scripts/test_insert_enrollment.py`: inserts a sample enrollment row and verifies count changes.

## Configuration Notes

- Some scripts include absolute paths from a local machine. Replace these before running in another environment.
- SQLAlchemy scripts import backend modules from `aadhaar-portal/backend/...`; make sure that code and its dependencies are present.
- SQLite DB files are git-ignored, so data varies by developer machine.

## Troubleshooting

### API script fails with connection errors

- Confirm backend is running at `127.0.0.1:8000`.
- Confirm login credentials used by scripts are valid.

### Frontend script fails

- Confirm frontend is running at `127.0.0.1:3000`.
- Verify route `/pages/login.html` exists.

### SQLAlchemy import fails

- Confirm app/backend code exists under `aadhaar-portal/`.
- Install backend dependencies in your active virtual environment.

### DB table missing errors

- Confirm database initialization/migrations have been executed.
- Confirm script path points to the intended database file.

## Roadmap Improvements

- Replace hardcoded paths with environment variables.
- Centralize URLs and DB paths in a single config module.
- Add dependency lock/setup files (`requirements.txt` or `pyproject.toml`).
- Add automated test/health script wrappers for CI.

## License

No license file is currently present. Add one before public distribution.
