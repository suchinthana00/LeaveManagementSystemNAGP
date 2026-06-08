import json
import logging

import pika

from shared.config import get_settings


logger = logging.getLogger("leave-events")


def publish_event(event_type: str, payload: dict) -> None:
    settings = get_settings()
    body = json.dumps({"event_type": event_type, "payload": payload})
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=settings.rabbitmq_host, port=settings.rabbitmq_port)
        )
        channel = connection.channel()
        channel.queue_declare(queue=settings.rabbitmq_queue, durable=False)
        channel.basic_publish(exchange="", routing_key=settings.rabbitmq_queue, body=body)
        connection.close()
    except Exception as exc:  # pragma: no cover - infrastructure dependent
        logger.error("Failed to publish event %s: %s", event_type, exc)
