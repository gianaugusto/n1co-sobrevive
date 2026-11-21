# Contributing

Thanks for helping! The project aims to stay **simple and objective**: a clear base other people can learn from and extend.

## Workflow

1. Open an issue for anything non-trivial before coding.
2. Branch from `main`, keep PRs small and focused.
3. Write the test first. Every behaviour change needs a unit test; anything touching the database, HTTP or Kafka also needs an integration test.
4. Run `make lint test` before pushing. CI runs the same checks.
5. If your change makes or reverses an architectural or technical decision, add or supersede an ADR (`docs/adr/`, copy `0000-template.md`).

## Code principles

- Follow the dependency rule: `domain` ← `application` ← `infrastructure` / `api`. The domain imports nothing from outside itself.
- SOLID, small functions, intention-revealing names, no comments that restate the code.
- New external dependencies (database, broker, …) go behind a port in `application/ports.py`.
- Public behaviour (REST or Kafka) changes must update `docs/api.md` or `docs/messaging-contract.md` in the same PR.

## Commits

Short imperative subject (`Add retry endpoint`). Explain *why* in the body when it is not obvious.

## Adding a PII type

1. Add the member to `PiiType` (`backend/src/forgetme/domain/models.py`) and to `PII_TYPES` (`frontend/src/api/types.ts`).
2. Document it in `docs/messaging-contract.md`.
3. No migration is needed: the column stores the value as text.
