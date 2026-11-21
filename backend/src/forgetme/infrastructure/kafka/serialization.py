"""JSON wire format of the two topics. See docs/messaging-contract.md."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from forgetme.application.ports import ForgetRequestMessage
from forgetme.domain.models import Feedback, FeedbackEvent


class InvalidMessageError(ValueError):
    """A message on the feedback topic does not follow the contract."""


def request_to_bytes(message: ForgetRequestMessage) -> bytes:
    payload: dict[str, Any] = {
        "process_id": str(message.process_id),
        "tenant_id": message.tenant_id,
        "key": message.key,
        "type": message.type.value,
        "requested_at": message.requested_at.isoformat(),
        "attempt": message.attempt,
        "target": message.target,
    }
    return json.dumps(payload).encode("utf-8")


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise InvalidMessageError("occurred_at must be an ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise InvalidMessageError(f"occurred_at is not ISO 8601: {value!r}") from error
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def feedback_from_bytes(raw: bytes) -> Feedback:
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as error:
        raise InvalidMessageError("payload is not valid JSON") from error
    if not isinstance(payload, dict):
        raise InvalidMessageError("payload must be a JSON object")
    try:
        subscriber = payload["subscriber"]
        if not isinstance(subscriber, str) or not subscriber.strip():
            raise InvalidMessageError("subscriber must be a non-empty string")
        detail = payload.get("detail")
        return Feedback(
            process_id=UUID(str(payload["process_id"])),
            subscriber=subscriber.strip(),
            event=FeedbackEvent(payload["event"]),
            occurred_at=_parse_timestamp(payload["occurred_at"]),
            detail=None if detail is None else str(detail),
        )
    except KeyError as error:
        raise InvalidMessageError(f"missing field {error}") from error
    except ValueError as error:  # bad UUID or unknown event (InvalidMessageError is one too)
        raise InvalidMessageError(str(error)) from error
