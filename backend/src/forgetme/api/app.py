from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Protocol

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from forgetme.api.auth import TokenVerifier
from forgetme.api.routes import UseCases, router
from forgetme.domain.errors import (
    DomainError,
    ProcessNotFoundError,
    PublishError,
    RetryNotAllowedError,
    SubscriberNotFoundError,
)


class Lifecycle(Protocol):
    """Something started with the app and stopped with it (Kafka clients, DB engine)."""

    async def start(self) -> None: ...

    async def stop(self) -> None: ...


_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    ProcessNotFoundError: 404,
    SubscriberNotFoundError: 404,
    RetryNotAllowedError: 409,
    PublishError: 503,
}


async def _handle_domain_error(request: Request, error: Exception) -> JSONResponse:
    code = next((c for cls, c in _STATUS_BY_ERROR.items() if isinstance(error, cls)), 400)
    return JSONResponse({"detail": str(error)}, status_code=code)


def create_app(
    *,
    use_cases: UseCases,
    verifier: TokenVerifier,
    cors_origins: Sequence[str] = (),
    resources: Sequence[Lifecycle] = (),
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        started: list[Lifecycle] = []
        try:
            for resource in resources:
                await resource.start()
                started.append(resource)
            yield
        finally:
            for resource in reversed(started):
                await resource.stop()

    app = FastAPI(title="forgetme-services", version="0.1.0", lifespan=lifespan)
    app.state.use_cases = use_cases
    app.state.verifier = verifier
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.include_router(router)
    return app
