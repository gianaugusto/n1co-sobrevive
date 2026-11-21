---
description: Add a new PII type end to end (backend enum, frontend list, docs, tests)
argument-hint: <type name, e.g. phone>
allowed-tools: Read, Edit, Write, Bash(make:*), Bash(pytest:*), Bash(npm test:*)
---

Add the PII type `$ARGUMENTS` (lowercase value, UPPERCASE member name):

1. `backend/src/forgetme/domain/models.py`: add the member to `PiiType`.
2. `frontend/src/api/types.ts`: add the value to `PII_TYPES`; update the option expectation in `CreateProcessForm.test.tsx`.
3. `docs/messaging-contract.md`: list the new `type` and what `key` means for it.
4. Add or extend a test proving a process can be created with it (`backend/tests/integration/test_api.py`).
5. No migration is needed (the column is text). Run `make lint test`.
