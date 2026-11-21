import json
from uuid import uuid4

from forgetme.application.use_cases import CreateProcess, HandleFeedback
from forgetme.domain.models import PiiType, ProcessStatus
from forgetme.infrastructure.kafka.consumer import FeedbackProcessor
from tests.fakes import InMemoryStore, RecordingPublisher


def raw(process_id, event) -> bytes:
    return json.dumps(
        {
            "process_id": str(process_id),
            "subscriber": "billing",
            "event": event,
            "occurred_at": "2026-01-01T12:00:00Z",
        }
    ).encode()


async def test_valid_message_reaches_the_use_case():
    store = InMemoryStore()
    process = await CreateProcess(store.uow, RecordingPublisher()).execute(
        "acme", "jane", PiiType.EMAIL
    )
    processor = FeedbackProcessor(HandleFeedback(store.uow), retry_delay=0)

    await processor.process(raw(process.id, "SUCCEEDED"))

    assert process.status is ProcessStatus.COMPLETED


async def test_malformed_message_is_skipped_without_raising():
    store = InMemoryStore()
    await FeedbackProcessor(HandleFeedback(store.uow), retry_delay=0).process(b"garbage")
    assert store.commits == 0


async def test_transient_failures_are_retried_then_succeed():
    calls = []

    class Flaky:
        async def execute(self, feedback):
            calls.append(feedback)
            if len(calls) < 3:
                raise RuntimeError("db down")
            return True

    await FeedbackProcessor(Flaky(), max_attempts=3, retry_delay=0).process(raw(uuid4(), "STARTED"))
    assert len(calls) == 3


async def test_persistent_failure_is_given_up_without_raising():
    class Broken:
        calls = 0

        async def execute(self, feedback):
            Broken.calls += 1
            raise RuntimeError("db down")

    await FeedbackProcessor(Broken(), max_attempts=2, retry_delay=0).process(
        raw(uuid4(), "STARTED")
    )
    assert Broken.calls == 2
