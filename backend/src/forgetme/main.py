"""Composition root: the only place that wires concrete adapters to the application.

Run with: ``uvicorn forgetme.main:build_app --factory``
"""

from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from forgetme.api.app import create_app
from forgetme.api.auth import Auth0TokenVerifier
from forgetme.api.routes import UseCases
from forgetme.application.use_cases import (
    CreateProcess,
    GetProcess,
    HandleFeedback,
    ListProcesses,
    ListSubscribers,
    RetrySubscriber,
)
from forgetme.config import Settings, get_settings
from forgetme.infrastructure.db.repositories import SqlAlchemyUnitOfWork
from forgetme.infrastructure.db.session import create_engine, create_session_factory
from forgetme.infrastructure.kafka.consumer import FeedbackProcessor, KafkaFeedbackConsumer
from forgetme.infrastructure.kafka.publisher import KafkaRequestPublisher


class _EngineResource:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        await self._engine.dispose()


def build_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    if not settings.auth0_domain or not settings.auth0_audience:
        raise RuntimeError("AUTH0_DOMAIN and AUTH0_AUDIENCE must be set")

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    publisher = KafkaRequestPublisher(
        settings.kafka_bootstrap_servers, settings.kafka_requests_topic
    )
    consumer = KafkaFeedbackConsumer(
        settings.kafka_bootstrap_servers,
        settings.kafka_feedback_topic,
        settings.kafka_consumer_group,
        FeedbackProcessor(HandleFeedback(uow_factory)),
    )
    use_cases = UseCases(
        create_process=CreateProcess(uow_factory, publisher),
        get_process=GetProcess(uow_factory),
        list_processes=ListProcesses(uow_factory),
        list_subscribers=ListSubscribers(uow_factory),
        retry_subscriber=RetrySubscriber(uow_factory, publisher),
    )
    return create_app(
        use_cases=use_cases,
        verifier=Auth0TokenVerifier(settings.auth0_domain, settings.auth0_audience),
        cors_origins=settings.cors_origins,
        # Started in order, stopped in reverse: the consumer stops before the DB closes.
        resources=[_EngineResource(engine), publisher, consumer],
    )
