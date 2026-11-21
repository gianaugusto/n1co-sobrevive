# 12. Testing strategy: unit and integration

- Status: Accepted
- Date: 2026-11-21

## Context

Unit and integration tests were an explicit requirement, and contributors must be able to run them without installing a cluster.

## Decision

**Unit tests** cover the domain and every use case with in-memory fakes, plus pure adapters logic (serialization, feedback processor, JWT verification). **Integration tests** (marker `integration`) run real SQLAlchemy repositories, the migration, and the full HTTP → use case → database flow with a fake broker and fake verifier. They default to in-memory SQLite and switch to PostgreSQL with `DATABASE_URL`. One more test talks to a real Kafka broker and is skipped unless `KAFKA_BOOTSTRAP_SERVERS` is set. CI runs everything against PostgreSQL and Kafka started by docker compose. Frontend: Vitest + Testing Library at component and dashboard level. Tests are written first for new behaviour.

## Alternatives considered

- Testcontainers: needs Docker for every run; plain compose is simpler and shared with local development.
- Only mocks: would not catch mapping, migration or SQL problems.

## Consequences

- `make test` works with no Docker; confidence on PostgreSQL and Kafka comes from CI.
- SQLite ignores row locks, so locking behaviour is only exercised on PostgreSQL.
