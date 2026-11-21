# 11. React, Vite, TypeScript and Tailwind for the frontend

- Status: Accepted
- Date: 2026-11-21

## Context

Operators need to create requests and follow progress (id, key, type, timestamp, subscribers with start date, history and retry).

## Decision

A single-page app with React 18, TypeScript (`strict`), Vite, Tailwind CSS 4. No router or state library: a custom hook polls the list every 5 s, which is enough for a status board. The HTTP layer is a small injectable client (`createApiClient`) so components are tested with fakes. Vitest and Testing Library for tests.

## Alternatives considered

- Next.js: server rendering is not needed behind a login.
- Redux/React Query: more machinery than three screens of state justify.
- WebSockets/SSE for live updates: polling is simpler; revisit if load demands it.

## Consequences

- Few dependencies, easy to read.
- Up to 5 s of staleness in the UI.
