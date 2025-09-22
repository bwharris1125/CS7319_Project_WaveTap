# Project TODOs and Roadmap

This document captures prioritized recommendations and concrete steps to evolve the WaveTap SDR/ADS-B codebase from "prototype" to a maintainable developer and production-ready project.

Each item includes: goal summary, files to change, acceptance criteria, and effort estimate.

---

## 1) Persistor interface + JSON raw storage (in-progress)
Goal: Provide a simple persistence abstraction and store the `raw` ADS-B payload as JSON instead of a Python string.

Why: JSON is queryable, safe to parse, and interoperable. A `Persistor` interface makes it easy to swap storage engines (SQLite, Postgres).

Files to add/change:
- `src/core/interfaces.py` (new) — define `Persistor` protocol
- `src/database/db.py` (refactor) — implement `Persistor`, store `raw` as JSON
- `tests/test_database.py` (update) — assert `raw` round-trips as JSON

Acceptance criteria:
- Tests pass
- `raw` column contains valid JSON (not `str(...)`)

Effort: 1-2 hours

---

## 2) Add validation for `AircraftData`
Goal: Harden the `AircraftData` model with input validation.

Why: Catch invalid or malformed decoder output early and get better typing guarantees. Pydantic integrates well with FastAPI.

Files to add/change:
- `src/utilities/aircraft_data.py` — add Pydantic model or validators
- `tests/test_aircraft_data.py` — tests for valid and invalid inputs

Acceptance criteria:
- Creating `AircraftData` with invalid fields raises a clear error
- Existing tests continue to pass

Effort: 1-2 hours

---

## 3) Default PNG export via Plotly + Kaleido
Goal: Use Plotly+Kaleido for headless PNG export and keep Folium for interactive HTML.

Why: Eliminates Selenium and browser dependencies for CI and automated image generation.

Files:
- `src/gui/mapping_util.py` — provide `backend='plotly'|'folium'` option
- `src/gui/map_example.py` — demonstrate both export paths

Acceptance criteria:
- PNG export works without Selenium (requires `kaleido`)
- Folium path still available

Effort: 1-2 hours

---

## 4) DB fixtures & integration tests
Goal: Add pytest fixtures for in-memory DB and expand tests for `list_recent`, indexes, and upsert behavior.

Files:
- `tests/conftest.py` — `aircraft_db` fixture
- `tests/test_database.py` — expanded tests

Acceptance criteria:
- Tests cover common DB operations and edge cases

Effort: 1-2 hours

---

## 5) SQLAlchemy & Alembic (migration readiness)
Goal: Move from raw sqlite3 usage to SQLAlchemy models and add Alembic migrations.

Why: Easier schema evolution, multi-DB support, and cleaner queries.

Files:
- `src/database/models.py` — SQLAlchemy models
- `alembic/` — migration scripts
- Update DB access layer to use SQLAlchemy sessions

Acceptance criteria:
- Tests run using SQLAlchemy-backed DB
- Migrations applied successfully on dev DB

Effort: 4-8 hours

---

## 6) FastAPI skeleton + endpoints
Goal: Provide a lightweight API to query recent aircraft, last seen by ICAO, and a WebSocket for live updates.

Files:
- `src/api/app.py` — FastAPI app
- `Dockerfile` updates

Acceptance criteria:
- App starts and exposes `/aircraft/latest` returning JSON from DB

Effort: 3-6 hours

---

## 7) CI: GitHub Actions + pre-commit
Goal: Run ruff, pytest, and optionally mypy on PRs; enable pre-commit hooks.

Files:
- `.github/workflows/ci.yml`
- `.pre-commit-config.yaml`

Acceptance criteria:
- PRs run CI and block on failures

Effort: 2-4 hours

---

## 8) Simulated capture (hardware-less dev)
Goal: Add a `SimulatedCapture` module that emits synthetic ADS-B messages for local dev.

Files:
- `src/sdr_cap/simulated.py`
- Tests that consume simulated messages

Acceptance criteria:
- Developers can run a demo without SDR hardware

Effort: 2-4 hours

---

## 9) Plan geospatial storage (PostGIS)
Goal: Design a migration path to Postgres+PostGIS if spatial queries are needed.

Files:
- `doc/ops/postgis.md`

Acceptance criteria:
- Documented schema and example queries

Effort: 2-3 hours

---

## 10) Observability & metrics
Goal: Add Prometheus metrics for message throughput and processing latency.

Files:
- `src/observability/metrics.py`
- Integrate metrics into capture pipeline

Acceptance criteria:
- `/metrics` endpoint exposes counters and histograms

Effort: 2-4 hours

---

## NOTE: WAL checkpointing on worker stop (future)
It may be useful to have `DBWorker.stop()` perform an explicit WAL checkpoint (e.g. `PRAGMA wal_checkpoint(TRUNCATE)`) before closing the connection so test runs and short-lived DB files don't leave `-wal` and `-shm` artifacts around. This can be implemented later as a small, safe enhancement.


# Suggested immediate next step
I can implement Item 1 (Persistor interface and JSON `raw` storage) now — it's low risk and unblocks a bunch of follow-up work. Confirm and I'll start the change and run the tests.
