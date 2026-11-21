# forgetme-services Implementation Plan

**Goal:** Build the forget-me orchestrator (API, Kafka, Postgres, React UI, docs, ADRs, agent setup).
**Architecture:** Layered backend (domain -> application -> infrastructure -> api) with ports/adapters; React SPA.
**Tech Stack:** Python, FastAPI, SQLAlchemy 2 async, Alembic, aiokafka, PyJWT (Auth0), React, Vite, TypeScript, Tailwind.
**Spec:** docs/superpowers/specs/2026-11-21-forgetme-orchestrator-design.md

## Tasks
1. Backend domain (aggregate, status derivation, idempotent feedback, retry rules) with unit tests.
2. Backend application use cases over ports (UnitOfWork, MessagePublisher) with in-memory fakes and unit tests.
3. Infrastructure: SQLAlchemy repositories + Alembic migration; Kafka serialization, publisher, consumer.
4. API: routes, schemas, Auth0 JWT verification, error mapping; integration tests (HTTP + DB).
5. Frontend: Auth0 login, create form, process list, subscriber detail with retry; vitest tests.
6. Docs, 17 ADRs, CLAUDE.md, .claude agents/commands, compose, CI, license, contributing.
7. Run all tests and builds available locally; report what could not run.

## Review Focus
- Feedback for an unknown process id is ignored, not an error.
- SUCCEEDED/FAILED arriving before STARTED registers the subscriber implicitly.
- Duplicate feedback events are ignored.
- Retry only for a FAILED subscriber; unknown subscriber -> 404, non-failed -> 409.
- Malformed Kafka feedback payloads are skipped without killing the consumer.
