"""Runs against a real broker. Skipped unless KAFKA_BOOTSTRAP_SERVERS is set.

Locally: ``docker compose up -d --wait kafka`` then
``KAFKA_BOOTSTRAP_SERVERS=localhost:9092 pytest tests/integration/test_kafka.py``.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from forgetme.application.use_cases import CreateProcess, GetProcess, HandleFeedback
from forgetme.domain.models import PiiType, ProcessStatus
from forgetme.infrastructure.kafka.consumer import FeedbackProcessor, KafkaFeedbackConsumer
from forgetme.infrastructure.kafka.publisher import KafkaRequestPublisher

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not BOOTSTRAP, reason="KAFKA_BOOTSTRAP_SERVERS not set"),
]


async def eventually(check, timeout: float = 30.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        result = await check()
        if result:
            return result
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("condition not met in time")
        await asyncio.sleep(0.5)


async def test_request_is_published_and_feedback_completes_the_process(uow_factory):
    suffix = uuid4().hex[:8]
    requests_topic, feedback_topic = f"test.requests.{suffix}", f"test.feedback.{suffix}"

    publisher = KafkaRequestPublisher(BOOTSTRAP, requests_topic)
    subscriber_side = AIOKafkaConsumer(
        requests_topic,
        bootstrap_servers=BOOTSTRAP,
        group_id=f"subscriber-{suffix}",
        auto_offset_reset="earliest",
    )
    feedback_producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    consumer = KafkaFeedbackConsumer(
        BOOTSTRAP,
        feedback_topic,
        f"orchestrator-{suffix}",
        FeedbackProcessor(HandleFeedback(uow_factory), retry_delay=0.1),
    )
    await publisher.start()
    await subscriber_side.start()
    await feedback_producer.start()
    await consumer.start()
    try:
        process = await CreateProcess(uow_factory, publisher).execute(
            "acme", "jane@example.com", PiiType.EMAIL
        )

        message = await asyncio.wait_for(subscriber_side.getone(), timeout=30)
        assert json.loads(message.value)["process_id"] == str(process.id)

        for event in ("STARTED", "SUCCEEDED"):
            await feedback_producer.send_and_wait(
                feedback_topic,
                key=str(process.id).encode(),
                value=json.dumps(
                    {
                        "process_id": str(process.id),
                        "subscriber": "billing",
                        "event": event,
                        "occurred_at": datetime.now(timezone.utc).isoformat(),
                    }
                ).encode(),
            )

        async def completed():
            current = await GetProcess(uow_factory).execute(process.id)
            return current.status is ProcessStatus.COMPLETED

        await eventually(completed)
    finally:
        await consumer.stop()
        await feedback_producer.stop()
        await subscriber_side.stop()
        await publisher.stop()
