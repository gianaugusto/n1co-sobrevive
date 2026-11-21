# Architecture Decision Records

Every architectural and technical decision of this project, with its reasoning. Format: [0000-template.md](0000-template.md). Add a new ADR for each new decision; supersede, never edit, accepted ones.

| # | Decision |
|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions |
| [0002](0002-orchestrator-not-eraser.md) | The service orchestrates; it does not erase data |
| [0003](0003-python-fastapi.md) | Python and FastAPI for the backend |
| [0004](0004-layered-architecture-ports-and-adapters.md) | Layered architecture with ports and adapters |
| [0005](0005-postgresql-sqlalchemy-alembic.md) | PostgreSQL, SQLAlchemy 2 (async) and Alembic |
| [0006](0006-kafka-two-topic-contract.md) | Kafka with a request topic and a feedback topic |
| [0007](0007-subscriber-discovery-via-started.md) | Subscribers are discovered through a STARTED event |
| [0008](0008-process-status-and-idempotent-feedback.md) | Derived process status and idempotent feedback |
| [0009](0009-targeted-retry.md) | Retries are targeted at one subscriber |
| [0010](0010-auth0-authentication.md) | Auth0 for API protection and UI login |
| [0011](0011-frontend-react-vite-tailwind.md) | React, Vite, TypeScript and Tailwind for the frontend |
| [0012](0012-testing-strategy.md) | Testing strategy: unit and integration |
| [0013](0013-publish-after-commit-outbox-deferred.md) | Publish after commit; transactional outbox deferred |
| [0014](0014-rest-api-design.md) | REST API design |
| [0015](0015-tooling-and-ci.md) | Tooling and continuous integration |
| [0016](0016-open-source-license-and-docs-language.md) | MIT license and English documentation |
| [0017](0017-silent-subscriber-timeout-deferred.md) | Detecting silent subscribers is deferred |
