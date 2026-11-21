"""HTTP request and response models."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, StringConstraints

from forgetme.domain.models import (
    FeedbackEvent,
    ForgetProcess,
    PiiType,
    ProcessStatus,
    Subscriber,
    SubscriberProgress,
    SubscriberStatus,
)

TenantId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
PiiKey = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=512)]


class CreateProcessIn(BaseModel):
    tenant_id: TenantId
    key: PiiKey
    type: PiiType


class ResultOut(BaseModel):
    event: FeedbackEvent
    detail: str | None
    occurred_at: datetime


class SubscriberProgressOut(BaseModel):
    name: str
    started_at: datetime
    status: SubscriberStatus
    attempt: int
    results: list[ResultOut]

    @classmethod
    def from_domain(cls, progress: SubscriberProgress) -> SubscriberProgressOut:
        return cls(
            name=progress.name,
            started_at=progress.started_at,
            status=progress.status,
            attempt=progress.attempt,
            results=[
                ResultOut(event=r.event, detail=r.detail, occurred_at=r.occurred_at)
                for r in progress.results
            ],
        )


class ProcessOut(BaseModel):
    id: UUID
    tenant_id: str
    key: str
    type: PiiType
    status: ProcessStatus
    requested_at: datetime
    subscribers: list[SubscriberProgressOut]

    @classmethod
    def from_domain(cls, process: ForgetProcess) -> ProcessOut:
        return cls(
            id=process.id,
            tenant_id=process.tenant_id,
            key=process.key,
            type=process.type,
            status=process.status,
            requested_at=process.requested_at,
            subscribers=[SubscriberProgressOut.from_domain(s) for s in process.subscribers],
        )


class SubscriberOut(BaseModel):
    name: str
    first_seen_at: datetime
    last_seen_at: datetime

    @classmethod
    def from_domain(cls, subscriber: Subscriber) -> SubscriberOut:
        return cls(
            name=subscriber.name,
            first_seen_at=subscriber.first_seen_at,
            last_seen_at=subscriber.last_seen_at,
        )
