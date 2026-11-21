# Subscriber guide

How to make your service take part in forget processes. The wire format is in [messaging-contract.md](messaging-contract.md).

## Checklist

1. Subscribe to `forget.requests` with **your own consumer group** (every subscriber needs every message).
2. Ignore messages whose `target` is set to another name, and `type`s you do not store.
3. Publish `STARTED` to `forget.feedback` (key = `process_id`).
4. Erase the data found through `key` (idempotently), for the given `tenant_id`.
5. Publish `SUCCEEDED`, or `FAILED` with a useful `detail`.

## Minimal example (Python, aiokafka)

```python
import json
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

NAME = "billing"

async def run(bootstrap: str) -> None:
    consumer = AIOKafkaConsumer("forget.requests", bootstrap_servers=bootstrap, group_id=f"{NAME}-forget")
    producer = AIOKafkaProducer(bootstrap_servers=bootstrap)
    await consumer.start(); await producer.start()

    async def report(request, event, detail=None):
        await producer.send_and_wait("forget.feedback", key=request["process_id"].encode(), value=json.dumps({
            "process_id": request["process_id"], "subscriber": NAME, "event": event,
            "occurred_at": datetime.now(timezone.utc).isoformat(), "detail": detail,
        }).encode())

    async for message in consumer:
        request = json.loads(message.value)
        if request["target"] not in (None, NAME):
            continue
        await report(request, "STARTED")
        try:
            deleted = await erase(request["tenant_id"], request["type"], request["key"])
            await report(request, "SUCCEEDED", f"{deleted} records erased")
        except Exception as error:
            await report(request, "FAILED", str(error))
```

## Common mistakes

- Sharing a consumer group with other subscribers: each would see only some requests.
- Forgetting `STARTED`: the process may complete without waiting for you.
- Using a different `subscriber` name on retries: it would appear as a new subscriber.
