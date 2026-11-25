# Architecture decision records

ADR-001 to ADR-005 were reconstructed from the code during the 2026 revamp.
The **Context**, **Options** and **Decision** lines describe what the code
does. Lines marked `TODO(confirm)` are the reasons the code suggests; the
project team should confirm or correct them, since the original reasoning
was not written down. ADR-006 onward were made during the revamp, and their
reasons are recorded as they were decided.

## ADR-001: One FastAPI app with a router per domain

- Context: the dashboard has distinct areas (live stats, history, insights,
  anomalies, export, import, chat) that share auth and a database session.
- Options considered: one module with all routes; a router per area;
  separate services.
- Decision: one FastAPI app, one `APIRouter` per area under `backend/routes/`,
  mounted with a URL prefix in `backend/main.py`. The same app serves the
  static frontend.
- Why: `TODO(confirm)` keeps each area's queries in one file while sharing
  `get_db` and `get_current_admin` through FastAPI dependencies; one process
  is enough for the data volume (thousands of rows).
- Trade-off accepted: everything scales and deploys together.

## ADR-002: SQLite by default, MySQL through configuration

- Context: the project needs a database that a reviewer can run with no
  setup, and the proposal targeted a "centralised" database.
- Options considered: SQLite only; MySQL only; SQLAlchemy with both.
- Decision: SQLAlchemy models with `DB_ENGINE=sqlite` as the default and
  MySQL (`pymysql`) selected by `DB_ENGINE=mysql` or a full `DB_URL`.
- Why: `TODO(confirm)` SQLite needs no server, so the demo and the tests run
  anywhere; MySQL is available for a shared, multi-user deployment.
- Trade-off accepted: the two engines differ in details (enum types, date
  functions), and the test suite only covers SQLite.

## ADR-003: Threshold-based surge detection

- Context: the portal should flag sudden enrolment spikes per region.
- Options considered: fixed percentage threshold over a recent average;
  statistical score (z-score) over a longer window; a learned model.
- Decision: a region is flagged when today's enrolments are at least
  `threshold_pct` % (default 50, adjustable 10–500) above its average over
  the previous 7 days (`routes/anomalies.py`).
- Why: `TODO(confirm)` simple to explain to non-technical users, needs only a
  week of history, and the threshold is a single tunable number.
- Trade-off accepted: it ignores normal variation (a noisy region triggers
  more often than a stable one), only looks at today, and needs `daily_stats`
  to be up to date.

## ADR-004: Vanilla JavaScript and Chart.js instead of a SPA framework

- Context: the frontend is two pages (login and a tabbed dashboard) showing
  charts from a JSON API.
- Options considered: React or another SPA framework with a build step;
  server-rendered templates; plain HTML/JS with a charting library.
- Decision: static HTML, CSS and vanilla JS, with Chart.js 4.4.1 from a CDN,
  served by FastAPI.
- Why: `TODO(confirm)` no build step or Node toolchain, the backend can serve
  the files directly, and two pages do not need client-side routing or
  component state management.
- Trade-off accepted: `app.js` is one large file with manual DOM updates;
  adding many more views would get harder to maintain.

## ADR-005: Chatbot as a server-side proxy to Anthropic Claude

- Context: the chatbot should answer questions about the current dashboard
  numbers without exposing an API key in the browser.
- Options considered: call the LLM from the browser; proxy through the
  backend; no LLM.
- Decision: `POST /api/chat/ask` builds a summary of current aggregates from
  the database, puts it in the system prompt, and calls Anthropic Claude from
  the server with `ANTHROPIC_API_KEY`. Without a key it returns 503.
- Why: `TODO(confirm)` the key never reaches the client, and grounding the
  prompt in live aggregates lets the answers quote real dashboard numbers.
- Trade-off accepted: each question sends dashboard aggregates to a third
  party, and answers depend on an external service and its cost.

## ADR-006: Read-only public demo on regenerated synthetic data

- Context: the repo needed a live demo for reviewers. The committed CSVs end
  in April 2026, so every "last 30 days" view in a demo built from them was
  empty, and a public demo must not accept uploads.
- Options considered: load the committed CSVs; regenerate data at each start
  without a seed; regenerate with a fixed seed and dates ending today.
- Decision: `scripts/demo_bootstrap.py` regenerates 730 days of synthetic
  data ending today with seed 2026, loads it into SQLite when the database is
  empty, and creates a `Viewer` login. `DEMO_MODE=true` rejects uploads.
- Why: recent-window views have data, the data is the same structure on
  every deploy, and a Viewer cannot change anything.
- Trade-off accepted: the demo's numbers shift by date and differ from the
  committed CSVs; the demo database resets on every restart.

## ADR-007: Reject uploads with missing columns instead of filling them in

- Context: the ingestion pipeline filled missing columns with defaults
  (e.g. random biometric scores, region `MH-MUM`, gender `Other`), which
  silently invents data.
- Options considered: keep filling; reject the whole file; reject per row.
- Decision: uploads are checked first; a file missing a required column gets
  400 with the missing columns listed. The per-value defaults inside the
  pipeline are unchanged.
- Why: an analytics portal should not report numbers it made up; a clear
  error lets the uploader fix the file.
- Trade-off accepted: files with alternative layouts need editing before
  upload; unknown districts and invalid ages inside an accepted file are still
  mapped to defaults (see [TESTING.md](TESTING.md)).

## ADR-008: In-memory per-IP rate limits with slowapi

- Context: login accepted unlimited password attempts, and every chat
  request costs money at the LLM provider.
- Options considered: no limits; slowapi with in-memory storage; slowapi
  with Redis; limits at a reverse proxy.
- Decision: slowapi, in memory, keyed on client IP: 5 logins and 10 chat
  requests per minute, configurable by environment variable. Render runs
  uvicorn with `--proxy-headers` so the real client IP is used.
- Why: the app runs as a single process, so in-memory counters are enough
  and need no extra service; limits live next to the routes and are testable.
- Trade-off accepted: counters reset on restart and are not shared between
  processes; users behind one shared IP share a limit.

## ADR-009: Chatbot sees only bounded aggregates, marked as data

- Context: the chat route puts live database numbers into the LLM prompt
  next to free-text user questions, which opens the door to prompt injection
  and to leaking records.
- Options considered: send query results as-is; let the model call tools to
  query the database; send a fixed-shape summary of aggregates.
- Decision: keep the existing fixed-shape summary (counts, averages, region
  names only), cap it at 4,000 characters, wrap it in `<dashboard_data>` tags
  described as data, add rules telling the model to ignore instructions in
  user messages, and limit input sizes (422). Tests check that no IDs,
  usernames or per-record dates reach the summary and that its size does not
  grow with the data.
- Why: the model can only ever see what the summary contains, so even a
  successful injection cannot reveal individual records.
- Trade-off accepted: the chatbot cannot answer questions that need detail
  beyond the summary; injection defences in the prompt reduce, but do not
  remove, the chance of the model being steered.

## ADR-010: Drop incomplete biometric rows instead of filling them

- Context: the biometric cleaner filled missing scores with random numbers
  and bad dates with "now", and the fill crashed on current pandas, so no
  biometric data was ever stored.
- Options considered: make the random fill work; fill with a mean or median;
  drop incomplete rows.
- Decision: drop rows with a missing or non-numeric score or an unparseable
  date, and log how many were dropped. Extends ADR-007.
- Why: averages and "low quality" anomalies should be computed only from
  measured values.
- Trade-off accepted: files with many gaps load fewer rows; the importer does
  not report which rows were dropped, only the count in the server log.
