# Backend guidance

Layout: `src/forgetme/{domain,application,infrastructure,api}`, `main.py` (composition root), `migrations/`, `tests/{unit,integration}`.

- New use case: class in `application/use_cases.py` taking `UnitOfWorkFactory` (and a publisher if needed), one `execute` method. Unit-test it with `tests/fakes.py` first.
- New persistence need: extend the port in `application/ports.py`, implement it in `infrastructure/db/repositories.py`, add the fake, add an Alembic migration (`migrations/versions/`, next number), update `orm.py`.
- New HTTP endpoint: schema in `api/schemas.py`, route in `api/routes.py` with `dependencies=[read]` or `[write]`, map new domain errors in `api/app.py` (`_STATUS_BY_ERROR`), document in `docs/api.md`.
- Use `async with uow_factory() as uow:` and call `await uow.commit()` explicitly; no commit means rollback.
- Run: `cd backend && pytest`, `ruff check . && ruff format .`, `mypy src`.
- Python must stay compatible with 3.10 (use `str, Enum`, not `StrEnum`).
