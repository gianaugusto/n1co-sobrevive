from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from forgetme.domain.models import (
    Feedback,
    FeedbackEvent,
    ForgetProcess,
    PiiType,
    ProcessStatus,
)

pytestmark = pytest.mark.integration
T0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def new_process(minutes: int = 0) -> ForgetProcess:
    return ForgetProcess(
        id=uuid4(),
        tenant_id="acme",
        key="jane@example.com",
        type=PiiType.EMAIL,
        requested_at=T0 + timedelta(minutes=minutes),
    )


async def test_process_round_trip_keeps_timezone(uow_factory):
    process = new_process()
    async with uow_factory() as uow:
        await uow.processes.add(process)
        await uow.commit()

    async with uow_factory() as uow:
        loaded = await uow.processes.get(process.id)
    assert loaded == process
    assert loaded.requested_at.tzinfo is not None


async def test_unknown_process_is_none(uow_factory):
    async with uow_factory() as uow:
        assert await uow.processes.get(uuid4()) is None


async def test_uncommitted_work_is_rolled_back(uow_factory):
    process = new_process()
    async with uow_factory() as uow:
        await uow.processes.add(process)
    async with uow_factory() as uow:
        assert await uow.processes.get(process.id) is None


async def test_feedback_history_is_appended_across_saves(uow_factory):
    process = new_process()
    async with uow_factory() as uow:
        await uow.processes.add(process)
        await uow.commit()

    for minute, event, detail in [
        (1, FeedbackEvent.STARTED, None),
        (2, FeedbackEvent.FAILED, "timeout"),
        (3, FeedbackEvent.STARTED, None),
    ]:
        async with uow_factory() as uow:
            loaded = await uow.processes.get(process.id, lock=True)
            loaded.apply_feedback(
                Feedback(process.id, "billing", event, T0 + timedelta(minutes=minute), detail)
            )
            await uow.processes.save(loaded)
            await uow.commit()

    async with uow_factory() as uow:
        loaded = await uow.processes.get(process.id)
    billing = loaded.find_subscriber("billing")
    assert [r.event for r in billing.results] == [
        FeedbackEvent.STARTED,
        FeedbackEvent.FAILED,
        FeedbackEvent.STARTED,
    ]
    assert billing.results[1].detail == "timeout"
    assert billing.started_at == T0 + timedelta(minutes=1)
    assert loaded.status is ProcessStatus.IN_PROGRESS


async def test_retry_attempt_is_persisted(uow_factory):
    process = new_process()
    process.apply_feedback(Feedback(process.id, "crm", FeedbackEvent.FAILED, T0))
    async with uow_factory() as uow:
        await uow.processes.add(process)
        await uow.commit()
    async with uow_factory() as uow:
        loaded = await uow.processes.get(process.id)
        loaded.prepare_retry("crm")
        await uow.processes.save(loaded)
        await uow.commit()
    async with uow_factory() as uow:
        assert (await uow.processes.get(process.id)).find_subscriber("crm").attempt == 2


async def test_list_is_newest_first_and_paged(uow_factory):
    processes = [new_process(minutes) for minutes in range(3)]
    async with uow_factory() as uow:
        for process in processes:
            await uow.processes.add(process)
        await uow.commit()

    async with uow_factory() as uow:
        page = await uow.processes.list(limit=2, offset=0)
        rest = await uow.processes.list(limit=2, offset=2)
    assert [p.id for p in page] == [processes[2].id, processes[1].id]
    assert [p.id for p in rest] == [processes[0].id]


async def test_subscribers_are_registered_once_and_track_last_seen(uow_factory):
    async with uow_factory() as uow:
        await uow.subscribers.touch("billing", T0)
        await uow.subscribers.touch("crm", T0)
        await uow.commit()
    async with uow_factory() as uow:
        await uow.subscribers.touch("billing", T0 + timedelta(hours=1))
        await uow.subscribers.touch("billing", T0 - timedelta(hours=1))  # out-of-order event
        await uow.commit()
    async with uow_factory() as uow:
        subscribers = await uow.subscribers.list()

    assert [s.name for s in subscribers] == ["billing", "crm"]
    assert subscribers[0].first_seen_at == T0
    assert subscribers[0].last_seen_at == T0 + timedelta(hours=1)
