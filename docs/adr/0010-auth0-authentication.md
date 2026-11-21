# 10. Auth0 for API protection and UI login

- Status: Accepted
- Date: 2026-11-21

## Context

The API changes who is forgotten, so it must be protected, and operators need to log in to the UI.

## Decision

Auth0 is the identity provider. The React SPA logs in with the Authorization Code + PKCE flow (`@auth0/auth0-react`, tokens kept in memory). The API validates RS256 access tokens with PyJWT: signature through Auth0's JWKS, `iss`, `aud` and `exp` are required. Authorisation uses Auth0 RBAC permissions in the token's `permissions` claim: `forget:read` for GETs, `forget:write` for creating and retrying. There is no switch to disable authentication; tests inject a fake verifier.

## Alternatives considered

- Self-managed JWT/session auth: security-sensitive code the project should not own.
- API keys: no user identity and no per-person audit.

## Consequences

- Needs an Auth0 tenant (a free tier exists); setup is in `docs/auth0-setup.md`.
- The JWKS fetch is blocking, so the permission dependency is a sync function run in FastAPI's thread pool.
