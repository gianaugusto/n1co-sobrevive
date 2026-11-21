# 16. MIT license and English documentation

- Status: Accepted
- Date: 2026-11-21

## Context

The project is a community base; it should be easy to adopt, including commercially, and understood across countries.

## Decision

MIT license. Documentation, code, commit messages and ADRs are written in English. Public behaviour (REST, Kafka) is documented next to the code and must change in the same pull request as the code.

## Alternatives considered

- Apache-2.0: also fine, adds a patent grant at the cost of length.
- Portuguese docs: would limit the audience; translations can be added under `docs/pt-BR/` later.

## Consequences

- Anyone can reuse the project; no warranty.
