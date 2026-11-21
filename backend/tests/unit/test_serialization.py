import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from forgetme.application.ports import ForgetRequestMessage
from forgetme.domain.models import FeedbackEvent, PiiType
from forgetme.infrastructure.kafka.serialization import (
    InvalidMessageError,
    feedback_from_bytes,
    request_to_bytes,
)


def test_request_message_follows_the_contract():
    process_id = uuid4()
    when = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    raw = request_to_bytes(
        ForgetRequestMessage(process_id, "acme", "jane", PiiType.USERNAME, when, 2, "billing")
    )

    assert json.loads(raw) == {
        "process_id": str(process_id),
        "tenant_id": "acme",
        "key": "jane",
        "type": "username",
        "requested_at": "2026-01-01T12:00:00+00:00",
        "attempt": 2,
        "target": "billing",
    }


def feedback_payload(**overrides):
    payload = {
        "process_id": str(uuid4()),
        "subscriber": "billing",
        "event": "SUCCEEDED",
        "occurred_at": "2026-01-01T12:00:00Z",
        "detail": "3 rows deleted",
    }
    payload.update(overrides)
    return json.dumps(payload).encode()


def test_feedback_is_parsed_including_zulu_timestamps():
    feedback = feedback_from_bytes(feedback_payload())

    assert feedback.event is FeedbackEvent.SUCCEEDED
    assert feedback.subscriber == "billing"
    assert feedback.occurred_at == datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert feedback.detail == "3 rows deleted"


def test_naive_timestamps_are_read_as_utc():
    feedback = feedback_from_bytes(feedback_payload(occurred_at="2026-01-01T12:00:00"))
    assert feedback.occurred_at.tzinfo is timezone.utc


def test_detail_is_optional():
    payload = json.loads(feedback_payload())
    del payload["detail"]
    assert feedback_from_bytes(json.dumps(payload).encode()).detail is None


@pytest.mark.parametrize(
    "raw",
    [
        b"not json",
        b"[]",
        b"\xff\xfe",
        feedback_payload(process_id="nope"),
        feedback_payload(event="DONE"),
        feedback_payload(subscriber="  "),
        feedback_payload(subscriber=None),
        feedback_payload(occurred_at="yesterday"),
        feedback_payload(occurred_at=123),
        json.dumps({"subscriber": "x"}).encode(),
    ],
)
def test_malformed_feedback_is_rejected(raw):
    with pytest.raises(InvalidMessageError):
        feedback_from_bytes(raw)
