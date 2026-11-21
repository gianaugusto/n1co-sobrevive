# forgetme-services — Orchestrator Design

Status: **awaiting approval**

## Intent
Base open source project for the community: an orchestrator that coordinates the
erasure of PII ("right to be forgotten") across many services. Simple, objective,
SOLID, clean code, well documented, unit + integration tested.

## Goals
- API (FastAPI, Auth0-protected) to open a forget process: `tenant_id`, `key`, `type` (enum: `email`, `username`; extensible).
- Publish the request on Kafka topic `forget.requests`.
- Subscriber services consume it and answer on `forget.feedback`.
- Track every process and every subscriber's progress; allow retry per subscriber.
- Frontend (React + Tailwind + Auth0 login) to follow the processes.
- Docs, ADRs (one per decision), `CLAUDE.md` and `.claude/` agent setup.

## Non-goals
- The orchestrator never deletes PII itself.
- No subscriber SDK in v1 (only a documented message contract).

## Message contract
`forget.requests` (orchestrator -> subscribers):
`{ process_id, tenant_id, key, type, requested_at, target? , attempt }`
`target` is only set on retry: only the named subscriber must process it.

`forget.feedback` (subscribers -> orchestrator):
`{ process_id, subscriber, event: STARTED | SUCCEEDED | FAILED, detail?, occurred_at }`

## Behaviour
1. `POST /processes` creates a process (`PENDING`), publishes to `forget.requests`.
2. First `STARTED` from an unknown subscriber registers it in the subscriber registry; every `STARTED` adds that subscriber to the process waiting list with its start date.
3. `SUCCEEDED` / `FAILED` are appended to the subscriber's list of results (history, not overwritten).
4. Process status: `COMPLETED` only when **every** subscriber on the waiting list succeeded; `FAILED` if any is failed and none still running; otherwise `IN_PROGRESS`.
5. `POST /processes/{id}/subscribers/{name}/retry` republishes the request with `target=name`, `attempt+1`.
6. Feedback handling is idempotent (duplicate events are ignored).

## API (Auth0 JWT, audience + scopes)
- `POST /processes` · `GET /processes` · `GET /processes/{id}` · `POST /processes/{id}/subscribers/{name}/retry` · `GET /subscribers` · `GET /health`

Frontend shows: process id, key, type, timestamp, and per process the subscribers
(application name, start date, list of results, retry button).

## Architecture
Backend layers `domain` -> `application` (use cases + ports) -> `infrastructure` (SQLAlchemy repos, Kafka adapters) -> `api`. Dependencies point inward; Kafka and DB are replaceable adapters. Alembic migrations. Postgres.
Frontend: Vite + React + TypeScript + Tailwind + `@auth0/auth0-react`.

## Approaches considered
1. **Orchestrator with waiting list built from STARTED events (chosen, as requested).** Simple, no central config; subscribers are discovered.
2. Fixed subscriber list in config: predictable completion but needs deploy per new service.
3. Per-subscriber topics: more isolation, much more operational weight.

## Open limitation (my call, documented in an ADR)
A subscriber that never sends `STARTED` is invisible to that process. Mitigation: the registry of known subscribers is shown in the UI, and a process stays `IN_PROGRESS` for known-but-silent subscribers only if an optional timeout setting is enabled (off by default).

## Tests
Unit (pytest, vitest) for domain and use cases with fakes. Integration (pytest + Postgres and Kafka via docker-compose/Testcontainers) run in CI; Docker is not available in the authoring environment so these are not executed there.

## Builder calls (mine)
Python 3.12, `aiokafka`, SQLAlchemy 2 async + `asyncpg`, `uv`-free plain `pyproject.toml`, Ruff + mypy, GitHub Actions CI, MIT license.
