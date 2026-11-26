# Changelog

All notable changes to this project. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-11-25

First tagged release, after a full revamp of the repository.

### Added
- The application code on `main` at the repository root (previously only on
  `branch-name`, with `main` holding a broken submodule pointer).
- `scripts/create_admin.py`: create or reset admin accounts from environment
  variables or a prompt.
- pytest suite (110 tests, 75% backend line coverage) with in-memory SQLite
  and a mocked LLM client; GitHub Actions CI with ruff, pytest and oxlint.
- Read-only demo mode (`DEMO_MODE`), `scripts/demo_bootstrap.py` with seeded
  synthetic data, and a Render blueprint (`render.yaml`).
- Per-IP rate limits on login (5/min) and chat (10/min).
- `limit`/`offset` pagination on `/api/anomalies/list`,
  `/api/history/regional-comparison` and `/api/history/update-history`.
- Database indexes on the date and region columns used by the aggregates.
- Docs: README, SETUP, DATA, API, ARCHITECTURE, DECISIONS, TESTING,
  CONTRIBUTORS, LICENSE (MIT), banner and screenshots.
- Dependabot, pre-commit hooks, PR and issue templates.

### Changed
- Chatbot: default model `claude-opus-5-5` (the previous default was
  retired), async client, SDK error classes instead of string matching,
  server-side refusal fallbacks, aggregate-only and size-capped context
  wrapped as data, anti-injection rules, input limits.
- CORS allows only `CORS_ORIGINS` instead of every origin.
- Unhandled errors return a JSON 500 without internal details; import
  failures no longer return HTTP 200.
- The frontend reads its API base URL from `frontend/js/config.js` instead of
  a hard-coded `http://localhost:8000`.
- Import routes require the `SuperAdmin` role, a size limit (10 MB) and the
  required columns.
- All dependencies pinned; unused `scikit-learn`, `google-generativeai` and
  `openai` removed; `anthropic` and `slowapi` added.
- Rule-based features are labelled as rule-based (recommendations, forecast,
  coverage gaps).

### Fixed
- Imported enrolment and update dates were replaced with the import date.
- Biometric data never loaded (pandas `fillna` error); incomplete rows are now
  dropped instead of being filled with random values.
- Lower-case `male` / `female` became `Other`.
- `/health` returned 404.
- `.env.template` set `SECRET_KEY`, which the code never read.

### Security
- No default JWT secret: production refuses to start without
  `JWT_SECRET_KEY`.
- Hard-coded admin credentials removed from scripts, docs, the login page and
  `schema.sql`.
- `.env` and SQLite databases are git-ignored and no longer committed.

### Removed
- Duplicate debug scripts, generated status documents, the `files/`
  prototype, stray files and editor settings.
