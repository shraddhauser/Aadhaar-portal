# Aadhaar Portal

Aadhaar Portal is a Python-based analytics and monitoring workspace for Aadhaar enrollment data.
This repository currently contains operational helper scripts focused on:

- API smoke checks
- Frontend reachability checks
- SQLite data inspection
- SQLAlchemy-based DB verification and test inserts

## Current Repository Layout

```text
Aadhaar-portal/
├── aadhaar-portal/                # Application folder (backend/frontend code expected here)
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
└── aadhaar_analytics.db           # SQLite database (generated/used at runtime)
```

## Prerequisites

- Python 3.9+
- SQLite (bundled with Python via sqlite3 module)
- Running backend service on http://127.0.0.1:8000 (for API scripts)
- Running frontend service on http://127.0.0.1:3000 (for frontend check script)

## Quick Start

1. Clone and enter the repository.
2. Create and activate a virtual environment.
3. Install project dependencies (if/when app dependencies are available in the app folder).
4. Run scripts from repository root.

Example (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python .\scripts\smoke_test.py
```

## Script Reference

### API and Frontend Health

- `scripts/smoke_test.py`
  - Checks key backend routes and login endpoint.
- `scripts/check_api_data.py`
  - Logs in and verifies live/history API JSON endpoints.
- `scripts/check_frontend.py`
  - Confirms login page is reachable on frontend server.

### SQLite Inspection

- `scripts/inspect_db.py`
  - Reads root-level `aadhaar_analytics.db` and prints enrollment/daily stats date info.
- `scripts/check_db_dates.py`
  - Prints min/max/count for `enrollments`, `daily_stats`, and `updates`.
- `scripts/inspect_outer_db.py`
  - Inspects a hardcoded external DB path.
- `scripts/inspect_db_real.py`
  - Inspects a hardcoded local DB path and basic table/date metadata.
- `scripts/check_both_dbs.py`
  - Compares two hardcoded DB locations and table counts.
- `scripts/list_tables_outer.py`
  - Lists tables in `scripts/aadhaar_analytics.db`.

### SQLAlchemy Validation

- `scripts/print_db_info.py`
  - Imports backend DB config and prints effective DB settings.
- `scripts/query_with_sqlalchemy.py`
  - Uses ORM session to count `Enrollment` and `DailyStat` records.
- `scripts/test_insert_enrollment.py`
  - Inserts a sample enrollment row through ORM, then checks row count.

## Important Notes

- Several scripts contain hardcoded absolute paths from a local development machine.
  Update those paths before use in another environment.
- Some scripts import modules from `aadhaar-portal/backend/...`.
  Ensure backend code exists in that folder and dependencies are installed.
- Database files (`*.db`) are ignored by git, so local DB state may differ per developer.

## Recommended Cleanup

To improve portability, consider:

- Replacing hardcoded DB paths with environment variables.
- Adding a single config module for host URLs and DB paths.
- Adding a `requirements.txt` or `pyproject.toml` for reproducible setup.
- Splitting script outputs into logs for easier CI integration.

## Troubleshooting

- Connection refused on API scripts:
  - Start backend server on port 8000.
- Frontend check fails:
  - Start frontend server on port 3000 and verify route `/pages/login.html`.
- SQLAlchemy import errors:
  - Verify backend package exists under `aadhaar-portal/` and dependencies are installed.
- Missing table errors:
  - Confirm database initialization/migrations were run before checks.

## License

No license file is currently present in this repository.
Add one if you plan to distribute the project publicly.
