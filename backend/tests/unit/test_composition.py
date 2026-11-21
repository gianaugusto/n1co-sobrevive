import pytest

from forgetme.config import Settings
from forgetme.main import build_app


def settings(**overrides) -> Settings:
    base = {
        "auth0_domain": "tenant.auth0.com",
        "auth0_audience": "https://api",
        "database_url": "sqlite+aiosqlite://",
    }
    return Settings(**{**base, **overrides})


def test_app_can_be_wired_outside_an_event_loop():
    """uvicorn --factory calls build_app before any loop runs; Kafka clients must be lazy."""
    app = build_app(settings())
    paths = set(app.openapi()["paths"])
    assert {"/health", "/api/v1/processes", "/api/v1/subscribers"} <= paths


def test_app_refuses_to_start_without_auth0_configuration():
    with pytest.raises(RuntimeError, match="AUTH0_DOMAIN"):
        build_app(settings(auth0_domain="", auth0_audience=""))
