---
description: Run lint, type checks and every test suite, then summarise failures
allowed-tools: Bash(make:*), Read
---

Run `make lint` and then `make test`. If something fails, show the first failure of each tool with the file and line, explain the cause in one sentence, and propose the minimal fix. Do not change code unless asked. If a tool cannot run (for example Docker is missing), say which check was skipped.
