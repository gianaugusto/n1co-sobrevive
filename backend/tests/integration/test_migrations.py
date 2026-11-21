import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration
BACKEND = Path(__file__).resolve().parents[2]


def test_migrations_create_every_mapped_table(tmp_path):
    from forgetme.infrastructure.db.orm import Base

    url = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'm.db'}")
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    try:
        command.upgrade(config, "head")
        sync_url = url.replace("+aiosqlite", "").replace("+asyncpg", "")
        tables = set(inspect(create_engine(sync_url)).get_table_names())
        assert set(Base.metadata.tables) <= tables
    finally:
        command.downgrade(config, "base")
