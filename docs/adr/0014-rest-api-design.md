# 14. REST API design

- Status: Accepted
- Date: 2026-11-21

## Context

The UI and any integration need a small, predictable HTTP interface.

## Decision

Resources under `/api/v1`: `processes` (create, list with `limit`/`offset`, get), the action `POST /processes/{id}/subscribers/{name}/retry`, and `subscribers`. Domain errors are mapped in one place: unknown resource `404`, retry not allowed `409`, broker failure `503`; validation errors `422`; auth errors `401`/`403`. Process responses always include the subscribers and their history, so one call is enough to render the detail view. `/health` is public.

## Alternatives considered

- GraphQL: flexibility not needed for three screens.
- Unversioned paths: breaking changes would hit every client.

## Consequences

- The list endpoint returns full histories; if volume grows, a summary variant should be added.
