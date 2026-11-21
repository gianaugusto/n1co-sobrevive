# 6. Kafka with a request topic and a feedback topic

- Status: Accepted
- Date: 2026-11-21

## Context

Subscribers are independent services, written by different teams, that must learn about requests and answer asynchronously.

## Decision

Two topics: `forget.requests` (orchestrator → subscribers, fan-out: each subscriber uses its own consumer group) and `forget.feedback` (subscribers → orchestrator, one consumer group). JSON payloads documented in `docs/messaging-contract.md`; both topics are keyed by `process_id` so one process stays ordered. The orchestrator commits feedback offsets only after processing (at-least-once); malformed messages are logged and skipped, transient handler failures are retried 3 times and then logged. `aiokafka` is the client.

## Alternatives considered

- REST callbacks/webhooks: every subscriber needs an HTTP endpoint and retry logic.
- One topic for both directions: every party would read the other's traffic.
- Avro/Protobuf + schema registry: better evolution guarantees but heavy for a basic project; can be adopted later by versioning the contract.

## Consequences

- Subscribers need only a Kafka client to participate.
- No dead-letter topic yet: a feedback message that keeps failing is dropped after logging.
- Payload changes must be backward compatible (add optional fields only).
