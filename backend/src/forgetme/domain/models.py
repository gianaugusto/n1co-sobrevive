"""Domain model of the forget-me orchestrator.

``ForgetProcess`` is the aggregate root: every state change of a process and of its
subscribers goes through it, so its invariants live in one place.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID

from forgetme.domain.errors import RetryNotAllowedError, SubscriberNotFoundError


class PiiType(str, Enum):
    """Kind of identifier stored in ``ForgetProcess.key``. Add new members to extend."""

    EMAIL = "email"
    USERNAME = "username"


class FeedbackEvent(str, Enum):
    """Event a subscriber reports on the feedback topic."""

    STARTED = "STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class SubscriberStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ProcessStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_EVENT_TO_STATUS = {
    FeedbackEvent.STARTED: SubscriberStatus.IN_PROGRESS,
    FeedbackEvent.SUCCEEDED: SubscriberStatus.SUCCEEDED,
    FeedbackEvent.FAILED: SubscriberStatus.FAILED,
}


@dataclass(frozen=True)
class Feedback:
    """A feedback message received from a subscriber."""

    process_id: UUID
    subscriber: str
    event: FeedbackEvent
    occurred_at: datetime
    detail: str | None = None


@dataclass(frozen=True)
class SubscriberResult:
    """One entry of a subscriber's history of returns."""

    event: FeedbackEvent
    occurred_at: datetime
    detail: str | None = None


@dataclass
class SubscriberProgress:
    """Progress of one subscriber application inside one process."""

    name: str
    started_at: datetime
    attempt: int = 1
    results: list[SubscriberResult] = field(default_factory=list)

    @property
    def status(self) -> SubscriberStatus:
        if not self.results:
            return SubscriberStatus.IN_PROGRESS
        return _EVENT_TO_STATUS[self.results[-1].event]

    def record(self, result: SubscriberResult) -> bool:
        """Append ``result`` unless it is a duplicate. Returns whether it was added."""
        if result in self.results:
            return False
        self.results.append(result)
        return True


@dataclass
class ForgetProcess:
    """A request to forget one PII key of one tenant, tracked across all subscribers."""

    id: UUID
    tenant_id: str
    key: str
    type: PiiType
    requested_at: datetime
    subscribers: list[SubscriberProgress] = field(default_factory=list)

    @property
    def status(self) -> ProcessStatus:
        if not self.subscribers:
            return ProcessStatus.PENDING
        statuses = {subscriber.status for subscriber in self.subscribers}
        if SubscriberStatus.IN_PROGRESS in statuses:
            return ProcessStatus.IN_PROGRESS
        if SubscriberStatus.FAILED in statuses:
            return ProcessStatus.FAILED
        return ProcessStatus.COMPLETED

    def find_subscriber(self, name: str) -> SubscriberProgress | None:
        return next((s for s in self.subscribers if s.name == name), None)

    def apply_feedback(self, feedback: Feedback) -> bool:
        """Apply a subscriber event. Returns ``False`` when it was a duplicate (ignored).

        A subscriber we have not seen yet joins the waiting list, whatever its first
        event is: a late ``SUCCEEDED`` must not be lost because ``STARTED`` was missed.
        """
        subscriber = self.find_subscriber(feedback.subscriber)
        if subscriber is None:
            subscriber = SubscriberProgress(feedback.subscriber, started_at=feedback.occurred_at)
            self.subscribers.append(subscriber)
        return subscriber.record(
            SubscriberResult(feedback.event, feedback.occurred_at, feedback.detail)
        )

    def prepare_retry(self, name: str) -> int:
        """Validate a retry and return the new attempt number of subscriber ``name``."""
        subscriber = self.find_subscriber(name)
        if subscriber is None:
            raise SubscriberNotFoundError(self.id, name)
        if subscriber.status is not SubscriberStatus.FAILED:
            raise RetryNotAllowedError(name, subscriber.status.value)
        subscriber.attempt += 1
        return subscriber.attempt


@dataclass(frozen=True)
class Subscriber:
    """A service known to the orchestrator because it once sent feedback."""

    name: str
    first_seen_at: datetime
    last_seen_at: datetime
