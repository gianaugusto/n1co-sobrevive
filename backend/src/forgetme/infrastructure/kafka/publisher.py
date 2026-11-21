from __future__ import annotations

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from forgetme.application.ports import ForgetRequestMessage
from forgetme.domain.errors import PublishError
from forgetme.infrastructure.kafka.serialization import request_to_bytes


class KafkaRequestPublisher:
    """Publishes forget requests. Keyed by process id so one process stays ordered."""

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        # aiokafka clients must be created inside the running event loop, not at wiring time.
        self._producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap_servers)
        await self._producer.start()

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()

    async def publish_request(self, message: ForgetRequestMessage) -> None:
        if self._producer is None:
            raise PublishError("Kafka publisher is not started")
        try:
            await self._producer.send_and_wait(
                self._topic, value=request_to_bytes(message), key=str(message.process_id).encode()
            )
        except KafkaError as error:
            raise PublishError(f"Could not publish to '{self._topic}': {error}") from error
