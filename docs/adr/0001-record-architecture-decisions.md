# 1. Record architecture decisions

- Status: Accepted
- Date: 2026-11-21

## Context

This is an open source base project meant to be read, forked and extended. Contributors need to know not only *what* the code does but *why* it is built this way, and that knowledge is lost when it lives only in chat threads or people's heads.

## Decision

We record every architectural and technical decision as an ADR in `docs/adr/`, one file per decision, numbered sequentially (`NNNN-short-title.md`), using `0000-template.md`. ADRs are immutable once accepted: to change a decision, add a new ADR that *supersedes* it and mark the old one `Superseded by NNNN`.

## Alternatives considered

- Wiki or Notion pages: drift away from the code and are not versioned with it.
- Only code comments: cannot hold alternatives and trade-offs.

## Consequences

- Decisions are reviewable in pull requests.
- Small overhead per significant decision; the `new-adr` Claude command and `adr-writer` agent in `.claude/` reduce it.
