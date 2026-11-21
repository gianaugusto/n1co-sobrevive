# 8. Derived process status and idempotent feedback

- Status: Accepted
- Date: 2026-11-21

## Context

Kafka delivers at least once, so duplicates and reordering happen. Process status must always be consistent with the facts received.

## Decision

Status is **derived**, never stored: a subscriber's status is its last event; a process is `PENDING` (no subscribers), `IN_PROGRESS` (any subscriber in progress), `FAILED` (none in progress, at least one failed) or `COMPLETED` (all succeeded). History is append-only; a feedback identical to one already recorded (same event, timestamp and detail) is ignored. Feedback for an unknown process id is logged and dropped.

## Alternatives considered

- Stored status column updated on every event: can drift from the history and needs extra care under concurrency.
- Event deduplication by message id: the contract has no id, and adding one burdens every subscriber.

## Consequences

- Replaying the same messages yields the same state.
- Status is computed from loaded subscribers, which are always loaded together with the process.
