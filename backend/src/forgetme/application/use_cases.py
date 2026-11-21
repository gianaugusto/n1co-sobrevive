"""Use cases. Each one is a small class with a single ``execute`` method."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from uuid import UUID, uuid4

from forgetme.application.ports import ForgetRequestMessage, MessagePublisher, UnitOfWork
from forgetme.domain.errors import ProcessNotFoundError
from forgetme.domain.models import Feedback, ForgetProcess, PiiType, Subscriber

logger = logging.getLogger(__name__)

UnitOfWorkFactory = Callable[[], UnitOfWork]
Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreateProcess:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, publisher: MessagePublisher, clock: Clock = utc_now
    ) -> None:
        self._uow_factory = uow_factory
        self._publisher = publisher
        self._clock = clock

    async def execute(self, tenant_id: str, key: str, pii_type: PiiType) -> ForgetProcess:
        process = ForgetProcess(
            id=uuid4(), tenant_id=tenant_id, key=key, type=pii_type, requested_at=self._clock()
        )
        async with self._uow_factory() as uow:
            await uow.processes.add(process)
            await uow.commit()
        # Published after the commit: if this fails the process stays PENDING (see ADR 0013).
        await self._publisher.publish_request(
            ForgetRequestMessage(
                process_id=process.id,
                tenant_id=tenant_id,
                key=key,
                type=pii_type,
                requested_at=process.requested_at,
            )
        )
        return process


class GetProcess:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, process_id: UUID) -> ForgetProcess:
        async with self._uow_factory() as uow:
            process = await uow.processes.get(process_id)
        if process is None:
            raise ProcessNotFoundError(process_id)
        return process


class ListProcesses:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, limit: int = 50, offset: int = 0) -> Sequence[ForgetProcess]:
        async with self._uow_factory() as uow:
            return await uow.processes.list(limit, offset)


class ListSubscribers:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self) -> Sequence[Subscriber]:
        async with self._uow_factory() as uow:
            return await uow.subscribers.list()


class HandleFeedback:
    """Applies a subscriber's feedback message to its process."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, feedback: Feedback) -> bool:
        """Returns ``True`` when the feedback changed state, ``False`` when ignored."""
        async with self._uow_factory() as uow:
            process = await uow.processes.get(feedback.process_id, lock=True)
            if process is None:
                logger.warning(
                    "Ignoring feedback for unknown process %s from %s",
                    feedback.process_id,
                    feedback.subscriber,
                )
                return False
            changed = process.apply_feedback(feedback)
            if changed:
                await uow.processes.save(process)
            await uow.subscribers.touch(feedback.subscriber, feedback.occurred_at)
            await uow.commit()
            return changed


class RetrySubscriber:
    def __init__(self, uow_factory: UnitOfWorkFactory, publisher: MessagePublisher) -> None:
        self._uow_factory = uow_factory
        self._publisher = publisher

    async def execute(self, process_id: UUID, subscriber: str) -> ForgetProcess:
        async with self._uow_factory() as uow:
            process = await uow.processes.get(process_id, lock=True)
            if process is None:
                raise ProcessNotFoundError(process_id)
            attempt = process.prepare_retry(subscriber)
            await uow.processes.save(process)
            await uow.commit()
        await self._publisher.publish_request(
            ForgetRequestMessage(
                process_id=process.id,
                tenant_id=process.tenant_id,
                key=process.key,
                type=process.type,
                requested_at=process.requested_at,
                attempt=attempt,
                target=subscriber,
            )
        )
        return process
