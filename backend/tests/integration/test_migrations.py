import asyncio
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from forgetme.infrastructure.db.orm import Base

pytestmark = pytest.mark.integration
BACKEND = Path(__file__).resolve().parents[2]


async def _table_names(url: str) -> set[str]:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as connection:
            return set(await connection.run_sync(lambda c: inspect(c).get_table_names()))
    finally:
        await engine.dispose()


def test_migrations_create_every_mapped_table(tmp_path):
    url = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'm.db'}")
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    try:
        command.upgrade(config, "head")
        assert set(Base.metadata.tables) <= asyncio.run(_table_names(url))
    finally:
        command.downgrade(config, "base")
