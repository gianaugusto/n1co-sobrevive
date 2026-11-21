# 4. Layered architecture with ports and adapters

- Status: Accepted
- Date: 2026-11-21

## Context

SOLID and clean code were explicit requirements. The service touches three volatile things (database, Kafka, identity provider) that must not leak into business rules, and the rules must be testable without them.

## Decision

Four layers with inward-only dependencies: `domain` (aggregate `ForgetProcess`, enums, errors) ← `application` (one class per use case, plus ports `UnitOfWork`, `ProcessRepository`, `SubscriberRepository`, `MessagePublisher`) ← `infrastructure` (SQLAlchemy, aiokafka) and `api` (FastAPI). `main.py` is the only composition root. Use cases get their collaborators by constructor injection; state changes go through the aggregate, which enforces invariants.

## Alternatives considered

- Everything in route handlers: fastest to write, impossible to unit test without infrastructure.
- Full DDD with domain events, CQRS and a mediator: more ceremony than a base project should teach.

## Consequences

- Use cases and domain are covered by fast unit tests with in-memory fakes (`backend/tests/fakes.py`).
- Swapping Kafka or the database means writing one adapter.
- More files than a single-module app; the layout is documented in `docs/architecture.md`.
