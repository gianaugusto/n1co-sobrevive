# 17. Detecting silent subscribers is deferred

- Status: Accepted
- Date: 2026-11-21

## Context

Because subscribers join a process through `STARTED` (ADR 0007), a subscriber that is down and never starts is not on the waiting list, so a process can become `COMPLETED` without it.

## Decision

v1 accepts and documents this limit. The planned mitigation is an optional setting that snapshots the registry's known subscribers when a process is created and keeps the process `IN_PROGRESS` until each of them answers or a timeout expires (off by default). It is **not implemented** yet. Until then, the subscriber registry (`GET /api/v1/subscribers`) lets operators compare who they expect with who answered.

## Alternatives considered

- Implementing the snapshot/timeout now: extra state and scheduling for an edge case, before real usage shows the right defaults.
- Static expected list: see ADR 0007.

## Consequences

- Compliance-critical users should treat a completed process as "every subscriber that answered succeeded" until this is built.
