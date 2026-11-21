# 5. PostgreSQL, SQLAlchemy 2 (async) and Alembic

- Status: Accepted
- Date: 2026-11-21

## Context

Process state, per-subscriber progress and history must be durable and queryable, and concurrent feedback for the same process must not corrupt it.

## Decision

PostgreSQL as the database; SQLAlchemy 2.0 async ORM (`asyncpg` driver) in the infrastructure layer only; Alembic for migrations. Tables: `forget_processes`, `process_subscribers` (unique per process+name), `subscriber_results` (append-only history), `subscribers` (registry). The ORM is mapped to/from domain objects by hand so the domain stays free of SQLAlchemy. `HandleFeedback` and retries load the process with `SELECT … FOR UPDATE`, serialising concurrent changes to one process. A `UTCDateTime` type guarantees timezone-aware datetimes on every database.

## Alternatives considered

- MongoDB: the process aggregate fits a document, but the project requires PostgreSQL, and relational history is easy to query.
- SQLAlchemy models as domain entities: couples business rules to the ORM.
- Raw SQL: more code, no migrations tooling.

## Consequences

- Integration tests run on in-memory SQLite by default and on PostgreSQL in CI with the same test code; row locking is a no-op on SQLite.
- Hand-written mapping is more code but keeps the dependency rule intact.
