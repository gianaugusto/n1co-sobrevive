"""Runtime configuration, read from environment variables (or a local ``.env`` file)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://forgetme:forgetme@localhost:5432/forgetme"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_requests_topic: str = "forget.requests"
    kafka_feedback_topic: str = "forget.feedback"
    kafka_consumer_group: str = "forgetme-orchestrator"

    auth0_domain: str = ""
    auth0_audience: str = ""

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
