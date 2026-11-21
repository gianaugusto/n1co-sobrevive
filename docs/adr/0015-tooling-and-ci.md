# 15. Tooling and continuous integration

- Status: Accepted
- Date: 2026-11-21

## Context

Contributors should get the same fast feedback locally and in CI, with little setup.

## Decision

Backend: `ruff` (lint + format), `mypy --strict`, `pytest` with `pytest-asyncio`. Frontend: `tsc --noEmit`, Vitest, Vite build. A `Makefile` is the single entry point (`make up`, `make test`, `make lint`). `docker-compose.yml` provides PostgreSQL and Kafka (KRaft, single node, no Zookeeper). GitHub Actions runs lint, types, tests (PostgreSQL + Kafka) and the frontend build. Dependency ranges are declared in `pyproject.toml` / `package.json`; the frontend commits its lockfile.

## Alternatives considered

- Poetry/uv: good tools, but plain `pip` + `pyproject.toml` has the lowest barrier for newcomers.
- Separate linters (flake8, black, isort): ruff replaces all of them.

## Consequences

- The compose and Dockerfiles are exercised by CI, not by the unit tests.
