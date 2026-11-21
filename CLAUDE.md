# forgetme-services — instructions for Claude Code

Open source **orchestrator for PII erasure**. It accepts a request (`tenant_id`, `key`, `type`), publishes it to Kafka, tracks every subscriber service's feedback, and reports whether **all** succeeded. It never deletes data itself. Read `README.md` and `docs/architecture.md` first.

## Stack

Backend: Python, FastAPI, SQLAlchemy 2 async, PostgreSQL, Alembic, aiokafka, PyJWT (Auth0). Frontend: React 18, TypeScript, Vite, Tailwind 4, `@auth0/auth0-react`. Tests: pytest, Vitest.

## Commands

```bash
make up              # PostgreSQL + Kafka (docker compose)
make test            # backend + frontend tests
make test-backend    # SQLite by default; DATABASE_URL=postgresql+asyncpg://... for Postgres
make lint            # ruff, mypy --strict, tsc
make format          # ruff fix + format
```

Always finish a change with `make lint test`. Never claim something works without running it; say so when a check could not be run (e.g. Docker unavailable).

## Architecture rules (backend/src/forgetme)

- `domain` ← `application` ← `infrastructure` / `api`. **Dependencies point inward only.** The domain imports nothing outside itself and no framework.
- Business rules live in the `ForgetProcess` aggregate; use cases (`application/use_cases.py`) orchestrate, one class per use case with an `execute` method.
- External systems are reached through ports in `application/ports.py`; adapters live in `infrastructure/`. Wiring happens only in `main.py`.
- Process status is **derived** from subscriber events, never stored. Feedback handling must stay idempotent.
- Auth: every endpoint except `/health` requires a permission (`forget:read` / `forget:write`). Never add a way to bypass authentication.
- Public contracts: REST (`docs/api.md`) and Kafka (`docs/messaging-contract.md`). Changing either means updating the doc in the same change; Kafka payload changes must stay backward compatible.

## Code style

Clear code over clever code: small functions, intention-revealing names, no comments that restate the code (comment *why*). Keep it simple — no abstraction without a second use. Python is typed (`mypy --strict`); TypeScript is `strict`. Max line length 100.

## Testing rules

Write the test first. New behaviour needs a unit test (fakes in `backend/tests/fakes.py`); anything touching the DB, HTTP or Kafka also needs an integration test (`backend/tests/integration`, marker `integration`). See `docs/adr/0012-testing-strategy.md`.

## Decisions

Every architectural/technical decision is an ADR in `docs/adr/` (index in `docs/adr/README.md`). Before changing something structural, read the relevant ADR. If you make or reverse a decision, add a new ADR with `/new-adr` (never edit an accepted one; supersede it).

## Known limits — do not "fix" silently

Silent subscribers (ADR 0017) and the missing outbox (ADR 0013) are documented, deliberate v1 gaps. Implement them only when asked, with an ADR.

## Agents and commands (`.claude/`)

| Agent | Use for |
|---|---|
| `backend-engineer` | Backend features and fixes, respecting the layers |
| `frontend-engineer` | React/Tailwind work |
| `test-writer` | Adding missing unit/integration tests |
| `adr-writer` | Drafting ADRs |
| `code-reviewer` | Reviewing a diff against these rules (read-only) |

| Command | What it does |
|---|---|
| `/check` | Run lint, types and all tests, summarise failures |
| `/new-adr <title>` | Create the next numbered ADR from the template |
| `/add-pii-type <name>` | Add a new `PiiType` end to end |
| `/add-endpoint <description>` | Add a REST endpoint through all layers |

Folder-specific guidance: `backend/CLAUDE.md`, `frontend/CLAUDE.md`.
