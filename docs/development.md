# Development

## Requirements

Python ≥ 3.10 (3.12 in Docker/CI), Node ≥ 20, Docker (for PostgreSQL and Kafka).

## Setup

```bash
cp .env.example .env && cp frontend/.env.example frontend/.env   # fill in Auth0 values
make up         # PostgreSQL :5432, Kafka :9092, topics forget.requests / forget.feedback
make install
make migrate
make api        # http://localhost:8000/docs
make web        # http://localhost:5173
```

Everything in Docker instead: `docker compose --profile app up --build`.

## Tests

| Command | What runs |
|---|---|
| `make test-backend` | unit tests + integration tests on **in-memory SQLite** (no Docker needed) |
| `DATABASE_URL=postgresql+asyncpg://forgetme:forgetme@localhost:5432/forgetme make test-backend` | the same integration tests on PostgreSQL |
| `KAFKA_BOOTSTRAP_SERVERS=localhost:9092 make test-backend` | also runs `tests/integration/test_kafka.py` against a real broker (skipped otherwise) |
| `make test-frontend` | Vitest + Testing Library |

See [ADR 0012](adr/0012-testing-strategy.md) for what goes in each kind of test.

## Migrations

```bash
cd backend
alembic revision -m "describe change"   # then edit the generated file
alembic upgrade head
```

## Lint and types

`make lint` (ruff, mypy `--strict`, `tsc`). `make format` fixes formatting.

## Trying the flow without a real subscriber

Publish a feedback message by hand:

```bash
echo '{"process_id":"<id>","subscriber":"demo","event":"STARTED","occurred_at":"2026-01-01T12:00:00Z"}' | \
  docker compose exec -T kafka /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic forget.feedback
```
