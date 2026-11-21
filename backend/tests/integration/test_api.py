"""Full HTTP -> use cases -> database flow, with a fake broker and a fake token verifier."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from forgetme.api.app import create_app
from forgetme.api.auth import AuthError, Principal
from forgetme.api.routes import UseCases
from forgetme.application.use_cases import (
    CreateProcess,
    GetProcess,
    HandleFeedback,
    ListProcesses,
    ListSubscribers,
    RetrySubscriber,
)
from forgetme.domain.models import Feedback, FeedbackEvent
from tests.fakes import RecordingPublisher

pytestmark = pytest.mark.integration
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class StubVerifier:
    TOKENS = {
        "writer": Principal("u1", frozenset({"forget:read", "forget:write"})),
        "reader": Principal("u2", frozenset({"forget:read"})),
    }

    def verify(self, token: str) -> Principal:
        try:
            return self.TOKENS[token]
        except KeyError:
            raise AuthError("bad token") from None


@pytest.fixture
def publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def handle_feedback(uow_factory) -> HandleFeedback:
    return HandleFeedback(uow_factory)


@pytest.fixture
async def client(uow_factory, publisher):
    app = create_app(
        use_cases=UseCases(
            create_process=CreateProcess(uow_factory, publisher),
            get_process=GetProcess(uow_factory),
            list_processes=ListProcesses(uow_factory),
            list_subscribers=ListSubscribers(uow_factory),
            retry_subscriber=RetrySubscriber(uow_factory, publisher),
        ),
        verifier=StubVerifier(),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


WRITER = {"Authorization": "Bearer writer"}
READER = {"Authorization": "Bearer reader"}
BODY = {"tenant_id": "acme", "key": "jane@example.com", "type": "email"}


async def test_health_is_public(client):
    assert (await client.get("/health")).json() == {"status": "ok"}


async def test_create_process_returns_pending_process_and_publishes(client, publisher):
    response = await client.post("/api/v1/processes", json=BODY, headers=WRITER)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert (body["tenant_id"], body["key"], body["type"]) == ("acme", "jane@example.com", "email")
    assert body["subscribers"] == []
    assert str(publisher.messages[0].process_id) == body["id"]


async def test_full_flow_start_fail_retry_succeed(client, publisher, handle_feedback):
    created = (await client.post("/api/v1/processes", json=BODY, headers=WRITER)).json()
    pid = created["id"]
    from uuid import UUID

    async def feedback(subscriber, event, detail=None):
        await handle_feedback.execute(Feedback(UUID(pid), subscriber, event, NOW, detail))

    await feedback("billing", FeedbackEvent.STARTED)
    await feedback("crm", FeedbackEvent.STARTED)
    await feedback("billing", FeedbackEvent.SUCCEEDED)
    await feedback("crm", FeedbackEvent.FAILED, "timeout")

    detail = (await client.get(f"/api/v1/processes/{pid}", headers=READER)).json()
    assert detail["status"] == "FAILED"
    crm = next(s for s in detail["subscribers"] if s["name"] == "crm")
    assert crm["status"] == "FAILED"
    assert [r["event"] for r in crm["results"]] == ["STARTED", "FAILED"]
    assert crm["results"][1]["detail"] == "timeout"

    retry = await client.post(f"/api/v1/processes/{pid}/subscribers/crm/retry", headers=WRITER)
    assert retry.status_code == 202
    assert (publisher.messages[-1].target, publisher.messages[-1].attempt) == ("crm", 2)

    await feedback("crm", FeedbackEvent.STARTED)
    await feedback("crm", FeedbackEvent.SUCCEEDED)
    final = (await client.get(f"/api/v1/processes/{pid}", headers=READER)).json()
    assert final["status"] == "COMPLETED"


async def test_list_processes_and_subscribers(client, handle_feedback):
    from uuid import UUID

    pid = (await client.post("/api/v1/processes", json=BODY, headers=WRITER)).json()["id"]
    await handle_feedback.execute(Feedback(UUID(pid), "billing", FeedbackEvent.STARTED, NOW))

    processes = (await client.get("/api/v1/processes?limit=10", headers=READER)).json()
    subscribers = (await client.get("/api/v1/subscribers", headers=READER)).json()
    assert [p["id"] for p in processes] == [pid]
    assert [s["name"] for s in subscribers] == ["billing"]


@pytest.mark.parametrize(
    "body",
    [
        {**BODY, "type": "phone"},
        {**BODY, "tenant_id": "   "},
        {**BODY, "key": ""},
        {"tenant_id": "acme"},
    ],
)
async def test_create_validates_input(client, body):
    assert (await client.post("/api/v1/processes", json=body, headers=WRITER)).status_code == 422


async def test_unknown_process_is_404(client):
    assert (await client.get(f"/api/v1/processes/{uuid4()}", headers=READER)).status_code == 404


async def test_malformed_process_id_is_422(client):
    assert (await client.get("/api/v1/processes/not-a-uuid", headers=READER)).status_code == 422


async def test_retry_of_unknown_subscriber_is_404(client):
    pid = (await client.post("/api/v1/processes", json=BODY, headers=WRITER)).json()["id"]
    response = await client.post(f"/api/v1/processes/{pid}/subscribers/ghost/retry", headers=WRITER)
    assert response.status_code == 404


async def test_retry_of_running_subscriber_is_409(client, handle_feedback):
    from uuid import UUID

    pid = (await client.post("/api/v1/processes", json=BODY, headers=WRITER)).json()["id"]
    await handle_feedback.execute(Feedback(UUID(pid), "billing", FeedbackEvent.STARTED, NOW))
    response = await client.post(
        f"/api/v1/processes/{pid}/subscribers/billing/retry", headers=WRITER
    )
    assert response.status_code == 409


async def test_broker_failure_returns_503_and_keeps_process_pending(uow_factory):
    app = create_app(
        use_cases=UseCases(
            create_process=CreateProcess(uow_factory, RecordingPublisher(fail=True)),
            get_process=GetProcess(uow_factory),
            list_processes=ListProcesses(uow_factory),
            list_subscribers=ListSubscribers(uow_factory),
            retry_subscriber=RetrySubscriber(uow_factory, RecordingPublisher()),
        ),
        verifier=StubVerifier(),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        assert (await http.post("/api/v1/processes", json=BODY, headers=WRITER)).status_code == 503
        listed = (await http.get("/api/v1/processes", headers=READER)).json()
    assert [p["status"] for p in listed] == ["PENDING"]


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/v1/processes"),
        ("post", "/api/v1/processes"),
        ("get", f"/api/v1/processes/{uuid4()}"),
        ("get", "/api/v1/subscribers"),
        ("post", f"/api/v1/processes/{uuid4()}/subscribers/x/retry"),
    ],
)
async def test_every_endpoint_requires_a_token(client, method, path):
    assert (await getattr(client, method)(path)).status_code == 401


async def test_reader_cannot_write(client):
    response = await client.post("/api/v1/processes", json=BODY, headers=READER)
    assert response.status_code == 403
