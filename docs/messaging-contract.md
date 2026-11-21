# Messaging contract

Two Kafka topics, JSON (UTF-8) payloads. Names are configurable (`KAFKA_REQUESTS_TOPIC`, `KAFKA_FEEDBACK_TOPIC`).

## `forget.requests` — orchestrator → subscribers

Key: `process_id`.

```json
{
  "process_id": "6f1c1f44-7f4e-4a0e-9a53-0f0f2f6d3c11",
  "tenant_id": "acme",
  "key": "jane@example.com",
  "type": "email",
  "requested_at": "2026-01-01T12:00:00+00:00",
  "attempt": 1,
  "target": null
}
```

| Field | Meaning |
|---|---|
| `process_id` | UUID of the forget process. Echo it in every feedback message. |
| `tenant_id` | Tenant that owns the data. |
| `key` | Value used to find the user's data. Its meaning depends on `type`. |
| `type` | `email` or `username`. Subscribers must ignore types they do not understand. |
| `requested_at` | ISO 8601 timestamp. |
| `attempt` | `1` for the first request, increased on each retry. |
| `target` | `null` = every subscriber must handle it. A name = **only** the subscriber with that name must handle it (retry); all others ignore it. |

## `forget.feedback` — subscribers → orchestrator

Key: **use `process_id`** so all events of a process stay ordered in one partition.

```json
{
  "process_id": "6f1c1f44-7f4e-4a0e-9a53-0f0f2f6d3c11",
  "subscriber": "billing",
  "event": "FAILED",
  "occurred_at": "2026-01-01T12:05:00Z",
  "detail": "timeout calling payments-db"
}
```

| Field | Required | Meaning |
|---|---|---|
| `process_id` | yes | UUID from the request. Unknown ids are ignored. |
| `subscriber` | yes | Your application name. Stable and unique; it identifies you in the UI and for retries. |
| `event` | yes | `STARTED`, `SUCCEEDED` or `FAILED`. |
| `occurred_at` | yes | ISO 8601. Without a timezone it is read as UTC. |
| `detail` | no | Free text shown in the UI (error message, rows deleted…). |

### Rules

- Send `STARTED` as soon as you begin. That is what puts you on the waiting list.
- Finish with exactly one `SUCCEEDED` or `FAILED` per attempt. A retry starts with a new `STARTED`.
- Sending the same event twice (same `event`, `occurred_at`, `detail`) is harmless; it is ignored.
- Malformed messages are logged and skipped; they never block the consumer.
- Erasing must be **idempotent**: a retry or redelivery may ask you to forget data that is already gone. That is a success.
