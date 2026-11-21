"""Integration fixtures.

By default tests run on in-memory SQLite so they work anywhere. Set ``DATABASE_URL`` to a
``postgresql+asyncpg://`` URL (CI does) to run the very same tests on PostgreSQL.
"""

import os
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from forgetme.infrastructure.db.orm import Base
from forgetme.infrastructure.db.repositories import SqlAlchemyUnitOfWork

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite://")


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    options = {"poolclass": StaticPool} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_async_engine(DATABASE_URL, **options)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def uow_factory(session_factory):
    return lambda: SqlAlchemyUnitOfWork(session_factory)
