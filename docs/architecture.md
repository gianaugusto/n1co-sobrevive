# Architecture

## The idea

forgetme is an **orchestrator**. It owns the *process* of forgetting a person, not the data. Services
that hold PII (billing, CRM, analytics…) are **subscribers**; they do the deletion and report back.
See [ADR 0002](adr/0002-orchestrator-not-eraser.md) and [ADR 0007](adr/0007-subscriber-discovery-via-started.md).

## Flow

1. `POST /api/v1/processes` stores a `ForgetProcess` (status `PENDING`) and publishes it on `forget.requests`.
2. A subscriber consumes the request and publishes `STARTED` on `forget.feedback`. The orchestrator adds it to the process's **waiting list** (and to the global subscriber registry the first time).
3. The subscriber finishes and publishes `SUCCEEDED` or `FAILED` (with an optional `detail`).
4. Every event is appended to that subscriber's history, so the UI shows all returns, not just the last.
5. `POST …/subscribers/{name}/retry` republishes the request with `target = name`; only that subscriber reacts.

## Status rules

Subscriber status = its **last** event: `STARTED → IN_PROGRESS`, `SUCCEEDED`, `FAILED`.

| Process status | When |
|---|---|
| `PENDING` | nobody has reported yet |
| `IN_PROGRESS` | at least one subscriber is in progress |
| `FAILED` | nobody is in progress and at least one failed |
| `COMPLETED` | every subscriber on the waiting list succeeded |

Duplicate events are ignored, so Kafka's at-least-once delivery is safe ([ADR 0008](adr/0008-process-status-and-idempotent-feedback.md)).

## Layers (backend)

```
api             FastAPI routes, schemas, Auth0 dependency      → application
infrastructure  SQLAlchemy repositories, Kafka adapters        → application, domain
application     use cases + ports (UnitOfWork, MessagePublisher) → domain
domain          ForgetProcess aggregate, enums, errors         → nothing
main.py         composition root: wires adapters to use cases
```

Dependencies only point inward. Use cases receive a *unit-of-work factory* and a *publisher* through
their constructors, so tests run them against in-memory fakes ([ADR 0004](adr/0004-layered-architecture-ports-and-adapters.md)).

## Data model

`forget_processes` 1─* `process_subscribers` 1─* `subscriber_results`; plus `subscribers` (registry).
Results are append-only.

## Known limits (v1)

- A service that never sends `STARTED` is invisible to a process ([ADR 0017](adr/0017-silent-subscriber-timeout-deferred.md)).
- Publishing happens after the database commit; there is no outbox yet ([ADR 0013](adr/0013-publish-after-commit-outbox-deferred.md)).
