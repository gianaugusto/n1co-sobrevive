# 13. Publish after commit; transactional outbox deferred

- Status: Accepted
- Date: 2026-11-21

## Context

Creating a process writes to the database and publishes to Kafka. These cannot be one atomic operation.

## Decision

The process is committed first, then published. If publishing fails the API answers `503`, the process stays `PENDING`, and nothing is lost silently. Retrying a subscriber follows the same order. A transactional outbox (write the message in the same transaction, relay it asynchronously) is the correct next step but is deferred to keep v1 simple.

## Alternatives considered

- Publish first, then save: could send a request for a process that was never stored.
- Outbox now: more tables and a relay worker for a basic project.

## Consequences

- Known gap: a crash between commit and publish leaves a `PENDING` process that was never published; an operator can see it in the UI.
- Follow-up work: outbox, and a purge policy for old processes (the `key` is PII).
