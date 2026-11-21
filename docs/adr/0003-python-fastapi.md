# 3. Python and FastAPI for the backend

- Status: Accepted
- Date: 2026-11-21

## Context

The project is a teaching-friendly base. It needs async I/O (Kafka consumer, database), automatic API documentation and strong typing for the request/response contract.

## Decision

Python with **FastAPI**, Pydantic v2 for validation, `mypy --strict` and `ruff` for quality. Code targets Python ≥ 3.10; Docker and CI use 3.12.

## Alternatives considered

- Django REST: heavier, sync-first, more framework than this service needs.
- Flask: no built-in validation or OpenAPI.
- Node/NestJS or .NET: valid; Python was chosen for its async ecosystem, typing support and low barrier for contributors.

## Consequences

- OpenAPI docs for free at `/docs`.
- Async stack end to end; blocking calls (JWKS fetch) must be kept in sync `def` dependencies so FastAPI runs them in a thread.
