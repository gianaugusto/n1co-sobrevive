"""SQLAlchemy tables. They are an infrastructure detail: the domain never imports them."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Timezone-aware UTC datetimes on every database (SQLite drops the timezone)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naive datetimes are not accepted; use timezone-aware UTC")
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        aware: datetime = (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )
        return aware


class Base(DeclarativeBase):
    pass


class ProcessRow(Base):
    __tablename__ = "forget_processes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    key: Mapped[str] = mapped_column(String(512))
    type: Mapped[str] = mapped_column(String(32))
    requested_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)

    subscribers: Mapped[list[SubscriberProgressRow]] = relationship(
        back_populates="process", cascade="all, delete-orphan", order_by="SubscriberProgressRow.id"
    )


class SubscriberProgressRow(Base):
    __tablename__ = "process_subscribers"
    __table_args__ = (UniqueConstraint("process_id", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[UUID] = mapped_column(ForeignKey("forget_processes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    attempt: Mapped[int] = mapped_column(Integer, default=1)

    process: Mapped[ProcessRow] = relationship(back_populates="subscribers")
    results: Mapped[list[ResultRow]] = relationship(
        back_populates="subscriber", cascade="all, delete-orphan", order_by="ResultRow.id"
    )


class ResultRow(Base):
    __tablename__ = "subscriber_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_subscriber_id: Mapped[int] = mapped_column(
        ForeignKey("process_subscribers.id", ondelete="CASCADE"), index=True
    )
    event: Mapped[str] = mapped_column(String(16))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime)

    subscriber: Mapped[SubscriberProgressRow] = relationship(back_populates="results")


class SubscriberRow(Base):
    __tablename__ = "subscribers"

    name: Mapped[str] = mapped_column(String(128), primary_key=True)
    first_seen_at: Mapped[datetime] = mapped_column(UTCDateTime)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime)
