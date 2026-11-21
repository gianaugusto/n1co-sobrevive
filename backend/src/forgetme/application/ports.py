"""Ports: what the application layer needs from the outside world."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol
from uuid import UUID

from forgetme.domain.models import ForgetProcess, PiiType, Subscriber


@dataclass(frozen=True)
class ForgetRequestMessage:
    """Message published on the requests topic. ``target`` is set only on retries."""

    process_id: UUID
    tenant_id: str
    key: str
    type: PiiType
    requested_at: datetime
    attempt: int = 1
    target: str | None = None


class ProcessRepository(Protocol):
    async def add(self, process: ForgetProcess) -> None: ...

    async def get(self, process_id: UUID, *, lock: bool = False) -> ForgetProcess | None:
        """Load a process. ``lock=True`` takes a row lock until the unit of work ends."""
        ...

    async def save(self, process: ForgetProcess) -> None: ...

    async def list(self, limit: int, offset: int) -> Sequence[ForgetProcess]: ...


class SubscriberRepository(Protocol):
    async def touch(self, name: str, seen_at: datetime) -> None:
        """Register ``name`` if unknown and update its last-seen date."""
        ...

    async def list(self) -> Sequence[Subscriber]: ...


class UnitOfWork(Protocol):
    """One transaction. Commit explicitly; leaving the block without commit rolls back."""

    @property
    def processes(self) -> ProcessRepository: ...

    @property
    def subscribers(self) -> SubscriberRepository: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...


class MessagePublisher(Protocol):
    async def publish_request(self, message: ForgetRequestMessage) -> None:
        """Publish to the requests topic. Raises ``PublishError`` on failure."""
        ...
