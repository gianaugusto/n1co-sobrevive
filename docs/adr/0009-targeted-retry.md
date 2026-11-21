# 9. Retries are targeted at one subscriber

- Status: Accepted
- Date: 2026-11-21

## Context

When one subscriber fails, repeating the request for everyone would make healthy subscribers redo (and re-report) their work.

## Decision

Retry is a per-subscriber action: `POST …/subscribers/{name}/retry` is allowed only for subscribers whose status is `FAILED`. The orchestrator increments the subscriber's `attempt` and republishes the request on `forget.requests` with `target = name` and the new `attempt`. Every other subscriber ignores messages whose `target` is not their name. The retried subscriber starts again with `STARTED`.

## Alternatives considered

- Re-publishing the original request to all: wasteful and confusing history.
- A dedicated retry topic per subscriber: topic sprawl.

## Consequences

- Subscribers must honour `target` (documented in the subscriber guide).
- Until the subscriber sends `STARTED` again, it still shows as `FAILED`.
