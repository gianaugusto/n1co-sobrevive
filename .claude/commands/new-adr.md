---
description: Create the next numbered ADR from the template
argument-hint: <decision title>
allowed-tools: Read, Write, Edit, Glob
---

Create an ADR for: $ARGUMENTS

1. List `docs/adr/` and take the next number.
2. Copy `docs/adr/0000-template.md` to `docs/adr/NNNN-<kebab-title>.md` and fill every section using the current conversation and code (ask me if the decision or its alternatives are unclear).
3. Add a row to `docs/adr/README.md`.
4. If it supersedes an ADR, mark the old one `Superseded by NNNN` (status line only).
