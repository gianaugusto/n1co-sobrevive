from datetime import datetime, timezone
from uuid import uuid4

import pytest

from forgetme.application.use_cases import (
    CreateProcess,
    GetProcess,
    HandleFeedback,
    ListProcesses,
    ListSubscribers,
    RetrySubscriber,
)
from forgetme.domain.errors import ProcessNotFoundError, PublishError, RetryNotAllowedError
from forgetme.domain.models import Feedback, FeedbackEvent, PiiType, ProcessStatus
from tests.fakes import InMemoryStore, RecordingPublisher

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def publisher() -> RecordingPublisher:
    return RecordingPublisher()


async def create(store, publisher):
    return await CreateProcess(store.uow, publisher, clock=lambda: NOW).execute(
        "acme", "jane@example.com", PiiType.EMAIL
    )


def fb(process_id, subscriber, event, detail=None) -> Feedback:
    return Feedback(process_id, subscriber, event, NOW, detail)


async def test_create_persists_process_and_publishes_request(store, publisher):
    process = await create(store, publisher)

    assert process.status is ProcessStatus.PENDING
    assert await store.processes.get(process.id) is process
    [message] = publisher.messages
    assert (message.process_id, message.tenant_id, message.key, message.type) == (
        process.id,
        "acme",
        "jane@example.com",
        PiiType.EMAIL,
    )
    assert message.target is None and message.attempt == 1


async def test_create_keeps_process_pending_when_publish_fails(store):
    with pytest.raises(PublishError):
        await create(store, RecordingPublisher(fail=True))

    [process] = await ListProcesses(store.uow).execute()
    assert process.status is ProcessStatus.PENDING


async def test_get_unknown_process_raises(store):
    with pytest.raises(ProcessNotFoundError):
        await GetProcess(store.uow).execute(uuid4())


async def test_list_returns_newest_first_with_paging(store, publisher):
    ids = []
    for minute in range(3):
        clock = lambda m=minute: datetime(2026, 1, 1, 12, m, tzinfo=timezone.utc)  # noqa: E731
        process = await CreateProcess(store.uow, publisher, clock=clock).execute(
            "acme", f"user{minute}", PiiType.USERNAME
        )
        ids.append(process.id)

    page = await ListProcesses(store.uow).execute(limit=2, offset=1)
    assert [p.id for p in page] == [ids[1], ids[0]]


async def test_feedback_updates_process_and_registers_subscriber(store, publisher):
    process = await create(store, publisher)
    handle = HandleFeedback(store.uow)

    assert await handle.execute(fb(process.id, "billing", FeedbackEvent.STARTED)) is True
    assert await handle.execute(fb(process.id, "billing", FeedbackEvent.SUCCEEDED)) is True

    assert process.status is ProcessStatus.COMPLETED
    [subscriber] = await ListSubscribers(store.uow).execute()
    assert subscriber.name == "billing"


async def test_feedback_for_unknown_process_is_ignored(store):
    handled = await HandleFeedback(store.uow).execute(fb(uuid4(), "billing", FeedbackEvent.STARTED))

    assert handled is False
    assert await ListSubscribers(store.uow).execute() == []


async def test_duplicate_feedback_changes_nothing(store, publisher):
    process = await create(store, publisher)
    handle = HandleFeedback(store.uow)
    message = fb(process.id, "billing", FeedbackEvent.STARTED)

    await handle.execute(message)
    assert await handle.execute(message) is False
    assert len(process.find_subscriber("billing").results) == 1


async def test_retry_publishes_targeted_request_with_new_attempt(store, publisher):
    process = await create(store, publisher)
    handle = HandleFeedback(store.uow)
    await handle.execute(fb(process.id, "billing", FeedbackEvent.STARTED))
    await handle.execute(fb(process.id, "billing", FeedbackEvent.FAILED, "boom"))

    await RetrySubscriber(store.uow, publisher).execute(process.id, "billing")

    retry = publisher.messages[-1]
    assert (retry.target, retry.attempt, retry.process_id) == ("billing", 2, process.id)


async def test_retry_of_running_subscriber_is_rejected_and_publishes_nothing(store, publisher):
    process = await create(store, publisher)
    await HandleFeedback(store.uow).execute(fb(process.id, "billing", FeedbackEvent.STARTED))

    with pytest.raises(RetryNotAllowedError):
        await RetrySubscriber(store.uow, publisher).execute(process.id, "billing")
    assert len(publisher.messages) == 1  # only the original request


async def test_retry_of_unknown_process_raises(store, publisher):
    with pytest.raises(ProcessNotFoundError):
        await RetrySubscriber(store.uow, publisher).execute(uuid4(), "billing")
