# 2. The service orchestrates; it does not erase data

- Status: Accepted
- Date: 2026-11-21

## Context

The requirement is a basic service for forgetting PII. PII lives in many services, each with its own storage and rules. A central service that reaches into every database would need credentials and schema knowledge for all of them.

## Decision

forgetme only **coordinates**: it accepts a request, publishes it, and tracks the answers of the services that actually hold the data (the *subscribers*). It stores the identifier to forget (`key`) only as long as needed to track the process, and never connects to subscribers' data stores.

## Alternatives considered

- Central eraser with direct database access: tight coupling, broad credentials, a security risk.
- Fire-and-forget publish without tracking: no proof that erasure happened, which compliance needs.

## Consequences

- Subscribers own their deletion logic and can be added without changing forgetme.
- The tracked `key` is itself PII; retention/purging of old processes is a future concern (see ADR 0013's follow-ups).
