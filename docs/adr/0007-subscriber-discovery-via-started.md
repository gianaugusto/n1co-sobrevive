# 7. Subscribers are discovered through a STARTED event

- Status: Accepted
- Date: 2026-11-21

## Context

forgetme must know which services must finish before a process is complete, but new services subscribe to the topic over time, and a static list would require a deployment for each one.

## Decision

A subscriber announces itself by publishing `STARTED` on the feedback topic. At that moment it is added to that process's **waiting list** (name + start date) and, the first time ever, to the global subscriber registry. A process is complete only when every subscriber on its waiting list has succeeded. A `SUCCEEDED`/`FAILED` that arrives without a prior `STARTED` also registers the subscriber, so a lost or reordered message cannot hide a result.

## Alternatives considered

- Static subscriber list in configuration: predictable, but needs a deploy per new service.
- Subscribers register through a REST endpoint: extra moving part and credentials.

## Consequences

- Zero configuration to onboard a service.
- A service that never sends `STARTED` is invisible to the process (ADR 0017).
