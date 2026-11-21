"""SQLAlchemy implementations of the repository and unit-of-work ports."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from forgetme.domain.models import (
    FeedbackEvent,
    ForgetProcess,
    PiiType,
    Subscriber,
    SubscriberProgress,
    SubscriberResult,
)
from forgetme.infrastructure.db.orm import (
    ProcessRow,
    ResultRow,
    SubscriberProgressRow,
    SubscriberRow,
)

_EAGER = (selectinload(ProcessRow.subscribers).selectinload(SubscriberProgressRow.results),)


def _to_domain(row: ProcessRow) -> ForgetProcess:
    return ForgetProcess(
        id=row.id,
        tenant_id=row.tenant_id,
        key=row.key,
        type=PiiType(row.type),
        requested_at=row.requested_at,
        subscribers=[
            SubscriberProgress(
                name=sub.name,
                started_at=sub.started_at,
                attempt=sub.attempt,
                results=[
                    SubscriberResult(FeedbackEvent(r.event), r.occurred_at, r.detail)
                    for r in sub.results
                ],
            )
            for sub in row.subscribers
        ],
    )


def _result_row(result: SubscriberResult) -> ResultRow:
    return ResultRow(event=result.event.value, detail=result.detail, occurred_at=result.occurred_at)


def _to_row(process: ForgetProcess) -> ProcessRow:
    row = ProcessRow(
        id=process.id,
        tenant_id=process.tenant_id,
        key=process.key,
        type=process.type.value,
        requested_at=process.requested_at,
    )
    _sync_subscribers(row, process)
    return row


def _sync_subscribers(row: ProcessRow, process: ForgetProcess) -> None:
    """Bring ``row`` up to date. Results are append-only, so only new ones are inserted."""
    existing = {sub.name: sub for sub in row.subscribers}
    for progress in process.subscribers:
        sub_row = existing.get(progress.name)
        if sub_row is None:
            sub_row = SubscriberProgressRow(name=progress.name, started_at=progress.started_at)
            row.subscribers.append(sub_row)
        sub_row.attempt = progress.attempt
        for result in progress.results[len(sub_row.results) :]:
            sub_row.results.append(_result_row(result))


class SqlAlchemyProcessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, process: ForgetProcess) -> None:
        self._session.add(_to_row(process))

    async def get(self, process_id: UUID, *, lock: bool = False) -> ForgetProcess | None:
        row = await self._load(process_id, lock=lock)
        return _to_domain(row) if row else None

    async def save(self, process: ForgetProcess) -> None:
        row = await self._load(process.id)
        if row is None:
            self._session.add(_to_row(process))
            return
        _sync_subscribers(row, process)

    async def list(self, limit: int, offset: int) -> Sequence[ForgetProcess]:
        statement = (
            select(ProcessRow)
            .options(*_EAGER)
            .order_by(ProcessRow.requested_at.desc(), ProcessRow.id)
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.scalars(statement)).all()
        return [_to_domain(row) for row in rows]

    async def _load(self, process_id: UUID, *, lock: bool = False) -> ProcessRow | None:
        statement = select(ProcessRow).where(ProcessRow.id == process_id).options(*_EAGER)
        if lock:
            # No-op on SQLite; on PostgreSQL it serialises concurrent feedback for one process.
            statement = statement.with_for_update(of=ProcessRow)
        return (await self._session.scalars(statement)).one_or_none()


class SqlAlchemySubscriberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def touch(self, name: str, seen_at: datetime) -> None:
        row = await self._session.get(SubscriberRow, name)
        if row is None:
            self._session.add(SubscriberRow(name=name, first_seen_at=seen_at, last_seen_at=seen_at))
        else:
            row.last_seen_at = max(row.last_seen_at, seen_at)

    async def list(self) -> Sequence[Subscriber]:
        rows = (
            await self._session.scalars(select(SubscriberRow).order_by(SubscriberRow.name))
        ).all()
        return [Subscriber(r.name, r.first_seen_at, r.last_seen_at) for r in rows]


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.processes = SqlAlchemyProcessRepository(self._session)
        self.subscribers = SqlAlchemySubscriberRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        try:
            await self._session.rollback()  # no-op after a commit
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()
