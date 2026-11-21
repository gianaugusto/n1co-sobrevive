from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from forgetme.domain.errors import RetryNotAllowedError, SubscriberNotFoundError
from forgetme.domain.models import (
    Feedback,
    FeedbackEvent,
    ForgetProcess,
    PiiType,
    ProcessStatus,
    SubscriberStatus,
)

T0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_process() -> ForgetProcess:
    return ForgetProcess(
        id=uuid4(), tenant_id="acme", key="jane@example.com", type=PiiType.EMAIL, requested_at=T0
    )


def feedback(
    process: ForgetProcess, subscriber: str, event: FeedbackEvent, minutes: int = 0, detail=None
) -> Feedback:
    return Feedback(process.id, subscriber, event, T0 + timedelta(minutes=minutes), detail)


def test_new_process_is_pending():
    assert make_process().status is ProcessStatus.PENDING


def test_started_adds_subscriber_to_waiting_list_with_start_date():
    process = make_process()
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.STARTED, minutes=2))

    subscriber = process.find_subscriber("billing")
    assert subscriber is not None
    assert subscriber.started_at == T0 + timedelta(minutes=2)
    assert subscriber.status is SubscriberStatus.IN_PROGRESS
    assert process.status is ProcessStatus.IN_PROGRESS


def test_process_completes_only_when_every_subscriber_succeeded():
    process = make_process()
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.STARTED))
    process.apply_feedback(feedback(process, "crm", FeedbackEvent.STARTED))
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.SUCCEEDED, 1))
    assert process.status is ProcessStatus.IN_PROGRESS

    process.apply_feedback(feedback(process, "crm", FeedbackEvent.SUCCEEDED, 2))
    assert process.status is ProcessStatus.COMPLETED


def test_process_fails_when_a_subscriber_failed_and_none_is_running():
    process = make_process()
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.STARTED))
    process.apply_feedback(feedback(process, "crm", FeedbackEvent.STARTED))
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.FAILED, 1, "timeout"))
    assert process.status is ProcessStatus.IN_PROGRESS  # crm still running

    process.apply_feedback(feedback(process, "crm", FeedbackEvent.SUCCEEDED, 2))
    assert process.status is ProcessStatus.FAILED


def test_results_keep_the_history_of_returns():
    process = make_process()
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.STARTED))
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.FAILED, 1, "boom"))

    events = [r.event for r in process.find_subscriber("billing").results]
    assert events == [FeedbackEvent.STARTED, FeedbackEvent.FAILED]
    assert process.find_subscriber("billing").results[-1].detail == "boom"


def test_duplicate_feedback_is_ignored():
    process = make_process()
    message = feedback(process, "billing", FeedbackEvent.STARTED)
    assert process.apply_feedback(message) is True
    assert process.apply_feedback(message) is False
    assert len(process.find_subscriber("billing").results) == 1


def test_success_before_started_still_registers_the_subscriber():
    process = make_process()
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.SUCCEEDED, 3))

    assert process.find_subscriber("billing").started_at == T0 + timedelta(minutes=3)
    assert process.status is ProcessStatus.COMPLETED


def test_retry_increments_attempt_for_failed_subscriber():
    process = make_process()
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.STARTED))
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.FAILED, 1))

    assert process.prepare_retry("billing") == 2
    assert process.find_subscriber("billing").attempt == 2


def test_retry_restart_brings_subscriber_back_in_progress():
    process = make_process()
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.FAILED))
    process.prepare_retry("billing")
    process.apply_feedback(feedback(process, "billing", FeedbackEvent.STARTED, 5))

    assert process.status is ProcessStatus.IN_PROGRESS


def test_retry_of_unknown_subscriber_is_rejected():
    with pytest.raises(SubscriberNotFoundError):
        make_process().prepare_retry("ghost")


@pytest.mark.parametrize("event", [FeedbackEvent.STARTED, FeedbackEvent.SUCCEEDED])
def test_retry_of_non_failed_subscriber_is_rejected(event):
    process = make_process()
    process.apply_feedback(feedback(process, "billing", event))
    with pytest.raises(RetryNotAllowedError):
        process.prepare_retry("billing")
