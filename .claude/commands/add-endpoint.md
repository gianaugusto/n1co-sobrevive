---
description: Add a REST endpoint through every backend layer, test-first
argument-hint: <what the endpoint does>
allowed-tools: Read, Edit, Write, Bash(make:*), Bash(pytest:*)
---

Add an endpoint: $ARGUMENTS

Follow `backend/CLAUDE.md`. Order: failing integration test in `backend/tests/integration/test_api.py` (include 401/403 cases) → use case (+ unit test with fakes) → port/repository change and migration if needed → schema and route with `read`/`write` permission → error mapping → `docs/api.md`. Finish with `make lint test-backend` and report the results.
