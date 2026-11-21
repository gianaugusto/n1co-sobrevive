from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from aiokafka import AIOKafkaConsumer

from forgetme.application.use_cases import HandleFeedback
from forgetme.infrastructure.kafka.serialization import InvalidMessageError, feedback_from_bytes

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Turns one raw feedback message into a use-case call. Pure logic, no Kafka I/O."""

    def __init__(
        self, handler: HandleFeedback, max_attempts: int = 3, retry_delay: float = 1.0
    ) -> None:
        self._handler = handler
        self._max_attempts = max_attempts
        self._retry_delay = retry_delay

    async def process(self, raw: bytes) -> None:
        """Never raises: a bad message must not stop the consumer."""
        try:
            feedback = feedback_from_bytes(raw)
        except InvalidMessageError as error:
            logger.warning("Skipping malformed feedback message: %s", error)
            return
        for attempt in range(1, self._max_attempts + 1):
            try:
                await self._handler.execute(feedback)
                return
            except Exception:
                logger.exception(
                    "Handling feedback failed (attempt %s/%s)", attempt, self._max_attempts
                )
                if attempt < self._max_attempts:
                    await asyncio.sleep(self._retry_delay)
        logger.error("Giving up on feedback for process %s", feedback.process_id)


class KafkaFeedbackConsumer:
    """Background task that reads the feedback topic. Offsets commit after processing."""

    def __init__(
        self, bootstrap_servers: str, topic: str, group_id: str, processor: FeedbackProcessor
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._processor = processor
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        # aiokafka clients must be created inside the running event loop, not at wiring time.
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._run(self._consumer), name="feedback-consumer")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        if self._consumer is not None:
            await self._consumer.stop()

    async def _run(self, consumer: AIOKafkaConsumer) -> None:
        async for message in consumer:
            await self._processor.process(message.value or b"")
            await consumer.commit()
