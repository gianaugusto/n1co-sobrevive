"""In-memory test doubles for the application ports."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from uuid import UUID

from forgetme.application.ports import ForgetRequestMessage
from forgetme.domain.errors import PublishError
from forgetme.domain.models import ForgetProcess, Subscriber


class InMemoryProcesses:
    def __init__(self) -> None:
        self.items: dict[UUID, ForgetProcess] = {}

    async def add(self, process: ForgetProcess) -> None:
        self.items[process.id] = process

    async def get(self, process_id: UUID, *, lock: bool = False) -> ForgetProcess | None:
        return self.items.get(process_id)

    async def save(self, process: ForgetProcess) -> None:
        self.items[process.id] = process

    async def list(self, limit: int, offset: int) -> Sequence[ForgetProcess]:
        ordered = sorted(self.items.values(), key=lambda p: p.requested_at, reverse=True)
        return ordered[offset : offset + limit]


class InMemorySubscribers:
    def __init__(self) -> None:
        self.items: dict[str, Subscriber] = {}

    async def touch(self, name: str, seen_at: datetime) -> None:
        known = self.items.get(name)
        first = known.first_seen_at if known else seen_at
        self.items[name] = Subscriber(name, first, seen_at)

    async def list(self) -> Sequence[Subscriber]:
        return sorted(self.items.values(), key=lambda s: s.name)


class InMemoryStore:
    """Shared state; ``uow()`` hands out units of work over it."""

    def __init__(self) -> None:
        self.processes = InMemoryProcesses()
        self.subscribers = InMemorySubscribers()
        self.commits = 0

    def uow(self) -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(self)


class InMemoryUnitOfWork:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self.processes = store.processes
        self.subscribers = store.subscribers

    async def __aenter__(self) -> InMemoryUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self._store.commits += 1


class RecordingPublisher:
    def __init__(self, fail: bool = False) -> None:
        self.messages: list[ForgetRequestMessage] = []
        self.fail = fail

    async def publish_request(self, message: ForgetRequestMessage) -> None:
        if self.fail:
            raise PublishError("broker down")
        self.messages.append(message)
